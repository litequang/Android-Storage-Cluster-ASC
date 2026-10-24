"""Read-only node insights derived from one validated runtime document."""
import json
import math

from .scoring import unknown, score


def observations(doc, node):
    result = unknown()
    approved = next((n for n in doc['tables']['catalog_nodes'] if n['node_id'] == node['node_id']), None)
    if node['state'] != 'active' or not approved or approved['approved_generation'] != node['token_version']:
        return result
    def put(name, value, stamp, samples=1):
        if value is not None and type(stamp) is int:
            result[name].update(value=value, observed_at=stamp, samples=samples)
    stamp = approved['checked_at']
    if stamp is not None:
        put('reachable', approved['last_error'] is None, stamp)
    if stamp is not None and approved['last_error'] is None:
        ratios = []
        caps = json.loads(approved['capabilities'] or '{}')
        for volume in caps.get('volumes', []):
            values = [volume.get(k) for k in ('free_bytes', 'quota', 'reserve', 'used_bytes')]
            if (volume.get('state') == 'online' and volume.get('writable') is True and
                    all(type(v) is int and v >= 0 for v in values)):
                free, quota, reserve, used = values
                if quota:
                    ratios.append(max(0, min(1, min(free-reserve, quota-used)/quota)))
        if ratios:
            put('capacity_ratio', max(ratios), stamp)
    profile = json.loads(node['profile'])
    # Explicit runtime RAM only; never preset/readiness_score or assumed RAM.
    ram = profile.get('memory_mb')
    if type(ram) in (int, float) and math.isfinite(ram) and 0 <= ram <= 1048576:
        put('memory_mb', ram, node['last_seen'])
    from .history import summary
    state = doc.get('insights')
    if state:
        latest = state['history'].get(node['node_id'])
        if latest and latest['generation'] == node['token_version']:
            report = summary(state, node['node_id'], '24h', latest['last_sample_at'])
            if report['probe_samples']:
                put('reliability', report['reliability']/100, latest['last_sample_at'], report['probe_samples'])
    return result


def scores(view, at):
    doc = view['document']
    return {'nodes': [{'node_id': n['node_id'], **score(observations(doc, n), at)}
                      for n in doc['tables']['nodes']],
            'cluster_id': doc['cluster_id'], 'epoch': doc['epoch'],
            'revision': doc['catalog']['revision'], 'control_revision': doc['revision'],
            'applied_index': view['state']['index'], 'term': view['state']['term'],
            'stale': view.get('stale', True), 'read_only': True}
