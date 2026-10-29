"""Read-only contract/actual Raft TLS partition/takeover and passive recovery view."""
import copy
import hashlib
import io
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
import time
from asc.catalog.common import CatalogError, canonical, uid
from asc.client import ClientError, request_json
from asc.observability.core import observe
from asc.observability.client import Observer, RecoveryObserver
from asc.external.recovery import stage
from tests import test_external as memory
from tests import test_external_cluster as fixture


class ObservationUnitTests(unittest.TestCase):
    setUp=memory.ExternalBackupTests.setUp

    def test_leader_hint_never_grants_quorum_or_calls_takeover(self):
        doc=self.source.doc;before=canonical(doc)
        def view(strong=False):
            if strong:raise CatalogError('quorum_read_unavailable',503)
            return {'document':copy.deepcopy(doc),'state':{'index':100,'term':4,'document_sha256':hashlib.sha256(before).hexdigest()}}
        def forbidden(*args,**kwargs):raise AssertionError('observation must not activate/write')
        runtime=SimpleNamespace(cluster=doc['cluster_id'],epoch=doc['epoch'],node_id='test-voter',view=view,
            ensure_ready=forbidden,commit=forbidden,operation=forbidden,
            client=SimpleNamespace(status=lambda:dict(cluster_id=doc['cluster_id'],node_id='test-voter',role='Leader',term='4',quarantined=False)))
        result=observe(runtime,True)
        self.assertFalse(result['writer_authority']);self.assertFalse(result['runtime']['leader_confirmed'])
        self.assertFalse(result['runtime']['quorum_available']);self.assertEqual(result['runtime']['state'],'QUORUM UNAVAILABLE')
        self.assertTrue(all(f['protected'] is None for f in result['files']))
        self.assertEqual(canonical(doc),before)

    def test_verified_passive_stage_reports_read_only_and_corruption_never_healthy(self):
        backup=self.engine.create(self.source,self.roots)
        root=self.base/'recovery-view';root.mkdir(mode=0o700)
        stage(self.store,backup['backup_id'],backup['manifest_sha256'],root,self.roots,self.source.doc['cluster_id'],100)
        before={p.relative_to(root):p.read_bytes() for p in root.rglob('*') if p.is_file()}
        observer=RecoveryObserver(root,backup['manifest_sha256'],self.source.doc['cluster_id'],100)
        result=observer.state();self.assertEqual(result['runtime']['state'],'RECOVERY READ-ONLY')
        self.assertFalse(result['writer_authority']);self.assertFalse(result['backup']['recovery']['credentials_restored'])
        self.assertEqual(result['backup']['recovery']['objects'],2)
        self.assertFalse((root/'registry.sqlite3').exists());self.assertFalse((root/'node.json').exists())
        self.assertEqual(before,{p.relative_to(root):p.read_bytes() for p in root.rglob('*') if p.is_file()})
        next((root/'objects').glob('*.blob')).write_bytes(b'actual corrupt synthetic stage')
        failed=observer.state();self.assertEqual(failed['runtime']['state'],'UNKNOWN');self.assertFalse(failed['writer_authority'])
        self.assertIsNone(failed['backup']['recovery']['verified_at'])


