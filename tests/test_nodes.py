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
