"""Single-writer operator snapshot/restore adapter over canonical metadata and I/O.

No Catalog clone, quorum envelope, bytes deletion or external backup. Progress is
durable; each owner-driven step resumes the same canonical upload intent.
"""
import copy
import re
import shutil
import tempfile
import threading
from ...catalog.audit import verify_file
from ...catalog.common import CatalogError, canonical, content, digest, identifier, logical_path, now, uid
from ...bridge.contract import Refused
from ...bridge import private
from ...client import ClientError
from ...storage.errors import StorageError
from . import document

FILE_FIELDS = ('file_id', 'logical_path', 'version', 'size', 'sha256')


class HistoryError(Exception):
    def __init__(self, status, code): self.status, self.code = status, code


def integer(value, maximum=2**63-1):
    if type(value) is not int or not 0 <= value <= maximum: raise ValueError('invalid history integer')


class History:
    def __init__(self, api):
        self.api = api
        self.path = api.root/'dashboard/history.json'
        self.required = api.root/'dashboard/history-required.json'
        self.lock, self.step_lock = threading.RLock(), threading.Lock()
        self._load()  # Invalid existing progress never becomes a fresh document.

    def _catalog(self):
        return self.api.service.metadata.snapshot()

    def _load(self):
        self.api.pairings._ready()
        point = self._catalog()
        try:
            present=[]
            for path in (self.path,self.required):
                try: path.lstat();present.append(True)
                except FileNotFoundError: present.append(False)
            if not any(present):
                return dict(format=1, mode='single-writer-demo', cluster_id=point['cluster_id'], epoch=point['epoch'],
                            document_id=uid(), revision=0, snapshots={}, restores={}, requests={})
            if not all(present): raise ValueError('incomplete operator history')
            doc = document.read(self.path)
            if (set(doc) != {'format','mode','cluster_id','epoch','document_id','revision','snapshots','restores','requests'}
                    or type(doc['format']) is not int or doc['format'] != 1 or doc['mode'] != 'single-writer-demo'
                    or (doc['cluster_id'],doc['epoch']) != (point['cluster_id'],point['epoch'])): raise ValueError()
            identifier(doc['document_id'])
            if canonical(private.read(self.required)) != canonical(dict(format=1,cluster_id=doc['cluster_id'],epoch=doc['epoch'],document_id=doc['document_id'])): raise ValueError()
            integer(doc['revision'],1000000)
            for name, limit in (('snapshots',16),('restores',64),('requests',128)):
                if type(doc[name]) is not dict or len(doc[name]) > limit: raise ValueError()
                for item in doc[name]: identifier(item)
            files = {e['file']['file_id']: {k:e['file'][k] for k in FILE_FIELDS} for e in point['files']}
            def exact_file(file):
                if type(file) is not dict or set(file) != set(FILE_FIELDS) or files.get(file.get('file_id')) != file: raise ValueError()
                identifier(file['file_id']);logical_path(file['logical_path']);content(file['size'],file['sha256'])
                if type(file['version']) is not int or not 1 <= file['version'] <= 1000000: raise ValueError()
            def proof(value, file):
                if (type(value) is not dict or set(value) != {'file_id','sha256','size','domains','verified_at'}
                        or any(value[k] != file[k] for k in ('file_id','sha256','size'))
                        or type(value['domains']) is not list or len(value['domains']) != 2
                        or any(type(d) is not str or not 1 <= len(d) <= 64 for d in value['domains'])
                        or len(set(value['domains'])) != 2): raise ValueError()
                integer(value['verified_at'])
            for snap in doc['snapshots'].values():
                if set(snap) != {'manifest','manifest_sha256','state','cursor','proofs','verified_at','last_error'}: raise ValueError()
                m=snap['manifest']
                if (set(m) != {'format','mode','cluster_id','epoch','catalog_revision','catalog_digest','created_at','label','prefix','files'}
                        or type(m['format']) is not int or m['format'] != 1 or m['mode'] != doc['mode']
                        or (m['cluster_id'],m['epoch']) != (doc['cluster_id'],doc['epoch'])
                        or type(m['label']) is not str or not 1 <= len(m['label']) <= 64
                        or type(m['prefix']) is not str or snap['manifest_sha256'] != digest(m)
                        or not re.fullmatch('[0-9a-f]{64}',m['catalog_digest'])
                        or type(m['files']) is not list or not 1 <= len(m['files']) <= 256): raise ValueError()
                integer(m['catalog_revision']);integer(m['created_at'])
                if m['prefix']: logical_path(m['prefix'])
                for file in m['files']: exact_file(file)
                if len({f['file_id'] for f in m['files']}) != len(m['files']): raise ValueError()
                integer(snap['cursor'],len(m['files']))
                if (snap['state'] not in ('UNVERIFIED','VERIFYING','VERIFIED') or type(snap['proofs']) is not list
                        or len(snap['proofs']) != snap['cursor'] or snap['last_error'] not in (None,'backup_unavailable')): raise ValueError()
                for index,p in enumerate(snap['proofs']): proof(p,m['files'][index])
                if snap['state'] == 'VERIFIED':
                    integer(snap['verified_at'])
                    if snap['cursor'] != len(m['files']): raise ValueError()
                elif snap['verified_at'] is not None: raise ValueError()
            for job in doc['restores'].values():
                if (set(job) != {'source_file','snapshot_id','target_version','target_file_id','state','created_at','updated_at','last_error','proof'}
                        or job['state'] not in ('PENDING','COPYING','VERIFYING','COMPLETED','BLOCKED')
                        or job['last_error'] not in (None,'restore_unavailable','copies_pending','version_conflict')): raise ValueError()
                exact_file(job['source_file']);integer(job['target_version'],1000000)
                if job['target_version'] < 1: raise ValueError()
                integer(job['created_at']);integer(job['updated_at'])
                if job['snapshot_id'] is not None:
                    snap=doc['snapshots'][job['snapshot_id']]
                    if job['source_file'] not in snap['manifest']['files']: raise ValueError()
                if job['target_file_id'] is not None:
                    target=files.get(job['target_file_id'])
                    if not target or any(target[k] != job['source_file'][k] for k in ('logical_path','size','sha256')) or target['version'] != job['target_version']: raise ValueError()
                if job['state'] == 'COMPLETED':
                    if job['target_file_id'] is None: raise ValueError()
                    proof(job['proof'],files[job['target_file_id']])
                elif job['proof'] is not None: raise ValueError()
            for receipt in doc['requests'].values():
                if (set(receipt) != {'intent','result'} or not re.fullmatch('[0-9a-f]{64}',receipt['intent'])
                        or type(receipt['result']) is not dict or set(receipt['result']) not in ({'snapshot_id'},{'restore_id'})): raise ValueError()
                field,value=next(iter(receipt['result'].items()));identifier(value)
                if value not in doc['snapshots' if field=='snapshot_id' else 'restores']: raise ValueError()
            return doc
        except (ValueError, KeyError, TypeError, OSError, StorageError, Refused, RecursionError):
            raise HistoryError(503,'history_state_unavailable') from None

    def _save(self, doc):
        if doc['revision'] >= 1000000 or len(canonical(doc)) > document.LIMIT:
            raise HistoryError(507,'history_limit')
        doc['revision'] += 1
        try:
            if doc['revision']==1:
                # A crash between required-record publication and the document
                # is held, never interpreted as a fresh empty snapshot history.
                private.create(self.required,dict(format=1,cluster_id=doc['cluster_id'],epoch=doc['epoch'],document_id=doc['document_id']))
            document.write(self.path,doc)
        except (ValueError,OSError,StorageError,Refused): raise HistoryError(503,'history_state_unavailable') from None

    def view(self):
        with self.lock:
            doc=self._load()
            return {k:copy.deepcopy(v) for k,v in doc.items() if k not in ('requests','document_id')} | {
                'history_api_version':1,'scope':'in-cluster immutable references; no external backup or writer authority',
                'physical_deletions':0,'retention':'all recorded references retained; no automatic expiration'}

    def create(self, action, obj):
        fields={'history_api_version','request_id','label','prefix'} if action=='snapshot' else {'history_api_version','request_id','file_id','snapshot_id'}
        if type(obj) is not dict or set(obj) != fields or type(obj['history_api_version']) is not int or obj['history_api_version'] != 1: raise ValueError()
        identifier(obj['request_id']);intent=digest({'action':action,'payload':obj})
        with self.lock:
            doc=self._load();previous=doc['requests'].get(obj['request_id'])
            if previous:
                if previous['intent'] != intent: raise HistoryError(409,'history_intent_conflict')
                return copy.deepcopy(previous['result']) | {'replayed':True}
            if len(doc['requests']) >= 128: raise HistoryError(507,'history_limit')
            point=self._catalog();files=[{k:e['file'][k] for k in FILE_FIELDS} for e in point['files']]
            item_id=uid()
            if action=='snapshot':
                if (type(obj['label']) is not str or not obj['label'].strip() or len(obj['label']) > 64
                        or any(ord(c)<32 for c in obj['label']) or type(obj['prefix']) is not str): raise ValueError()
                if obj['prefix']: logical_path(obj['prefix'])
                if len(doc['snapshots']) >= 16: raise HistoryError(507,'history_limit')
                selected=sorted([f for f in files if not obj['prefix'] or f['logical_path'].startswith(obj['prefix']+'/')],key=lambda f:(f['logical_path'],f['version']))
                if not selected: raise HistoryError(409,'snapshot_empty')
                manifest=dict(format=1,mode='single-writer-demo',cluster_id=point['cluster_id'],epoch=point['epoch'],
                    catalog_revision=point['revision'],catalog_digest=point['head_digest'],created_at=now(),
                    label=obj['label'],prefix=obj['prefix'],files=selected)
                doc['snapshots'][item_id]=dict(manifest=manifest,manifest_sha256=digest(manifest),state='UNVERIFIED',cursor=0,proofs=[],verified_at=None,last_error=None)
                result={'snapshot_id':item_id}
            else:
                identifier(obj['file_id']);file=next((f for f in files if f['file_id']==obj['file_id']),None)
                if file is None: raise HistoryError(404,'not_found')
                if obj['snapshot_id'] is not None:
                    identifier(obj['snapshot_id']);snap=doc['snapshots'].get(obj['snapshot_id'])
                    if not snap or snap['state'] != 'VERIFIED' or file not in snap['manifest']['files']: raise HistoryError(409,'snapshot_not_verified')
                if len(doc['restores']) >= 64: raise HistoryError(507,'history_limit')
                versions=[f['version'] for f in files if f['logical_path']==file['logical_path']]
                versions += [j['target_version'] for j in doc['restores'].values() if j['source_file']['logical_path']==file['logical_path']]
                version=max(versions)+1
                if version > 1000000 or file['size'] > self.api.cfg['max_upload_bytes']: raise HistoryError(413,'restore_too_large')
                doc['restores'][item_id]=dict(source_file=file,snapshot_id=obj['snapshot_id'],target_version=version,
                    target_file_id=None,state='PENDING',created_at=now(),updated_at=now(),last_error=None,proof=None)
                result={'restore_id':item_id}
            doc['requests'][obj['request_id']]={'intent':intent,'result':result};self._save(doc)
            return result | {'replayed':False}

    def _verify_ready(self, file_id):
        # Share the canonical worker's I/O admission. An unfinished COPY or a
        # busy verifier is not evidence that retained bytes became corrupt.
        service=self.api.service
        if not service._tick.acquire(blocking=False): raise CatalogError('backup_unavailable',503)
        try:
            service.refresh();entry=service.catalog.file(file_id)
            if entry['available_replicas'] < 2 or entry['verified_replicas'] < 2:
                raise CatalogError('backup_unavailable',503)
            return verify_file(service,file_id,2)
        finally: service._tick.release()

    def step(self, kind, item_id):
        identifier(item_id)
        if kind not in ('snapshots','restores'): raise ValueError()
        if not self.step_lock.acquire(blocking=False): raise HistoryError(429,'history_busy')
        try:
            with self.lock:
                doc=self._load();row=copy.deepcopy(doc[kind].get(item_id))
                if row is None: raise HistoryError(404,'not_found')
                if row['state'] in ('VERIFIED','COMPLETED','BLOCKED'): return {'state':row['state'],'historical':True}
            if kind=='snapshots':
                proof=None
                try:
                    proof,_=self._verify_ready(row['manifest']['files'][row['cursor']]['file_id'])
                except (CatalogError,ClientError,OSError,ValueError): pass
                with self.lock:
                    doc=self._load();row=doc[kind][item_id];row['state']='VERIFYING'
                    if proof:
                        row['proofs'].append(proof);row['cursor']+=1;row['last_error']=None
                        if row['cursor']==len(row['manifest']['files']): row.update(state='VERIFIED',verified_at=now())
                    else: row['last_error']='backup_unavailable'
                    self._save(doc)
                    return {'state':row['state'],'cursor':row['cursor'],'total':len(row['manifest']['files']),'error':row['last_error']}
            with self.lock:
                doc=self._load();doc[kind][item_id].update(state='COPYING',updated_at=now(),last_error=None);self._save(doc)
            file=row['source_file'];target_id=row['target_file_id'];proof=None;error=None
            try:
                intent=dict(idempotency_key='dashboard-restore-'+item_id,logical_path=file['logical_path'],
                    size=file['size'],sha256=file['sha256'],version=row['target_version'],policy='replicated_2')
                plan=self.api.client.request('POST','uploads',intent)
                target_id=plan['file']['file']['file_id']
                with self.lock:
                    doc=self._load();doc[kind][item_id]['target_file_id']=target_id;self._save(doc)
                if not plan['completed']:
                    with self.api.transfer() as directory:
                        if shutil.disk_usage(directory).free < file['size']+8*1024**2: raise OSError('insufficient spool')
                        with tempfile.TemporaryFile(dir=directory) as stream:
                            self.api.client.download(file['file_id'],stream)  # Existing SHA/fallback; no RAM body.
                            self.api.client.upload(stream,file['logical_path'],intent['idempotency_key'],version=row['target_version'])
                proof,_=self._verify_ready(target_id)
            except (CatalogError,ClientError) as exc:
                error='version_conflict' if exc.code in ('logical_version_exists','idempotency_conflict') else 'copies_pending' if target_id else 'restore_unavailable'
            except (OSError,ValueError): error='restore_unavailable'
            with self.lock:
                doc=self._load();row=doc[kind][item_id]
                row.update(target_file_id=target_id,proof=proof,updated_at=now(),last_error=error,
                    state='COMPLETED' if proof else 'BLOCKED' if error=='version_conflict' else 'VERIFYING' if target_id else 'PENDING')
                self._save(doc)
                return {'state':row['state'],'target_file_id':target_id,'target_version':row['target_version'],'error':error}
        finally: self.step_lock.release()
