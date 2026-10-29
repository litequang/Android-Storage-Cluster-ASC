"""Bounded optional replication extension, preserving all existing authority."""
from ..catalog.common import CatalogError, key, content, digest


def empty():
    return {'schema': 1, 'requests': {}}


def validate(state, doc):
    try:
        if (not isinstance(state,dict) or set(state)-{'moves','retired','archived_jobs','gc_plans','gc_jobs'}!={'schema','requests'} or
                type(state['schema']) is not int or state['schema']!=1 or
                not isinstance(state['requests'],dict) or len(state['requests'])>256):
            raise ValueError()
        for request,receipt in state['requests'].items():
            key(request)
            if set(receipt)!={'intent','result'} or not isinstance(receipt['result'],dict):raise ValueError()
            content(0,receipt['intent'])
        from ..catalog.common import identifier
        moves=state.get('moves',{})
        if not isinstance(moves,dict) or len(moves)>128:raise ValueError()
        files={f['file_id'] for f in doc['catalog']['files']}
        for move_id,move in moves.items():
            identifier(move_id);identifier(move['source_replica_id']);identifier(move['file_id'])
            if (set(move)!={'source_replica_id','file_id','job_id','state','created_at','updated_at'} or
                    move['file_id'] not in files or move['state'] not in ('COPY_PENDING','READY','RETIRED')):raise ValueError()
            if move['job_id'] is not None:identifier(move['job_id'])
            for field in ('created_at','updated_at'):
                if type(move[field]) is not int or not 0<=move[field]<2**63:raise ValueError()
        from .proofs import physical
        from ..catalog.metadata import REPLICA_FIELDS
        retired=state.get('retired',{})
        if not isinstance(retired,dict) or len(retired)>256:raise ValueError()
        physical_ids=set()
        for replica_id,row in retired.items():
            identifier(replica_id)
            if set(row)!={'replica','file','required_domains','proofs','retired_at','term'}:raise ValueError()
            replica=row['replica'];file=row['file']
            if set(replica)!=REPLICA_FIELDS or replica['replica_id']!=replica_id:raise ValueError()
            for field in ('replica_id','file_id','volume_id','local_file_id'):identifier(replica[field])
            if set(file)!={'file_id','logical_path','version','size','sha256'}:raise ValueError()
            if not any(all(f[k]==v for k,v in file.items()) for f in doc['catalog']['files']):raise ValueError()
            if replica['file_id']!=file['file_id']:raise ValueError()
            if type(row['required_domains']) is not int or not 1<=row['required_domains']<=3:raise ValueError()
            if not isinstance(row['proofs'],list) or not row['required_domains']<=len(row['proofs'])<=3:raise ValueError()
            domains=set()
            for proof in row['proofs']:
                if set(proof)!={'replica_id','node_id','volume_id','local_file_id','device_id','generation','size','sha256','verified_at'}:raise ValueError()
                for field in ('replica_id','volume_id','local_file_id'):identifier(proof[field])
                if (proof['size'],proof['sha256'])!=(file['size'],file['sha256']):raise ValueError()
                if type(proof['generation']) is not int or proof['generation']<1:raise ValueError()
                if type(proof['verified_at']) is not int or not 0<=proof['verified_at']<=row['retired_at']:raise ValueError()
                if not isinstance(proof['device_id'],str) or not 1<=len(proof['device_id'])<=64:raise ValueError()
                domains.add(proof['device_id'])
            if len(domains)<row['required_domains']:raise ValueError()
            for field in ('retired_at','term'):
                if type(row[field]) is not int or not 0<=row[field]<2**63:raise ValueError()
            if row['term']<1 or physical(replica) in physical_ids:raise ValueError()
            physical_ids.add(physical(replica))
        if any(r['replica_id'] in retired or physical(r) in physical_ids for r in doc['catalog']['replicas']):
            raise CatalogError('retired_object_reintroduction',409)
        for job in doc['tables']['catalog_jobs']:
            if job['state']=='COMPLETED':continue
            if (job['source_replica_id'] in retired or
                    (job['target_node_id'],job['target_volume_id'],job['target_local_file_id']) in physical_ids):
                raise CatalogError('retired_object_reintroduction',409)
        for move in moves.values():
            if (move['state']=='RETIRED') != (move['source_replica_id'] in retired):raise ValueError()
            if move['state']!='RETIRED' and not any(r['replica_id']==move['source_replica_id'] and r['file_id']==move['file_id'] for r in doc['catalog']['replicas']):raise ValueError()
        archives=state.get('archived_jobs',{})
        if not isinstance(archives,dict) or len(archives)>512:raise ValueError()
        current_jobs={j['job_id'] for j in doc['tables']['catalog_jobs']}
        for job_id,record in archives.items():
            identifier(job_id)
            if (set(record)!={'job_id','file_id','kind','state','created_at','updated_at','archived_at','original_sha256','completion_sha256'} or
                    record['job_id']!=job_id or record['file_id'] not in files or record['kind'] not in ('UPLOAD','COPY') or
                    record['state']!='COMPLETED' or job_id in current_jobs):raise ValueError()
            for field in ('created_at','updated_at','archived_at'):
                if type(record[field]) is not int or not 0<=record[field]<2**63:raise ValueError()
            content(0,record['original_sha256']);content(0,record['completion_sha256'])
        plans=state.get('gc_plans',{});gc_jobs=state.get('gc_jobs',{})
        if not isinstance(plans,dict) or len(plans)>64 or not isinstance(gc_jobs,dict) or len(gc_jobs)>128:raise ValueError()
        for plan_id,plan in plans.items():
            identifier(plan_id)
            if (set(plan)!={'plan_id','retired_replica_id','graph_sha256','term','generated_at','expires_at',
                           'source_control_revision','source_applied_index','required_domains','proofs','plan_sha256'} or
                    plan['plan_id']!=plan_id or plan['retired_replica_id'] not in retired or
                    plan['plan_sha256']!=digest({k:v for k,v in plan.items() if k!='plan_sha256'})):
                raise ValueError()
            content(0,plan['graph_sha256'])
            for field in ('term','generated_at','expires_at','source_control_revision','source_applied_index'):
                if type(plan[field]) is not int or not 0<=plan[field]<2**63:raise ValueError()
            if plan['term']<1 or plan['expires_at']!=plan['generated_at']+60:raise ValueError()
            _proofs(plan['proofs'],retired[plan['retired_replica_id']]['file'],plan['required_domains'],plan['generated_at'])
        targets=set()
        for job_id,job in gc_jobs.items():
            identifier(job_id)
            if (set(job)!={'gc_job_id','retired_replica_id','plan_id','plan_sha256','confirmed_graph_sha256','confirmed_term',
                          'state','created_at','updated_at','required_domains','permit_term','permit_hash','run_id',
                          'permit_expires_at','proofs','attempts','last_error','completed_at'} or job['gc_job_id']!=job_id or
                    job['retired_replica_id'] not in retired or job['plan_id'] not in plans or
                    job['state'] not in ('RESERVED','RUNNING','DONE')):raise ValueError()
            plan=plans[job['plan_id']]
            if not plan['generated_at']<=job['created_at']<plan['expires_at']:raise ValueError()
            if (job['retired_replica_id']!=plan['retired_replica_id'] or job['plan_sha256']!=plan['plan_sha256'] or
                    job['confirmed_graph_sha256']!=plan['graph_sha256'] or job['confirmed_term']!=plan['term'] or
                    job['retired_replica_id'] in targets):raise ValueError()
            targets.add(job['retired_replica_id'])
            for field in ('created_at','updated_at','attempts','confirmed_term'):
                if type(job[field]) is not int or not 0<=job[field]<2**63:raise ValueError()
            if type(job['required_domains']) is not int or not plan['required_domains']<=job['required_domains']<=3:raise ValueError()
            if job['state']=='RESERVED':
                if any(job[f] is not None for f in ('permit_term','permit_hash','run_id','permit_expires_at','completed_at')) or job['proofs']:raise ValueError()
            else:
                identifier(job['run_id']);content(0,job['permit_hash'])
                for field in ('permit_term','permit_expires_at'):
                    if type(job[field]) is not int or job[field]<1:raise ValueError()
                if job['state']=='RUNNING' and (job['permit_term']!=doc['authority']['term'] or job['completed_at'] is not None or not job['updated_at']<job['permit_expires_at']<=job['updated_at']+120):raise ValueError()
                _proofs(job['proofs'],retired[job['retired_replica_id']]['file'],job['required_domains'],job['updated_at'])
                if job['state']=='DONE' and (type(job['completed_at']) is not int or job['completed_at']<job['created_at']):raise ValueError()
            if job['last_error'] not in (None,'controller_restart','execution_unconfirmed'):raise ValueError()
        return state
    except (ValueError,KeyError,TypeError,AttributeError):
        raise CatalogError('invalid_replication_projection',409) from None


