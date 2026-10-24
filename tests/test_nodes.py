"""Node insights contract/engine and safety integration tests."""
import copy
import unittest

from asc.nodes import scoring


class ScoreContractTests(unittest.TestCase):
    def test_unknown_is_explicit_and_has_no_manufacturer_default(self):
        observations = scoring.unknown()
        self.assertEqual(scoring.validate(observations), observations)
        self.assertTrue(all(v['value'] is None and v['samples'] == 0 for v in observations.values()))
        self.assertEqual(sum(scoring.WEIGHTS.values()), 100)

    def test_rejects_nonfinite_types_missing_fields_and_wrong_provenance(self):
        for value in [True, float('nan'), float('inf'), -1, 1.1, '1']:
            obj = scoring.unknown()
            obj['capacity_ratio'].update(value=value, observed_at=10, samples=1)
            with self.subTest(value=value), self.assertRaises(ValueError):
                scoring.validate(obj)
        for patch in [{'source': 'manufacturer-baseline'}, {'samples': True},
                      {'observed_at': 10}, {'extra': 1}]:
            obj = scoring.unknown(); obj['memory_mb'].update(patch)
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                scoring.validate(obj)
        obj = scoring.unknown(); del obj['reachable']
        with self.assertRaises(ValueError): scoring.validate(obj)

    def test_known_zero_is_distinct_from_unknown_and_all_boundaries_validate(self):
        obj = scoring.unknown()
        for name, value in [('capacity_ratio', 0), ('reachable', False),
                            ('reliability', 0), ('memory_mb', 0), ('thermal_c', -40)]:
            obj[name].update(value=value, observed_at=0, samples=1)
        self.assertEqual(scoring.validate(obj), obj)
        for name, limits in scoring.RANGES.items():
            high = copy.deepcopy(obj); high[name]['value'] = limits[1]
            scoring.validate(high)


class ScoreEngineTests(unittest.TestCase):
    def measured(self, **values):
        obj = scoring.unknown()
        for name, value in values.items():
            obj[name].update(value=value, observed_at=1000, samples=10)
        return obj

    def test_all_unknown_is_null_and_zero_confidence(self):
        result = scoring.score(scoring.unknown(), 1000)
        self.assertIsNone(result['score']); self.assertIsNone(result['reliability'])
        self.assertEqual(result['confidence'], 0)

    def test_exact_weighted_result_and_independent_confidence(self):
        obj = self.measured(capacity_ratio=.5, reachable=True, reliability=.8,
                            memory_mb=4096, thermal_c=50)
        original = copy.deepcopy(obj)
        result = scoring.score(obj, 1000)
        self.assertEqual(result['score'], 69)
        self.assertEqual(result['reliability'], 80)
        self.assertEqual(result['confidence'], 100)
        obj['reliability']['samples'] = 1
        self.assertEqual(scoring.score(obj, 1000)['confidence'], 73)
        self.assertEqual(original['reliability']['samples'], 10)

    def test_stale_future_and_inclusive_freshness_do_not_create_zero_values(self):
        obj = self.measured(reachable=False)
        self.assertEqual(scoring.score(obj, 1120)['score'], 0)
        for stamp in (1121, 999):
            result = scoring.score(obj, stamp)
            self.assertIsNone(result['score'])
            self.assertEqual(result['components']['reachable']['status'], 'UNKNOWN')
        self.assertEqual(obj['reachable']['value'], False)

    def test_partial_coverage_extremes_and_monotonicity(self):
        for metric, values in [('capacity_ratio', [0,.5,1]), ('reliability',[0,.5,1]),
                               ('memory_mb',[0,4096,8192]), ('thermal_c',[65,50,35])]:
            results=[scoring.score(self.measured(**{metric:v}),1000)['score'] for v in values]
            self.assertEqual(results,[0,50,100])
        result = scoring.score(self.measured(reachable=True),1000)
        self.assertEqual(result['score'],100); self.assertEqual(result['confidence'],20)
        with self.assertRaises(ValueError): scoring.score(scoring.unknown(),True)


