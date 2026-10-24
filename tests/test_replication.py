"""Phase 3C synthetic state/replication safety tests; no real data or devices."""
import copy
from types import SimpleNamespace
from unittest import mock
import unittest

from asc.catalog.common import CatalogError, uid
from asc.failover import state
from asc.replication.service import Replication
from tests import test_catalog, test_backup


def fixture_runtime(test):
    fixture=test_catalog.CatalogTests();fixture.setUp();test.addCleanup(fixture.doCleanups)
    file_id=fixture.create(policy='single')['file']['file_id'];fixture.complete_upload(file_id)
    with fixture.reg.connect() as db:doc=state.export(db,1,{'node_id':'voter-a','term':4})
    cluster=uid();doc['cluster_id']=doc['catalog']['cluster_id']=cluster
    state.validate(doc)
    runtime=test_backup.ProjectionRuntime(doc)
    service=SimpleNamespace(runtime=runtime,refresh=mock.Mock())
    replication=Replication(service)
    replication.enable({'request_id':'phase3c-enable'})
    return fixture,file_id,runtime,service,replication


class DynamicPolicyTests(unittest.TestCase):
    def setUp(self):
        self.fixture,self.file_id,self.runtime,self.service,self.replication=fixture_runtime(self)

    def test_policy_transitions_schedule_missing_domains_without_erasing_bytes(self):
        original=copy.deepcopy(self.runtime.doc['catalog']['replicas'])
        for count in (2,3,1):
            result=self.replication.policy({'request_id':'policy-'+str(count),'file_id':self.file_id,'copies':count})
            self.assertEqual(result['desired_replicas'],count)
            self.assertEqual(result['physical_deletions'],0)
        copies=[j for j in self.runtime.doc['tables']['catalog_jobs'] if j['kind']=='COPY']
        self.assertEqual(len(copies),2)
        self.assertEqual(len({j['target_node_id'] for j in copies}),2)
        self.assertEqual(self.runtime.doc['catalog']['replicas'],original)
        self.assertEqual(self.runtime.doc['catalog']['files'][0]['policy'],'single')

    def test_retry_same_intent_never_duplicates_jobs_or_conflicts_silently(self):
        obj={'request_id':'stable-policy','file_id':self.file_id,'copies':3}
        first=self.replication.policy(obj);index=self.runtime.index
        self.assertEqual(self.replication.policy(obj),first)
        self.assertEqual(self.runtime.index,index)
        with self.assertRaises(CatalogError):self.replication.policy({**obj,'copies':1})
        self.assertEqual(self.runtime.index,index)
        first=self.replication.reconcile({'request_id':'stable-reconcile'})
        self.assertEqual(first,self.replication.reconcile({'request_id':'stable-reconcile'}))
        self.assertTrue(all(not f['scheduled_jobs'] for f in first['files']))

    def test_failed_quorum_and_invalid_count_never_change_projection(self):
        original=copy.deepcopy(self.runtime.doc)
        for count in (True,0,4,None,'2'):
            with self.assertRaises(ValueError):
                self.replication.policy({'request_id':'invalid-count','file_id':self.file_id,'copies':count})
        with mock.patch.object(self.runtime,'commit',side_effect=CatalogError('quorum_read_unavailable',503)):
            with self.assertRaises(CatalogError):
                self.replication.policy({'request_id':'no-quorum','file_id':self.file_id,'copies':3})
        self.assertEqual(self.runtime.doc,original)

    def test_roundtrip_takeover_preserve_3a_3b_and_replay_state(self):
        from asc.backup.state import empty as backup_empty
        from asc.nodes.history import empty as insights_empty
        self.runtime.doc['backup']=backup_empty();self.runtime.doc['insights']=insights_empty()
        reg=state.prepare_registry(self.runtime.doc);self.addCleanup(reg.db.close)
        self.assertEqual(state.export(reg.db,self.runtime.doc['revision'],self.runtime.doc['authority']),self.runtime.doc)
        newer=state.takeover(self.runtime.doc,'voter-b',5)
        for field in ('backup','insights','replication'):
            self.assertEqual(newer[field],self.runtime.doc[field])

    def test_capacity_shortage_reports_deficit_and_keeps_existing_copy(self):
        for node in self.runtime.doc['tables']['catalog_nodes']:node['storage_allowed']=0
        original=copy.deepcopy(self.runtime.doc['catalog']['replicas'])
        result=self.replication.policy({'request_id':'insufficient-targets','file_id':self.file_id,'copies':3})
        self.assertEqual(result['desired_replicas'],3)
        self.assertEqual(result['scheduled_jobs'],[])
        self.assertEqual(self.runtime.doc['catalog']['replicas'],original)


