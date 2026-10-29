"""Checkpoint-bound replica reduction proposals; no apply, grants or filesystem IO."""
import json
from ..catalog.common import CatalogError, POLICIES, identifier
from ..catalog.placement import readable
from ..backup.state import pinned, status
from .preferences import effective
from .scoring import score
from .view import observations


def preview(view, file_id, at):
    identifier(file_id)
    doc=view['document'];catalog=doc['catalog']
    file=next((f for f in catalog['files'] if f['file_id']==file_id),None)
    if file is None:raise CatalogError('file_not_found',404)
    replicas=[r for r in catalog['replicas'] if r['file_id']==file_id]
    backup=doc.get('backup');insights=doc.get('insights',{})
    holds=[]
    if view.get('stale',True):holds.append('stale_view')
    if backup and file_id in pinned(backup):holds.append('retained_snapshot_or_restore')
    if backup and status(backup,file_id) != 'LIVE':holds.append('retained_or_expired_version_requires_separate_review')
    if any(j['file_id']==file_id and j['state'] != 'COMPLETED' for j in doc['tables']['catalog_jobs']):
        holds.append('unfinished_catalog_job')
    if backup and any(j['kind']=='RESTORE' and j['source_file_id']==file_id and j['state']!='COMPLETED'
                      for j in backup['jobs'].values()):holds.append('unfinished_restore')
    lifecycle={n['node_id']:n for n in doc['tables']['nodes']}
    nodes={n['node_id']:{**n,**{k:lifecycle[n['node_id']][k] for k in ('state','last_seen','token_version','profile')}}
           for n in doc['tables']['catalog_nodes'] if n['node_id'] in lifecycle}
    valid=[];held=[]
    for replica in replicas:
        node=nodes.get(replica['node_id'])
        if (replica['state']!='VERIFIED' or node is None or
                replica['volume_id'] not in json.loads(node['volume_ids']) or
                not readable(node,replica['volume_id'],at=at) or
                type(replica['verified_at']) is not int or not 0<=at-replica['verified_at']<=300):
            held.append({'replica_id':replica['replica_id'],'reason':'unavailable_suspect_or_stale_proof'})
            continue
        pref=effective(insights,node['node_id'],node['token_version'])
        report=score(observations(doc,lifecycle[node['node_id']]),at)
        valid.append({'replica_id':replica['replica_id'],'device_id':node['device_id'],'preference':pref,
                      'ranking_points':(report['score'] or 0)*report['confidence']/100})
    required=POLICIES[file['policy']]
    domains={r['device_id'] for r in valid}
    if len(domains)<required:holds.append('insufficient_current_independent_domains')
    # Keep strongest approved independent domains, favoring protected/preferred copies.
    preference_rank={'protected':0,'preferred':1,'auto':2,'avoid-new-storage':3,'drain':4}
    ranked=sorted(valid,key=lambda r:(preference_rank[r['preference']],-r['ranking_points'],r['replica_id']))
    keep=[];kept_domains=set()
    for row in ranked:
        if row['device_id'] not in kept_domains and len(kept_domains)<required:
            keep.append(row['replica_id']);kept_domains.add(row['device_id'])
    candidates=[]
    for row in ranked:
        if row['replica_id'] in keep:continue
        if row['preference']=='protected':
            held.append({'replica_id':row['replica_id'],'reason':'protected_preference'})
        elif not holds:
            candidates.append({**row,'reason':'excess_after_retaining_policy_independent_domains',
                               'requires_fresh_byte_verification':True})
    return {'preview_schema':1,'file_id':file_id,'version':file['version'],'policy':file['policy'],
            'required_domains':required,'available_domains':len(domains),'keep_replica_ids':keep,
            'candidates':candidates,'holds':holds,'held_replicas':held,
            'dry_run':True,'apply_supported':False,'physical_deletions':0,
            'cluster_id':doc['cluster_id'],'epoch':doc['epoch'],'revision':catalog['revision'],
            'control_revision':doc['revision'],'applied_index':view['state']['index'],
            'term':view['state']['term'],'stale':view.get('stale',True),'read_only':True,
            'evaluated_at':at,'verification_evidence':'historical; never authorizes deletion'}
