"""Owner UI projections of the existing Registry/Catalog; no second Catalog or writer."""
import json
import time
from ...catalog.placement import eligible, readable


def fresh(timestamp, maximum, at):
    return type(timestamp) is int and 0 <= at - timestamp <= maximum


def known_number(value):
    return value if type(value) is int and value >= 0 else None


def complete_sum(values):
    return sum(values) if all(v is not None for v in values) else None


class Views:
    def __init__(self, service, cluster_name):
        self.service, self.name = service, cluster_name

    def _nodes(self):
        with self.service.registry.connect() as db:
            lifecycle = [dict(row) for row in db.execute('SELECT node_id,name,state,profile,last_seen,token_version FROM nodes WHERE node_id!=? ORDER BY joined_at,node_id', ('local-controller',))]
            approved = {row['node_id']: dict(row) for row in db.execute('SELECT * FROM catalog_nodes')}
            held = {(row['target_node_id'], row['target_volume_id']): row['bytes'] for row in db.execute("SELECT j.target_node_id,j.target_volume_id,SUM(f.size*2) bytes FROM catalog_jobs j JOIN catalog_files f USING(file_id) WHERE j.state IN ('PENDING','RUNNING','RETRY') GROUP BY j.target_node_id,j.target_volume_id")}
            counts = {row['node_id']: row['n'] for row in db.execute('SELECT node_id,COUNT(*) n FROM catalog_replicas GROUP BY node_id')}
        at = int(time.time())
        result = []
        for row in lifecycle:
            approval = approved.get(row['node_id'])
            online = ('unknown' if not fresh(row['last_seen'], 10**10, at) else
                      'online' if row['state'] == 'active' and at - row['last_seen'] < 100 else 'offline')
            current = bool(approval and row['state'] == 'active' and approval['approved_generation'] == row['token_version'])
            node = {**(approval or {}), **row}
            caps = json.loads(approval['capabilities'] or '{}') if approval else {}
            probe_fresh = current and fresh(approval['checked_at'], 60, at) and approval['last_error'] is None
            volumes = []
            for v in caps.get('volumes', []):
                if v.get('volume_id') not in json.loads(approval['volume_ids']):
                    continue
                measured = probe_fresh and online == 'online' and v.get('state') == 'online'
                values = {key: known_number(v.get(key)) if measured else None for key in ('quota', 'used_bytes', 'free_bytes', 'reserve')}
                available = None
                if measured and v.get('writable') is True and all(x is not None for x in values.values()):
                    available = max(0, min(values['quota'] - values['used_bytes'], values['free_bytes'] - values['reserve']) - held.get((row['node_id'], v['volume_id']), 0))
                volumes.append({'volume_id': v['volume_id'], 'kind': v.get('kind') if probe_fresh and v.get('kind') in ('internal', 'termux_sd') else None,
                                'state': v.get('state') if probe_fresh else 'unknown', 'checked_at': approval['checked_at'],
                                **values, 'available_bytes': available, 'readable': v.get('readable') if measured else None,
                                'writable': v.get('writable') if measured else None})
            result.append({'node_id': row['node_id'], 'name': row['name'], 'online': online, 'lifecycle_state': row['state'],
                           'last_seen': row['last_seen'], 'approved': current, 'storage_approved': current and bool(approval['storage_allowed']),
                           'failure_domain': approval['device_id'] if current else None,
                           'probe_error': ('storage_unavailable' if approval['last_error'] else None) if approval else None,
                           'volumes': volumes, 'recorded_replicas': counts.get(row['node_id'], 0), '_core': node})
        return result

    def file(self, file_id, nodes=None):
        entry = self.service.catalog.file(file_id)  # Keep Core's replica/domain/protection authority.
        nodes = nodes if nodes is not None else self._nodes()
        by_id = {n['node_id']: n for n in nodes}
        replicas = []
        unknown = False
        for r in entry['replicas']:
            node = by_id.get(r['node_id'])
            available = None
            if r['state'] != 'VERIFIED':
                available = False
            elif node:
                core = node['_core']
                if node['online'] == 'offline' or not node['approved'] or core.get('last_error') and fresh(core.get('checked_at'), 60, int(time.time())):
                    available = False
                elif eligible(core):
                    available = readable(core, r['volume_id'])
            unknown |= available is None
            replicas.append({key: r.get(key) for key in ('replica_id', 'node_id', 'volume_id', 'state', 'verified_at')})
            replicas[-1].update(node_name=node['name'] if node else None, available=available,
                                status='available' if available is True else 'unknown' if available is None else 'degraded')
        protected = entry['verified_replicas'] >= 2 and entry['available_replicas'] >= 2
        return {'file_id': entry['file']['file_id'], 'logical_path': entry['file']['logical_path'],
                'size': entry['file']['size'], 'sha256': entry['file']['sha256'], 'version': entry['file']['version'],
                'desired_replicas': entry['desired_replicas'], 'verified_replicas': entry['verified_replicas'],
                'known_available_replicas': entry['available_replicas'],
                'available_replicas': None if unknown else entry['available_replicas'], 'protected': protected,
                'protection': 'protected' if protected else 'unknown' if unknown else 'degraded',
                'state': entry['state'], 'replicas': replicas}

    def state(self):
        nodes = self._nodes()
        with self.service.registry.connect() as db:
            ids = [r[0] for r in db.execute('SELECT file_id FROM catalog_files ORDER BY created_at,file_id LIMIT 257')]
            cluster_id = db.execute("SELECT value FROM settings WHERE key='cluster_id'").fetchone()[0]
        files = [self.file(file_id, nodes) for file_id in ids[:256]]
        volumes = [v for n in nodes if n['storage_approved'] for v in n['volumes']]
        # Free space on multiple volumes in one phone may alias the same filesystem.
        domains = [n['failure_domain'] for n in nodes if n['storage_approved'] for _ in n['volumes']]
        unobserved = any(n['storage_approved'] and not n['volumes'] for n in nodes)
        ambiguous = len(domains) != len(set(domains))
        capacity = {key: None if unobserved else complete_sum([v[field] for v in volumes])
                    for key, field in (('approved_quota_bytes', 'quota'), ('used_bytes', 'used_bytes'), ('available_bytes', 'available_bytes'))}
        if ambiguous:
            capacity['available_bytes'] = None
        public = [{k: v for k, v in n.items() if k != '_core'} for n in nodes]
        return {'cluster': {'name': self.name, 'cluster_id': cluster_id, 'controller': 'online', 'mode': 'single-writer-demo'},
                'as_of': int(time.time()), 'nodes': public, 'files': files, 'files_truncated': len(ids) > 256,
                'counts': {'paired_nodes': len(nodes), 'online': sum(n['online'] == 'online' for n in nodes),
                           'offline': sum(n['online'] == 'offline' for n in nodes), 'unknown': sum(n['online'] == 'unknown' for n in nodes),
                           'files': len(ids) if len(ids) <= 256 else None,
                           'protected_files': sum(f['protected'] for f in files), 'unprotected_files': sum(not f['protected'] for f in files)},
                'capacity': capacity, 'capacity_note': 'shared_filesystem_unknown' if ambiguous else None,
                'node_approval': 'CLI only; owner confirms physical failure domain'}
