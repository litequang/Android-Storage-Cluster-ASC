"""Short-lived file/job-scoped credentials; raw node/admin secrets never leave their owner."""
import hashlib
import json
import secrets
from .common import CatalogError, now
from .state import insert


def mint(registry, node_id, volume_id, side, local_file_id=None, job=None, ttl=120):
    raw, stamp = secrets.token_urlsafe(32), now()
    with registry.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        node = db.execute('SELECT n.*,c.approved_generation,c.storage_allowed,c.volume_ids FROM nodes n '
                          'JOIN catalog_nodes c USING(node_id) WHERE node_id=?',(node_id,)).fetchone()
        if (not node or node['state']!='active' or not node['storage_allowed'] or
                node['token_version']!=node['approved_generation'] or
                json.loads(node['profile']).get('protected') is True or volume_id not in json.loads(node['volume_ids'])):
            raise CatalogError('node_not_approved',403)
        db.execute('DELETE FROM transfer_grants WHERE expires_at<=?',(stamp,))
        if db.execute('SELECT COUNT(*) FROM transfer_grants').fetchone()[0]>=4096:
            raise CatalogError('transfer_grant_limit',429)
        expires = min(stamp+ttl,job['lease_until']) if job else stamp+ttl
        insert(db,'transfer_grants',{'grant_hash':hashlib.sha256(raw.encode()).hexdigest(),
            'node_id':node_id,'volume_id':volume_id,'node_generation':node['token_version'],
            'job_id':job['job_id'] if job else None,'side':side,'run_token':job['run_token'] if job else None,
            'local_file_id':local_file_id,'expires_at':expires})
    return raw


def authorize(db, node, grant_hash, volume_id, operation, scope):
    row=db.execute('SELECT * FROM transfer_grants WHERE grant_hash=?',(grant_hash,)).fetchone()
    if (not row or row['node_id']!=node['node_id'] or row['volume_id']!=volume_id or
            row['node_generation']!=node['token_version'] or row['expires_at']<=now() or not isinstance(scope,dict) or
            set(scope)!={'method','resource'}):
        return None
    method, resource = scope.get('method'), scope.get('resource')
    if not isinstance(method,str) or not isinstance(resource,str):
        return None
    approved=db.execute('SELECT * FROM catalog_nodes WHERE node_id=?',(node['node_id'],)).fetchone()
    if (not approved or not approved['storage_allowed'] or approved['approved_generation']!=node['token_version'] or
            volume_id not in json.loads(approved['volume_ids'])):
        return None
    if row['side']=='inspect':
        allowed = operation=='list' and method=='GET' and resource in ('status','files','inventory')
        return {'principal':'catalog-inspect','expires_at':row['expires_at'],'constraints':{'kind':'inspect'}} if allowed else None
    job=None
    if row['job_id']:
        job=db.execute('SELECT j.*,f.size,f.sha256 FROM catalog_jobs j JOIN catalog_files f USING(file_id) WHERE job_id=?',
                       (row['job_id'],)).fetchone()
        if (not job or job['run_token']!=row['run_token'] or job['lease_until']<=now() or
                job['state'] not in ('PENDING','RUNNING','RETRY')):
            return None
        if job['kind']=='COPY' and job['state']!='RUNNING':
            return None
    if row['side'] in ('read','source','audit'):
        local=row['local_file_id']
        allowed=(method=='GET' and operation=='read' and resource in ('files/'+local,'files/'+local+'/content') or
                 method=='POST' and operation=='verify' and resource=='files/'+local+'/verify')
        return {'principal':'catalog-read','expires_at':row['expires_at'],'constraints':{'kind':'read'}} if allowed else None
    if row['side']!='target' or not job or job['target_node_id']!=node['node_id'] or job['target_volume_id']!=volume_id:
        return None
    allowed=operation=='write' and (resource=='uploads' and method=='POST' or
        resource.startswith('uploads/') and method in ('GET','PUT','POST'))
    if job['target_local_file_id']:
        local=job['target_local_file_id']
        allowed=allowed or method=='GET' and operation=='read' and resource in ('files/'+local,'files/'+local+'/content')
        allowed=allowed or method=='POST' and operation=='verify' and resource=='files/'+local+'/verify'
    if not allowed:
        return None
    return {'principal':'job:'+job['job_id'],'expires_at':row['expires_at'],
            'constraints':{'kind':'target','idempotency_key':job['idempotency_key'],'logical_path':job['logical_path'],
                'size':job['size'],'sha256':job['sha256'],'session_id':job['target_session_id'],
                'local_file_id':job['target_local_file_id']}}
