"""Guarded GC planning/confirmation. Physical execution is separately unavailable."""
import copy
from .planner import graph
from .proofs import verify,recheck,nodes
from .arena import require_controller
from ..catalog.common import CatalogError, digest, identifier, key, now, uid


def confirmation(plan_id,plan_sha256):
    return 'DELETE-ISOLATED-TEST-OBJECT:'+plan_id+':'+plan_sha256


class GarbageCollection:
    def __init__(self,replication):
        self.replication=replication;self.service=replication.service;self.runtime=replication.runtime

    def prepare(self,obj):
        identifier(obj['retired_replica_id']);key(obj.get('request_id'))
        action='gc-prepare';intent=digest({'action':action,'payload':obj})
        self.service.refresh()
        with self.runtime.operation() as view:
            doc=view['document'];extension=doc.get('replication')
            if extension is None:raise CatalogError('phase3c_not_enabled',409)
            previous=extension['requests'].get(obj['request_id'])
            if previous:
                if previous['intent']!=intent:raise CatalogError('request_id_conflict',409)
                return copy.deepcopy(previous['result'])
            retired=extension.get('retired',{}).get(obj['retired_replica_id'])
            if not retired:raise CatalogError('retired_replica_not_found',404)
            rows,_=graph(doc,now());candidate=next(r for r in rows if r['retired_replica_id']==obj['retired_replica_id'])
            if not candidate['eligible']:raise CatalogError('gc_references_held',409)
            file_id=retired['file']['file_id'];required=self.replication.required(doc,file_id)
            excluded={nodes(doc)[retired['replica']['node_id']]['device_id']}
            proofs=verify(self.service,doc,file_id,{obj['retired_replica_id']},required,exclude_devices=excluded)
            proof_term=doc['authority']['term']
        def change(doc,extension,view):
            if doc['authority']['term']!=proof_term:raise CatalogError('stale_survivor_proof',409)
            rows,graph_sha=graph(doc,now())
            candidate=next(r for r in rows if r['retired_replica_id']==obj['retired_replica_id'])
            if not candidate['eligible']:raise CatalogError('gc_references_held',409)
            required=self.replication.required(doc,file_id)
            recheck(doc,file_id,proofs,{obj['retired_replica_id']},required,exclude_devices=excluded)
            if len(extension.get('gc_plans',{}))>=64:raise CatalogError('gc_plan_limit',409)
            stamp=now();plan_id=uid()
            record={'plan_id':plan_id,'retired_replica_id':obj['retired_replica_id'],
                    'graph_sha256':graph_sha,'term':proof_term,'generated_at':stamp,'expires_at':stamp+60,
                    'source_control_revision':doc['revision'],'source_applied_index':view['state']['index'],
                    'required_domains':required,'proofs':proofs}
            record['plan_sha256']=digest(record)
            extension.setdefault('gc_plans',{})[plan_id]=record
            return {'plan_id':plan_id,'plan_sha256':record['plan_sha256'],'expires_at':record['expires_at'],
                    'required_confirmation':confirmation(plan_id,record['plan_sha256']),'physical_deletions':0}
        return self.replication.edit(action,obj,change)

    def confirm(self,obj):
        require_controller(self.service)
        identifier(obj['plan_id']);key(obj.get('request_id'))
        def change(doc,extension,view):
            plan=extension.get('gc_plans',{}).get(obj['plan_id'])
            if not plan:raise CatalogError('gc_plan_not_found',404)
            if obj['confirmation']!=confirmation(obj['plan_id'],plan['plan_sha256']):raise CatalogError('gc_confirmation_required',409)
            if not plan['generated_at']<=now()<plan['expires_at']:raise CatalogError('gc_plan_expired',409)
            if plan['term']!=doc['authority']['term']:raise CatalogError('stale_gc_plan',409)
            rows,graph_sha=graph(doc,now())
            row=next(r for r in rows if r['retired_replica_id']==plan['retired_replica_id'])
            if graph_sha!=plan['graph_sha256'] or not row['eligible']:raise CatalogError('stale_gc_plan',409)
            retired=extension['retired'][plan['retired_replica_id']]
            required=max(plan['required_domains'],self.replication.required(doc,retired['file']['file_id']))
            excluded={nodes(doc)[retired['replica']['node_id']]['device_id']}
            recheck(doc,retired['file']['file_id'],plan['proofs'],{plan['retired_replica_id']},required,exclude_devices=excluded)
            existing=next((j for j in extension.get('gc_jobs',{}).values() if j['retired_replica_id']==plan['retired_replica_id']),None)
            if existing:return {'gc_job_id':existing['gc_job_id'],'state':existing['state'],'physical_deletions':0}
            if len(extension.get('gc_jobs',{}))>=128:raise CatalogError('gc_job_limit',409)
            job_id=uid();stamp=now()
            extension.setdefault('gc_jobs',{})[job_id]={'gc_job_id':job_id,'retired_replica_id':plan['retired_replica_id'],
                'plan_id':plan['plan_id'],'plan_sha256':plan['plan_sha256'],'confirmed_graph_sha256':graph_sha,
                'confirmed_term':doc['authority']['term'],'state':'RESERVED','created_at':stamp,'updated_at':stamp,
                'required_domains':required,'permit_term':None,'permit_hash':None,'run_id':None,'permit_expires_at':None,
                'proofs':[],'attempts':0,'last_error':None,'completed_at':None}
            return {'gc_job_id':job_id,'state':'RESERVED','physical_deletions':0}
        return self.replication.edit('gc-confirm',obj,change)
