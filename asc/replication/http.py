"""Owner-only replication API; parent Handler enforces quorum and admin auth."""
from .. import validation as valid


def handle(handler,parts,query):
    if query:raise ValueError()
    service=handler.server.catalog.replication
    if handler.command=='GET' and parts==['status']:
        doc=service.runtime.view()['document']
        return handler._json(200,{'enabled':'replication' in doc,'physical_gc_enabled':False,
                                  'replication_schema':doc.get('replication',{}).get('schema')})
    if handler.command=='GET' and parts==['gc-plan']:
        from .planner import plan
        from ..catalog.common import now
        return handler._json(200,plan(service.runtime.view(strong=True),now()))
    if handler.command=='GET' and parts==['moves']:
        return handler._json(200,{'moves':service.runtime.view()['document'].get('replication',{}).get('moves',{})})
    if handler.command!='POST':return handler._json(404,{'error':'not_found'})
    obj=handler._read_json()
    if parts==['enable']:
        valid.payload(obj,('request_id',));result=service.enable(obj)
    elif parts==['policy']:
        valid.payload(obj,('request_id','file_id','copies'));result=service.policy(obj)
    elif parts==['move']:
        valid.payload(obj,('request_id','replica_id'));result=service.move(obj)
    elif parts==['drain']:
        valid.payload(obj,('request_id','node_id'));result=service.drain(obj)
    elif parts==['complete-move']:
        valid.payload(obj,('request_id','move_id'));result=service.complete_move(obj)
    elif parts==['gc-prepare']:
        valid.payload(obj,('request_id','retired_replica_id'));result=handler.server.catalog.gc.prepare(obj)
    elif parts==['gc-confirm']:
        valid.payload(obj,('request_id','plan_id','confirmation'));result=handler.server.catalog.gc.confirm(obj)
    elif parts==['gc-execute']:
        valid.payload(obj,('gc_job_id',));result=handler.server.catalog.gc.execute(obj)
    elif parts==['archive-jobs']:
        valid.payload(obj,('request_id','retired_replica_id'));result=service.archive_jobs(obj)
    elif parts==['reconcile']:
        valid.payload(obj,('request_id',));result=service.reconcile(obj)
    else:return handler._json(404,{'error':'not_found'})
    return handler._json(200,result)