class ScoreViewTests(unittest.TestCase):
    def setUp(self):
        from asc.failover.state import MemoryRegistry, export
        from asc.catalog.common import uid
        self.reg = MemoryRegistry(uid()); self.addCleanup(self.reg.db.close)
        self.reg.seed_self('local', {'memory_mb': 4096})
        self.doc = export(self.reg.db, 1, {'node_id': 'voter-a', 'term': 4})

    def test_readonly_snapshot_keeps_exact_checkpoint_and_unknown_unapproved_inputs(self):
        from asc.nodes.view import scores
        original = copy.deepcopy(self.doc)
        result = scores({'document': self.doc,'state':{'index':88,'term':4},'stale':True},1000)
        self.assertEqual(result['applied_index'],88)
        self.assertTrue(result['stale']); self.assertTrue(result['read_only'])
        self.assertIsNone(result['nodes'][0]['score'])
        self.assertEqual(original,self.doc)

    def test_api_requires_admin_and_never_enters_mutation_operation(self):
        from types import SimpleNamespace
        from unittest import mock
        from asc.failover.service import RuntimeHandler
        h = object.__new__(RuntimeHandler)
        h.command='GET';h.path='/catalog/v1/nodes/scores'
        runtime = SimpleNamespace(view=mock.Mock(return_value={'document':self.doc,
                                  'state':{'index':88,'term':4},'stale':True}))
        h.server=SimpleNamespace(catalog=SimpleNamespace(runtime=runtime))
        h._admin=mock.Mock(return_value=False);h._json=mock.Mock()
        h._runtime_dispatch();runtime.view.assert_not_called()
        h._admin.return_value=True
        h._runtime_dispatch()
        runtime.view.assert_called_once_with(strong=False)
        self.assertEqual(h._json.call_args.args[0],200)
        self.assertTrue(h._json.call_args.args[1]['read_only'])


