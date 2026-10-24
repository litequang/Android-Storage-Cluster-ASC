"""Owner-only replication API; parent Handler enforces quorum and admin auth."""
from .. import validation as valid


def handle(handler,parts,query):
    if query:raise ValueError()
    service=handler.server.catalog.replication
    if handler.command=='GET' and parts==['status']:
        doc=service.runtime.view()['document']
        return handler._json(200,{'enabled':'replication' in doc,'physical_gc_enabled':False,
                                  'replication_schema':doc.get('replication',{}).get('schema')})
    if handler.command!='POST':return handler._json(404,{'error':'not_found'})
    obj=handler._read_json()
    if parts==['enable']:
        valid.payload(obj,('request_id',));result=service.enable(obj)
    elif parts==['policy']:
        valid.payload(obj,('request_id','file_id','copies'));result=service.policy(obj)
    elif parts==['reconcile']:
        valid.payload(obj,('request_id',));result=service.reconcile(obj)
    else:return handler._json(404,{'error':'not_found'})
    return handler._json(200,result)
