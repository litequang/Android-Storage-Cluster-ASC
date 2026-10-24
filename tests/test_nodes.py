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