class TelemetryHistoryTests(unittest.TestCase):
    def test_hourly_coalescing_retention_and_unknown_gaps(self):
        from asc.nodes import history
        state=history.empty()
        obs=ScoreEngineTests().measured(reachable=True,capacity_ratio=.5)
        for day in range(40):
            at=day*86400+1000
            for item in obs.values():
                if item['value'] is not None:item['observed_at']=at
            history.record(state,'node-a',1,obs,at)
            history.record(state,'node-a',1,obs,at+1)
        self.assertEqual(len(state['history']['node-a']['days']),30)
        self.assertEqual(len(state['history']['node-a']['hours']),1)
        report=history.summary(state,'node-a','24h',at)
        self.assertEqual(report['probe_samples'],1)
        self.assertEqual(report['observed_buckets'],1)
        self.assertIsNone(report['buckets'][0]['metrics']['reachable']['mean'])
        self.assertEqual(history.summary(state,'node-a','7d',at)['probe_samples'],7)
        self.assertEqual(history.summary(state,'node-a','30d',at)['probe_samples'],30)
        self.assertIsNone(report['continuous_uptime'])
        history.validate(state,[{'node_id':'node-a'}])

    def test_failed_probe_is_measured_zero_and_no_sensor_data_is_invented(self):
        from asc.nodes import history
        state=history.empty();obs=ScoreEngineTests().measured(reachable=False)
        history.record(state,'node-a',1,obs,1000)
        report=history.summary(state,'node-a','24h',1000)
        self.assertEqual(report['reliability'],0)
        self.assertIsNone(report['buckets'][-1]['metrics']['thermal_c']['mean'])
        history.record(state,'node-a',1,scoring.unknown(),5000)
        self.assertEqual(state['history']['node-a']['last_sample_at'],1000)

    def test_history_refuses_nonfinite_and_future_schema(self):
        from asc.nodes import history
        state=history.empty();state['schema']=2
        with self.assertRaises(ValueError):history.validate(state,[])
        state=history.empty()
        history.record(state,'node-a',1,ScoreEngineTests().measured(reachable=True),1000)
        state['history']['node-a']['hours'][0]['metrics']['reachable']['sum']=float('nan')
        with self.assertRaises(ValueError):history.validate(state,[{'node_id':'node-a'}])

    def test_extension_roundtrip_takeover_and_backup_never_lose_history(self):
        from asc.failover import state as projection
        from asc.backup.state import empty as backup_empty
        from asc.catalog.common import uid
        from asc.nodes import history
        reg=projection.MemoryRegistry(uid());self.addCleanup(reg.db.close)
        reg.seed_self('local',{})
        doc=projection.export(reg.db,1,{'node_id':'voter-a','term':4})
        doc['backup']=backup_empty();doc['insights']=history.empty()
        history.record(doc['insights'],'local-controller',1,ScoreEngineTests().measured(reachable=True),1000)
        projection.validate(doc)
        prepared=projection.prepare_registry(doc);self.addCleanup(prepared.db.close)
        self.assertEqual(projection.export(prepared.db,1,doc['authority']),doc)
        newer=projection.takeover(doc,'voter-b',5)
        self.assertEqual(newer['insights'],doc['insights'])
        self.assertEqual(newer['backup'],doc['backup'])

    def test_enable_lost_reply_replays_and_conflicting_request_is_rejected(self):
        from asc.failover import state as projection
        from asc.catalog.common import uid,CatalogError
        from asc.nodes.service import Insights
        from tests import test_backup
        from types import SimpleNamespace
        reg=projection.MemoryRegistry(uid());self.addCleanup(reg.db.close)
        runtime=test_backup.ProjectionRuntime(projection.export(reg.db,1,{'node_id':'voter-a','term':4}))
        service=Insights(SimpleNamespace(runtime=runtime))
        runtime.crash=True
        with self.assertRaises(test_backup.fixture.helpers.SimulatedCrash):
            service.enable({'request_id':'enable-insights'})
        index=runtime.index
        self.assertTrue(service.enable({'request_id':'enable-insights'})['enabled'])
        self.assertEqual(runtime.index,index)
        with self.assertRaises(CatalogError):
            service.edit('different',{'request_id':'enable-insights'},lambda d,s:{})


class PreferenceTests(unittest.TestCase):
    def setUp(self):
        from asc.failover import state
        from asc.catalog.common import uid
        from asc.nodes.service import Insights
        from tests.test_backup import ProjectionRuntime
        from types import SimpleNamespace
        reg=state.MemoryRegistry(uid());self.addCleanup(reg.db.close)
        reg.seed_self('local',{})
        self.runtime=ProjectionRuntime(state.export(reg.db,1,{'node_id':'voter-a','term':4}))
        self.service=Insights(SimpleNamespace(runtime=self.runtime))
        self.service.enable({'request_id':'enable-preferences'})

    def test_modes_are_replay_safe_and_never_move_or_delete_existing_catalog(self):
        from asc.nodes.preferences import MODES,effective
        original=copy.deepcopy(self.runtime.doc['catalog'])
        for mode in MODES:
            obj={'request_id':'pref-'+mode,'mode':mode}
            first=self.service.preference('local-controller',obj)
            index=self.runtime.index
            self.assertEqual(first,self.service.preference('local-controller',obj))
            self.assertEqual(index,self.runtime.index)
            self.assertEqual(effective(self.runtime.doc['insights'],'local-controller',1),mode)
            self.assertEqual(first['physical_deletions'],0)
            self.assertFalse(first['automatic_movement'])
        self.assertEqual(original,self.runtime.doc['catalog'])

    def test_generation_change_retains_restriction_but_cannot_promote_stale_preferred(self):
        from asc.nodes.preferences import effective,BLOCK_NEW
        for mode in ['preferred',*BLOCK_NEW]:
            self.service.preference('local-controller',{'request_id':'generation-'+mode,'mode':mode})
            self.assertEqual(effective(self.runtime.doc['insights'],'local-controller',2),
                             mode if mode in BLOCK_NEW else 'auto')

    def test_invalid_modes_and_conflicting_requests_do_not_commit(self):
        from asc.catalog.common import CatalogError
        for mode in ['Prefer',None,{},'delete']:
            with self.assertRaises((ValueError,TypeError)):
                self.service.preference('local-controller',{'request_id':'bad-pref','mode':mode})
        obj={'request_id':'stable-pref','mode':'drain'}
        self.service.preference('local-controller',obj)
        index=self.runtime.index
        with self.assertRaises(CatalogError):
            self.service.preference('local-controller',{**obj,'mode':'auto'})
        self.assertEqual(index,self.runtime.index)