def transition(before,after):
    """Monotone retirement/receipt/history fences across all Runtime writers."""
    old=before.get('replication')
    if old is None:return
    new=after.get('replication')
    if new is None:raise CatalogError('replication_downgrade_forbidden',409)
    for field in ('requests','retired','archived_jobs','gc_plans'):
        for key,value in old.get(field,{}).items():
            if new.get(field,{}).get(key)!=value:raise CatalogError('replication_history_changed',409)
    for move_id,move in old.get('moves',{}).items():
        current=new.get('moves',{}).get(move_id)
        if not current or any(current[k]!=move[k] for k in ('source_replica_id','file_id','job_id','created_at')):
            raise CatalogError('replication_history_changed',409)
        if move['state']=='RETIRED' and current['state']!='RETIRED':raise CatalogError('replication_history_changed',409)
    previous=before['catalog'];current=after['catalog']
    if not previous['revision']<=current['revision']<=previous['revision']+1024:
        raise CatalogError('catalog_transition_invalid',409)
    events={e['revision']:e for e in current['events']}
    for event in previous['events']:
        if event['revision']>current['revision']-1024 and events.get(event['revision'])!=event:
            raise CatalogError('retained_history_changed',409)
    if current['revision']>previous['revision']:
        first=events.get(previous['revision']+1)
        if not first or first['previous_digest']!=previous['head_digest']:
            raise CatalogError('catalog_transition_invalid',409)

    from .archive import record as archive_record
    previous_jobs={j['job_id']:j for j in before['tables']['catalog_jobs']}
    current_jobs={j['job_id']:j for j in after['tables']['catalog_jobs']}
    for job_id,job in previous_jobs.items():
        if job_id in current_jobs:continue
        archived=new.get('archived_jobs',{}).get(job_id)
        if (job['state']!='COMPLETED' or not archived or archived!=archive_record(job,archived['archived_at'])):
            raise CatalogError('job_reference_removed_without_archive',409)
    for job_id,record in new.get('archived_jobs',{}).items():
        if job_id not in old.get('archived_jobs',{}):
            job=previous_jobs.get(job_id)
            if not job or job['state']!='COMPLETED' or record!=archive_record(job,record['archived_at']):
                raise CatalogError('job_archive_not_proven',409)

    for job_id,job in old.get('gc_jobs',{}).items():
        current=new.get('gc_jobs',{}).get(job_id)
        if not current:raise CatalogError('gc_reservation_removed',409)
        for field in ('gc_job_id','retired_replica_id','plan_id','plan_sha256','confirmed_graph_sha256','confirmed_term','created_at'):
            if current[field]!=job[field]:raise CatalogError('gc_reservation_changed',409)
        if job['state']=='DONE' and current!=job:raise CatalogError('gc_completion_changed',409)
        if current['attempts']<job['attempts'] or current['required_domains']<job['required_domains']:raise CatalogError('gc_attempt_rollback',409)


