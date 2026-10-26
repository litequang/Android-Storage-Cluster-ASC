"""Shared Core heartbeat transport with an explicit configuration/profile.

No process HOME, hardware discovery, filesystem, credential creation, thread or
runtime bootstrap. Host wrappers retain their device/ownership/storage guards
and metadata-cache persistence. A successful heartbeat is NOT storage approval,
byte proof, Leader/writer authority or automatic failover permission.
"""
from .client import ClientError, request_json


def heartbeat(config, profile, *, send=None):
    """Existing agent_once wire/cluster checks, reusable by trusted native hosts.

    Optional send is trusted in-process transport injection for the single-writer
    route, never an IPC argument. Distributed routing remains the existing pinned
    Discovery implementation; this helper does not change membership or fencing.
    """
    if 'controllers' in config:
        from .failover.discovery import Discovery
        snapshot = Discovery(config['cluster_id'], config['controllers'], config['token']).request(
            'POST', '/api/v1/heartbeat', {'node_id': config['node_id'], 'profile': profile})
    else:
        transport = request_json if send is None else send
        snapshot = transport(config['controller'], config['pin'], 'POST', '/api/v1/heartbeat',
                             {'node_id': config['node_id'], 'profile': profile}, token=config['token'])
    if snapshot['cluster_id'] != config['cluster_id']:
        raise ClientError('Cluster ID mismatch; refusing snapshot')
    return snapshot