class ObservationClusterFixture(fixture.ExternalFixture,unittest.TestCase):
    def observer(self,**kwargs):return Observer(self.cluster,self.epoch,self.endpoints,**kwargs)

    def exercise_api(self):
        leader=self.make_cluster()
        data=b'Core observer immutable bytes\0'*1200
        upload=self.owner.upload(io.BytesIO(data),'observer/real.bin','observer_actual_key','replicated_3')
        if upload['job_state']!='COMPLETED':self.wait_job(upload['job_id'])
        self.wait_copies(upload['file']['file']['file_id'],3)
        self.owner.request('POST','backup/enable',{'request_id':uid()})
        snapshot=self.owner.request('POST','backup/snapshots',{'request_id':uid(),'copies':2})
        deadline=time.monotonic()+60
        while time.monotonic()<deadline:
            if self.owner.request('GET','backup/snapshots')['snapshots'][snapshot['snapshot_id']]['state']=='VERIFIED':break
            time.sleep(.2)
        else:self.fail('Actual backup did not reach verified state')
        frozen={str(home):hashlib.sha256((home/'registry.sqlite3').read_bytes()).hexdigest() for home in self.homes}
        state=self.observer().state()
        self.assertTrue(state['runtime']['strong_read_confirmed']);self.assertTrue(state['runtime']['leader_confirmed'])
        self.assertEqual(state['runtime']['leader_id'],self.endpoints[self.wait_ready()]['node_id'])
        self.assertEqual(state['runtime']['static_voters'],3);self.assertEqual(len(state['runtime']['controllers']),3)
        self.assertEqual(len(state['nodes']),3);self.assertEqual(state['files'][0]['desired_replicas'],3)
        self.assertTrue(state['files'][0]['protected']);self.assertEqual(state['files'][0]['available_replicas'],3)
        self.assertTrue(state['read_only']);self.assertFalse(state['writer_authority']);self.assertTrue(state['jobs'])
        self.assertTrue(state['backup']['enabled']);self.assertEqual(state['backup']['snapshots'][0]['state'],'VERIFIED')
        self.assertIsInstance(state['backup']['snapshots'][0]['verified_at'],int)
        self.assertEqual(state['backup']['external']['state'],'UNKNOWN')
        raw=json.dumps(state)
        for endpoint,node in zip(self.endpoints,self.nodes):
            for secret in (endpoint['token'],node['token']):self.assertNotIn(secret,raw)
        for home in self.homes:self.assertEqual(hashlib.sha256((home/'registry.sqlite3').read_bytes()).hexdigest(),frozen[str(home)])
        endpoint=self.endpoints[leader]
        with self.assertRaises(ClientError) as denied:
            request_json(endpoint['origin'],endpoint['pin'],'POST','/cluster/v1/observability',{},endpoint['token'])
        self.assertEqual(denied.exception.status,403)
        with self.assertRaises(ClientError) as node_denied:
            request_json(endpoint['origin'],endpoint['pin'],'GET','/cluster/v1/observability',token=self.nodes[0]['token'])
        self.assertEqual(node_denied.exception.status,401)
        wrong=Observer(self.cluster,self.epoch,[dict(e,pin='0'*64) for e in self.endpoints]).state()
        self.assertEqual(wrong['runtime']['state'],'UNKNOWN');self.assertIsNone(wrong['counts']['files'])
        self.assertFalse(wrong['runtime']['strong_read_confirmed'])

    def exercise_faults(self):
        leader=self.make_cluster();observer=self.observer()
        self.assertTrue(observer.state()['runtime']['quorum_available'])
        self.partition(leader,True);new=self.wait_ready(exclude=(leader,))
        result=observer.state();self.assertTrue(result['runtime']['quorum_available'])
        self.assertEqual(result['runtime']['leader_id'],self.endpoints[new]['node_id'])
        old=next(c for c in result['runtime']['controllers'] if c['node_id']==self.endpoints[leader]['node_id'])
        self.assertFalse(old['leader_confirmed'])
        self.split([{0},{1},{2}])  # One all-voter partition; partition(i) resets the whole split.
        denied=observer.state();self.assertEqual(denied['runtime']['state'],'QUORUM UNAVAILABLE')
        self.assertFalse(denied['runtime']['quorum_available']);self.assertFalse(denied['writer_authority'])
        self.assertIsNone(denied['capacity']['available_bytes'])
        self.split([set(range(3))])
        restored=self.wait_ready();self.assertTrue(observer.state()['runtime']['strong_read_confirmed'])
        self.kill_python(restored);self.stop(restored,crash=True);self.wait_ready(exclude=(restored,))
        result=observer.state();self.assertTrue(result['runtime']['quorum_available'])
        lost=next(c for c in result['runtime']['controllers'] if c['node_id']==self.endpoints[restored]['node_id'])
        self.assertEqual(lost['state'],'OFFLINE');self.assertEqual(lost['voter_process'],'UNKNOWN')
        self.assertEqual(result['runtime']['state'],'DEGRADED')
        self.start(restored);self.launch_python(restored);self.wait_ready()
        self.assertTrue(observer.state()['runtime']['strong_read_confirmed'])
        print('4.1 Core observer PASS: actual pinned three-voter stale Leader/partition/quorum loss/Controller death/reconnect; no writer authority',flush=True)


class ObservationAPITests(ObservationClusterFixture):
    def test_real_owner_tls_sanitized_three_node_files_jobs_no_original_registry_writes(self):self.exercise_api()


class ObservationFaultTests(ObservationClusterFixture):
    def test_real_stale_leader_partition_quorum_loss_controller_death_and_reconnect(self):self.exercise_faults()