class MovePlanningTests(unittest.TestCase):
    def setUp(self):
        self.fixture,self.file_id,self.runtime,self.service,self.replication=fixture_runtime(self)
        from asc.nodes.history import empty
        self.runtime.doc['insights']=empty()
        self.source=self.runtime.doc['catalog']['replicas'][0]

    def test_drain_creates_one_durable_copy_and_never_removes_source(self):
        original=copy.deepcopy(self.runtime.doc['catalog']['replicas'])
        obj={'request_id':'drain-source','node_id':self.source['node_id']}
        result=self.replication.drain(obj)
        self.assertEqual(len(result['move_ids']),1)
        self.assertEqual(result,self.replication.drain(obj))
        again=self.replication.drain({**obj,'request_id':'drain-again'})
        self.assertEqual(again['move_ids'],result['move_ids'])
        self.assertEqual(self.runtime.doc['catalog']['replicas'],original)
        job=next(j for j in self.runtime.doc['tables']['catalog_jobs'] if j['kind']=='COPY')
        self.assertNotEqual(job['target_node_id'],self.source['node_id'])
        move=self.runtime.doc['replication']['moves'][result['move_ids'][0]]
        self.assertEqual(move['state'],'COPY_PENDING')
        state.validate(state.takeover(self.runtime.doc,'voter-b',5))

    def test_unavailable_capacity_keeps_only_readable_copy_and_reports_block(self):
        for node in self.runtime.doc['tables']['catalog_nodes']:node['storage_allowed']=0
        original=copy.deepcopy(self.runtime.doc['catalog']['replicas'])
        result=self.replication.drain({'request_id':'drain-shortage','node_id':self.source['node_id']})
        self.assertEqual(result['move_ids'],[])
        self.assertEqual(result['blocked_replicas'][0]['replica_id'],self.source['replica_id'])
        self.assertEqual(self.runtime.doc['catalog']['replicas'],original)
        self.assertEqual(self.runtime.doc['insights']['preferences'][self.source['node_id']]['mode'],'drain')

    def test_move_job_survives_sql_roundtrip_and_does_not_duplicate_on_new_request(self):
        obj={'request_id':'move-source','replica_id':self.source['replica_id']}
        first=self.replication.move(obj)
        second=self.replication.move({**obj,'request_id':'move-source-again'})
        self.assertEqual(first['move_ids'],second['move_ids'])
        reg=state.prepare_registry(self.runtime.doc);self.addCleanup(reg.db.close)
        self.assertEqual(state.export(reg.db,self.runtime.doc['revision'],self.runtime.doc['authority']),self.runtime.doc)


def finish_copy(replication,runtime,job_id):
    from asc.catalog.queue import JobQueue
    def apply(reg,catalog):
        queue=JobQueue(catalog);job=queue.claim(job_id)
        job=queue.checkpoint(job,uid(),uid())
        file=catalog._file(reg.db,job['file_id'])
        catalog.mutate('COMPLETE',{'job_id':job_id,'run_token':job['run_token'],'proof':{
            'file_id':job['target_local_file_id'],'volume_id':job['target_volume_id'],
            'logical_path':job['logical_path'],'size':file['size'],'sha256':file['sha256'],
            'state':'COMMITTED','physically_verified':True}})
    replication.workspace(runtime.doc,apply)


