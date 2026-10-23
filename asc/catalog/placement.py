"""Conservative placement from controller-probed, owner-approved capability records."""
import json
from .common import now


def active_nodes(db):
    return [dict(row) for row in db.execute(
        'SELECT c.*,n.state,n.last_seen,n.token_version,n.profile FROM catalog_nodes c JOIN nodes n USING(node_id)')]


def eligible(node):
    try:
        profile = json.loads(node['profile'])
        return (node['state'] == 'active' and now() - node['last_seen'] < 100 and
                node['approved_generation'] == node['token_version'] and
                profile.get('protected') is not True and node['last_error'] is None and
                node['checked_at'] is not None and now() - node['checked_at'] <= 60)
    except (ValueError, TypeError, KeyError, AttributeError):
        return False


def readable(node,volume_id):
    if not eligible(node):return False
    try:
        return any(v.get('volume_id')==volume_id and v.get('state')=='online' and v.get('readable') is True
                   for v in json.loads(node['capabilities'] or '{}').get('volumes',[]))
    except (ValueError,TypeError,AttributeError):return False


def candidates(db, size, exclude_devices=()):
    result = []
    for node in active_nodes(db):
        if not eligible(node) or not node['storage_allowed'] or node['device_id'] in exclude_devices:
            continue
        capabilities = json.loads(node['capabilities'] or '{}')
        if type(capabilities.get('max_upload_bytes')) is not int or capabilities['max_upload_bytes'] < size:
            continue
        # Queue counts are real observations; unmeasured external CPU/load remains unknown.
        running = db.execute("SELECT COUNT(*) FROM catalog_jobs WHERE state='RUNNING' AND target_node_id=?",
                             (node['node_id'],)).fetchone()[0]
        if running:
            continue
        for volume in capabilities.get('volumes', []):
            if volume.get('state') != 'online' or volume.get('writable') is not True:
                continue
            values = [volume.get(k) for k in ('free_bytes', 'quota', 'reserve', 'used_bytes')]
            if any(type(v) is not int or v < 0 for v in values):
                continue
            free, quota, reserve, used = values
            held = db.execute("SELECT COALESCE(SUM(f.size*2),0) FROM catalog_jobs j JOIN catalog_files f USING(file_id) "
                              "WHERE j.target_node_id=? AND j.target_volume_id=? AND j.state IN ('PENDING','RUNNING','RETRY')",
                              (node['node_id'], volume['volume_id'])).fetchone()[0]
            available = min(free - reserve, quota - used) - held
            if available >= size * 2:
                result.append({'node_id': node['node_id'], 'device_id': node['device_id'],
                               'volume_id': volume['volume_id'], 'available_bytes': available,
                               'origin': node['origin'], 'pin': node['pin']})
    return sorted(result, key=lambda r: (-r['available_bytes'], r['node_id'], r['volume_id']))
