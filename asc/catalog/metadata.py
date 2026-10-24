"""Consistent snapshots/ordered deltas and an atomic read-only node cache."""
from contextlib import contextmanager
import json
import re
from pathlib import Path
import sqlite3
from .common import (CatalogError, MAX_SNAPSHOT, ZERO, canonical, content, digest, identifier,
                     logical_path, now, policy)
from .state import Catalog
from ..client import ClientError, request_json
from ..identity import ensure_private_home
from .. import validation as valid


class MetadataSource:
    def __init__(self, registry):
        self.registry, self.catalog = registry, Catalog(registry)

    def snapshot(self):
        with self.registry.connect() as db:
            db.execute('BEGIN')
            state = self.catalog._state(db)
            cluster=db.execute("SELECT value FROM settings WHERE key='cluster_id'").fetchone()[0]
            ids=[r[0] for r in db.execute('SELECT file_id FROM catalog_files ORDER BY file_id')]
            value={'schema_version':1,'cluster_id':cluster,'epoch':state['epoch'],'revision':state['revision'],
                   'head_digest':state['head_digest'],'created_at':now(),
                   'files':[self.catalog._aggregate(db,i) for i in ids]}
        value['digest']=digest(value)
        if len(canonical(value))>MAX_SNAPSHOT-4096:
            raise CatalogError('snapshot_limit',507)
        return value

    def changes(self, after):
        if type(after) is not int or after<0:
            raise CatalogError('invalid_revision',400)
        with self.registry.connect() as db:
            db.execute('BEGIN')
            state=self.catalog._state(db)
            cluster=db.execute("SELECT value FROM settings WHERE key='cluster_id'").fetchone()[0]
            if after>state['revision']:
                raise CatalogError('resync_required',409)
            cursor=db.execute('SELECT * FROM catalog_events WHERE revision>? ORDER BY revision LIMIT 100',(after,))
            events=[];size=0
            try:
                for row in cursor:
                    if not events and row['revision']!=after+1:
                        raise CatalogError('resync_required',409)
                    item=dict(row);item['payload']=json.loads(item['payload'])
                    item_size=len(canonical(item))
                    if size+item_size>MAX_SNAPSHOT-4096:
                        if not events:raise CatalogError('resync_required',409)
                        break
                    events.append(item);size+=item_size
            finally:
                cursor.close()
            if after<state['revision'] and not events:
                raise CatalogError('resync_required',409)
        return {'schema_version':1,'cluster_id':cluster,'epoch':state['epoch'],'from_revision':after,
                'through_revision':events[-1]['revision'] if events else after,
                'current_revision':state['revision'],'head_digest':state['head_digest'],'events':events}


FILE_FIELDS={'file_id','logical_path','version','size','sha256','policy','created_at','updated_at','revision'}
REPLICA_FIELDS={'replica_id','file_id','node_id','volume_id','local_file_id','state','created_at','updated_at','verified_at'}


def aggregate(value, revision):
    if not isinstance(value,dict) or set(value)!={'file','replicas'}:
        raise CatalogError('invalid_metadata',409)
    file=value['file'];replicas=value['replicas']
    if not isinstance(file,dict) or set(file)!=FILE_FIELDS or not isinstance(replicas,list) or len(replicas)>2048:
        raise CatalogError('invalid_metadata',409)
    identifier(file['file_id']);logical_path(file['logical_path']);content(file['size'],file['sha256']);policy(file['policy'])
    if type(file['version']) is not int or file['version']<1:
        raise CatalogError('invalid_metadata',409)
    for field in ('created_at','updated_at','revision'):
        if type(file[field]) is not int or not 0<=file[field]<=2**63-1:
            raise CatalogError('invalid_metadata',409)
    if file['revision']>revision:
        raise CatalogError('invalid_revision',409)
    seen=set()
    for row in replicas:
        if not isinstance(row,dict) or set(row)!=REPLICA_FIELDS or row['file_id']!=file['file_id']:
            raise CatalogError('invalid_metadata',409)
        for field in ('replica_id','file_id','volume_id','local_file_id'):
            identifier(row[field])
        valid.node_id(row['node_id'])
        if row['replica_id'] in seen or row['state'] not in ('VERIFIED','MISSING','CORRUPT','UNAVAILABLE','METADATA_CONFLICT'):
            raise CatalogError('invalid_metadata',409)
        seen.add(row['replica_id'])
        for field in ('created_at','updated_at','verified_at'):
            if row[field] is not None and (type(row[field]) is not int or row[field]<0):
                raise CatalogError('invalid_metadata',409)
        if row['state']=='VERIFIED' and row['verified_at'] is None:
            raise CatalogError('invalid_metadata',409)
    return value


