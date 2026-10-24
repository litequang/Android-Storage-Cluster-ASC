"""Replay-safe replication policy through existing actual-term quorum CAS."""
import copy

from . import state
from ..catalog.common import CatalogError, digest, identifier, key, POLICIES
from ..catalog.state import Catalog
from ..failover.state import prepare_registry, export


class Replication:
    def __init__(self, service):
        self.service,self.runtime=service,service.runtime

    def edit(self, action, obj, change, enable=False):
        request=key(obj.get('request_id'))
        intent=digest({'action':action,'payload':obj})
        with self.runtime.lock,self.runtime.operation() as view:
            doc=copy.deepcopy(view['document'])
            if 'replication' not in doc:
                if not enable:raise CatalogError('phase3c_not_enabled',409)
                doc['replication']=state.empty()
            extension=doc['replication']
            if request in extension['requests']:
                receipt=extension['requests'][request]
                if receipt['intent']!=intent:raise CatalogError('request_id_conflict',409)
                return copy.deepcopy(receipt['result'])
            if len(extension['requests'])>=256:raise CatalogError('replication_request_limit',409)
            result=change(doc,extension,view)
            extension['requests'][request]={'intent':intent,'result':result}
            doc['revision']+=1
            self.runtime.commit(view,doc,'replication-'+digest(request),intent)
            return result

    @staticmethod
    def workspace(doc, change):
        reg=prepare_registry(doc)
        try:
            result=change(reg,Catalog(reg))
            prepared=export(reg.db,doc['revision'],doc['authority'])
            for field in ('catalog','tables','inventory_cursor'):
                doc[field]=prepared[field]
            return result
        finally:reg.db.close()

    def enable(self,obj):
        return self.edit('enable',obj,lambda d,s,v:{'enabled':True,'replication_schema':1,
                         'physical_gc_enabled':False},enable=True)

    def policy(self,obj):
        identifier(obj['file_id'])
        count=obj['copies']
        if type(count) is not int or count not in (1,2,3):raise ValueError('invalid_replica_count')
        self.service.refresh()
        def change(doc,extension,view):
            def apply(reg,catalog):
                policy=next(name for name,n in POLICIES.items() if n==count)
                catalog.mutate('POLICY',{'file_id':obj['file_id'],'policy':policy})
                scheduled=catalog.schedule(obj['file_id'])
                report=catalog.file(obj['file_id'])
                return {k:report[k] for k in ('desired_replicas','verified_replicas','available_replicas')}|{
                    'file_id':obj['file_id'],'policy':policy,'scheduled_jobs':scheduled,'physical_deletions':0}
            return self.workspace(doc,apply)
        return self.edit('policy',obj,change)

    def reconcile(self,obj):
        self.service.refresh()
        def change(doc,extension,view):
            def apply(reg,catalog):
                from ..backup.state import status
                reports=[]
                for file in list(doc['catalog']['files']):
                    if status(doc.get('backup',{'files':{}}),file['file_id'])=='EXPIRED':continue
                    scheduled=catalog.schedule(file['file_id'])
                    report=catalog.file(file['file_id'])
                    reports.append({'file_id':file['file_id'],'desired_replicas':report['desired_replicas'],
                                    'available_replicas':report['available_replicas'],'scheduled_jobs':scheduled})
                return {'files':reports,'physical_deletions':0}
            return self.workspace(doc,apply)
        return self.edit('reconcile',obj,change)
