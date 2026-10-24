"""Bounded optional replication extension, preserving all existing authority."""
from ..catalog.common import CatalogError, key, content


def empty():
    return {'schema': 1, 'requests': {}}


def validate(state, doc):
    try:
        if (not isinstance(state,dict) or set(state)-{'moves'}!={'schema','requests'} or
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
                    move['file_id'] not in files or move['state'] not in ('COPY_PENDING','READY')):raise ValueError()
            if move['job_id'] is not None:identifier(move['job_id'])
            for field in ('created_at','updated_at'):
                if type(move[field]) is not int or not 0<=move[field]<2**63:raise ValueError()
        return state
    except (ValueError,KeyError,TypeError,AttributeError):
        raise CatalogError('invalid_replication_projection',409) from None
