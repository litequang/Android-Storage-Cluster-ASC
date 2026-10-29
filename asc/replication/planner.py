"""Pure full-reference GC plan. No reference eviction, grants or filesystem IO."""
from collections import defaultdict
import json
from ..catalog.common import digest, CatalogError
from ..backup.state import status
from .proofs import physical, nodes, survivors
from ..catalog.placement import readable
from ..nodes.preferences import effective


def references(doc, at):
    index=defaultdict(list);files=defaultdict(list)
    replicas={r['replica_id']:r for r in doc['catalog']['replicas']}
    replicas.update({k:r['replica'] for k,r in doc.get('replication',{}).get('retired',{}).items()})
    backup=doc.get('backup',{})
    for row in doc['catalog']['replicas']:
        lifecycle=status(backup or {'files':{}},row['file_id'])
        index[physical(row)].append(({'LIVE':'live_version','TRASH':'trash_version','EXPIRED':'retained_version'}[lifecycle],row['file_id']))
    for file_id,row in backup.get('files',{}).items():
        if row['state']=='TRASH':files[file_id].append(('trash_pin',file_id))
    for snapshot_id,snapshot in backup.get('snapshots',{}).items():
        if snapshot['state']!='EXPIRED':
            for file in snapshot['files']:files[file['file_id']].append(('snapshot_pin',snapshot_id))
    for job_id,job in backup.get('jobs',{}).items():
        # Includes terminal jobs: retained evidence is never silently ignored.
        ids={p['file_id'] for p in job['proofs']}
        ids.update(f for f in (job['source_file_id'],job['target_file_id']) if f is not None)
        snapshot=backup.get('snapshots',{}).get(job['snapshot_id'])
        if snapshot:ids.update(f['file_id'] for f in snapshot['files'])
        for file_id in ids:files[file_id].append(('backup_job_reference',job_id))
    for job in doc['tables']['catalog_jobs']:
        target=(job['target_node_id'],job['target_volume_id'],job['target_local_file_id'])
        if job['target_local_file_id'] is not None:index[target].append(('catalog_job_reference',job['job_id']))
        source=replicas.get(job['source_replica_id'])
        if source:index[physical(source)].append(('catalog_job_reference',job['job_id']))
        target_replica=replicas.get(job['replica_id'])
        if target_replica:index[physical(target_replica)].append(('catalog_job_reference',job['job_id']))
    for grant in doc['tables']['transfer_grants']:
        if grant['expires_at']>at and grant['local_file_id'] is not None:
            index[(grant['node_id'],grant['volume_id'],grant['local_file_id'])].append(('in_flight_grant',grant['grant_hash']))
    for job_id,job in doc.get('replication',{}).get('gc_jobs',{}).items():
        for proof in job['proofs']:index[physical(proof)].append(('gc_survivor_job_reference',job_id))
    for event in doc['catalog']['events']:
        for replica in event['payload']['replicas']:
            index[physical(replica)].append(('retained_history',str(event['revision'])))
    return index,files


def graph(doc, at):
    from .service import Replication
    index,file_pins=references(doc,at)
    approved=nodes(doc);rows=[]
    for replica_id,retired in sorted(doc.get('replication',{}).get('retired',{}).items()):
        replica=retired['replica'];file=retired['file']
        refs=sorted(set(index.get(physical(replica),[])+file_pins.get(file['file_id'],[])))
        hold_codes={code for code,_ in refs}
        target=approved.get(replica['node_id'])
        excluded_domains={target['device_id']} if target else set()
        remaining=survivors(doc,file['file_id'],{replica_id},exclude_devices=excluded_domains)
        required=Replication.required(doc,file['file_id'])
        if len({n['device_id'] for _,n in remaining})<required:hold_codes.add('insufficient_current_independent_domains')
        target=approved.get(replica['node_id'])
        if (not target or target['state']!='active' or not target['storage_allowed'] or
                json.loads(target['profile']).get('protected') is True or target['token_version']!=target['approved_generation'] or
                replica['volume_id'] not in json.loads(target['volume_ids'])):
            hold_codes.add('target_identity_not_approved')
        elif not readable(target,replica['volume_id'],at=at):hold_codes.add('target_not_current')
        elif effective(doc.get('insights',{}),target['node_id'],target['token_version'])=='protected':hold_codes.add('protected_preference')
        # The source is never inferred from unknown inventory; only durable retirements qualify.
        for job_id,job in doc.get('replication',{}).get('gc_jobs',{}).items():
            if job['retired_replica_id']==replica_id:
                hold_codes.add('gc_already_completed' if job['state']=='DONE' else 'gc_reserved')
        holds=sorted(hold_codes)
        rows.append({'retired_replica_id':replica_id,'node_id':replica['node_id'],
                     'volume_id':replica['volume_id'],'local_file_id':replica['local_file_id'],
                     'file_id':file['file_id'],'logical_bytes':file['size'],'required_domains':required,
                     'holds':holds,'eligible':not holds,
                     'reference_counts':{code:sum(c==code for c,_ in refs) for code in sorted({c for c,_ in refs})},
                     'reference_examples':{code:[i for c,i in refs if c==code][:8] for code in sorted({c for c,_ in refs})}})
    # Bind all relevant live versions/approvals/generations/preferences and every exact pin,
    # excluding changing counters, nonce receipts and unrelated inspect/read grants.
    basis={'cluster_id':doc['cluster_id'],'epoch':doc['epoch'],'files':doc['catalog']['files'],
           'replicas':doc['catalog']['replicas'],'retired':doc.get('replication',{}).get('retired',{}),
           'nodes':[{k:n[k] for k in ('node_id','state','token_version','profile')} for n in doc['tables']['nodes']],
           'approvals':[{k:n[k] for k in ('node_id','device_id','origin','pin','storage_allowed','approved_generation','volume_ids')} for n in doc['tables']['catalog_nodes']],
           'preferences':doc.get('insights',{}).get('preferences',{}),
           'eligibility':[(r['retired_replica_id'],r['holds'],r['required_domains']) for r in rows],
           'references':[(rid,sorted(set(index.get(physical(r['replica']),[])+file_pins.get(r['file']['file_id'],[]))))
                         for rid,r in sorted(doc.get('replication',{}).get('retired',{}).items())]}
    return rows,digest(basis)


def plan(view,at):
    doc=view['document']
    if 'replication' not in doc:raise CatalogError('phase3c_not_enabled',409)
    rows,graph_sha=graph(doc,at)
    if view.get('stale',True):
        for row in rows:row['holds']=sorted(set(row['holds'])|{'stale_view'});row['eligible']=False
    result={'gc_plan_schema':1,'cluster_id':doc['cluster_id'],'epoch':doc['epoch'],
            'term':doc['authority']['term'],'control_revision':doc['revision'],
            'applied_index':view['state']['index'],'generated_at':at,'expires_at':at+60,
            'graph_sha256':graph_sha,'candidates':rows,'stale':view.get('stale',True),
            'eligible_logical_bytes':sum(r['logical_bytes'] for r in rows if r['eligible']),
            'held_logical_bytes':sum(r['logical_bytes'] for r in rows if not r['eligible']),
            'physical_deletions':0,'physical_gc_enabled':False,
            'unknown_or_native_count':None,'unknown_or_native_objects':'HELD; not eligible without proven retirement provenance'}
    result['plan_sha256']=digest(result)
    return result
