"""Actual Linux synthetic Raft/TLS/process/IO disaster archive fault matrix."""
from contextlib import contextmanager
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest
from unittest import mock

from asc.catalog.client import ClusterClient
from asc.catalog.common import CatalogError, canonical, digest, uid
from asc.client import ClientError
from asc.external.engine import BackupEngine
from asc.external.local import Tree
from asc.external.source import PinnedSource
from asc.external.verify import inventory, verify, retention_preview
from asc.external.recovery import stage, verify_stage
from tests import test_external_cluster as fixture


class ExternalFaultTests(fixture.ExternalFixture,unittest.TestCase):
    def mark(self,n,label):print(f'Phase3D {n:02d} PASS: {label}',flush=True)

    def assert_bundle(self,store,result,data):
        report=verify(store,result['backup_id'],result['manifest_sha256'],0,self.cluster)
        self.assertEqual(report['state'],'VERIFIED')
        folder=store.path/'completed'/result['backup_id']
        for file_id,body in data.items():
            self.assertEqual((folder/'objects'/(file_id+'.blob')).read_bytes(),body)
        return folder

    def test_real_tls_offline_corruption_authority_crash_resume_and_readonly_disaster_staging(self):
        self.make_cluster();owner=self.owner
        owner.request('POST','backup/enable',{'request_id':uid()})
        owner.request('POST','nodes/enable',{'request_id':uid()})
        owner.request('POST','replication/enable',{'request_id':uid()})
        originals={}
        for version in (1,2):
            data=(b'phase3d retained version '+str(version).encode()+b'\0')*2500
            uploaded=owner.upload(io.BytesIO(data),'dr/fault-versions.bin','dr-fault-version-'+str(version),'replicated_3',version)
            if uploaded['job_state']!='COMPLETED':self.wait_job(uploaded['job_id'])
            file_id=uploaded['file']['file']['file_id'];self.wait_copies(file_id,3);originals[file_id]=data
            owner.request('POST','backup/snapshots',{'request_id':uid(),'copies':3})
        old_file=next(iter(originals))
        owner.request('POST','backup/delete',{'request_id':uid(),'file_id':old_file})
        store,roots=self.external_store();engine=BackupEngine(store);source=PinnedSource(owner)
        baseline=engine.create(source,roots);folder=self.assert_bundle(store,baseline,originals)
        exact=(folder/'metadata.json').read_bytes();doc=json.loads(exact)
        self.assertEqual(set(doc)&{'backup','insights','replication'},{'backup','insights','replication'})
        self.assertEqual(len(doc['backup']['snapshots']),2)
        self.mark(1,'exact-source runtime2/all extensions/two versions/snapshot/TRASH and SHA bytes')

        # Capture is a point, not a moving list: a real new upload while exporting
        # does not relabel the old snapshot as latest history or omit captured IDs.
        parent=self
        class ChangingSource(PinnedSource):
            changed=False
            def streams(inner,file,manifest):
                if not inner.changed:
                    inner.changed=True
                    result=owner.upload(io.BytesIO(b'later committed bytes'),'dr/later.bin','dr-later-upload','replicated_2')
                    if result['job_state']!='COMPLETED':parent.wait_job(result['job_id'])
                    inner.new_id=result['file']['file']['file_id'];parent.wait_copies(inner.new_id,2)
                return super().streams(file,manifest)
        changing=ChangingSource(owner);point=engine.create(changing,roots)
        captured=json.loads((store.path/'completed'/point['backup_id']/'manifest.json').read_bytes())
        self.assertNotIn(changing.new_id,{f['file_id'] for f in captured['files']})
        current=owner.request('POST','external/capture',{})['capture']['state']['index']
        self.assertEqual(verify(store,point['backup_id'],point['manifest_sha256'],current)['state'],'STALE')
        originals[changing.new_id]=b'later committed bytes'
        self.mark(2,'source changes during backup retain exact captured history; newer known index reports STALE')

        # Actual all-voter partition AFTER bytes, BEFORE final current-authority
        # check. The direct endpoint prevents retry discovery hiding rejection.
        leader=self.wait_ready();e=self.endpoints[leader]
        direct=ClusterClient(e['origin'],e['pin'],e['token'])
        class PartitionAtFinal(PinnedSource):
            def revalidate(inner,manifest):
                parent.split([{0},{1},{2}])
                try:
                    with parent.assertRaises(ClientError) as denied:super().revalidate(manifest)
                    parent.assertGreaterEqual(denied.exception.status,400)
                    parent.denial_seen=True
                    raise ClientError('actual quorum denied',503)
                finally:pass
        before=set(p.name for p in (store.path/'working').iterdir())
        self.denial_seen=False
        with self.assertRaises(ClientError):engine.create(PartitionAtFinal(direct),roots)
        self.assertTrue(self.denial_seen)
        pending=(set(p.name for p in (store.path/'working').iterdir())-before).pop()
        self.assertFalse((store.path/'working'/pending/'complete.json').exists())
        self.assertEqual(list((store.path/'working'/pending/'objects').glob('*.part')),[])
        self.split([set(range(3))]);self.wait_ready()
        resumed=engine.resume(source,pending,roots);self.assert_bundle(store,resumed,originals)
        for known in originals:self.wait_copies(known,3 if known!=changing.new_id else 2)
        self.mark(3,'real lost quorum before final gate denies COMPLETE; heal and same capture resume')

        # Kill actual Controller AND its voter at final gate. All external bytes
        # survive, but dead endpoint cannot publish. New legitimate term can resume.
        leader=self.wait_ready();e=self.endpoints[leader];direct=ClusterClient(e['origin'],e['pin'],e['token'])
        old_term=int(self.clients[leader].status()['term'])
        parent.crash_seen=False
        class CrashController(PinnedSource):
            def revalidate(inner,manifest):
                parent.crash_seen=True
                parent.kill_python(leader);parent.stop(leader,crash=True)
                return super().revalidate(manifest)
        before=set(p.name for p in (store.path/'working').iterdir())
        try:engine.create(CrashController(direct),roots)
        except (ClientError,CatalogError,OSError) as exc:
            failure=(type(exc).__name__,getattr(exc,'code',None))
        else:self.fail('actual crash must reject final endpoint')
        pending=(set(p.name for p in (store.path/'working').iterdir())-before).pop()
        for attempt in range(5):
            if parent.crash_seen:break
            for known in originals:self.wait_copies(known,3 if known!=changing.new_id else 2)
            try:engine.resume(CrashController(direct),pending,roots)
            except (ClientError,CatalogError,OSError) as exc:failure=(type(exc).__name__,getattr(exc,'code',None))
        self.assertTrue(parent.crash_seen,'must reach actual final crash hook; earlier denial is not crash evidence: '+str(failure))
        self.assertIsNone(self.python[leader]);self.assertIsNone(self.processes[leader])
        self.assertFalse((store.path/'working'/pending/'complete.json').exists())
        new=self.wait_ready(exclude=(leader,));self.assertGreater(int(self.clients[new].status()['term']),old_term)
        resumed=engine.resume(source,pending,roots);self.assert_bundle(store,resumed,originals)
        self.start(leader);self.partition(leader,True);self.launch_python(leader)
        with self.assertRaises(ClientError):self.direct(leader,'POST','/catalog/v1/external/capture',{})
        with self.assertRaises(ClientError):self.direct(leader,'POST','/catalog/v1/external/check',
            {'cluster_id':self.cluster,'epoch':self.epoch,'source_index':baseline['source_index']})
        with self.assertRaises(ClientError):self.direct(leader,'POST','/catalog/v1/uploads',
            {'idempotency_key':'dr-stale-writer-key','logical_path':'dr/stale-writer.bin',
             'size':1,'sha256':hashlib.sha256(b'x').hexdigest(),'policy':'single'})
        self.partition(leader,False);self.wait_ready()
        self.assertNotIn('dr/stale-writer.bin',{f['logical_path'] for f in self.cached(self.wait_ready())['document']['catalog']['files']})
        self.mark(4,'actual Controller/voter crash, higher-term resume; isolated former Leader cannot export/authorize')

        # Black-box CLI worker terminates at an actual durable object boundary.
        # No product fault switch; only this child test wraps original publish.
        private=self.base/'operator';private.mkdir(mode=0o700)
        config=private/'cluster-client.json';config.write_bytes(canonical({'cluster_id':self.cluster,'controllers':self.endpoints}))
        config.chmod(0o600)
        args=['--store',str(store.path),'--owner-config',str(config)]
        for root in roots:args+=['--source-root',str(root)]
        script=("import os; from asc.external.local import Tree; from asc.external.cli import main; "
            "original=Tree.publish; "
            "exec('def crash(self,part,final):\\n original(self,part,final)\\n os._exit(91)'); "
            "Tree.publish=crash; main()")
        # Use real newline escape interpreted by exec in child code.
        script=script.replace('\\\\n','\\n')
        before=set(p.name for p in (store.path/'working').iterdir())
        process=subprocess.run([sys.executable,'-B','-c',script,'create',*args],cwd=fixture.fixture.ROOT,
            stdin=subprocess.DEVNULL,capture_output=True,timeout=120)
        self.assertEqual(process.returncode,91,'must observe actual exit91 after original durable publish')
        pending=(set(p.name for p in (store.path/'working').iterdir())-before).pop()
        objects=store.path/'working'/pending/'objects';first=next(objects.glob('*.blob'));inode=first.stat().st_ino
        self.assertFalse((store.path/'working'/pending/'complete.json').exists())
        retry=subprocess.run([sys.executable,'-B','-m','asc.external.cli','resume','--backup-id',pending,*args],
            cwd=fixture.fixture.ROOT,stdin=subprocess.DEVNULL,capture_output=True,timeout=120)
        self.assertEqual(retry.returncode,0,'normal CLI resume must finish actual process-crash state')
        replayed=json.loads(retry.stdout);self.assert_bundle(store,replayed,originals)
        self.assertEqual((store.path/'completed'/pending/'objects'/first.name).stat().st_ino,inode)
        self.mark(5,'actual backup process exit91, durable journal/object boundary, normal CLI resume without duplicate objects')

        # Inject explicit ENOSPC at a real object fsync while using actual TLS/IO.
        real_fsync=os.fsync;seen=False
        def no_space(fd):
            nonlocal seen
            try:path=os.readlink('/proc/self/fd/'+str(fd))
            except OSError:path=''
            if '/private-external/working/' in path and path.endswith('.part'):
                seen=True;raise OSError(28,'synthetic ENOSPC')
            return real_fsync(fd)
        before=set(p.name for p in (store.path/'working').iterdir())
        with mock.patch('asc.external.engine.os.fsync',side_effect=no_space),self.assertRaises(CatalogError):engine.create(source,roots)
        self.assertTrue(seen)
        pending=(set(p.name for p in (store.path/'working').iterdir())-before).pop()
        self.assertFalse((store.path/'working'/pending/'complete.json').exists())
        fixed=engine.resume(source,pending,roots);self.assert_bundle(store,fixed,originals)
        self.mark(6,'explicit ENOSPC fault at actual object fsync denies COMPLETE; retry preserves source and Backup ID')

        # An offline storage cohost and actual damaged independent replica must
        # not prevent using the third real independently approved healthy source.
        leader=self.wait_ready();offline=(leader+1)%3;damaged=(leader+2)%3
        self.kill_python(offline);self.stop(offline,crash=True);self.wait_ready(exclude=(offline,))
        report=owner.request('GET','files/'+old_file+'?consistency=strong')
        corrupt=next(r for r in report['replicas'] if r['node_id']==self.nodes[damaged]['node_id'])
        corrupt_body=self.base/('volume-'+str(damaged))/'objects'/(corrupt['local_file_id']+'.blob')
        corrupt_body.write_bytes(b'actually corrupt synthetic source')
        healthy=engine.create(source,roots);self.assert_bundle(store,healthy,originals)
        self.assertEqual(corrupt_body.read_bytes(),b'actually corrupt synthetic source')
        self.assertEqual(retention_preview(store)['physical_deletions'],0)
        self.mark(7,'actual offline node +corrupt source; third healthy source SHA fallback, corrupt/last/retained bytes not deleted')

        # Pending owner upload has a real Catalog/job but no verified bytes.
        size=13;owner.request('POST','uploads',{'idempotency_key':'dr-missing-pending','logical_path':'dr/pending.bin',
            'size':size,'sha256':hashlib.sha256(b'never sent!!!').hexdigest(),'policy':'replicated_2'})
        before=set(p.name for p in (store.path/'working').iterdir())
        with self.assertRaises((CatalogError,ClientError)):engine.create(source,roots)
        pending=(set(p.name for p in (store.path/'working').iterdir())-before).pop()
        self.assertFalse((store.path/'working'/pending/'complete.json').exists())
        self.mark(8,'actual pending upload without bytes is INCOMPLETE, never silently omitted')

        # Total live authority loss cannot promote the archive. Offline staging
        # still verifies/copies original historical identity and every captured body.
        for i in range(3):self.kill_python(i)
        self.stop_all()
        recovered=self.base/'recovery-without-cluster';recovered.mkdir(mode=0o700)
        stage_result=stage(store,baseline['backup_id'],baseline['manifest_sha256'],recovered,roots,self.cluster,baseline['source_index'])
        self.assertEqual(stage_result['state'],'VERIFIED_RECOVERY_STAGING')
        self.assertFalse(stage_result['writer_authority']);self.assertFalse(stage_result['credentials_restored'])
        self.assertEqual((recovered/'metadata.json').read_bytes(),exact)
        self.assertEqual(verify_stage(recovered,baseline['manifest_sha256'])['objects'],2)
        for file_id,data in list(originals.items())[:2]:
            self.assertEqual(hashlib.sha256((recovered/'objects'/(file_id+'.blob')).read_bytes()).hexdigest(),hashlib.sha256(data).hexdigest())
        # Completion reply loss is replay of an historical archive, not permission
        # to produce new backup or write metadata without a cluster.
        self.assertTrue(engine.resume(source,baseline['backup_id'],roots)['replayed'])
        with self.assertRaises((CatalogError,ClientError,OSError)):engine.create(source,roots)
        self.assertEqual(retention_preview(store)['physical_deletions'],0)
        self.mark(9,'all live authority absent: offline exact read-only recovery only, no credentials/writer/GC; completed ACK replay safe')