def _proofs(proofs,file,required,stamp):
    from ..catalog.common import identifier
    if type(required) is not int or not 1<=required<=3 or not isinstance(proofs,list) or not required<=len(proofs)<=3:raise ValueError()
    domains=set()
    for proof in proofs:
        if set(proof)!={'replica_id','node_id','volume_id','local_file_id','device_id','generation','size','sha256','verified_at'}:raise ValueError()
        for field in ('replica_id','volume_id','local_file_id'):identifier(proof[field])
        if (proof['size'],proof['sha256'])!=(file['size'],file['sha256']):raise ValueError()
        if type(proof['generation']) is not int or proof['generation']<1:raise ValueError()
        if type(proof['verified_at']) is not int or not 0<=proof['verified_at']<=stamp:raise ValueError()
        if not isinstance(proof['device_id'],str) or not 1<=len(proof['device_id'])<=64:raise ValueError()
        domains.add(proof['device_id'])
    if len(domains)<required:raise ValueError()


def takeover(state):
    import copy
    result=copy.deepcopy(state)
    for job in result.get('gc_jobs',{}).values():
        if job['state']!='DONE':
            job.update(state='RESERVED',permit_term=None,permit_hash=None,run_id=None,permit_expires_at=None,
                       proofs=[],completed_at=None,last_error='controller_restart')
    return result
