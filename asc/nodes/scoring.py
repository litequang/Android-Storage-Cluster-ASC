"""Versioned, deterministic node score contract (not voter/byte-proof authority)."""
import math

SCHEMA = 1
FRESH_SECONDS = 120
WEIGHTS = {'capacity_ratio': 30, 'reachable': 20, 'reliability': 30,
           'memory_mb': 10, 'thermal_c': 10}
SOURCES = {'capacity_ratio': 'controller-probe', 'reachable': 'controller-probe',
           'reliability': 'controller-probe-history', 'memory_mb': 'agent-runtime',
           'thermal_c': 'agent-runtime'}
RANGES = {'capacity_ratio': (0, 1), 'reliability': (0, 1),
          'memory_mb': (0, 1048576), 'thermal_c': (-40, 150)}


def unknown():
    return {name: {'value': None, 'observed_at': None, 'source': source, 'samples': 0}
            for name, source in SOURCES.items()}


def validate(observations):
    """Reject malformed observations; missing measurements use the UNKNOWN shape."""
    if not isinstance(observations, dict) or set(observations) != set(WEIGHTS):
        raise ValueError('invalid_score_observations')
    for name, item in observations.items():
        if (not isinstance(item, dict) or set(item) != {'value', 'observed_at', 'source', 'samples'} or
                item['source'] != SOURCES[name] or type(item['samples']) is not int or
                not 0 <= item['samples'] <= 1000000):
            raise ValueError('invalid_score_observations')
        value, stamp = item['value'], item['observed_at']
        if value is None:
            if stamp is not None or item['samples'] != 0:
                raise ValueError('invalid_score_observations')
            continue
        if type(stamp) is not int or not 0 <= stamp < 2**63 or item['samples'] < 1:
            raise ValueError('invalid_score_observations')
        if name == 'reachable':
            if type(value) is not bool:
                raise ValueError('invalid_score_observations')
        elif (type(value) not in (int, float) or not math.isfinite(value) or
                not RANGES[name][0] <= value <= RANGES[name][1]):
            raise ValueError('invalid_score_observations')
    return observations
