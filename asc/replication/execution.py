"""Confirmed synthetic GC execution and fresh exact-object quorum authority."""
import copy
import hashlib
import hmac
import json
import secrets

from .arena import require_controller
from .planner import graph
from .proofs import nodes, verify, recheck
from ..catalog.common import CatalogError, digest, identifier, now, uid
from ..storage.client import StorageClient
from ..client import ClientError


def contract(doc, job):
    retired=doc['replication']['retired'][job['retired_replica_id']]
    replica,file=retired['replica'],retired['file']
    return {'kind':'gc','gc_job_id':job['gc_job_id'],'retired_replica_id':job['retired_replica_id'],
            **{k:replica[k] for k in ('node_id','volume_id','local_file_id')},
            **{k:file[k] for k in ('file_id','size','sha256')},
            'logical_path':'_asc-global/'+file['file_id']+'/'+job['retired_replica_id'],
            'cluster_id':doc['cluster_id'],'epoch':doc['epoch'],'plan_sha256':job['plan_sha256'],
            **{k:job[k] for k in ('permit_term','run_id','permit_expires_at')}}


def permit_hash(raw,target,volume_id):
    return digest({'grant_sha256':hashlib.sha256(raw.encode()).hexdigest(),'volume_id':volume_id,
                   **{k:target[k] for k in ('node_id','token_version','approved_generation','device_id','origin','pin')}})


def proof_fingerprint(doc):
    # Bind every reference, policy and approval plus effective protection. The
    # self-reported storage/free-space heartbeat is not destructive authority.
    # Actual freshness/readability still runs in _target and proofs.recheck.
    binding={**doc,'tables':{**doc['tables'],'nodes':[
        {**node,'profile':json.dumps({'protected':json.loads(node['profile']).get('protected')})}
        for node in doc['tables']['nodes']]}}
    return graph(binding,now())[1]


