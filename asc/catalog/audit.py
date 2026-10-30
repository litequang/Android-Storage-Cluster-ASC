"""Canonical physical readback shared by backup adapters; no writer authority."""
from .common import CatalogError, now
from .placement import active_nodes, readable
from ..client import ClientError


def verify_file(service, file_id, copies=1):
    entry = service.catalog.file(file_id)
    with service.registry.connect() as db:
        nodes = {n['node_id']: n for n in active_nodes(db)}
    domains, source = [], None
    for replica in entry['replicas']:
        node = nodes.get(replica['node_id'])
        if replica['state'] != 'VERIFIED' or not node or not readable(node, replica['volume_id']) or node['device_id'] in domains:
            continue
        try:
            client = service._client(replica['node_id'], replica['volume_id'], 'audit', replica['local_file_id'])
            service._proof(client, replica['local_file_id'], replica['volume_id'],
                '_asc-global/'+file_id+'/'+replica['replica_id'], entry['file'])
            domains.append(node['device_id'])
            source = source or (client, replica)
            if len(domains) >= copies:
                return {'file_id': file_id, 'sha256': entry['file']['sha256'], 'size': entry['file']['size'],
                        'domains': domains, 'verified_at': now()}, source
        except (OSError, ValueError, CatalogError, ClientError) as exc:
            service._bad_replica(replica, exc)
    raise CatalogError('backup_unavailable', 503)
