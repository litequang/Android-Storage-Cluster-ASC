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
