"""Bounded optional replication extension, preserving all existing authority."""
from ..catalog.common import CatalogError, key, content


def empty():
    return {'schema': 1, 'requests': {}}


def validate(state, doc):
    try:
        if (not isinstance(state,dict) or set(state)-{'moves','retired'}!={'schema','requests'} or
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
        return state
    except (ValueError,KeyError,TypeError,AttributeError):
        raise CatalogError('invalid_replication_projection',409) from None
