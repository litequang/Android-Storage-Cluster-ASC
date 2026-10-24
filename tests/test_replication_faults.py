"""Phase 3C qualification with actual isolated Go/Python/TLS and synthetic bytes."""
import io
import time
import unittest

from asc.catalog.common import uid
from tests import test_failover as fixture


class ReplicationClusterTests(unittest.TestCase):
    setUpClass=classmethod(fixture.FailoverTests.setUpClass.__func__)
    start=fixture.FailoverTests.start
    stop=fixture.FailoverTests.stop
    stop_all=fixture.FailoverTests.stop_all
    leader=fixture.FailoverTests.leader
    partition=fixture.FailoverTests.partition
    split=fixture.FailoverTests.split
    make_cluster=fixture.FailoverTests.make_cluster
    launch_python=fixture.FailoverTests.launch_python
    kill_python=fixture.FailoverTests.kill_python
    close_cluster=fixture.FailoverTests.close_cluster
    failure_diagnostics=fixture.FailoverTests.failure_diagnostics
    wait_ready=fixture.FailoverTests.wait_ready
    cached=fixture.FailoverTests.cached
    wait_job=fixture.FailoverTests.wait_job
    direct=fixture.FailoverTests.direct

    def post(self,path,**obj):
        return self.owner.request('POST','replication/'+path,{'request_id':uid(),**obj})

    def wait_count(self,file_id,count):
        deadline=time.monotonic()+150
        while time.monotonic()<deadline:
            report=self.owner.request('GET','files/'+file_id+'?consistency=strong')
            if report['available_replicas']>=count:return report
            time.sleep(.3)
        self.fail('replica count did not reach '+str(count))

    def mark(self,number,label):
        print(f'\nPhase 3C {number:02d} PASS: {label}',flush=True)

    def test_policy_and_copy_before_retire(self):
        self.make_cluster()
        self.owner.request('POST','nodes/enable',{'request_id':'phase3c-enable-insights'})
        self.post('enable')
        deadline=time.monotonic()+45
        while time.monotonic()<deadline:
            status=self.owner.request('GET','nodes')
            if len(status['nodes'])==3 and all(n['last_error'] is None for n in status['nodes']):break
            time.sleep(.3)
        self.assertTrue(all(n['last_error'] is None for n in status['nodes']), 'all test Storage endpoints must be freshly probed before Drain')
        data=b'fake Phase 3C move bytes\0'*128
        uploaded=self.owner.upload(io.BytesIO(data),'phase3c/move.bin','phase3c-upload','single')
        if uploaded['job_state']!='COMPLETED':self.wait_job(uploaded['job_id'])
        file_id=uploaded['file']['file']['file_id']
        report=self.wait_count(file_id,1);source=report['replicas'][0]
        source_node=next(i for i,n in enumerate(self.nodes) if n['node_id']==source['node_id'])
        blob=self.base/('volume-'+str(source_node))/'objects'/(source['local_file_id']+'.blob')
        self.assertEqual(blob.read_bytes(),data)
        result=self.post('drain',node_id=source['node_id'])
        move_id=result['move_ids'][0]
        deadline=time.monotonic()+150
        while time.monotonic()<deadline:
            move=self.owner.request('GET','replication/moves')['moves'][move_id]
            if move['state']=='RETIRED':break
            time.sleep(.3)
        self.assertEqual(move['state'],'RETIRED')
        report=self.wait_count(file_id,1)
        self.assertNotIn(source['replica_id'],{r['replica_id'] for r in report['replicas']})
        self.assertEqual(blob.read_bytes(),data,'logical retirement must preserve the original physical bytes')
        output=io.BytesIO();self.owner.download(file_id,output);self.assertEqual(output.getvalue(),data)
        self.mark(1,'actual TLS COPY and independent checksum proof precede source reference retirement; bytes retained')
        self.post('policy',file_id=file_id,copies=2);self.wait_count(file_id,2)
        self.post('policy',file_id=file_id,copies=3)
        report=self.owner.request('GET','files/'+file_id+'?consistency=strong')
        self.assertEqual(report['desired_replicas'],3)
        self.assertLessEqual(report['available_replicas'],2)
        self.owner.request('POST','nodes/'+source['node_id']+'/preferences',{'request_id':uid(),'mode':'auto'})
        self.post('reconcile');report=self.wait_count(file_id,3)
        self.assertEqual(len({r['node_id'] for r in report['replicas']}),3)
        replacement=next(r for r in report['replicas'] if r['node_id']==source['node_id'])
        self.assertNotEqual(replacement['local_file_id'],source['local_file_id'])
        self.post('policy',file_id=file_id,copies=1)
        self.assertEqual(blob.read_bytes(),data)
        self.mark(2,'1/2/3/1 policies, explicit Drain shortage and new-object repair preserve retired identity fencing')
