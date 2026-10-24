"""Controller orchestration: measured placement, physical verification and durable repairs."""
import json
import sqlite3
import threading
import time
from . import grants
from .common import CatalogError, identifier, now, origin
from .metadata import MetadataSource
from .placement import active_nodes, eligible, readable
from .queue import JobQueue
from .state import Catalog, insert
from .transport import source_stream
from .. import validation as valid
from ..client import ClientError
from ..runtime import foreground_lock
from ..storage.client import StorageClient


class CatalogService:
    def __init__(self,registry,rate=4*1024**2,timeout=300):
        if type(rate) is not int or not 65536<=rate<=64*1024**2:
            raise ValueError('invalid catalog transfer rate')
        self.registry,self.catalog=registry,Catalog(registry)
        self.queue,self.metadata=JobQueue(self.catalog,timeout),MetadataSource(registry)
        self.rate,self.timeout=rate,timeout
        self._tick=threading.Lock();self._owner=None
        self._stop=threading.Event();self._thread=None
        self.fault_hook=None

    def start(self,background=False):
        if self._owner is not None:
            raise ValueError('catalog worker already started')
        owner=foreground_lock(self.registry.path.parent,'catalog-worker')
        owner.__enter__();self._owner=owner
        try:
            self.queue.recover()
            if background:
                self._thread=threading.Thread(target=self._loop,daemon=True);self._thread.start()
            return self
        except BaseException:
            self.close();raise

    def close(self):
        self._stop.set()
        if self._thread:self._thread.join()
        with self._tick:
            if self._owner is not None:
                self._owner.__exit__(None,None,None);self._owner=None

    def _loop(self):
        last_reconcile=0
        while not self._stop.is_set():
            try:
                if time.monotonic()-last_reconcile>=30:
                    self.reconcile();last_reconcile=time.monotonic()
                self.run_one()
            except (OSError,ValueError,ClientError,CatalogError,sqlite3.Error):
                pass  # Fixed job/health states carry diagnostics; never log secret-bearing exceptions.
            self._stop.wait(1)

    def register(self,node_id,endpoint,pin,device_id,volume_ids,metadata_allowed=True,storage_allowed=True):
        valid.node_id(node_id);valid.name(device_id)
        endpoint,pin=origin(endpoint,pin) if storage_allowed else ('','')
        if (not isinstance(volume_ids,list) or len(volume_ids)>8 or storage_allowed and not volume_ids or
                type(metadata_allowed) is not bool or type(storage_allowed) is not bool):
            raise CatalogError('invalid_node_approval',400)
        for volume_id in volume_ids:identifier(volume_id)
        with self.registry.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            node=db.execute('SELECT * FROM nodes WHERE node_id=?',(node_id,)).fetchone()
            if (not node or node['state']!='active' or node_id=='local-controller' or
                    json.loads(node['profile']).get('protected') is True):
                raise CatalogError('protected_or_inactive_node',403)
            exists=db.execute('SELECT node_id FROM catalog_nodes WHERE node_id=?',(node_id,)).fetchone()
            if not exists and db.execute('SELECT COUNT(*) FROM catalog_nodes').fetchone()[0]>=16:
                raise CatalogError('catalog_node_limit',409)
            values=(endpoint,pin,device_id,int(metadata_allowed),int(storage_allowed),node['token_version'],
                    json.dumps(sorted(set(volume_ids))),node_id)
            if exists:
                db.execute('UPDATE catalog_nodes SET origin=?,pin=?,device_id=?,metadata_allowed=?,storage_allowed=?,'
                           'approved_generation=?,volume_ids=?,capabilities=NULL,checked_at=NULL,last_error=NULL WHERE node_id=?',values)
            else:
                insert(db,'catalog_nodes',dict(zip(('origin','pin','device_id','metadata_allowed','storage_allowed',
                                                    'approved_generation','volume_ids','node_id'),values)))
        return {'node_id':node_id,'approved':True}

    def node(self,node_id):
        with self.registry.connect() as db:
            row=db.execute('SELECT * FROM catalog_nodes WHERE node_id=?',(node_id,)).fetchone()
        if not row:raise CatalogError('node_not_approved',403)
        return dict(row)

    def _client(self,node_id,volume_id,side,local_file_id=None,job=None):
        node=self.node(node_id)
        token=grants.mint(self.registry,node_id,volume_id,side,local_file_id,job,
                          ttl=min(900,self.timeout) if job or side=='audit' else 120)
        return StorageClient(node['origin'],node['pin'],token,volume_id,timeout=self.timeout if job or side in ('audit','read') else 12)

    def refresh(self):
        with self.registry.connect() as db:nodes=active_nodes(db)
        for node in nodes:
            if not node['storage_allowed']:continue
            error=None;caps=None
            try:
                if (node['state']!='active' or node['token_version']!=node['approved_generation'] or
                        json.loads(node['profile']).get('protected') is True):
                    raise CatalogError('node_not_approved',403)
                volumes=[];limit=None;rate=None
                for volume_id in json.loads(node['volume_ids']):
                    reply=self._client(node['node_id'],volume_id,'inspect').json('GET','status')
                    if reply.get('node_id')!=node['node_id'] or reply.get('storage_version')!=1:
                        raise CatalogError('capability_identity_mismatch',409)
                    if len(reply.get('volumes',[]))!=1 or reply['volumes'][0].get('volume_id')!=volume_id:
                        raise CatalogError('capability_identity_mismatch',409)
                    row=reply['volumes'][0]
                    for field in ('quota','reserve','free_bytes','total_bytes','used_bytes'):
                        if row.get(field) is not None and (type(row[field]) is not int or row[field]<0):
                            raise CatalogError('invalid_capability',409)
                    volumes.append(row);limit=reply.get('max_upload_bytes');rate=reply.get('bytes_per_second')
                    if type(limit) is not int or not 1<=limit<=1024**3 or type(rate) is not int or rate<1:
                        raise CatalogError('invalid_capability',409)
                caps={'storage_version':1,'volumes':volumes,'max_upload_bytes':limit,'bytes_per_second':rate,'external_load':None,'stability':None}
            except (OSError,ValueError,ClientError,CatalogError):
                error='storage_unavailable'
            with self.registry.connect() as db:
                db.execute('UPDATE catalog_nodes SET capabilities=COALESCE(?,capabilities),checked_at=?,last_error=? WHERE node_id=?',
                           (json.dumps(caps) if caps is not None else None,now(),error,node['node_id']))

    def upload_plan(self,obj):
        self.refresh()
        entry=self.catalog.mutate('CREATE',obj);file_id=entry['file']['file_id']
        with self.registry.connect() as db:
            job=dict(db.execute("SELECT * FROM catalog_jobs WHERE file_id=? AND kind='UPLOAD'",(file_id,)).fetchone())
        if job['state']=='COMPLETED':
            return {'completed':True,'file':self.catalog.file(file_id)}
        job=self.queue.upload_lease(job['job_id'])
        node=self.node(job['target_node_id'])
        grant=grants.mint(self.registry,job['target_node_id'],job['target_volume_id'],'target',job=job,ttl=300)
        return {'completed':False,'file':self.catalog.file(file_id),'job_id':job['job_id'],
                'idempotency_key':job['idempotency_key'],'local_logical_path':job['logical_path'],
                'target':{'node_id':job['target_node_id'],'volume_id':job['target_volume_id'],
                          'origin':node['origin'],'pin':node['pin'],'grant':grant,'timeout':self.timeout}}

    def _proof(self,client,local_id,volume_id,logical_path,file,deadline=None):
        verification=client.json('POST','files/'+local_id+'/verify',{})
        if verification.get('state')!='COMMITTED':
            state=verification.get('state')
            raise CatalogError('replica_missing' if state=='MISSING' else 'replica_corrupt' if state=='CORRUPT' else 'replica_unavailable',
                               404 if state=='MISSING' else 422 if state=='CORRUPT' else 503)
        row=client.json('GET','files/'+local_id)['file']
        if (row.get('file_id')!=local_id or row.get('volume_id')!=volume_id or row.get('logical_path')!=logical_path or
                row.get('size')!=file['size'] or row.get('sha256')!=file['sha256'] or row.get('state')!='COMMITTED'):
            raise CatalogError('replica_metadata_mismatch',409)
        with source_stream(client,local_id,file['size'],file['sha256'],self.rate,
                           deadline or time.time()+self.timeout,purpose='verification') as reader:
            while reader.count<file['size']:reader.read(65536)
        return {**row,'physically_verified':True}

    def _choose_source(self,job,file):
        entry=self.catalog.file(file['file_id'])
        with self.registry.connect() as db:nodes={n['node_id']:n for n in active_nodes(db)}
        target=nodes.get(job['target_node_id'])
        for replica in entry['replicas']:
            node=nodes.get(replica['node_id'])
            if (replica['state']!='VERIFIED' or not node or not readable(node,replica['volume_id']) or
                    not target or node['device_id']==target['device_id']):
                continue
            try:
                job=self.queue.source(job,replica['replica_id'])
                client=self._client(replica['node_id'],replica['volume_id'],'source',replica['local_file_id'],job)
                self._proof(client,replica['local_file_id'],replica['volume_id'],
                            '_asc-global/'+file['file_id']+'/'+replica['replica_id'],file,job['lease_until'])
                return job,replica,client
            except (OSError,ClientError,CatalogError) as exc:
                self._bad_replica(replica,exc)
        raise CatalogError('no_verified_source',503)

    def _bad_replica(self,replica,exc):
        status=getattr(exc,'status',None)
        state='MISSING' if status==404 else 'CORRUPT' if status==422 else 'METADATA_CONFLICT' if status==409 else 'UNAVAILABLE'
        self.catalog.mutate('REPLICA_STATE',{'replica_id':replica['replica_id'],'state':state})

    def _execute(self,job):
        entry=self.catalog.file(job['file_id']);file=entry['file']
        target=self._client(job['target_node_id'],job['target_volume_id'],'target',job=job)
        if job['kind']=='COPY':
            session=target.initiate(job['idempotency_key'],job['logical_path'],file['size'],file['sha256'])
            job=self.queue.checkpoint(job,session['session_id'],session['file_id'])
            if session['state']=='NEEDS_REVIEW' and getattr(self,'failover',False):
                target.commit(session['session_id'])  # Fresh runtime scope + exact retained-body revalidation.
                session['state']='COMMITTED'
            if session['state'] not in ('READY','COMMITTED'):
                job,replica,source=self._choose_source(job,file)
                with source_stream(source,replica['local_file_id'],file['size'],file['sha256'],self.rate,job['lease_until']) as reader:
                    target.upload(session['session_id'],reader,file['size'])
            if session['state']!='COMMITTED':
                target.commit(session['session_id'])
            if self.fault_hook:self.fault_hook('after_commit',job)
        proof=self._proof(target,job['target_local_file_id'],job['target_volume_id'],job['logical_path'],file,job['lease_until'])
        self.catalog.mutate('COMPLETE',{'job_id':job['job_id'],'run_token':job['run_token'],'proof':proof})
        self.catalog.schedule(job['file_id'])

    def run_one(self,job_id=None):
        if self._owner is None:
            raise ValueError('catalog worker ownership lock required')
        if not self._tick.acquire(blocking=False):return None
        job=None
        try:
            self.refresh();job=self.queue.claim(job_id)
            if job:
                try:self._execute(job)
                except (OSError,ValueError,ClientError,CatalogError) as exc:
                    label=getattr(exc,'code',None)
                    allowed={'job_timeout','no_verified_source','stale_job_lease','node_credential_changed',
                             'replica_missing','replica_corrupt','replica_metadata_mismatch','source_checksum_mismatch'}
                    self.queue.failed_attempt(job,label if label in allowed else 'transfer_unavailable')
            return self.queue.get(job['job_id']) if job else None
        finally:self._tick.release()

    def confirm_upload(self,job_id,session_id,local_file_id):
        job=self.queue.ack_upload(job_id,session_id,local_file_id)
        self.run_one(job_id)
        return {'file':self.catalog.file(job['file_id']),'job_id':job_id,'job_state':self.queue.get(job_id)['state']}

    def download_plan(self,file_id):
        self.refresh()
        entry=self.catalog.file(file_id);result=[]
        with self.registry.connect() as db:nodes={n['node_id']:n for n in active_nodes(db)}
        for replica in entry['replicas']:
            node=nodes.get(replica['node_id'])
            if replica['state']!='VERIFIED' or not node or not readable(node,replica['volume_id']):continue
            client=self._client(replica['node_id'],replica['volume_id'],'read',replica['local_file_id'])
            result.append({'replica_id':replica['replica_id'],'node_id':replica['node_id'],
                'volume_id':replica['volume_id'],'local_file_id':replica['local_file_id'],
                'origin':client.origin,'pin':client.pin,'grant':client.grant,'timeout':self.timeout})
        return {'file':entry,'candidates':result}

    def metadata_allowed(self,node_id,token):
        if not self.registry.authenticate_node(node_id,token):return False
        with self.registry.connect() as db:
            row=db.execute('SELECT c.*,n.token_version,n.profile FROM catalog_nodes c JOIN nodes n USING(node_id) WHERE node_id=?',(node_id,)).fetchone()
        return bool(row and row['metadata_allowed'] and row['approved_generation']==row['token_version']
                    and json.loads(row['profile']).get('protected') is not True)

    def metadata_ack(self,obj):
        with self.registry.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            state=self.catalog._state(db)
            revision=obj['revision']
            if type(revision) is not int or revision<0 or revision>state['revision'] or obj['epoch']!=state['epoch']:
                raise CatalogError('invalid_metadata_ack',409)
            expected=state['head_digest'] if revision==state['revision'] else ('0'*64 if revision==0 else None)
            if expected is None:
                row=db.execute('SELECT digest FROM catalog_events WHERE revision=?',(revision,)).fetchone()
                expected=row[0] if row else None
            if expected!=obj['head_digest']:
                raise CatalogError('invalid_metadata_ack',409)
            previous=db.execute('SELECT metadata_revision FROM catalog_nodes WHERE node_id=?',(obj['node_id'],)).fetchone()[0]
            if previous is not None and previous>revision:
                raise CatalogError('metadata_ack_rollback',409)
            db.execute('UPDATE catalog_nodes SET metadata_revision=?,metadata_digest=?,metadata_synced_at=? WHERE node_id=?',
                       (revision,expected,now(),obj['node_id']))
        return {'ok':True}

    def status(self):
        with self.registry.connect() as db:
            state=self.catalog._state(db)
            rows=db.execute('SELECT node_id,device_id,metadata_allowed,storage_allowed,checked_at,last_error,'
                            'metadata_revision,metadata_synced_at FROM catalog_nodes ORDER BY node_id').fetchall()
        return {'cluster_id':self.registry.cluster_id(),'epoch':state['epoch'],'revision':state['revision'],
                'writer':'single-controller','raft_enabled':False,'nodes':[dict(r) for r in rows]}

    def reconcile(self,max_verify=8):
        """Bounded physical verification. Unknown files/objects are reported and preserved."""
        if not self._tick.acquire(blocking=False):
            return {'busy':True}
        try:
            self.refresh()
            with self.registry.connect() as db:
                nodes=active_nodes(db)
                replicas=[dict(r) for r in db.execute('SELECT * FROM catalog_replicas ORDER BY COALESCE(verified_at,0),replica_id')]
            report={'checked':0,'uncatalogued':[],'unreferenced_objects':[],'recovered_uploads':[],
                    'errors':[],'scheduled':[],'inventory_truncated':False}
            with self.registry.connect() as db:
                saved=db.execute("SELECT value FROM settings WHERE key='catalog_inventory_cursor'").fetchone()
            cursor=json.loads(saved[0]) if saved else {'version':1,'next_pair':0,'offsets':{}}
            if cursor.get('version')!=1 or type(cursor.get('next_pair')) is not int or not isinstance(cursor.get('offsets'),dict):
                raise CatalogError('invalid_inventory_cursor',409)
            pairs=sorted([(n,v) for n in nodes if eligible(n) and n['storage_allowed']
                          for v in json.loads(n['volume_ids'])],key=lambda p:(p[0]['node_id'],p[1]))
            if pairs:
                start=cursor['next_pair']%len(pairs)
                selected=[pairs[(start+i)%len(pairs)] for i in range(min(16,len(pairs)))]
                for node,volume_id in selected:
                    cursor_key=node['node_id']+'/'+volume_id
                    offset=cursor['offsets'].get(cursor_key,0)
                    if type(offset) is not int or not 0<=offset<=10000:
                        raise CatalogError('invalid_inventory_cursor',409)
                    try:
                        client=self._client(node['node_id'],volume_id,'inspect')
                        inventory=client.json('GET','inventory?offset='+str(offset))
                        for group in inventory.get('objects',[]):
                            for item in group.get('unreferenced_objects',[]):
                                if len(report['unreferenced_objects'])<256:
                                    report['unreferenced_objects'].append({'node_id':node['node_id'],'volume_id':volume_id,**item})
                                else:report['inventory_truncated']=True
                        known={r['local_file_id'] for r in replicas if r['node_id']==node['node_id'] and r['volume_id']==volume_id}
                        for item in inventory['files']:
                            if item['file_id'] in known:continue
                            with self.registry.connect() as db:
                                job=db.execute('SELECT * FROM catalog_jobs WHERE target_node_id=? AND target_volume_id=? AND logical_path=?',
                                               (node['node_id'],volume_id,item['logical_path'])).fetchone()
                            upload=item.get('upload')
                            if (job and job['kind']=='UPLOAD' and job['state'] in ('PENDING','RETRY') and upload and
                                    upload['principal']=='job:'+job['job_id'] and upload['idempotency_key']==job['job_id']):
                                self.queue.ack_upload(job['job_id'],upload['session_id'],item['file_id'])
                                report['recovered_uploads'].append(job['job_id'])
                            elif len(report['uncatalogued'])<256:
                                report['uncatalogued'].append({'node_id':node['node_id'],'volume_id':volume_id,'local_file_id':item['file_id']})
                            else:report['inventory_truncated']=True
                        cursor['offsets'][cursor_key]=inventory['next_offset'] or 0
                        if inventory['next_offset'] is not None:report['inventory_truncated']=True
                    except (OSError,ValueError,ClientError,CatalogError):
                        report['errors'].append({'node_id':node['node_id'],'error':'inventory_unavailable'})
                cursor['next_pair']=(start+len(selected))%len(pairs)
                approved={n['node_id']+'/'+v for n in nodes for v in json.loads(n['volume_ids'])}
                cursor['offsets']={k:v for k,v in cursor['offsets'].items() if k in approved}
                with self.registry.connect() as db:
                    db.execute("INSERT OR REPLACE INTO settings VALUES('catalog_inventory_cursor',?)",(json.dumps(cursor),))
            node_map={n['node_id']:n for n in nodes}
            for replica in replicas:
                if report['checked']>=max_verify:break
                node=node_map.get(replica['node_id'])
                if not node or not eligible(node):continue
                try:
                    file=self.catalog.file(replica['file_id'])['file']
                    audit=self._client(replica['node_id'],replica['volume_id'],'audit',replica['local_file_id'])
                    self._proof(audit,replica['local_file_id'],replica['volume_id'],
                                '_asc-global/'+file['file_id']+'/'+replica['replica_id'],file)
                    self.catalog.mutate('REVERIFY',{'replica_id':replica['replica_id'],'physically_verified':True})
                except (OSError,ValueError,ClientError,CatalogError) as exc:
                    self._bad_replica(replica,exc)
                report['checked']+=1
            with self.registry.connect() as db:
                ids=[r[0] for r in db.execute('SELECT file_id FROM catalog_files')]
            for file_id in ids:
                report['scheduled'].extend(self.catalog.schedule(file_id))
            return report
        finally:
            self._tick.release()
