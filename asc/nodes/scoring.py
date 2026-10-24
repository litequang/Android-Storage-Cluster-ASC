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


def score(observations, at):
    """Compute explainable advisory score without IO, clock sampling or mutation."""
    validate(observations)
    if type(at) is not int or not 0 <= at < 2**63:
        raise ValueError('invalid_score_time')
    components, total, known, confidence = {}, 0, 0, 0
    for name, weight in WEIGHTS.items():
        item = observations[name]
        value, stamp = item['value'], item['observed_at']
        fresh = value is not None and 0 <= at - stamp <= FRESH_SECONDS
        normalized = None
        if fresh:
            if name in ('capacity_ratio', 'reliability'):
                normalized = value * 100
            elif name == 'reachable':
                normalized = 100 if value else 0
            elif name == 'memory_mb':
                normalized = min(100, value * 100 / 8192)
            else:
                normalized = max(0, min(100, (65 - value) * 100 / 30))
            total += weight * normalized
            known += weight
            confidence += weight * (min(1, item['samples']/10) if name == 'reliability' else 1)
        components[name] = {**item, 'status': 'KNOWN' if fresh else 'UNKNOWN',
                            'normalized': normalized, 'weight': weight,
                            'weighted_points': None if normalized is None else round(normalized*weight/100, 4)}
    return {'score_schema': SCHEMA, 'score': round(total/known, 2) if known else None,
            'confidence': round(confidence, 2),
            'reliability': components['reliability']['normalized'],
            'known_weight': known, 'evaluated_at': at, 'advisory_only': True,
            'components': components}
