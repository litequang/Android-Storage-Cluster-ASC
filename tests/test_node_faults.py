"""Phase 3B real Go/Python/TLS fault qualification using synthetic temp volumes."""
import copy
import io
import time
import unittest

from asc.catalog.common import uid, CatalogError
from asc.client import ClientError
from tests import test_failover as fixture
from tests import test_backup as backup_fixture


class NodeFaultTests(unittest.TestCase):
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
    wait_backup=backup_fixture.BackupClusterTests.wait_backup
    backup_job=backup_fixture.BackupClusterTests.backup_job

    def mark(self, number, label):
        print(f'\nPhase 3B {number:02d} PASS: {label}',flush=True)

    def post(self,path,**obj):
        return self.owner.request('POST',path,{'request_id':uid(),**obj})

    def test_node_insights_placement_and_retention_fault_matrix(self):
        leader=self.make_cluster()
        request={'request_id':'phase3b-real-enable'}
        self.owner.request('POST','nodes/enable',request)
        self.assertTrue(self.owner.request('POST','nodes/enable',request)['enabled'])
        self.post('backup/enable')
        follower=next(i for i in range(3) if i!=leader)
        read=self.direct(follower,'GET','/catalog/v1/nodes/scores')
        self.assertTrue(read['stale']);self.assertTrue(read['read_only'])
        with self.assertRaises(ClientError) as denied:
            self.direct(leader,'GET','/catalog/v1/nodes/scores',token=self.nodes[0]['token'])
        self.assertEqual(denied.exception.status,401)
        self.mark(1,'explicit enable/replay and owner-only follower read-only scores')

        avoid=self.nodes[2]['node_id'];preferred=self.nodes[0]['node_id']
        self.post('nodes/'+avoid+'/preferences',mode='drain')
        self.post('nodes/'+preferred+'/preferences',mode='preferred')
        data=b'fake Phase 3B retained bytes\0'*128
        uploaded=self.owner.upload(io.BytesIO(data),'phase3b/retained.bin','phase3b-real-upload','replicated_2')
        if uploaded['job_state']!='COMPLETED':self.wait_job(uploaded['job_id'])
        file_id=uploaded['file']['file']['file_id']
        deadline=time.monotonic()+150
        while time.monotonic()<deadline:
            report=self.owner.request('GET','files/'+file_id+'?consistency=strong')
            if report['verified_replicas']>=2:break
            time.sleep(.3)
        self.assertEqual(report['verified_replicas'],2)
        self.assertNotIn(avoid,{r['node_id'] for r in report['replicas']})
        output=io.BytesIO();self.owner.download(file_id,output)
        self.assertEqual(output.getvalue(),data)
        self.mark(2,'preferred/drained placement stores exact bytes on two independent approved domains')

        deadline=time.monotonic()+40
        while time.monotonic()<deadline:
            history=self.owner.request('GET','nodes/'+preferred+'/history?window=30d&consistency=strong')
            if history['probe_samples']:break
            time.sleep(.3)
        self.assertGreater(history['probe_samples'],0)
        self.assertEqual(len(history['buckets']),30)
        self.assertIsNone(history['continuous_uptime'])
        self.mark(3,'real pinned probes persist bounded history with UNKNOWN gaps and observed reliability')

        snapshot=self.post('backup/snapshots',copies=2)
        self.wait_backup(snapshot['job_id'])
        preview=self.owner.request('GET','files/'+file_id+'/reduction-preview?consistency=strong')
        self.assertIn('retained_snapshot_or_restore',preview['holds'])
        self.assertEqual(preview['candidates'],[])
        self.assertEqual(preview['physical_deletions'],0)
        self.assertFalse(preview['apply_supported'])
        with self.assertRaises(ClientError) as absent:
            self.owner.request('POST','files/'+file_id+'/reduction-apply',{})
        self.assertEqual(absent.exception.status,404)
        saved=copy.deepcopy(self.cached(leader)['document']['insights'])
        manifest=self.owner.request('GET','backup/snapshots')['snapshots'][snapshot['snapshot_id']]
        self.mark(4,'snapshot-pinned reduction remains dry-run; no apply route and no physical deletion')

        old=leader
        self.kill_python(old)
        leader=self.wait_ready(exclude=(old,))
        self.assertNotEqual(old,leader)
        self.stop(old);self.start(old);self.launch_python(old)
        self.wait_ready()
        scores=self.owner.request('GET','nodes/scores?consistency=strong')['nodes']
        self.assertEqual(next(n for n in scores if n['node_id']==avoid)['preference'],'drain')
        self.assertEqual(self.cached(leader)['document']['insights']['preferences'],saved['preferences'])
        with self.assertRaises(ClientError):
            self.direct(old,'POST','/catalog/v1/nodes/'+avoid+'/preferences',{'request_id':uid(),'mode':'auto'})
        self.mark(5,'Python Leader loss/watchdog takeover preserves preferences; former Leader rejects writes')

        self.split([{0},{1},{2}])
        time.sleep(4)
        for i in range(3):
            with self.assertRaises(ClientError):
                self.direct(i,'POST','/catalog/v1/nodes/'+avoid+'/preferences',{'request_id':uid(),'mode':'auto'})
        self.split([set(range(3))]);leader=self.wait_ready()
        self.mark(6,'all minority Controllers reject preference mutations during quorum loss')

        snapshots=0
        for client in self.clients:
            try:client.request('POST','/v1/snapshot',{});snapshots+=1
            except CatalogError:pass
        self.assertGreater(snapshots,0)
        for i in range(3):self.kill_python(i)
        self.stop_all()
        for i in range(3):self.start(i)
        for i in range(3):self.launch_python(i)
        leader=self.wait_ready()
        current=self.cached(leader)['document']['insights']
        self.assertEqual(current['preferences'],saved['preferences'])
        self.assertEqual(current['requests'],saved['requests'])
        for node_id,row in saved['history'].items():
            self.assertGreaterEqual(current['history'][node_id]['last_sample_at'],row['last_sample_at'])
            self.assertTrue(all(bucket in current['history'][node_id]['days'] for bucket in row['days']))
        self.assertEqual(self.owner.request('GET','backup/snapshots')['snapshots'][snapshot['snapshot_id']],manifest)
        output=io.BytesIO();self.owner.download(file_id,output)
        self.assertEqual(output.getvalue(),data)
        self.mark(7,'actual Go snapshots and all-process restart retain history/preferences/Phase 3A manifest and bytes')