class SmartPlacementTests(unittest.TestCase):
    def setUp(self):
        from tests import test_catalog
        self.fixture=test_catalog.CatalogTests(methodName='test_global_idempotency_explicit_versions_and_no_false_replica_count')
        self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.reg=self.fixture.reg;self.nodes=self.fixture.nodes
        from asc.nodes.history import empty
        self.insights=empty()
        self.save()

    def save(self):
        import json
        with self.reg.connect() as db:
            db.execute("INSERT OR REPLACE INTO settings VALUES('phase3b_insights',?)",(json.dumps(self.insights),))

    def preference(self,index,mode):
        self.insights.setdefault('preferences',{})[self.nodes[index]['node_id']]={
            'mode':mode,'generation':1,'updated_at':0}
        self.save()

    def candidates(self,excluded=()):
        from asc.catalog.placement import candidates
        with self.reg.connect() as db:return candidates(db,4,excluded)

    def test_preferred_cannot_override_capacity_protection_domain_or_unknown(self):
        import json
        self.preference(0,'preferred')
        self.assertEqual(self.candidates()[0]['node_id'],self.nodes[0]['node_id'])
        self.assertNotIn(self.nodes[0]['node_id'],{r['node_id'] for r in self.candidates(['physical-0'])})
        with self.reg.connect() as db:
            db.execute('UPDATE nodes SET profile=? WHERE node_id=?',(json.dumps({'protected':True}),self.nodes[0]['node_id']))
        self.assertNotIn(self.nodes[0]['node_id'],{r['node_id'] for r in self.candidates()})
        with self.reg.connect() as db:
            db.execute("UPDATE nodes SET profile='{}' WHERE node_id=?",(self.nodes[0]['node_id'],))
            db.execute("UPDATE catalog_nodes SET capabilities='{}' WHERE node_id=?",(self.nodes[0]['node_id'],))
        self.assertNotIn(self.nodes[0]['node_id'],{r['node_id'] for r in self.candidates()})

    def test_avoid_drain_protected_block_new_but_preserve_existing_replicas_and_reads(self):
        from asc.catalog.placement import active_nodes,readable
        for mode in ['avoid-new-storage','drain','protected']:
            self.preference(0,mode)
            self.assertNotIn(self.nodes[0]['node_id'],{r['node_id'] for r in self.candidates()})
            with self.reg.connect() as db:
                node=next(n for n in active_nodes(db) if n['node_id']==self.nodes[0]['node_id'])
                self.assertTrue(readable(node,self.nodes[0]['volume_id']))
        for i in range(3):self.preference(i,'drain')
        self.assertEqual(self.candidates(),[])
        from asc.catalog.common import CatalogError
        with self.assertRaises(CatalogError):self.fixture.create()

    def test_real_catalog_upload_and_copy_schedule_keep_policy_and_domain_independence(self):
        self.preference(0,'preferred');self.preference(1,'avoid-new-storage')
        file_id=self.fixture.create()['file']['file_id']
        self.assertEqual(self.fixture.upload_job(file_id)['target_node_id'],self.nodes[0]['node_id'])
        self.fixture.complete_upload(file_id)
        jobs=self.fixture.catalog.schedule(file_id)
        self.assertEqual(len(jobs),1)
        with self.reg.connect() as db:
            target=db.execute('SELECT target_node_id FROM catalog_jobs WHERE job_id=?',(jobs[0],)).fetchone()[0]
        self.assertEqual(target,self.nodes[2]['node_id'])
        self.assertEqual(self.fixture.catalog.file(file_id)['desired_replicas'],2)

    def test_score_ranks_only_safe_targets_and_ties_are_deterministic(self):
        import json
        with self.reg.connect() as db:
            for i,node in enumerate(self.nodes):
                db.execute('UPDATE nodes SET profile=? WHERE node_id=?',(json.dumps({'memory_mb':8192 if i==2 else 0}),node['node_id']))
        first=self.candidates()
        self.assertEqual(first[0]['node_id'],self.nodes[2]['node_id'])
        self.assertEqual(first,self.candidates())
        self.assertGreater(first[0]['score_confidence'],0)
        # Pending double-copy reservations still reduce exact available capacity.
        self.fixture.create(policy='single')
        second=self.candidates()
        self.assertEqual(next(r for r in first if r['node_id']==self.nodes[2]['node_id'])['available_bytes']-
                         next(r for r in second if r['node_id']==self.nodes[2]['node_id'])['available_bytes'],8)


