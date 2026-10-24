"""Replay-safe replication policy through existing actual-term quorum CAS."""
import copy
import json
import threading

from . import state
from ..catalog.common import CatalogError, digest, identifier, key, POLICIES, now, uid
from ..catalog.state import Catalog
from ..failover.state import prepare_registry, export


class Replication:
    def __init__(self, service):
        self.service,self.runtime=service,service.runtime
        self._tick=threading.Lock()

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

    @staticmethod
    def required(doc,file_id):
        file=next(f for f in doc['catalog']['files'] if f['file_id']==file_id)
        required=POLICIES[file['policy']]
        backup=doc.get('backup',{})
        for job in backup.get('jobs',{}).values():
            snapshot=backup.get('snapshots',{}).get(job['snapshot_id'])
            if (job['kind']=='BACKUP' and snapshot and snapshot['state']!='EXPIRED' and
                    any(f['file_id']==file_id for f in snapshot['files'])):
                required=max(required,job['copies'])
        return required

    def plan_moves(self,doc,extension,replica_ids):
        from ..catalog.placement import active_nodes,candidates,readable
        results=[];blocked=[]
        def apply(reg,catalog):
            nodes={n['node_id']:n for n in active_nodes(reg.db)}
            for replica_id in replica_ids:
                previous=next((i for i,m in extension.get('moves',{}).items() if m['source_replica_id']==replica_id),None)
                if previous:results.append(previous);continue
                source=reg.db.execute('SELECT * FROM catalog_replicas WHERE replica_id=?',(replica_id,)).fetchone()
                if not source:raise CatalogError('replica_not_found',404)
                file=catalog._file(reg.db,source['file_id'])
                replicas=[dict(r) for r in reg.db.execute('SELECT * FROM catalog_replicas WHERE file_id=?',(source['file_id'],))]
                survivors={nodes[r['node_id']]['device_id'] for r in replicas if r['replica_id']!=replica_id and
                           r['state']=='VERIFIED' and r['node_id'] in nodes and readable(nodes[r['node_id']],r['volume_id'])}
                job_id=None
                if len(survivors)<self.required(doc,file['file_id']):
                    occupied={nodes[r['node_id']]['device_id'] for r in replicas if r['node_id'] in nodes}
                    pending=reg.db.execute("SELECT target_node_id FROM catalog_jobs WHERE file_id=? AND state!='COMPLETED'",(file['file_id'],))
                    occupied.update(nodes[r[0]]['device_id'] for r in pending if r[0] in nodes)
                    targets=candidates(reg.db,file['size'],occupied)
                    if not targets:
                        blocked.append({'replica_id':replica_id,'reason':'no_independent_eligible_target'});continue
                    job_id=catalog._new_job(reg.db,file['file_id'],targets[0],source=replica_id)
                if len(extension.get('moves',{}))>=128:raise CatalogError('move_limit',409)
                move_id=uid();stamp=now()
                extension.setdefault('moves',{})[move_id]={'source_replica_id':replica_id,'file_id':file['file_id'],
                    'job_id':job_id,'state':'COPY_PENDING' if job_id else 'READY','created_at':stamp,'updated_at':stamp}
                results.append(move_id)
            return {'move_ids':results,'blocked_replicas':blocked,'physical_deletions':0}
        return self.workspace(doc,apply)

    def move(self,obj):
        identifier(obj['replica_id']);self.service.refresh()
        return self.edit('move',obj,lambda d,s,v:self.plan_moves(d,s,[obj['replica_id']]))

    def drain(self,obj):
        from .. import validation as valid
        node_id=valid.node_id(obj['node_id']);self.service.refresh()
        def change(doc,extension,view):
            if 'insights' not in doc:raise CatalogError('phase3b_not_enabled',409)
            node=next((n for n in doc['tables']['nodes'] if n['node_id']==node_id),None)
            if not node:raise CatalogError('node_not_found',404)
            doc['insights'].setdefault('preferences',{})[node_id]={'mode':'drain','generation':node['token_version'],'updated_at':now()}
            replica_ids=[r['replica_id'] for r in doc['catalog']['replicas'] if r['node_id']==node_id]
            return self.plan_moves(doc,extension,replica_ids)
        return self.edit('drain',obj,change)

    def complete_move(self,obj):
        from .proofs import verify,recheck,physical,nodes
        from ..nodes.preferences import effective
        identifier(obj['move_id']);key(obj.get('request_id'))
        self.service.refresh()
        view=self.runtime.view();doc=view['document']
        move=doc.get('replication',{}).get('moves',{}).get(obj['move_id'])
        if not move:raise CatalogError('move_not_found',404)
        if move['state']=='RETIRED':
            return self.edit('complete-move',obj,lambda d,s,v:{'move_id':obj['move_id'],'state':'RETIRED','physical_deletions':0})
        if move['job_id']:
            job=next((j for j in doc['tables']['catalog_jobs'] if j['job_id']==move['job_id']),None)
            if not job or job['state']!='COMPLETED':raise CatalogError('copy_not_verified',409)
        source_id=move['source_replica_id'];file_id=move['file_id']
        proofs=verify(self.service,doc,file_id,{source_id},self.required(doc,file_id))
        proof_term=doc['authority']['term']
        self.service.refresh()
        def change(doc,extension,view):
            if doc['authority']['term']!=proof_term:raise CatalogError('stale_survivor_proof',409)
            move=extension['moves'][obj['move_id']]
            if move['state']=='RETIRED':return {'move_id':obj['move_id'],'state':'RETIRED','physical_deletions':0}
            source=next((r for r in doc['catalog']['replicas'] if r['replica_id']==source_id),None)
            if not source:raise CatalogError('source_replica_changed',409)
            node=nodes(doc).get(source['node_id'])
            if (not node or json.loads(node['profile']).get('protected') is True or
                    effective(doc.get('insights',{}),node['node_id'],node['token_version'])=='protected'):
                raise CatalogError('protected_replica',403)
            for job in doc['tables']['catalog_jobs']:
                if job['state']=='COMPLETED':continue
                if (job['source_replica_id']==source_id or
                        (job['target_node_id'],job['target_volume_id'],job['target_local_file_id'])==physical(source)):
                    raise CatalogError('replica_in_flight',409)
            required=self.required(doc,file_id)
            recheck(doc,file_id,proofs,{source_id},required)
            if len(extension.get('retired',{}))>=256:raise CatalogError('retirement_limit',409)
            file=next(f for f in doc['catalog']['files'] if f['file_id']==file_id)
            stamp=now()
            record={'replica':dict(source),'file':{k:file[k] for k in ('file_id','logical_path','version','size','sha256')},
                    'required_domains':required,'proofs':proofs,'retired_at':stamp,'term':proof_term}
            def retire(reg,catalog):
                reg.db.execute('DELETE FROM catalog_replicas WHERE replica_id=?',(source_id,))
                catalog._event(reg.db,file_id);reg.db.commit()
            self.workspace(doc,retire)
            extension.setdefault('retired',{})[source_id]=record
            move.update(state='RETIRED',updated_at=stamp)
            return {'move_id':obj['move_id'],'state':'RETIRED','physical_deletions':0}
        return self.edit('complete-move',obj,change)

    def tick(self):
        if not self._tick.acquire(blocking=False):return
        try:
            doc=self.runtime.view()['document']
            jobs={j['job_id']:j for j in doc['tables']['catalog_jobs']}
            for move_id,move in doc.get('replication',{}).get('moves',{}).items():
                if (move['state']!='RETIRED' and (move['job_id'] is None or
                        jobs.get(move['job_id'],{}).get('state')=='COMPLETED')):
                    return self.complete_move({'move_id':move_id,'request_id':'move-retire-'+move_id})
        finally:self._tick.release()

    def archive_jobs(self,obj):
        from .archive import record
        from .proofs import physical
        identifier(obj['retired_replica_id'])
        def change(doc,extension,view):
            retired=extension.get('retired',{}).get(obj['retired_replica_id'])
            if not retired:raise CatalogError('retired_replica_not_found',404)
            target=physical(retired['replica']);replica_id=obj['retired_replica_id']
            jobs=[j for j in doc['tables']['catalog_jobs'] if j['source_replica_id']==replica_id or j['replica_id']==replica_id or
                  (j['target_node_id'],j['target_volume_id'],j['target_local_file_id'])==target]
            if any(j['state']!='COMPLETED' for j in jobs):raise CatalogError('job_still_retains_object',409)
            if len(extension.get('archived_jobs',{}))+len(jobs)>512:raise CatalogError('job_archive_limit',409)
            archives={j['job_id']:record(j,now()) for j in jobs}
            def apply(reg,catalog):
                for job_id in archives:
                    # COMPLETED already denies these job grants; revoke retained rows too.
                    reg.db.execute('DELETE FROM transfer_grants WHERE job_id=?',(job_id,))
                    reg.db.execute('DELETE FROM catalog_jobs WHERE job_id=?',(job_id,))
            self.workspace(doc,apply)
            extension.setdefault('archived_jobs',{}).update(archives)
            return {'archived_job_ids':list(archives),'physical_deletions':0,'history_retained':True}
        return self.edit('archive-jobs',obj,change)
