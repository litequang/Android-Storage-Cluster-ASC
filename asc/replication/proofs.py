"""Current independent survivor evidence, not a cached destructive permission."""
import json
from ..catalog.common import CatalogError, now
from ..catalog.placement import readable
from ..client import ClientError


def physical(replica):
    return replica['node_id'],replica['volume_id'],replica['local_file_id']


def nodes(doc):
    lifecycle={n['node_id']:n for n in doc['tables']['nodes']}
    return {n['node_id']:{**n,**{k:lifecycle[n['node_id']][k] for k in ('state','last_seen','token_version','profile')}}
            for n in doc['tables']['catalog_nodes'] if n['node_id'] in lifecycle}


def survivors(doc,file_id,exclude=(),exclude_devices=()):
    approved=nodes(doc)
    return [(r,approved[r['node_id']]) for r in doc['catalog']['replicas'] if r['file_id']==file_id and
            r['replica_id'] not in exclude and r['state']=='VERIFIED' and r['node_id'] in approved and
            approved[r['node_id']]['device_id'] not in exclude_devices and
            r['volume_id'] in json.loads(approved[r['node_id']]['volume_ids']) and
            readable(approved[r['node_id']],r['volume_id'])]


def verify(service,doc,file_id,exclude,required,exclude_devices=()):
    file=next(f for f in doc['catalog']['files'] if f['file_id']==file_id)
    proofs=[];domains=set()
    for replica,node in survivors(doc,file_id,exclude,exclude_devices=exclude_devices):
        if node['device_id'] in domains:continue
        try:
            client=service._client(replica['node_id'],replica['volume_id'],'audit',replica['local_file_id'])
            result=service._proof(client,replica['local_file_id'],replica['volume_id'],
                           '_asc-global/'+file_id+'/'+replica['replica_id'],file)
            if result.get('physically_verified') is not True:raise CatalogError('survivor_verification_required',409)
        except (CatalogError,ClientError,OSError,ValueError):continue
        proofs.append({**{k:replica[k] for k in ('replica_id','node_id','volume_id','local_file_id')},
                       'device_id':node['device_id'],'generation':node['token_version'],
                       'size':file['size'],'sha256':file['sha256'],'verified_at':now()})
        domains.add(node['device_id'])
        if len(domains)>=required:return proofs
    raise CatalogError('survivor_verification_required',409)


def recheck(doc,file_id,proofs,exclude,required,exclude_devices=()):
    current={r['replica_id']:(r,n) for r,n in survivors(doc,file_id,exclude,exclude_devices=exclude_devices)}
    domains=set()
    file=next(f for f in doc['catalog']['files'] if f['file_id']==file_id)
    for proof in proofs:
        pair=current.get(proof['replica_id'])
        if not pair:raise CatalogError('survivor_proof_changed',409)
        replica,node=pair
        if (physical(proof)!=physical(replica) or proof['device_id']!=node['device_id'] or
                proof['generation']!=node['token_version'] or
                (proof['size'],proof['sha256'])!=(file['size'],file['sha256']) or
                not 0<=now()-proof['verified_at']<=120):
            raise CatalogError('survivor_proof_changed',409)
        domains.add(proof['device_id'])
    if len(domains)<required:raise CatalogError('survivor_verification_required',409)
