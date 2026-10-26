"""Canonical retry-safe enrollment payload and acceptance, shared by local hosts.

No HOME, interactive prompt, filesystem, device override or enrollment authority.
Registry.join remains the sole server transaction. Callers persist the returned
private operation BEFORE sending and retain it on any transport/response failure.
"""
import copy
import secrets

from .client import ClientError
from . import validation as valid


def new_pending(origin, pin, expected_cluster, name, profile, code, *,
                target=None, cluster=None, controllers=None):
    """Keep the existing CLI private pending format1 and wire payload exactly."""
    pending = {'config_version': 1, 'controller': origin, 'pin': pin,
               'target_node_id': target, 'cluster_id': cluster,
               'expected_cluster_id': expected_cluster,
               'payload': {'protocol_version': 1, 'code': code, 'name': name,
                           'profile': copy.deepcopy(profile),
                           'enrollment_id': secrets.token_urlsafe(32),
                           'enrollment_token': secrets.token_urlsafe(32)}}
    if target:
        pending['payload']['node_id'] = target
    if controllers:
        pending['controllers'] = copy.deepcopy(controllers)
    return pending


def accepted_identity(pending, reply):
    """Exact operation token/cluster/target checks before any identity publication.

    Transport supplies a pinned reply. This does not approve storage/domain,
    import Controller state or confer quorum/writer authority.
    """
    target = pending.get('target_node_id')
    if (reply['cluster_id'] != pending['expected_cluster_id'] or
            (target and reply['node_id'] != target) or
            reply['token'] != pending['payload']['enrollment_token']):
        raise ClientError('Enrollment response mismatch; preserve pending operation for recovery')
    valid.node_id(reply['node_id'])
    return {'config_version': 1, 'controller': pending['controller'], 'pin': pending['pin'],
            'node_id': reply['node_id'], 'token': reply['token'],
            'token_version': reply['token_version'], 'cluster_id': reply['cluster_id']}
