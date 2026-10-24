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
