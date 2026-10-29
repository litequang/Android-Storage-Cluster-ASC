"""Explicit pinned Core-only observer. No discovery adoption, POSTs or SQL fallback."""
import copy
from concurrent.futures import ThreadPoolExecutor
import threading
import time
from ..catalog.common import identifier, origin
from ..validation import node_id, secret
from ..client import request_json, ClientError
from .core import unavailable,downgrade,project


class Observer:
    def __init__(self,cluster_id,epoch,endpoints,minimum_index=0):
        identifier(cluster_id);identifier(epoch)
        if type(minimum_index) is not int or minimum_index<0 or type(endpoints) is not list or len(endpoints)!=3:
            raise ValueError('explicit static-three-voter observer configuration required')
        self.cluster,self.epoch,self.floor=cluster_id,epoch,minimum_index
        self.endpoints=[]
        for e in endpoints:
            if set(e)!={'node_id','origin','pin','token'}:raise ValueError('invalid owner endpoint')
            node_id(e['node_id']);secret(e['token']);address,pin=origin(e['origin'],e['pin'])
            self.endpoints.append(dict(e,origin=address,pin=pin))
        if len({e['node_id'] for e in self.endpoints})!=3 or len({e['origin'] for e in self.endpoints})!=3:
            raise ValueError('duplicate observer endpoints')
        self.lock=threading.Lock();self.last=None

    def _read(self,e):
        controller={'node_id':e['node_id'],'state':'UNKNOWN','role':None,'voter_process':'UNKNOWN','leader_confirmed':False}
        try:
            value=request_json(e['origin'],e['pin'],'GET','/cluster/v1/observability?consistency=strong',token=e['token'],timeout=23)
            if (value.get('observer_version')!=1 or type(value['observer_version']) is not int or value.get('read_only') is not True or
                    value.get('writer_authority') is not False or value['cluster'].get('mode')!='core-quorum' or
                    value['cluster']['cluster_id']!=self.cluster or value['runtime']['epoch']!=self.epoch or
                    value['controller']['node_id']!=e['node_id'] or
                    type(value['runtime']['checkpoint']['index']) is not int or value['runtime']['checkpoint']['index']<self.floor):
                raise ValueError()
            return value,value['controller']
        except ConnectionRefusedError:controller['state']='OFFLINE'
        except (ClientError,OSError,ValueError,KeyError,TypeError):pass
        return None,controller

    def state(self):
        if not self.lock.acquire(blocking=False):
            result=downgrade(self.last or unavailable(cluster_id=self.cluster,epoch=self.epoch),'UNKNOWN')
            result['runtime']['observation_busy']=True;return result
        try:
            with ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(self._read,self.endpoints))
            values=[v for v,c in rows if v is not None]
            strong=[v for v in values if v['runtime'].get('strong_read_confirmed') is True]
            chosen=max(strong or values,key=lambda v:v['runtime']['checkpoint']['index']) if values else None
            if strong:
                result=copy.deepcopy(chosen);self.floor=max(self.floor,result['runtime']['checkpoint']['index'])
            else:
                result=downgrade(chosen or self.last or unavailable(cluster_id=self.cluster,epoch=self.epoch),
                    'QUORUM UNAVAILABLE' if values else 'OFFLINE' if all(c['state']=='OFFLINE' for v,c in rows) else 'UNKNOWN')
                result['runtime']['quorum_available']=False if values else None
            result['runtime']['controllers']=[c for v,c in rows]
            result['runtime']['static_voters']=3
            if strong and any(c['state']!='ONLINE' for v,c in rows):result['runtime']['state']='DEGRADED'
            result['runtime']['observed_at']=int(time.time());result['read_only']=True;result['writer_authority']=False
            self.last=copy.deepcopy(result);return result
        finally:self.lock.release()

    def file(self,file_id):
        identifier(file_id)
        from ..catalog.common import CatalogError
        for file in self.state()['files']:
            if file['file_id']==file_id:return file
        raise CatalogError('file_not_found',404)


class RecoveryObserver:
    """Explicit passive stage mode; verify bytes, never activate/import a runtime."""
    def __init__(self,root,anchor,cluster_id,minimum_index,expected_epoch=None):
        from pathlib import Path
        from ..external.format import sha
        identifier(cluster_id);sha(anchor)
        if expected_epoch is not None:identifier(expected_epoch)
        self.epoch=expected_epoch
        if type(minimum_index) is not int or minimum_index<0:raise ValueError('invalid history floor')
        self.root,self.anchor,self.cluster,self.floor=Path(root),anchor,cluster_id,minimum_index

    def state(self):
        import fcntl
        import hashlib
        from ..external.local import Tree
        from ..external.recovery import verify_stage_tree
        from ..external.engine import load
        from ..catalog.common import CatalogError
        try:
            with Tree(self.root) as root, root.file('owner.lock') as lock:
                fcntl.flock(lock.fileno(),fcntl.LOCK_SH|fcntl.LOCK_NB)
                try:
                    report=verify_stage_tree(root,self.anchor)
                    manifest,metadata,doc=load(root)
                    if (manifest['cluster_id']!=self.cluster or manifest['source_index']<self.floor or
                            self.epoch is not None and manifest['epoch']!=self.epoch):
                        raise ValueError()
                    view={'document':doc,'state':{'index':manifest['source_index'],'term':manifest['source_term'],
                        'document_sha256':hashlib.sha256(metadata).hexdigest()}}
                    result=project(view,False)
                finally:fcntl.flock(lock.fileno(),fcntl.LOCK_UN)
            result['cluster']['mode']='recovery-read-only'
            result['runtime']['state']='RECOVERY READ-ONLY'
            result['backup']['recovery']={**report,'verified_at':int(time.time())}
            return result
        except (OSError,ValueError,KeyError,CatalogError):
            result=unavailable(cluster_id=self.cluster)
            result['cluster']['mode']='recovery-read-only'
            result['backup']['recovery']={'state':'UNKNOWN','writer_authority':False,'verified_at':None}
            return result

    def file(self,file_id):
        identifier(file_id)
        from ..catalog.common import CatalogError
        for file in self.state()['files']:
            if file['file_id']==file_id:return file
        raise CatalogError('file_not_found',404)
