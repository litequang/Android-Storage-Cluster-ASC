"""Real isolated staging IO, passive identity preservation and crash/resume."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import unittest
from unittest import mock

from asc.catalog.common import CatalogError, canonical, uid
from asc.external.cli import main
from asc.external.recovery import stage, verify_stage
from asc.external.local import Tree
from tests import test_external as fixture


class ExternalRecoveryTests(unittest.TestCase):
    setUp=fixture.ExternalBackupTests.setUp

    def prepare(self):
        result=self.engine.create(self.source,self.roots)
        dest=self.base/'isolated-recovery';dest.mkdir(mode=0o700)
        return result,dest

    def recover(self,result,dest,**kwargs):
        args=dict(store=self.store,backup_id=result['backup_id'],expected_sha256=result['manifest_sha256'],
            destination=dest,source_roots=self.roots,cluster_id=self.source.doc['cluster_id'],minimum_index=100)
        args.update(kwargs);return stage(**args)

    def test_exact_metadata_and_bytes_preserve_ids_without_any_live_authority(self):
        result,dest=self.prepare();before=canonical(self.source.doc)
        report=self.recover(result,dest)
        self.assertEqual(report['state'],'VERIFIED_RECOVERY_STAGING');self.assertFalse(report['writer_authority'])
        self.assertFalse(report['credentials_restored']);self.assertEqual((dest/'metadata.json').read_bytes(),before)
        for file_id,data in self.source.bodies.items():self.assertEqual((dest/'objects'/(file_id+'.blob')).read_bytes(),data)
        for name in ('registry.sqlite3','controller.json','node.json','storage.json','raft-state','.asc-volume.json'):
            self.assertFalse((dest/name).exists())
        self.assertEqual(verify_stage(dest,result['manifest_sha256'])['objects'],2)
        self.assertTrue(self.recover(result,dest)['replayed'])
        self.assertEqual(canonical(self.source.doc),before)

    def test_stale_wrong_cluster_anchor_and_corrupt_backup_touch_no_recovery_data(self):
        result,dest=self.prepare()
        for changed in ({'minimum_index':101},{'cluster_id':uid()},{'expected_sha256':'0'*64}):
            with self.subTest(changed=changed),self.assertRaises(CatalogError):self.recover(result,dest,**changed)
            self.assertFalse(list(dest.iterdir()))
        body=next((self.dest/'completed'/result['backup_id']/'objects').iterdir());body.write_bytes(b'bad')
        with self.assertRaises(CatalogError):self.recover(result,dest)
        self.assertFalse(list(dest.iterdir()))

    def test_nonempty_active_source_store_and_symlink_destinations_refused(self):
        result,dest=self.prepare();active=dest/'controller.json';active.write_text('synthetic active state')
        with self.assertRaises(CatalogError):self.recover(result,dest)
        self.assertEqual(active.read_text(),'synthetic active state')
        self.assertEqual([p.name for p in dest.iterdir()],['controller.json'])
        for forbidden in (self.source_root,self.dest,self.dest/'new'):
            with self.subTest(forbidden=forbidden),self.assertRaises(CatalogError):self.recover(result,forbidden)
        link=self.base/'recovery-link';link.symlink_to(dest,target_is_directory=True)
        with self.assertRaises(CatalogError):self.recover(result,link)

    def test_interrupted_staging_resumes_same_exact_intent_and_retains_completed_objects(self):
        result,dest=self.prepare();real=Tree.publish;calls=0
        def interrupted(tree,part,final):
            nonlocal calls
            calls+=1
            if calls==2:raise RuntimeError('synthetic power interruption')
            return real(tree,part,final)
        with mock.patch.object(Tree,'publish',interrupted),self.assertRaises(RuntimeError):self.recover(result,dest)
        self.assertFalse((dest/'READY.json').exists());first=next((dest/'objects').glob('*.blob'));inode=first.stat().st_ino
        with self.assertRaises(CatalogError):self.recover(result,dest,minimum_index=99)
        self.recover(result,dest)
        self.assertEqual(first.stat().st_ino,inode);self.assertEqual(len(list((dest/'objects').iterdir())),2)
        self.assertEqual(verify_stage(dest,result['manifest_sha256'])['state'],'VERIFIED_RECOVERY_STAGING')

    def test_missing_identity_or_modified_staged_metadata_is_never_verified(self):
        result,dest=self.prepare();self.recover(result,dest)
        data=json.loads((dest/'metadata.json').read_bytes());data.pop('authority')
        (dest/'metadata.json').write_bytes(canonical(data))
        with self.assertRaises(CatalogError):verify_stage(dest,result['manifest_sha256'])
        with self.assertRaises(CatalogError):self.recover(result,dest)
        self.assertNotIn('authority',json.loads((dest/'metadata.json').read_bytes()))

    def test_cli_stage_has_no_activate_option_and_roundtrips_passive_bytes(self):
        result,dest=self.prepare();out=io.StringIO()
        with redirect_stdout(out):
            code=main(['stage','--store',str(self.dest),'--backup-id',result['backup_id'],
                '--expected-sha256',result['manifest_sha256'],'--destination',str(dest),
                '--source-root',str(self.source_root),'--cluster-id',self.source.doc['cluster_id'],'--minimum-index','100'])
        self.assertEqual(code,0);self.assertFalse(json.loads(out.getvalue())['writer_authority'])
        self.assertEqual(verify_stage(dest,result['manifest_sha256'])['state'],'VERIFIED_RECOVERY_STAGING')