class MetadataReplica:
    """The only writes are validated transport imports; never a Global Catalog writer."""
    def __init__(self,path,cluster_id,read_only=False):
        self.path,self.cluster_id,self.read_only=Path(path),cluster_id,read_only
        if read_only:
            if not self.path.is_file():
                raise CatalogError('metadata_unavailable',404)
            with self.connect() as db:
                if db.execute('PRAGMA user_version').fetchone()[0]!=1:
                    raise CatalogError('unsupported_metadata_schema',409)
                state=self._state(db)
                if state and state['cluster_id']!=cluster_id:
                    raise CatalogError('cluster_identity_mismatch',409)
            return
        ensure_private_home(self.path.parent)
        with self.connect() as db:
            version=db.execute('PRAGMA user_version').fetchone()[0]
            if version not in (0,1):
                raise CatalogError('unsupported_metadata_schema',409)
            db.execute('CREATE TABLE IF NOT EXISTS replica_state(singleton INTEGER PRIMARY KEY,data TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS replica_files(file_id TEXT PRIMARY KEY,data TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS replica_events(revision INTEGER PRIMARY KEY,digest TEXT NOT NULL)')
            db.execute('PRAGMA user_version=1')
            state=self._state(db)
            if state and state['cluster_id']!=cluster_id:
                raise CatalogError('cluster_identity_mismatch',409)

    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path.resolve().as_uri()+'?mode=ro',uri=True) if self.read_only else sqlite3.connect(self.path,timeout=15)
        try:
            if not self.read_only:
                db.execute('PRAGMA synchronous=FULL')
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def _state(db):
        row=db.execute('SELECT data FROM replica_state WHERE singleton=1').fetchone()
        return json.loads(row[0]) if row else None

    def status(self):
        with self.connect() as db:
            state=self._state(db)
        if not state:
            return {'read_only':True,'stale':True,'revision':None,'last_sync_at':None}
        return {**state,'read_only':True,'stale':True,'lag':state['controller_revision']-state['revision']}

    def files(self):
        with self.connect() as db:
            rows=[json.loads(r[0]) for r in db.execute('SELECT data FROM replica_files ORDER BY file_id')]
        return {'files':rows,'metadata':self.status()}

    def file(self,file_id):
        with self.connect() as db:
            row=db.execute('SELECT data FROM replica_files WHERE file_id=?',(identifier(file_id),)).fetchone()
        if not row:
            raise CatalogError('file_not_found',404)
        return {'entry':json.loads(row[0]),'metadata':self.status(),'available_replicas':None}

    def _envelope(self,value):
        if (not isinstance(value,dict) or type(value.get('schema_version')) is not int or value.get('schema_version')!=1 or type(value.get('revision',value.get('current_revision'))) is not int or
                value.get('cluster_id')!=self.cluster_id or len(canonical(value))>MAX_SNAPSHOT):
            raise CatalogError('invalid_metadata',409)
        identifier(value.get('epoch'))
        if not isinstance(value.get('head_digest'),str) or not re.fullmatch('[a-f0-9]{64}',value['head_digest']):
            raise CatalogError('invalid_metadata',409)

    def install(self,value):
        if self.read_only:
            raise CatalogError('read_only_metadata',403)
        self._envelope(value)
        if set(value)!={'schema_version','cluster_id','epoch','revision','head_digest','created_at','files','digest'}:
            raise CatalogError('invalid_snapshot',409)
        if digest({k:v for k,v in value.items() if k!='digest'})!=value['digest']:
            raise CatalogError('snapshot_digest_mismatch',409)
        if (not isinstance(value['files'],list) or len(value['files'])>256 or value['revision']<0 or
                type(value['created_at']) is not int or value['created_at']<0):
            raise CatalogError('invalid_snapshot',409)
        entries=[aggregate(item,value['revision']) for item in value['files']]
        ids=[item['file']['file_id'] for item in entries]
        if len(set(ids))!=len(ids):
            raise CatalogError('invalid_snapshot',409)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            current=self._state(db)
            if current and (current['epoch']!=value['epoch'] or current['revision']>value['revision'] or
                    current['revision']==value['revision'] and current['head_digest']!=value['head_digest']):
                raise CatalogError('metadata_rollback_or_epoch_conflict',409)
            if current and current['revision']==value['revision']:
                stored=[json.loads(r[0]) for r in db.execute('SELECT data FROM replica_files ORDER BY file_id')]
                incoming=sorted(entries,key=lambda item:item['file']['file_id'])
                if canonical(stored)!=canonical(incoming):
                    raise CatalogError('snapshot_checkpoint_conflict',409)
            db.execute('DELETE FROM replica_files');db.execute('DELETE FROM replica_events')
            db.executemany('INSERT INTO replica_files VALUES(?,?)',
                           [(item['file']['file_id'],canonical(item).decode()) for item in entries])
            state={k:value[k] for k in ('cluster_id','epoch','revision','head_digest')}
            state.update(controller_revision=value['revision'],last_sync_at=now())
            db.execute('INSERT OR REPLACE INTO replica_state VALUES(1,?)',(canonical(state).decode(),))
        return self.status()

    def apply(self,value):
        if self.read_only:
            raise CatalogError('read_only_metadata',403)
        self._envelope(value)
        if set(value)!={'schema_version','cluster_id','epoch','from_revision','through_revision','current_revision','head_digest','events'}:
            raise CatalogError('invalid_metadata',409)
        if not isinstance(value['events'],list) or len(value['events'])>100:
            raise CatalogError('invalid_metadata',409)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            state=self._state(db)
            if not state or state['epoch']!=value['epoch'] or value['from_revision']>state['revision']:
                raise CatalogError('revision_gap',409)
            expected=value['from_revision']
            for event in value['events']:
                if not isinstance(event,dict) or set(event)!={'epoch','revision','previous_digest','digest','payload','created_at'}:
                    raise CatalogError('invalid_metadata',409)
                expected+=1
                if (type(event['revision']) is not int or event['revision']!=expected or event['epoch']!=state['epoch'] or
                        digest({k:v for k,v in event.items() if k!='digest'})!=event['digest']):
                    raise CatalogError('invalid_event_digest_or_order',409)
                if event['revision']<=state['revision']:
                    prior=db.execute('SELECT digest FROM replica_events WHERE revision=?',(event['revision'],)).fetchone()
                    if not prior or prior[0]!=event['digest']:
                        raise CatalogError('duplicate_event_conflict',409)
                    continue
                if event['revision']!=state['revision']+1 or event['previous_digest']!=state['head_digest']:
                    raise CatalogError('revision_gap',409)
                item=aggregate(event['payload'],event['revision'])
                if item['file']['revision']!=event['revision']:
                    raise CatalogError('invalid_metadata',409)
                db.execute('INSERT OR REPLACE INTO replica_files VALUES(?,?)',(item['file']['file_id'],canonical(item).decode()))
                db.execute('INSERT INTO replica_events VALUES(?,?)',(event['revision'],event['digest']))
                state.update(revision=event['revision'],head_digest=event['digest'])
            if (expected!=value['through_revision'] or value['current_revision']<state['revision'] or
                    value['through_revision']!=state['revision'] or
                    state['revision']==value['current_revision'] and state['head_digest']!=value['head_digest']):
                raise CatalogError('revision_gap',409)
            state.update(controller_revision=value['current_revision'],last_sync_at=now())
            db.execute('INSERT OR REPLACE INTO replica_state VALUES(1,?)',(canonical(state).decode(),))
            db.execute('DELETE FROM replica_events WHERE revision<=?',(state['revision']-1024,))
        return self.status()


