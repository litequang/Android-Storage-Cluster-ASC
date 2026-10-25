"""Small owner-only runtime API. No destination path/restore/write-authority API."""
from .format import FIELDS, integer, fail
from ..catalog.common import CatalogError, digest, identifier
from ..replication.proofs import survivors
from .. import validation as valid


def handle(handler, parsed):
    if not parsed.path.startswith('/catalog/v1/external/'):
        return False
    if parsed.query or parsed.fragment or handler.command!='POST':
        raise ValueError()
    if not handler._admin():return True
    obj=handler._read_json();service=handler.server.catalog;runtime=service.runtime
    action=parsed.path.removeprefix('/catalog/v1/external/')
    with runtime.operation() as view:
        if action=='capture':
            valid.payload(obj,())
            # Exact nested payload survives RuntimeHandler's transport labels.
            with runtime.lock:
                view=runtime.ensure_ready()
                state=view['state']
                result={'capture':{'document':view['document'],
                    'state':{k:state[k] for k in ('index','term','document_sha256')}}}
        elif action=='read':
            valid.payload(obj,('cluster_id','epoch','file'))
            if (obj['cluster_id'],obj['epoch'])!=(runtime.cluster,runtime.epoch):fail('external_source_identity_mismatch')
            descriptor=obj['file']
            if type(descriptor) is not dict or set(descriptor)!=set(FIELDS):raise ValueError()
            file_id=identifier(descriptor['file_id']);candidates=[]
            with runtime.lock:
                doc=runtime.ensure_ready()['document']
                file=next((f for f in doc['catalog']['files'] if f['file_id']==file_id),None)
                if file is None or descriptor!={k:file[k] for k in FIELDS}:fail('external_source_mismatch')
                # Owner explicit archive scope includes TRASH/EXPIRED versions;
                # ordinary user downloads retain their existing lifecycle gate.
                for replica,node in survivors(doc,file_id):
                    client=service._client(replica['node_id'],replica['volume_id'],'audit',replica['local_file_id'])
                    candidates.append({'origin':client.origin,'pin':client.pin,'grant':client.grant,
                        'volume_id':replica['volume_id'],'local_file_id':replica['local_file_id'],
                        'replica_id':replica['replica_id'],'node_id':replica['node_id'],
                        'timeout':service.timeout,'rate':service.rate})
            if not candidates:fail('external_source_unavailable',503)
            result={'candidates':candidates}
        elif action=='check':
            valid.payload(obj,('cluster_id','epoch','source_index'));integer(obj['source_index'],1)
            current=runtime.ensure_ready()
            if ((obj['cluster_id'],obj['epoch'])!=(runtime.cluster,runtime.epoch) or
                    current['state']['index']<obj['source_index']):fail('external_source_identity_mismatch')
            result={'current_authority':True,'current_index':current['state']['index'],
                    'writer_recovery_supported':False}
        else:raise CatalogError('not_found',404)
        handler._json(200,result)
    return True