class RetirementTests(unittest.TestCase):
    def setUp(self):
        self.fixture,self.file_id,self.runtime,self.service,self.replication=fixture_runtime(self)
        self.source=copy.deepcopy(self.runtime.doc['catalog']['replicas'][0])
        result=self.replication.move({'request_id':'start-test-move','replica_id':self.source['replica_id']})
        self.move_id=result['move_ids'][0]
        self.job_id=self.runtime.doc['replication']['moves'][self.move_id]['job_id']
        self.service._client=mock.Mock();self.service._proof=mock.Mock(return_value={'physically_verified':True})

    def complete(self):
        return self.replication.complete_move({'request_id':'retire-test-move','move_id':self.move_id})

    def test_copy_completion_and_fresh_independent_proof_required_before_retirement(self):
        with self.assertRaises(CatalogError) as caught:self.complete()
        self.assertEqual(caught.exception.code,'copy_not_verified')
        finish_copy(self.replication,self.runtime,self.job_id)
        self.assertEqual(len(self.runtime.doc['catalog']['replicas']),2)
        result=self.complete()
        self.assertEqual(result['physical_deletions'],0)
        self.assertEqual(len(self.runtime.doc['catalog']['replicas']),1)
        record=self.runtime.doc['replication']['retired'][self.source['replica_id']]
        self.assertEqual(record['replica'],self.source)
        self.assertEqual(record['proofs'][0]['sha256'],self.runtime.doc['catalog']['files'][0]['sha256'])
        self.service._proof.assert_called_once()
        self.assertEqual(result,self.complete())
        self.service._proof.assert_called_once()
        self.assertTrue(any(self.source in e['payload']['replicas'] for e in self.runtime.doc['catalog']['events']))
        state.validate(state.takeover(self.runtime.doc,'voter-b',5))

    def test_corrupt_survivor_or_no_quorum_cannot_retire_source(self):
        finish_copy(self.replication,self.runtime,self.job_id)
        original=copy.deepcopy(self.runtime.doc)
        self.service._proof.side_effect=CatalogError('replica_corrupt',422)
        with self.assertRaises(CatalogError):self.complete()
        self.assertEqual(self.runtime.doc,original)
        self.service._proof.side_effect=None
        with mock.patch.object(self.runtime,'commit',side_effect=CatalogError('no_quorum',503)):
            with self.assertRaises(CatalogError):self.complete()
        self.assertEqual(self.runtime.doc,original)

    def test_retired_physical_identity_cannot_reenter_catalog_under_another_replica_id(self):
        from asc.catalog.state import insert,Catalog
        finish_copy(self.replication,self.runtime,self.job_id);self.complete()
        reg=state.prepare_registry(self.runtime.doc);self.addCleanup(reg.db.close)
        replica={**self.source,'replica_id':uid()}
        insert(reg.db,'catalog_replicas',replica);Catalog(reg)._event(reg.db,self.file_id)
        doc=state.export(reg.db,self.runtime.doc['revision']+1,self.runtime.doc['authority'])
        with self.assertRaises(CatalogError) as caught:state.validate(doc)
        self.assertEqual(caught.exception.code,'retired_object_reintroduction')

    def test_new_policy_or_generation_during_proof_blocks_stale_retirement(self):
        finish_copy(self.replication,self.runtime,self.job_id)
        def changed(*args):
            self.runtime.doc['catalog']['files'][0]['policy']='replicated_3'
            return {'physically_verified':True}
        self.service._proof.side_effect=changed
        with self.assertRaises(CatalogError):self.complete()
        self.assertTrue(any(r['replica_id']==self.source['replica_id'] for r in self.runtime.doc['catalog']['replicas']))
