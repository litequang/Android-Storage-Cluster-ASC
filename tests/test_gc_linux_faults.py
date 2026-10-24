"""Actual Linux-only TLS/quorum/unlink faults on newly issued synthetic arenas."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing, contextmanager
import copy
import io
import json
import os
import sqlite3
import time
import unittest

from asc.catalog.common import CatalogError, uid
from asc.client import ClientError
from asc.storage.client import StorageClient
from tests.test_gc_faults import GCFixture
from tests import test_backup as backup_fixture


@unittest.skipUnless(os.name=='posix','Linux synthetic physical executor required')
class LinuxGCPhysicalTests(GCFixture,unittest.TestCase):
    wait_backup=backup_fixture.BackupClusterTests.wait_backup
    backup_job=backup_fixture.BackupClusterTests.backup_job

    def setUp(self):
        # Separate state per test; only compiled fixture binaries are shared.
        self.base=type(self).base/uid();self.base.mkdir()

    def mark(self,number,label):
        print(f'\nLinux GC {number:02d} PASS: {label}',flush=True)

    def target(self):
        self.make_cluster()
        self.owner.request('POST','nodes/enable',{'request_id':uid()});self.post('enable')
        deadline=time.monotonic()+45
        while time.monotonic()<deadline:
            status=self.owner.request('GET','nodes')
            if len(status['nodes'])==3 and all(n['last_error'] is None for n in status['nodes']):break
            time.sleep(.2)
        self.assertEqual(len(status['nodes']),3)
        self.assertTrue(all(n['last_error'] is None for n in status['nodes']))
        data=b'Linux isolated physical boundary original bytes\0'*64
        uploaded=self.owner.upload(io.BytesIO(data),'linux-gc/history.bin','linux-gc-upload-key','single')
        if uploaded['job_state']!='COMPLETED':self.wait_job(uploaded['job_id'])
        file_id=uploaded['file']['file']['file_id'];source=self.wait_count(file_id,1)['replicas'][0]
        index=next(i for i,n in enumerate(self.nodes) if n['node_id']==source['node_id'])
        body=self.base/('volume-'+str(index))/'objects'/(source['local_file_id']+'.blob')
        move=self.post('drain',node_id=source['node_id'])['move_ids'][0]
        deadline=time.monotonic()+150
        while time.monotonic()<deadline:
            state=self.owner.request('GET','replication/moves')['moves'][move]['state']
            if state=='RETIRED':break
            time.sleep(.2)
        self.assertEqual(state,'RETIRED');self.assertEqual(body.read_bytes(),data)
        self.post('archive-jobs',retired_replica_id=source['replica_id'])
        self.assertEqual(self.fixture_call('age',{'file_id':file_id})['appended'],1024)
        job_id=self.prepare_confirm(source['replica_id'])['gc_job_id']
        return {'file_id':file_id,'source':source,'index':index,'body':body,'data':data,'job_id':job_id,
                'home':self.homes[index]/'storage'}

    def storage_execute(self,raw,exact,target):
        return StorageClient(target['origin'],target['pin'],raw,exact['volume_id'],timeout=90).json(
            'POST','gc/'+exact['gc_job_id'],{})

    def journal(self,target):
        path=target['home']/('gc-journal-'+target['source']['volume_id']+'.sqlite3')
        with closing(sqlite3.connect(path)) as db:
            row=db.execute('SELECT phase FROM entries WHERE job_id=?',(target['job_id'],)).fetchone()
        return row[0] if row else None

    def response(self,target):
        return target['home']/('test-gc-response-'+target['job_id']+'.json')

    def denied(self,target,future):
        with self.assertRaises((ClientError,OSError)):future.result(timeout=90)
        # A client timeout alone cannot qualify a physical denial. Require the
        # actual Storage handler to record a rejected response before healing.
        self.assertTrue(self.response(target).exists(),'actual server denial evidence required')
        evidence=json.loads(self.response(target).read_bytes())
        self.assertGreaterEqual(evidence['status'],400)
        self.assertNotIn(evidence.get('state'),('DONE',))
        self.assertEqual(target['body'].read_bytes(),target['data'])

    @contextmanager
    def paused(self,target,point):
        raw,exact,node=self.issue(target['job_id'])
        marker=target['home']/('test-gc-pause-'+point)
        reached=target['home']/('test-gc-reached-'+point)
        self.response(target).unlink(missing_ok=True)
        reached.unlink(missing_ok=True);marker.write_text('pause synthetic executor')
        pool=ThreadPoolExecutor(max_workers=1)
        future=pool.submit(self.storage_execute,raw,exact,node)
        try:
            deadline=time.monotonic()+45
            while not reached.exists() and time.monotonic()<deadline:
                if future.done():future.result();self.fail('physical boundary not reached')
                time.sleep(.02)
            self.assertTrue(reached.exists(),'actual network authorization must reach physical boundary')
            yield future,marker,exact
        finally:
            marker.unlink(missing_ok=True)
            pool.shutdown(wait=True)

    def restart_target(self,target):
        i=target['index'];self.kill_python(i);self.stop(i,crash=True)
        self.start(i);self.launch_python(i);self.wait_ready()

    def execute_owner(self,job_id):
        for attempt in range(5):
            try:return self.owner.request('POST','replication/gc-execute',{'gc_job_id':job_id})
            except ClientError as exc:
                if exc.code not in ('stale_gc_proof','gc_execution_unconfirmed','precondition_conflict') or attempt==4:raise

    def snapshot_restart(self):
        succeeded=0
        for client in self.clients:
            try:client.request('POST','/v1/snapshot',{});succeeded+=1
            except CatalogError:pass
        self.assertGreater(succeeded,0,'must persist an actual Go snapshot')
        for i in range(3):self.kill_python(i)
        self.stop_all()
        for i in range(3):self.start(i)
        for i in range(3):self.launch_python(i)
        return self.wait_ready()

    def test_paused_quorum_term_crashes_and_durable_whole_cluster_replay(self):
        target=self.target();job=target['job_id']
        with self.paused(target,'before_final_authorize') as (future,marker,exact):
            old=self.wait_ready();self.split([{0},{1},{2}])
            with self.assertRaises(CatalogError):self.clients[old].state(True)
            marker.unlink()
            self.denied(target,future)
            self.assertEqual(self.journal(target),'DELETING')
        self.split([set(range(3))]);self.wait_ready()
        self.mark(1,'actual all-voter partition before final TLS callback denies unlink; journal intent retains bytes')

        with self.paused(target,'before_final_authorize') as (future,marker,exact):
            old=self.wait_ready();self.partition(old)
            new=self.wait_ready(exclude=(old,))
            self.assertGreater(self.cached(new)['document']['authority']['term'],exact['permit_term'])
            marker.unlink()
            self.denied(target,future)
        self.split([set(range(3))]);self.wait_ready()
        self.mark(2,'actual new majority term invalidates paused old-run authorization before unlink')

        with self.paused(target,'after-final-reply') as (future,marker,exact):
            proof=json.loads((target['home']/'test-gc-final-proof.json').read_bytes())
            self.assertEqual(proof['term'],exact['permit_term']);self.assertGreater(proof['index'],0)
            # Real time, real successful quorum reply; do not mock the executor clock.
            deadline=time.monotonic()+10.2
            while time.monotonic()<deadline:time.sleep(.05)
            marker.unlink()
            self.denied(target,future)
            self.assertEqual(json.loads(self.response(target).read_bytes())['error'],'gc_authority_budget_expired')
        self.mark(3,'paused real successful final TLS receipt exceeds freshness budget; no unlink')

        for point,absent in (('after_delete_intent',False),('after_unlink',True)):
            crash=target['home']/('test-gc-crash-'+point);crash.write_text('crash synthetic cohost')
            for attempt in range(5):
                raw,exact,node=self.issue(job)
                self.response(target).unlink(missing_ok=True)
                with self.assertRaises((ClientError,OSError)):self.storage_execute(raw,exact,node)
                if not crash.exists():break
                # A denied stale proof is not a crash. Keep the exact fault armed
                # and same job, require a real rejection, then obtain new proof.
                evidence=json.loads(self.response(target).read_bytes())
                self.assertGreaterEqual(evidence['status'],400)
                self.assertEqual(target['body'].read_bytes(),target['data'])
            self.assertFalse(crash.exists());self.assertTrue((target['home']/('test-gc-crashed-'+point)).exists())
            self.python[target['index']].wait(timeout=10)
            self.assertEqual(self.python[target['index']].returncode,91)
            self.assertEqual(target['body'].exists(),not absent)
            self.assertEqual(self.journal(target),'DELETING')
            self.restart_target(target)
            self.assertEqual(self.journal(target),'DELETING')
            if not absent:self.assertEqual(target['body'].read_bytes(),target['data'])
        result=self.execute_owner(job)
        expected={'gc_job_id':job,'state':'DONE','physical_deletions':1}
        self.assertEqual({k:result[k] for k in expected},expected)
        self.assertEqual(self.journal(target),'DONE');self.assertFalse(target['body'].exists())
        evidence=json.loads(self.response(target).read_bytes())
        self.assertTrue(evidence['replayed']);self.assertFalse(evidence['unlinked_now'])
        self.assertEqual(evidence['logical_bytes_removed_now'],0)
        self.mark(4,'real Node/cohost crashes before and after actual unlink; durable journal restart completes same job')

        saved=copy.deepcopy(self.cached(self.wait_ready())['document']['replication'])
        leader=self.snapshot_restart();current=self.cached(leader)['document']['replication']
        for key in ('gc_jobs','gc_plans','retired','archived_jobs','requests'):
            self.assertEqual(current[key],saved[key])
        self.assertEqual(self.journal(target),'DONE');self.assertFalse(target['body'].exists())
        replayed=self.execute_owner(job)
        self.assertEqual({k:replayed[k] for k in expected},expected)
        replay=self.owner.upload(io.BytesIO(target['data']),'linux-gc/history.bin','linux-gc-upload-key','single')
        self.assertEqual(replay['job_state'],'COMPLETED');self.assertFalse(target['body'].exists())
        output=io.BytesIO();self.owner.download(target['file_id'],output);self.assertEqual(output.getvalue(),target['data'])
        self.mark(5,'actual Go snapshot/all-process replay preserves DONE/fences/journal, upload replay and readable survivor')

    def test_actual_last_copy_corruption_and_new_snapshot_backup_version_pins(self):
        target=self.target();raw,exact,node=self.issue(target['job_id'])
        report=self.owner.request('GET','files/'+target['file_id']+'?consistency=strong')
        self.assertEqual(len(report['replicas']),1)
        survivor=report['replicas'][0]
        i=next(i for i,n in enumerate(self.nodes) if n['node_id']==survivor['node_id'])
        body=self.base/('volume-'+str(i))/'objects'/(survivor['local_file_id']+'.blob')
        for missing in (False,True):
            saved=body.read_bytes()
            if missing:body.rename(body.with_suffix('.held'))
            else:body.write_bytes(b'corrupt synthetic survivor')
            try:
                self.response(target).unlink(missing_ok=True)
                with self.assertRaises((ClientError,OSError)):self.storage_execute(raw,exact,node)
                self.assertGreaterEqual(json.loads(self.response(target).read_bytes())['status'],400)
                self.assertEqual(target['body'].read_bytes(),target['data'])
            finally:
                if missing:body.with_suffix('.held').rename(body)
                else:body.write_bytes(saved)
            # Restore only known synthetic fixture bytes, then real reconciliation/
            # streamed verification. No fabricated catalog proof or event eviction.
            self.owner.request('POST','reconcile',{})
        self.mark(6,'missing/corrupt sole survivor denies network physical GC and retains last readable retired bytes')

        self.owner.request('POST','backup/enable',{'request_id':uid()})
        with self.paused(target,'before_final_authorize') as (future,marker,exact):
            snapshot=self.owner.request('POST','backup/snapshots',{'request_id':uid(),'copies':1})
            marker.unlink()
            self.denied(target,future)
        self.wait_backup(snapshot['job_id'])
        candidate=next(r for r in self.owner.request('GET','replication/gc-plan')['candidates']
                       if r['retired_replica_id']==target['source']['replica_id'])
        self.assertIn('snapshot_pin',candidate['holds']);self.assertIn('backup_job_reference',candidate['holds'])
        self.assertFalse(candidate['eligible'])
        second=b'separate immutable version two\0'*64
        uploaded=self.owner.upload(io.BytesIO(second),'linux-gc/history.bin','linux-gc-upload-key-v2','single',version=2)
        if uploaded['job_state']!='COMPLETED':self.wait_job(uploaded['job_id'])
        second_id=uploaded['file']['file']['file_id']
        for file_id,data in ((target['file_id'],target['data']),(second_id,second)):
            output=io.BytesIO();self.owner.download(file_id,output);self.assertEqual(output.getvalue(),data)
        self.owner.request('POST','backup/delete',{'request_id':uid(),'file_id':target['file_id']})
        candidate=next(r for r in self.owner.request('GET','replication/gc-plan')['candidates']
                       if r['retired_replica_id']==target['source']['replica_id'])
        self.assertIn('trash_pin',candidate['holds'])
        with self.assertRaises(ClientError):self.execute_owner(target['job_id'])
        self.assertEqual(target['body'].read_bytes(),target['data'])
        self.mark(7,'new snapshot/backup reference during paused final boundary denies unlink; versions and trash remain pinned')

        manifest=copy.deepcopy(self.owner.request('GET','backup/snapshots')['snapshots'][snapshot['snapshot_id']])
        self.snapshot_restart()
        self.assertEqual(self.owner.request('GET','backup/snapshots')['snapshots'][snapshot['snapshot_id']],manifest)
        restored=self.owner.request('POST','backup/restore',{'request_id':uid(),'file_id':target['file_id'],
                                                          'snapshot_id':snapshot['snapshot_id']})
        self.wait_backup(restored['job_id'])
        restored_file=self.backup_job(restored['job_id'])['target_file_id']
        output=io.BytesIO();self.owner.download(restored_file,output);self.assertEqual(output.getvalue(),target['data'])
        self.assertEqual(target['body'].read_bytes(),target['data'])
        self.mark(8,'whole-cluster snapshot/replay retains backup/version pins and restores old exact bytes into new version')
