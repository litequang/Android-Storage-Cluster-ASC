"""Actual three-Go/TLS GC authorization. Physical execution remains Linux-only."""
import io
import os
import subprocess
import sys
import time
import unittest

from asc.catalog.common import CatalogError, canonical, uid
from asc.client import ClientError, request_json
from asc.storage.client import StorageClient
from tests import test_failover as fixture, test_replication_faults as replication_fixture


class GCFixture:
    setUpClass=classmethod(fixture.FailoverTests.setUpClass.__func__)
    start=fixture.FailoverTests.start
    stop=fixture.FailoverTests.stop
    stop_all=fixture.FailoverTests.stop_all
    leader=fixture.FailoverTests.leader
    partition=fixture.FailoverTests.partition
    split=fixture.FailoverTests.split
    make_cluster=fixture.FailoverTests.make_cluster
    kill_python=fixture.FailoverTests.kill_python
    close_cluster=fixture.FailoverTests.close_cluster
    failure_diagnostics=fixture.FailoverTests.failure_diagnostics
    wait_ready=fixture.FailoverTests.wait_ready
    cached=fixture.FailoverTests.cached
    wait_job=fixture.FailoverTests.wait_job
    direct=fixture.FailoverTests.direct
    wait_count=replication_fixture.ReplicationClusterTests.wait_count
    post=replication_fixture.ReplicationClusterTests.post

    def launch_python(self,i):
        proc=subprocess.Popen([sys.executable,'-B','-m','tests.gc_fixture','run','--config',str(self.homes[i]/'failover.json')],
            cwd=fixture.ROOT,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        self.python[i]=proc
        deadline=time.monotonic()+30
        while time.monotonic()<deadline:
            if proc.poll() is not None:
                out,err=proc.communicate(timeout=2)
                self.fail('synthetic GC cohost startup: '+(out+err).decode(errors='replace')[-2000:])
            try:
                e=self.endpoints[i];request_json(e['origin'],e['pin'],'GET','/api/v1/info',timeout=2);return
            except (ClientError,OSError):time.sleep(.1)
        self.fail('synthetic GC cohost startup timeout')

    def fixture_call(self,action,obj):
        leader=self.wait_ready();e=self.endpoints[leader]
        return request_json(e['origin'],e['pin'],'POST','/fixture/gc/'+action,obj,e['token'],timeout=120)

    def issue(self,job_id):
        for attempt in range(5):
            try:
                reply=self.fixture_call('issue',{'gc_job_id':job_id})
                return reply['raw'],reply['exact'],reply['target']
            except ClientError as exc:
                if exc.code not in ('stale_gc_proof','precondition_conflict') or attempt==4:raise
                # The stale attempt was denied; obtain new real proof on this job.

    def prepare_confirm(self,replica_id):
        for attempt in range(5):
            prepared=self.post('gc-prepare',retired_replica_id=replica_id)
            try:return self.post('gc-confirm',plan_id=prepared['plan_id'],confirmation=prepared['required_confirmation'])
            except ClientError as exc:
                if exc.code not in ('stale_gc_plan','gc_plan_expired','precondition_conflict') or attempt==4:raise
                # Preserve expired/stale plans; prepare and confirm a fresh exact SHA.

    def introspect(self,exact,raw,**changes):
        node=next(n for n in self.nodes if n['node_id']==exact['node_id'])
        obj={'node_id':node['node_id'],'grant':raw,'volume_id':exact['volume_id'],'operation':'gc',
             'scope':{'method':'POST','resource':'gc/'+exact['gc_job_id']},'nonce':uid()}
        obj.update(changes)
        leader=self.wait_ready();e=self.endpoints[leader]
        for attempt in range(5):
            obj['nonce']=uid()
            try:return request_json(e['origin'],e['pin'],'POST','/api/v1/storage/authorize',obj,node['token'],timeout=60)
            except ClientError as exc:
                if exc.code!='stale_gc_proof' or attempt==4:raise
                # New nonce means a newly streamed, quorum-committed authorization.


class GCClusterTests(GCFixture,unittest.TestCase):
    def test_real_quorum_scope_takeover_and_default_windows_lock(self):
        self.make_cluster()
        self.owner.request('POST','nodes/enable',{'request_id':uid()});self.post('enable')
        # Require real pinned probes before the first allocation (no guessed readiness).
        deadline=time.monotonic()+45
        while time.monotonic()<deadline:
            status=self.owner.request('GET','nodes')
            if len(status['nodes'])==3 and all(n['last_error'] is None for n in status['nodes']):break
            time.sleep(.3)
        self.assertTrue(all(n['last_error'] is None for n in status['nodes']))
        data=b'only synthetic exact GC object bytes\0'*64
        uploaded=self.owner.upload(io.BytesIO(data),'gc/synthetic.bin','gc-synthetic-upload','single')
        if uploaded['job_state']!='COMPLETED':self.wait_job(uploaded['job_id'])
        file_id=uploaded['file']['file']['file_id'];report=self.wait_count(file_id,1);source=report['replicas'][0]
        source_index=next(i for i,n in enumerate(self.nodes) if n['node_id']==source['node_id'])
        body=self.base/('volume-'+str(source_index))/'objects'/(source['local_file_id']+'.blob')
        move=self.post('drain',node_id=source['node_id'])['move_ids'][0]
        deadline=time.monotonic()+150
        while time.monotonic()<deadline:
            state=self.owner.request('GET','replication/moves')['moves'][move]['state']
            if state=='RETIRED':break
            time.sleep(.3)
        self.assertEqual(state,'RETIRED');self.assertEqual(body.read_bytes(),data)
        self.post('archive-jobs',retired_replica_id=source['replica_id'])
        # Exercise ordinary append/retention through the actual cohost's lock.
        self.assertEqual(self.fixture_call('age',{'file_id':file_id})['appended'],1024)
        confirmed=self.prepare_confirm(source['replica_id'])
        job_id=confirmed['gc_job_id']
        raw,exact,target=self.issue(job_id)
        proof=self.introspect(exact,raw)
        self.assertEqual(proof['constraints'],exact);self.assertEqual(proof['authority']['term'],exact['permit_term'])
        self.assertNotIn(raw.encode(),canonical(self.cached(self.wait_ready())['document']))
        for change in ({'volume_id':uid()},{'scope':{'method':'GET','resource':'gc/'+job_id}},
                       {'grant':uid().replace('-','')*2}):
            with self.subTest(change=tuple(change)),self.assertRaises(ClientError):self.introspect(exact,raw,**change)
        self.issue(job_id)
        with self.assertRaises(ClientError):self.introspect(exact,raw)
        print('GC fault PASS: actual TLS independent byte proof, committed exact nonce, wrong scope and superseded permit',flush=True)
        raw,exact,target=self.issue(job_id)
        if os.name=='nt':
            with self.assertRaises(ClientError) as locked:StorageClient(target['origin'],target['pin'],raw,exact['volume_id']).json('POST','gc/'+job_id,{})
            self.assertEqual(locked.exception.status,403)
            self.assertEqual(body.read_bytes(),data)
            with self.assertRaises(ClientError):self.owner.request('POST','replication/gc-execute',{'gc_job_id':job_id})
            print('GC fault PASS: Windows physical path remains locked, original bytes retained',flush=True)
        else:
            marker=self.homes[source_index]/'storage'/'test-gc-lost-ack';marker.write_text('synthetic fault')
            for attempt in range(5):
                try:self.owner.request('POST','replication/gc-execute',{'gc_job_id':job_id})
                except ClientError as exc:
                    if exc.code not in ('stale_gc_proof','gc_execution_unconfirmed'):raise
                if not marker.exists():break
            self.assertFalse(marker.exists(),'must drop an actual successful GC reply; a denied attempt is not lost ACK evidence')
            self.assertFalse(body.exists(),'lost ACK follows actual unlink, not a simulated success')
            result=self.owner.request('POST','replication/gc-execute',{'gc_job_id':job_id})
            self.assertEqual(result['state'],'DONE');self.assertFalse(body.exists())
            self.assertEqual(self.owner.request('POST','replication/gc-execute',{'gc_job_id':job_id})['state'],'DONE')
            print('GC fault PASS: actual Linux synthetic unlink, lost TLS ACK, same-job journal replay',flush=True)
        # A distinct reserved job is unnecessary to prove stale permit denial: DONE
        # already denies; on Windows the RUNNING permit must also fail after takeover.
        old=self.wait_ready();self.kill_python(old);self.stop(old,crash=True)
        new=self.wait_ready(exclude=(old,));self.assertNotEqual(new,old)
        e=self.endpoints[new];node=next(n for n in self.nodes if n['node_id']==exact['node_id'])
        obj={'node_id':node['node_id'],'grant':raw,'volume_id':exact['volume_id'],'operation':'gc',
             'scope':{'method':'POST','resource':'gc/'+job_id},'nonce':uid()}
        with self.assertRaises(ClientError):request_json(e['origin'],e['pin'],'POST','/api/v1/storage/authorize',obj,node['token'])
        remaining=[i for i in range(3) if i!=old]
        self.stop(remaining[0],crash=True)
        # With one voter left, even an otherwise well-formed exact request cannot commit.
        e=self.endpoints[remaining[1]]
        with self.assertRaises(ClientError):request_json(e['origin'],e['pin'],'POST','/api/v1/storage/authorize',obj,node['token'])
        if os.name=='nt':self.assertEqual(body.read_bytes(),data)
        print('GC fault PASS: actual Controller/Go Leader loss and quorum loss deny old exact permits',flush=True)