class GCExecution:
    def _target(self,doc,job_id):
        job=doc.get('replication',{}).get('gc_jobs',{}).get(job_id)
        if not job:raise CatalogError('gc_job_not_found',404)
        rows,_=graph(doc,now())
        row=next(r for r in rows if r['retired_replica_id']==job['retired_replica_id'])
        if set(row['holds'])-{'gc_reserved'}:raise CatalogError('gc_references_held',409)
        retired=doc['replication']['retired'][job['retired_replica_id']]
        target=nodes(doc)[retired['replica']['node_id']]
        required=max(job['required_domains'],self.replication.required(doc,retired['file']['file_id']))
        return job,retired,target,required

    def _prove(self,doc,job_id):
        job,retired,target,required=self._target(doc,job_id)
        proof_graph=proof_fingerprint(doc)
        proofs=verify(self.service,doc,retired['file']['file_id'],{job['retired_replica_id']},required,
                      exclude_devices={target['device_id']})
        return proofs,doc['authority']['term'],proof_graph

    def _recheck(self,doc,job_id,proofs,term,proof_graph):
        if doc['authority']['term']!=term:raise CatalogError('stale_survivor_proof',409)
        if proof_fingerprint(doc)!=proof_graph:raise CatalogError('stale_gc_proof',409)
        job,retired,target,required=self._target(doc,job_id)
        recheck(doc,retired['file']['file_id'],proofs,{job['retired_replica_id']},required,
                exclude_devices={target['device_id']})
        return job,target,required

    def issue(self,job_id):
        """Internal owner-execute step; raw bearer exists only in this call's memory."""
        require_controller(self.service);identifier(job_id)
        self.service.refresh()
        with self.runtime.operation() as view:
            proofs,term,proof_graph=self._prove(view['document'],job_id)
        raw=secrets.token_urlsafe(40)
        with self.runtime.lock,self.runtime.operation() as view:
            doc=copy.deepcopy(view['document'])
            job,target,required=self._recheck(doc,job_id,proofs,term,proof_graph)
            stamp=now()
            job.update(state='RUNNING',permit_term=term,permit_hash=permit_hash(raw,target,doc['replication']['retired'][job['retired_replica_id']]['replica']['volume_id']),
                       run_id=uid(),permit_expires_at=stamp+120,proofs=proofs,required_domains=required,
                       attempts=job['attempts']+1,updated_at=stamp,last_error='execution_unconfirmed')
            doc['revision']+=1
            self.runtime.commit(view,doc)
            return raw,contract(doc,job),copy.deepcopy(target)

    def _credential(self,doc,node_id,node_token,grant,volume_id,scope):
        if not isinstance(scope,dict) or set(scope)!={'method','resource'} or scope['method']!='POST':
            raise CatalogError('gc_scope_rejected',403)
        resource=scope['resource']
        if not isinstance(resource,str) or not resource.startswith('gc/'):raise CatalogError('gc_scope_rejected',403)
        job_id=identifier(resource[3:])
        job=doc.get('replication',{}).get('gc_jobs',{}).get(job_id)
        if (not job or job['state']!='RUNNING' or job['permit_term']!=doc['authority']['term'] or
                not now()<job['permit_expires_at']):
            raise CatalogError('gc_permit_rejected',403)
        exact=contract(doc,job)
        node=next((n for n in doc['tables']['nodes'] if n['node_id']==node_id),None)
        if (not node or node['state']!='active' or exact['node_id']!=node_id or exact['volume_id']!=volume_id or
                not hmac.compare_digest(node['token_hash'],hashlib.sha256(node_token.encode()).hexdigest())):
            raise CatalogError('gc_scope_rejected',403)
        target=nodes(doc).get(node_id)
        if not target or not hmac.compare_digest(job['permit_hash'],permit_hash(grant,target,volume_id)):
            raise CatalogError('gc_permit_rejected',403)
        return job,exact

    def authorize(self,node_id,node_token,grant,volume_id,scope,nonce):
        require_controller(self.service)
        # Do not hold the Runtime lock across survivor network IO. Its read grants
        # must themselves use the existing fresh Controller introspection path.
        with self.runtime.operation() as view:
            job,exact=self._credential(view['document'],node_id,node_token,grant,volume_id,scope)
            proofs,term,proof_graph=self._prove(view['document'],job['gc_job_id'])
        with self.runtime.lock,self.runtime.operation() as view:
            doc=view['document']
            current,checked=self._credential(doc,node_id,node_token,grant,volume_id,scope)
            if checked!=exact:raise CatalogError('gc_permit_changed',403)
            self._recheck(doc,job['gc_job_id'],proofs,term,proof_graph)
            intent=digest({'node_id':node_id,'grant_sha256':hashlib.sha256(grant.encode()).hexdigest(),
                           'volume_id':volume_id,'operation':'gc','scope':scope,'nonce':nonce})
            receipt=self.runtime.commit(view,doc,'authorize-'+nonce,intent)
            return {'principal':'gc:'+job['gc_job_id'],'expires_at':current['permit_expires_at'],
                    'constraints':exact,'authority':{'cluster_id':doc['cluster_id'],'epoch':doc['epoch'],
                    'term':receipt['term'],'index':receipt['index'],'nonce':nonce,'intent_sha256':intent}}

    @staticmethod
    def _result(job):
        return {'gc_job_id':job['gc_job_id'],'state':'DONE','physical_deletions':1}

    def execute(self,obj):
        require_controller(self.service);job_id=identifier(obj['gc_job_id'])
        with self.runtime.operation() as view:
            job=view['document'].get('replication',{}).get('gc_jobs',{}).get(job_id)
            if job and job['state']=='DONE':return self._result(job)
        raw,exact,target=self.issue(job_id)
        client=StorageClient(target['origin'],target['pin'],raw,exact['volume_id'],timeout=self.service.timeout)
        try:
            reply=client.json('POST','gc/'+job_id,{})
        except (ClientError,OSError):
            raise CatalogError('gc_execution_unconfirmed',503) from None
        expected={k:exact[k] for k in ('gc_job_id','node_id','volume_id','local_file_id','size','sha256')}
        if (not isinstance(reply,dict) or any(reply.get(k)!=v for k,v in expected.items()) or
                reply.get('state')!='DONE' or type(reply.get('physical_deletions')) is not int or reply['physical_deletions']!=1 or
                type(reply.get('unlinked_now')) is not bool or type(reply.get('replayed')) is not bool or
                reply['replayed']==reply['unlinked_now'] or type(reply.get('logical_bytes_removed_now')) is not int or
                reply['logical_bytes_removed_now']!=(exact['size'] if reply['unlinked_now'] else 0)):
            raise CatalogError('gc_completion_unconfirmed',409)
        with self.runtime.lock,self.runtime.operation() as view:
            doc=copy.deepcopy(view['document']);job=doc['replication']['gc_jobs'][job_id]
            if job['state']=='DONE':return self._result(job)
            if contract(doc,job)!=exact:raise CatalogError('gc_permit_changed',409)
            job.update(state='DONE',completed_at=now(),last_error=None)
            doc['revision']+=1
            self.runtime.commit(view,doc)
            return self._result(job)
