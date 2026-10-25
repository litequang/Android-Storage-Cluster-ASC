"""Sanitized read-only projection, reusing existing Catalog and Dashboard views."""
from contextlib import closing
from types import SimpleNamespace
import time
from ..catalog.state import Catalog
from ..failover.state import prepare_registry
from ..demo.dashboard.views import Views


def unavailable(state='UNKNOWN',cluster_id=None,epoch=None):
    return {'observer_version':1,'read_only':True,'writer_authority':False,
        'cluster':{'name':'ASC Core','cluster_id':cluster_id,'controller':'unknown','mode':'core-quorum'},
        'as_of':int(time.time()),'nodes':[],'files':[],'files_truncated':False,
        'counts':{k:None for k in ('paired_nodes','online','offline','unknown','files','protected_files','unprotected_files')},
        'capacity':{k:None for k in ('approved_quota_bytes','used_bytes','available_bytes')},
        'runtime':{'state':state,'quorum_available':None,'strong_read_confirmed':False,'leader_confirmed':False,
                   'leader_id':None,'controllers':[],'epoch':epoch},
        'jobs':[],'jobs_truncated':False,'backup':{'enabled':None,'snapshots':[],'jobs':[],
            'external':{'state':'UNKNOWN','verified_at':None},'recovery':{'state':'UNKNOWN','writer_authority':False}},
        'node_approval':'Read-only observer; no approval or mutation route'}


def downgrade(result,state):
    import copy
    result=copy.deepcopy(result)
    result['runtime'].update(state=state,quorum_available=None,strong_read_confirmed=False,leader_confirmed=False,leader_id=None)
    result['cluster']['controller']='unknown'
    for item in result['nodes']:
        item['online']='unknown'
        for volume in item['volumes']:
            volume.update(state='unknown',readable=None,writable=None,available_bytes=None,free_bytes=None)
    for file in result['files']:
        file.update(available_replicas=None,protected=None,protection='unknown')
        for replica in file['replicas']:replica.update(available=None,status='unknown')
    result['counts'].update(online=None,offline=None,unknown=None,protected_files=None,unprotected_files=None)
    result['capacity']['available_bytes']=None
    return result


def project(view,strong=False):
    doc=view['document']
    # Existing disposable Core SQL projection only, never a persistent Catalog.
    registry=prepare_registry(doc)
    try:
        registry.db.execute('PRAGMA query_only=ON')
        service=SimpleNamespace(registry=registry,catalog=Catalog(registry))
        result=Views(service,'ASC Core').state()
    finally:registry.db.close()
    result.update(observer_version=1,read_only=True,writer_authority=False)
    result['cluster'].update(mode='core-quorum',controller='online' if strong else 'unknown')
    result['runtime']={'state':'ONLINE' if strong else 'UNKNOWN','quorum_available':True if strong else None,
        'strong_read_confirmed':strong,'leader_confirmed':False,'leader_id':None,'epoch':doc['epoch'],
        'checkpoint':{k:view['state'][k] for k in ('index','term','document_sha256')},'control_revision':doc['revision'],'controllers':[]}
    for file in result['files']:
        available=file['available_replicas']
        file['protected']=(file['verified_replicas']>=file['desired_replicas'] and available>=file['desired_replicas']) if available is not None else None
        file['protection']='unknown' if file['protected'] is None else 'protected' if file['protected'] else 'degraded'
    known=not result['files_truncated'] and all(f['protected'] is not None for f in result['files'])
    result['counts'].update(protected_files=sum(f['protected'] is True for f in result['files']) if known else None,
                            unprotected_files=sum(f['protected'] is False for f in result['files']) if known else None)
    if strong and (result['counts']['offline'] or any(f['protected'] is False for f in result['files'])):
        result['runtime']['state']='DEGRADED'
    result['jobs']=[{k:j[k] for k in ('job_id','file_id','kind','state','updated_at')} for j in doc['tables']['catalog_jobs'][:100]]
    result['jobs_truncated']=len(doc['tables']['catalog_jobs'])>100
    backup=doc.get('backup')
    result['backup']={'enabled':backup is not None,
        'snapshots':[{'snapshot_id':sid,'state':s['state'],'created_at':s['manifest']['created_at'],'verified_at':s['verified_at'],'source_index':s['manifest']['source_index']} for sid,s in backup['snapshots'].items()] if backup else [],
        'jobs':[{'job_id':jid,'kind':j['kind'],'state':j['state'],'updated_at':j['updated_at']} for jid,j in backup['jobs'].items()] if backup else [],
        'external':{'state':'UNKNOWN','verified_at':None},'recovery':{'state':'NOT_ACTIVATED','writer_authority':False}}
    if backup:
        from ..backup.state import status as version_status
        for file in result['files']:file['version_state']=version_status(backup,file['file_id'])
    result['node_approval']='Core read-only observer; owner approval remains outside browser'
    return result if strong else downgrade(result,'UNKNOWN')


def observe(runtime,strong=False):
    """No ensure_ready, operation, commit, takeover, grants or worker activation."""
    from ..catalog.common import CatalogError
    status=None;confirmed=False;quorum=None;error=None
    try:status=runtime.client.status()
    except CatalogError:pass
    try:
        view=runtime.view(strong=strong)
        if strong:
            after=runtime.client.status()
            if (status and status['cluster_id']==runtime.cluster and after['cluster_id']==runtime.cluster and
                    status['node_id']==runtime.node_id==after['node_id'] and status['role']==after['role']=='Leader' and
                    int(status['term'])==int(after['term']) and not status['quarantined'] and not after['quarantined']):
                confirmed=True;quorum=True;status=after
    except CatalogError as exc:
        if strong and exc.code=='quorum_read_unavailable':quorum=False
        error='strong_read_unavailable' if strong else 'observation_unavailable'
        try:view=runtime.view()
        except CatalogError:
            result=unavailable(cluster_id=runtime.cluster,epoch=runtime.epoch)
            result['controller']={'node_id':runtime.node_id,'state':'UNKNOWN','role':None,'voter_process':'UNKNOWN','leader_confirmed':False}
            return result
    result=project(view,confirmed)
    authority=view['document']['authority']
    leader=bool(confirmed and authority=={'node_id':runtime.node_id,'term':int(status['term'])})
    result['runtime'].update(quorum_available=quorum,strong_read_confirmed=confirmed,leader_confirmed=leader,
                             leader_id=runtime.node_id if leader else None)
    if confirmed and not leader:result['runtime']['state']='DEGRADED'
    if quorum is False:result['runtime']['state']='QUORUM UNAVAILABLE'
    result['controller']={'node_id':runtime.node_id,'state':'ONLINE' if status else 'UNKNOWN',
        'role':status['role'] if status else None,'voter_process':'ONLINE' if status else 'UNKNOWN',
        'term':int(status['term']) if status else None,'leader_confirmed':leader,'error':error}
    return result