def synchronize(home,node):
    replica=MetadataReplica(Path(home)/'catalog-metadata.sqlite3',node['cluster_id'])
    prefix='/catalog/v1/metadata/'
    discovery=None
    if 'controllers' in node:
        from ..failover.discovery import Discovery
        discovery=Discovery(node['cluster_id'],node['controllers'],node['token'])
    def get(path):
        reply=(discovery.request('GET',prefix+path) if discovery else
               request_json(node['controller'],node['pin'],'GET',prefix+path,token=node['token']))
        version=reply.pop('protocol_version',None)
        if type(version) is not int or version!=1:raise CatalogError('unsupported_metadata_protocol',409)
        return reply
    status=replica.status()
    if status['revision'] is None:
        status=replica.install(get('snapshot?node_id='+node['node_id']))
    else:
        try:
            for _ in range(16):
                value=get('changes?node_id='+node['node_id']+'&after='+str(status['revision']))
                status=replica.apply(value)
                if status['lag']==0:
                    break
        except (CatalogError,ClientError) as exc:
            if isinstance(exc,ClientError) and exc.status!=409:
                raise
            status=replica.install(get('snapshot?node_id='+node['node_id']))
    ack={'node_id':node['node_id'],'epoch':status['epoch'],'revision':status['revision'],'head_digest':status['head_digest']}
    if discovery:
        discovery.request('POST',prefix+'ack',ack)
    else:
        request_json(node['controller'],node['pin'],'POST',prefix+'ack',ack,node['token'])
    return status
