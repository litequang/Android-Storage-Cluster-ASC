"""Owner client: admin token only reaches the pinned Controller."""
import hashlib
from ..client import ClientError, request_json
from ..storage.client import StorageClient
from .common import CatalogError


class ClusterClient:
    def __init__(self,origin,pin,admin_token):
        self.origin,self.pin,self.token=origin,pin,admin_token

    def request(self,method,path,obj=None):
        return request_json(self.origin,self.pin,method,'/catalog/v1/'+path,obj,self.token,timeout=300 if method=='POST' else 12)

    def upload(self,stream,logical_path,key,policy='replicated_2',version=1):
        stream.seek(0);size=0;sha=hashlib.sha256()
        while chunk:=stream.read(65536):
            size+=len(chunk);sha.update(chunk)
            if size>1024**3:raise CatalogError('upload_too_large',413)
        plan=self.request('POST','uploads',{'idempotency_key':key,'logical_path':logical_path,'size':size,
                          'sha256':sha.hexdigest(),'policy':policy,'version':version})
        if plan['completed']:return {'file':plan['file'],'job_state':'COMPLETED'}
        target=plan['target']
        client=StorageClient(target['origin'],target['pin'],target['grant'],target['volume_id'],timeout=target.get('timeout',300))
        session=client.initiate(plan['idempotency_key'],plan['local_logical_path'],size,sha.hexdigest())
        if session['state'] not in ('READY','COMMITTED'):
            stream.seek(0);client.upload(session['session_id'],stream,size)
        if session['state']!='COMMITTED':client.commit(session['session_id'])
        return self.request('POST','uploads/'+plan['job_id']+'/complete',
                            {'session_id':session['session_id'],'local_file_id':session['file_id']})

    def download(self,file_id,output):
        if not output.seekable():raise ValueError('fallback download requires a new seekable output')
        plan=self.request('POST','files/'+file_id+'/download',{})
        position=output.tell();file=plan['file']['file']
        for replica in plan['candidates']:
            output.seek(position);output.truncate()
            try:
                client=StorageClient(replica['origin'],replica['pin'],replica['grant'],replica['volume_id'],timeout=replica.get('timeout',300))
                result=client.download(replica['local_file_id'],output,file['size'],file['sha256'])
                return {**result,'replica_id':replica['replica_id'],'node_id':replica['node_id']}
            except (OSError,ClientError,ValueError):continue
        raise CatalogError('no_available_replica',503)