class HistoryGenerationTests(unittest.TestCase):
    def test_repair_retains_prior_generation_and_collects_new_generation_separately(self):
        from asc.nodes import history
        state=history.empty()
        obs=ScoreEngineTests().measured(reachable=False)
        history.record(state,'node-a',1,obs,1000)
        obs['reachable'].update(value=True,observed_at=1100)
        history.record(state,'node-a',2,obs,1100)
        self.assertEqual(len(state['history']['node-a']['hours']),2)
        history.validate(state,[{'node_id':'node-a'}])
        self.assertEqual(history.summary(state,'node-a','24h',1100,generation=2)['reliability'],100)
        self.assertEqual(history.summary(state,'node-a','24h',1100,generation=1)['reliability'],0)
        self.assertEqual(history.summary(state,'node-a','24h',1100)['buckets'][-1]['generations'],[1,2])


from tests import test_distributed as distributed_fixture


class SmartPlacementTLSTests(unittest.TestCase):
    setUp=distributed_fixture.DistributedTests.setUp
    stop_controller=distributed_fixture.DistributedTests.stop_controller
    controller=distributed_fixture.DistributedTests.controller
    owner=distributed_fixture.DistributedTests.owner
    assert_status=distributed_fixture.DistributedTests.assert_status
    upload_global=distributed_fixture.DistributedTests.upload_global
    drain=distributed_fixture.DistributedTests.drain

    def test_enabled_preferences_place_actual_bytes_on_independent_tls_nodes(self):
        import json
        from asc.nodes.history import empty
        state=empty()
        state['preferences']={self.nodes[0]['cfg']['node_id']:{'mode':'preferred','generation':1,'updated_at':0},
                              self.nodes[1]['cfg']['node_id']:{'mode':'drain','generation':1,'updated_at':0}}
        with self.reg.connect() as db:
            db.execute("INSERT INTO settings VALUES('phase3b_insights',?)",(json.dumps(state),))
        file_id=self.upload_global();self.drain()
        report=self.service.catalog.file(file_id)
        self.assertEqual(report['available_replicas'],2)
        self.assertEqual({r['node_id'] for r in report['replicas']},
                         {self.nodes[0]['cfg']['node_id'],self.nodes[2]['cfg']['node_id']})
        import io
        output=io.BytesIO();self.global_client.download(file_id,output)
        self.assertEqual(output.getvalue(),self.data)
