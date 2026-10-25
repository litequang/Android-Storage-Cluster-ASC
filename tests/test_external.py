"""External archive safety tests use actual private temporary filesystem IO."""
import copy
from contextlib import contextmanager
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from asc.catalog.common import CatalogError, canonical, digest, uid
from asc.catalog.state import Catalog, insert
from asc.failover import state
from asc.external.engine import BackupEngine, load
from asc.external.local import LocalStore, Tree
from asc.external.format import capture, validate


class MemorySource:
    """Unit-only authority fake; real quorum/TLS acceptance is a separate suite."""
    def __init__(self):
        self.reg=state.MemoryRegistry(uid());self.bodies={};self.fail_read=False
        for n,data in enumerate((b'old version\0'*9000,b'new retained bytes\0'*6000)):
            file_id=uid();self.bodies[file_id]=data
            insert(self.reg.db,'catalog_files',{'file_id':file_id,'logical_path':'versions/a.bin',
                'version':n+1,'size':len(data),'sha256':hashlib.sha256(data).hexdigest(),
                'policy':'replicated_2','created_at':10,'updated_at':10,'revision':0,
                'upload_key':'external-test-'+str(n),'upload_policy':'replicated_2'})
            insert(self.reg.db,'catalog_replicas',{'replica_id':uid(),'file_id':file_id,
                'node_id':uid(),'volume_id':uid(),'local_file_id':uid(),'state':'VERIFIED',
                'created_at':10,'updated_at':10,'verified_at':10})
            Catalog(self.reg)._event(self.reg.db,file_id)
        self.doc=state.export(self.reg.db,1,{'node_id':'test-voter','term':4})
        self.ready=True;self.reads=[]

    def close(self):self.reg.db.close()
    def capture(self):
        if not self.ready:raise CatalogError('controller_not_ready',503)
        return {'document':copy.deepcopy(self.doc),'state':{'index':100,'term':4,'document_sha256':digest(self.doc)}}
    @contextmanager
    def stream(self,file,manifest):
        self.reads.append(file['file_id'])
        if self.fail_read:raise OSError('synthetic interrupted source')
        yield io.BytesIO(self.bodies[file['file_id']])
    def revalidate(self,manifest):
        if not self.ready:raise CatalogError('controller_not_ready',503)


class ExternalBackupTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='asc-external-test-');self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name);self.source_root=self.base/'source';self.source_root.mkdir(mode=0o700)
        self.dest=self.base/'external';self.dest.mkdir(mode=0o700)
        self.source=MemorySource();self.addCleanup(self.source.close)
        self.roots=[self.source_root];self.store=LocalStore.initialize(self.dest,self.roots)
        self.engine=BackupEngine(self.store)

    def pending(self):
        return next((self.dest/'working').iterdir()).name

    def test_exact_all_versions_stream_sha_fsync_and_immutable_replay(self):
        before=copy.deepcopy(self.source.doc)
        result=self.engine.create(self.source,self.roots);root=self.dest/'completed'/result['backup_id']
        self.assertEqual(result['state'],'COMPLETE');self.assertEqual(result['objects'],2)
        with Tree(root) as tree:
            manifest,metadata,doc=load(tree)
        self.assertEqual(doc,before);self.assertEqual(metadata,canonical(before))
        self.assertEqual(result['manifest_sha256'],digest(manifest));self.assertFalse(manifest['writer_recovery_supported'])
        for file_id,data in self.source.bodies.items():self.assertEqual((root/'objects'/(file_id+'.blob')).read_bytes(),data)
        files={p.name:p.read_bytes() for p in root.rglob('*') if p.is_file()}
        reads=len(self.source.reads)
        replay=self.engine.resume(self.source,result['backup_id'],self.roots)
        self.assertTrue(replay['replayed']);self.assertEqual(len(self.source.reads),reads)
        self.assertEqual(files,{p.name:p.read_bytes() for p in root.rglob('*') if p.is_file()})
        self.assertEqual(self.source.doc,before)

    def test_interrupted_source_and_resume_rehash_no_duplicate_objects(self):
        self.source.fail_read=True
        with self.assertRaises(OSError):self.engine.create(self.source,self.roots)
        backup_id=self.pending();self.assertEqual(list((self.dest/'completed').iterdir()),[])
        self.source.fail_read=False
        result=self.engine.resume(self.source,backup_id,self.roots)
        self.assertEqual(result['backup_id'],backup_id)
        self.assertEqual(len(list((self.dest/'completed'/backup_id/'objects').iterdir())),2)

    def test_final_authority_loss_never_publishes_complete_and_resume_uses_same_capture(self):
        real=self.source.revalidate
        def lost(manifest):self.source.ready=False;return real(manifest)
        self.source.revalidate=lost
        with self.assertRaises(CatalogError):self.engine.create(self.source,self.roots)
        backup_id=self.pending();snapshot=(self.dest/'working'/backup_id/'manifest.json').read_bytes()
        self.assertFalse((self.dest/'working'/backup_id/'complete.json').exists())
        self.source.ready=True;self.source.revalidate=real
        self.engine.resume(self.source,backup_id,self.roots)
        self.assertEqual(snapshot,(self.dest/'completed'/backup_id/'manifest.json').read_bytes())

    def test_corrupt_source_and_missing_pending_upload_prevent_complete(self):
        file_id=next(iter(self.source.bodies));self.source.bodies[file_id]=b'bad'
        with self.assertRaises(CatalogError):self.engine.create(self.source,self.roots)
        self.assertFalse(list((self.dest/'completed').iterdir()))
        self.source.bodies.pop(file_id)
        with self.assertRaises(KeyError):self.engine.resume(self.source,self.pending(),self.roots)

    def test_resume_never_overwrites_corrupt_published_object(self):
        real=self.source.revalidate
        self.source.revalidate=mock.Mock(side_effect=CatalogError('controller_not_ready',503))
        with self.assertRaises(CatalogError):self.engine.create(self.source,self.roots)
        backup_id=self.pending();body=next((self.dest/'working'/backup_id/'objects').glob('*.blob'))
        body.write_bytes(b'corrupt external body')
        self.source.revalidate=real
        with self.assertRaises(CatalogError):self.engine.resume(self.source,backup_id,self.roots)
        self.assertEqual(body.read_bytes(),b'corrupt external body');self.assertFalse(list((self.dest/'completed').iterdir()))

    def test_overlap_public_directory_symlink_hardlink_and_traversal_refused(self):
        for dest,roots in [(self.source_root,[self.source_root]),(self.source_root/'child',[self.source_root]),(self.base,[self.source_root])]:
            with self.subTest(dest=dest),self.assertRaises(CatalogError):LocalStore.initialize(dest,roots)
        public=self.base/'public';public.mkdir(mode=0o755);public.chmod(0o755)
        with self.assertRaises(CatalogError):LocalStore.initialize(public,self.roots)
        link=self.base/'link';link.symlink_to(self.dest,target_is_directory=True)
        with self.assertRaises(CatalogError):
            with LocalStore(link).open():pass
        with self.assertRaises(CatalogError):self.engine.resume(self.source,'../outside',self.roots)
        marker=self.dest/'store.json';outside=self.base/'linked';os.link(marker,outside)
        with self.assertRaises(CatalogError):
            with self.store.open():pass

    def test_root_replacement_during_write_never_redirects_and_never_completes(self):
        real=self.source.stream
        @contextmanager
        def swapped(file,manifest):
            if self.dest.exists():
                self.dest.rename(self.base/'moved');self.dest.mkdir(mode=0o700)
            with real(file,manifest) as stream:yield stream
        self.source.stream=swapped
        with self.assertRaises(CatalogError):self.engine.create(self.source,self.roots)
        self.assertEqual(list(self.dest.iterdir()),[])
        self.assertFalse(list((self.base/'moved'/'completed').iterdir()))

    def test_snapshot_mismatch_future_format_and_changed_metadata_rejected(self):
        manifest,metadata=capture(self.source.capture(),uid(),10)
        for mutation in (lambda m:m.update(format=2),lambda m:m['files'].pop(),lambda m:m.update(source_index=True),lambda m:m.update(metadata_sha256='0'*64)):
            changed=copy.deepcopy(manifest);mutation(changed)
            with self.subTest(changed=changed['format']),self.assertRaises(CatalogError):validate(changed,metadata)
        with self.assertRaises(CatalogError):validate(manifest,metadata+b'\n')

    def test_disk_full_fsync_failure_does_not_publish_and_keeps_sources(self):
        before=copy.deepcopy(self.source.bodies)
        real=os.fsync;calls=0
        def disk_full(fd):
            nonlocal calls
            calls+=1
            if calls==9:raise OSError(28,'synthetic disk full')
            return real(fd)
        with mock.patch('asc.external.local.os.fsync',side_effect=disk_full),self.assertRaises(OSError):
            self.engine.create(self.source,self.roots)
        self.assertEqual(self.source.bodies,before);self.assertFalse(list((self.dest/'completed').iterdir()))

    def test_double_owner_refused_and_identity_marker_not_recreated(self):
        with self.store.open():
            with self.assertRaises(CatalogError):
                with self.store.open():pass
        (self.dest/'store.json').unlink()
        with self.assertRaises(FileNotFoundError):
            with self.store.open():pass
        self.assertFalse((self.dest/'store.json').exists())

    def test_crash_after_atomic_link_resumes_exact_owned_partial(self):
        with mock.patch('asc.external.local.Tree.finish_link',side_effect=RuntimeError('synthetic process death')):
            with self.assertRaises(RuntimeError):self.engine.create(self.source,self.roots)
        backup_id=self.pending();objects=self.dest/'working'/backup_id/'objects'
        final=next(objects.glob('*.blob'));part=next(objects.glob('*.part'))
        self.assertEqual(final.stat().st_ino,part.stat().st_ino)
        self.engine.resume(self.source,backup_id,self.roots)
        self.assertEqual(len(list((self.dest/'completed'/backup_id/'objects').iterdir())),2)
        self.assertTrue(all(p.stat().st_nlink==1 for p in (self.dest/'completed'/backup_id/'objects').iterdir()))
