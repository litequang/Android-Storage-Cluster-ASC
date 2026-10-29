"""Owner-session pairing facade. Existing Registry owns durable enrollment state."""
import hashlib
from pathlib import Path
import threading
import time
import uuid

from .. import validation as valid
from ..catalog.common import identifier
from ..identity import fingerprint_from_pem
from .state import inspect_state, read_json


class PairingError(Exception):
    def __init__(self,status,code):self.status,self.code=status,code


class Pairings:
    def __init__(self,root,service,client,clock=time.monotonic):
        self.root,self.service,self.client=Path(root),service,client
        self.clock=clock;self.lock=threading.Lock();self.tickets={}
        self._ready()

    def _ready(self):
        # Never adapt a quorum/unknown service by silently falling back to SQL.
        from .lan import DemoCatalog
        if not isinstance(self.service,DemoCatalog) or getattr(self.service,'failover',False):
            raise PairingError(403,'unsupported_runtime')
        marker=inspect_state(self.root)
        home=self.root/'controller'
        if marker['role']!='controller' or self.service.registry.path!=home/'registry.sqlite3':
            raise PairingError(403,'unsupported_runtime')
        cfg=read_json(home/'controller.json')
        origin=f"https://{marker['host']}:{marker['port']}"
        pin=fingerprint_from_pem(home/'server.crt')
        if self.client.origin!=origin or self.client.pin!=pin or self.service.registry.cluster_id()!=cfg['cluster_id']:
            raise PairingError(403,'cluster_binding_rejected')
        return cfg,origin,pin

    def create(self,owner,session_expires):
        from .lan import lifecycle_request
        with self.lock:
            self.tickets={k:v for k,v in self.tickets.items() if v['keep_until']>self.clock()}
            if session_expires<=self.clock():raise PairingError(401,'login_required')
            if len(self.tickets)>=32 or sum(t['owner']==owner for t in self.tickets.values())>=8:
                raise PairingError(429,'pairing_limit')
            cfg,origin,pin=self._ready()
            reply=lifecycle_request(self.client,'POST','admin/pair',{'ttl':600})
            code=valid.code(reply['code']);code_hash=hashlib.sha256(code.encode()).hexdigest()
            with self.service.registry.connect() as db:
                row=db.execute('SELECT expires_at FROM join_codes WHERE code_hash=?',(code_hash,)).fetchone()
            if row is None:raise PairingError(503,'pairing_unconfirmed')
            pairing_id=str(uuid.uuid4())
            self.tickets[pairing_id]={'owner':owner,'keep_until':session_expires,'code_hash':code_hash,
                'cluster_id':cfg['cluster_id'],'expires_at':row['expires_at']}
            # Raw one-use node grant returned only on this owner-authorized POST.
            return {'quick_join_version':1,'pairing_id':pairing_id,'code':code,'expires_at':row['expires_at'],
                'expires_in':max(0,row['expires_at']-int(time.time())),'controller':origin,'pin':pin,
                'cluster_id':cfg['cluster_id'],'runtime':'single-writer-demo','storage_auto_approval':False}

    def status(self,pairing_id,owner):
        identifier(pairing_id)
        with self.lock:
            ticket=self.tickets.get(pairing_id)
            if not ticket or ticket['owner']!=owner or ticket['keep_until']<=self.clock():
                raise PairingError(404,'pairing_not_found')
            ticket=dict(ticket)
        result={'quick_join_version':1,'pairing_id':pairing_id,'state':'unknown','node_id':None,
            'storage_approved':None,'failure_domain':None,'checked_at':int(time.time())}
        # Read-only current evidence, never cached approval or inferred capacity.
        self._ready()
        with self.service.registry.connect() as db:
            row=db.execute('SELECT used,node_id,expires_at FROM join_codes WHERE code_hash=?',(ticket['code_hash'],)).fetchone()
            if row is None:return result
            if not row['used']:
                return {**result,'state':'expired' if row['expires_at']<=int(time.time()) else 'waiting'}
            node=db.execute('SELECT state,token_version FROM nodes WHERE node_id=?',(row['node_id'],)).fetchone()
            if node is None:return result
            if node['state']!='active':return {**result,'state':'revoked','node_id':row['node_id']}
            approval=db.execute('SELECT storage_allowed,approved_generation,device_id FROM catalog_nodes WHERE node_id=?',
                                (row['node_id'],)).fetchone()
            approved=bool(approval and approval['approved_generation']==node['token_version'] and approval['storage_allowed'])
            return {**result,'state':'registered','node_id':row['node_id'],'storage_approved':approved,
                'failure_domain':approval['device_id'] if approved else None}

    def forget(self,owner):
        with self.lock:self.tickets={k:v for k,v in self.tickets.items() if v['owner']!=owner}

    def close(self):
        with self.lock:self.tickets.clear()
