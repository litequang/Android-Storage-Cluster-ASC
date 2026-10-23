"""Non-authoritative suggested node functions. Never confers consensus authority."""
import math


def recommend(nodes):
    """Suggest a topology from observed node profiles; never changes permissions."""
    recommendations = []
    possible = []
    for item in nodes:
        profile = item['profile']
        role = profile.get('recommended_role')
        if item.get('state') == 'revoked':
            suggested = 'excluded-revoked'
            reason = 'Credential revoked; no active duties permitted'
        elif profile.get('protected') or role == 'production-protected':
            suggested = 'hosting-protected-observer'
            reason = 'Production hosting must not be assigned heavy or auto-voter duties'
        elif role == 'unsupported':
            suggested = 'excluded'
            reason = 'Android/runtime capacity below baseline requirements'
        elif role == 'archive-only':
            suggested = 'offline-archive-candidate'
            reason = 'Older/low-resource Android, manual periodic backup only'
        elif not item.get('online'):
            suggested = 'standby-offline'
            reason = 'Node not recently connected; cannot be picked for an active duty'
        elif role in ('controller-candidate', 'backup-and-voter-candidate',
                      'storage-and-voter-candidate', 'general-storage-candidate'):
            suggested = 'voter-candidate'
            reason = 'Hardware appears suitable; eligibility still requires actual runtime tests'
            score = profile.get('readiness_score')
            # v0.4 stored arbitrary self-reported profiles; do not crash on legacy data.
            if type(score) not in (int, float) or not 0 <= score <= 100 or not math.isfinite(score):
                score = -1  # Internal sort sentinel, never reported as runtime telemetry.
            possible.append((score, item['node_id']))
        else:
            suggested = 'backup-storage-candidate'
            reason = 'Suggested from baseline device family and current presence'
        recommendations.append({'node_id': item['node_id'], 'node_name': item['name'],
                                'suggested_role': suggested, 'reason': reason})
    if possible:
        # Priority is purely advisory; the live controller is NEVER changed by scoring.
        chosen = sorted(possible, key=lambda pair: (-pair[0], pair[1]))[0][1]
        for r in recommendations:
            if r['node_id'] == chosen:
                r['suggested_role'] = 'preferred-controller-candidate'
                r['reason'] = 'Highest current advisory score among suitable online nodes; no election has taken place'
                break
    return recommendations
