"""Private UDS, Linux peer identity, separate application scopes and durable retries."""
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import socket
import socketserver
import sqlite3
import stat
import struct
import threading
import time
import uuid
from ..catalog.common import canonical, digest, identifier
from ..validation import code as normalized_code
from ..demo.installer import guard, private_path
from ..demo.state import inspect_state, read_db
from ..demo.locks import private_lock
from ..storage.errors import StorageError
from .contract import VERSION, MAX_FRAME, SCOPES, Refused, decode, request
from . import private
from .engine import Engine


def platform():
    if not hasattr(socket, 'AF_UNIX') or not hasattr(socket, 'SO_PEERCRED') or os.name != 'posix' or not hasattr(os, 'O_NOFOLLOW'):
        raise Refused('local_ipc_unsupported')


def separate(control, state):
    roots = [state]
    manifest = state / 'node/storage/manifest.sqlite3'
    if manifest.exists(): roots += read_db(manifest, 1, lambda db: [Path(r[0]) for r in db.execute('SELECT root FROM volumes')])
    if any(control == r or control in r.parents or r in control.parents for r in roots):
        raise Refused('control_overlaps_engine')


def provision(control, state, scopes=('read',)):
    platform(); guard(); state = private_path(state)
    if not (state/'demo.json').exists(): raise Refused('setup_required')
    marker = inspect_state(state)
    control = private_path(control); separate(control, state)
    if not set(scopes) <= {'read', 'join', 'lifecycle'} or 'read' not in scopes:
        raise Refused('invalid_scopes')
    # New authorization only, never engine identity; partial existing control held.
    control.mkdir(mode=0o700); private.directory(control)
    app = str(uuid.uuid4()); secret = secrets.token_urlsafe(32)
    prefix = os.environ.get('ASC_DEMO_PREFIX')
    state_info = state.lstat()
    cfg = {'format': 1, 'state_identity': [state_info.st_dev,state_info.st_ino], 'mode': 'demo-local-engine', 'state': str(state), 'installation_id': marker['installation_id'],
           'app_id': app, 'authorization_sha256': hashlib.sha256(secret.encode()).hexdigest(),
           'scopes': sorted(set(scopes)), 'prefix': prefix}
    private.initialize_journal(control)
    private.create(control / 'client.json', {'format': 1, 'app_id': app, 'authorization': secret})
    private.create(control / 'bridge.json', cfg)
    return {'format': 1, 'provisioned': True, 'scopes': cfg['scopes'], 'application_authorization_file': str(control / 'client.json'),
            'engine_initialized': False, 'cross_uid_supported': False}


def load(control):
    platform(); control = private.directory(control); cfg = private.read(control / 'bridge.json')
    if (set(cfg) != {'format','mode','state','installation_id','app_id','authorization_sha256','scopes','prefix','state_identity'} or
            type(cfg['format']) is not int or cfg['format'] != 1 or cfg['mode'] != 'demo-local-engine' or
            type(cfg['state_identity']) is not list or len(cfg['state_identity']) != 2 or any(type(x) is not int or x < 0 for x in cfg['state_identity']) or
            type(cfg['scopes']) is not list or not set(cfg['scopes']) <= {'read','join','lifecycle'} or 'read' not in cfg['scopes'] or
            not isinstance(cfg['authorization_sha256'],str) or len(cfg['authorization_sha256']) != 64 or
            cfg['prefix'] is not None and not isinstance(cfg['prefix'],str)):
        raise Refused('control_incompatible')
    identifier(cfg['installation_id']); identifier(cfg['app_id'])
    state = private_path(cfg['state']); separate(control, state)
    return cfg


class Bridge:
    def __init__(self, control):
        platform(); guard()
        self.root = private.directory(control); self.cfg = load(self.root)
        self.engine = Engine(self.cfg['state'], self.cfg['installation_id'], self.cfg['prefix'], self.cfg['state_identity'])
        info = self.root.lstat(); self.identity = (info.st_dev,info.st_ino)
        self.operation = threading.Lock()
        with private.journal(self.root): pass

    def dispatch(self, value, peer_uid):
        request(value)
        info = private.directory(self.root).lstat()
        if (info.st_dev,info.st_ino) != self.identity: raise Refused('control_identity_changed')
        if peer_uid != os.getuid() or value['app_id'] != self.cfg['app_id'] or not hmac.compare_digest(
                hashlib.sha256(value['authorization'].encode()).hexdigest(), self.cfg['authorization_sha256']):
            raise Refused('application_unauthorized')
        op = value['operation']
        if SCOPES[op] not in self.cfg['scopes']: raise Refused('scope_denied')
        self.engine.check()
        if op == 'status': return self.reply(value, self.engine.status())
        if op not in ('quick_join',): raise Refused('operation_not_supported')
        if not self.operation.acquire(blocking=False): raise Refused('operation_busy')
        try:
            params = dict(value['params']); raw_code = params.pop('code',None)
            if params.get('replace_code') is False: params.pop('replace_code')
            code_sha = hashlib.sha256(normalized_code(raw_code).encode()).hexdigest() if raw_code is not None else None
            intent = digest({'operation': op, 'params': params})
            with private.journal(self.root) as db:
                row = db.execute('SELECT app_id,intent,code_sha256,state,result FROM requests WHERE request_id=?', (value['request_id'],)).fetchone()
                if row:
                    if row[0] != value['app_id'] or row[1] != intent or code_sha is not None and code_sha != row[2]: raise Refused('request_id_conflict')
                    if row[3] == 'DONE': return self.reply(value, json.loads(row[4]), True)
                    if row[3] != 'RECEIVED': raise Refused('journal_incompatible')
                else:
                    if db.execute('SELECT COUNT(*) FROM requests').fetchone()[0] >= 256: raise Refused('request_limit')
                    db.execute('INSERT INTO requests VALUES(?,?,?,?,\'RECEIVED\',NULL)', (value['request_id'],value['app_id'],intent,code_sha))
            result = self.engine.quick_join(value['params'])
            with private.journal(self.root) as db:
                db.execute("UPDATE requests SET state='DONE',result=? WHERE request_id=?", (canonical(result).decode(),value['request_id']))
            return self.reply(value, result)
        finally: self.operation.release()

    def reply(self, value, result, replayed=False):
        return {'api_version': VERSION, 'request_id': value['request_id'], 'ok': True, 'result': result,
                'replayed': replayed, 'historical_receipt': replayed}

    def close(self): pass


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        self.connection.settimeout(3)
        value = None
        try:
            credentials = self.connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize('3i'))
            _, uid, _ = struct.unpack('3i', credentials)
            if uid != os.getuid(): raise Refused('application_unauthorized')
            raw = self.rfile.readline(MAX_FRAME + 2)
            if not raw.endswith(b'\n') or len(raw) > MAX_FRAME: raise Refused('invalid_frame')
            value = decode(raw); result = self.server.bridge.dispatch(value, uid)
        except Refused as exc:
            result = {'api_version':VERSION,'ok':False,'error':exc.code}
        except (ValueError,KeyError,TypeError,OSError,sqlite3.Error,StorageError):
            result = {'api_version':VERSION,'ok':False,'error':'operation_unconfirmed'}
        raw = canonical(result) + b'\n'
        if len(raw) > 65536: raw = b'{"api_version":1,"ok":false,"error":"response_limit"}\n'
        try: self.wfile.write(raw)
        except OSError: pass


class Server(socketserver.ThreadingUnixStreamServer):
    daemon_threads = False
    def __init__(self, path, bridge):
        self.bridge = bridge; self.slots = threading.BoundedSemaphore(8)
        super().__init__(str(path), Handler)
    def process_request(self, request, address):
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request); return
        try: super().process_request(request,address)
        except BaseException: self.slots.release(); raise
    def process_request_thread(self, request, address):
        try: super().process_request_thread(request,address)
        finally: self.slots.release()
    def handle_error(self, request, address): pass  # Never log frames/credentials.


class Runtime:
    def __init__(self, control):
        platform(); guard(); self.root = private.directory(control)
    def __enter__(self):
        self.owner = private_lock(self.root,'bridge'); self.owner.__enter__()
        try:
            self.bridge = Bridge(self.root); self.path = self.root / 'engine.sock'
            # Never remove/adopt an existing socket, including a stale one.
            if self.path.exists() or self.path.is_symlink(): raise Refused('socket_already_exists')
            self.server = Server(self.path,self.bridge); os.chmod(self.path,0o600)
            info = self.path.lstat(); self.socket_identity = (info.st_dev,info.st_ino)
            self.thread = threading.Thread(target=self.server.serve_forever,daemon=True); self.thread.start()
            return self
        except BaseException:
            if hasattr(self,'server'): self.server.server_close()
            if hasattr(self,'bridge'): self.bridge.close()
            self.owner.__exit__(None,None,None); raise
    def __exit__(self,*_):
        try:
            self.server.shutdown(); self.server.server_close(); self.thread.join(); self.bridge.close()
            info = self.path.lstat()
            if stat.S_ISSOCK(info.st_mode) and (info.st_dev,info.st_ino) == self.socket_identity:
                self.path.unlink()  # Only the socket exclusively created by this instance.
        finally: self.owner.__exit__(None,None,None)


def call(control, operation, params=None, request_id=None):
    control = private.directory(control); credential = private.read(control/'client.json')
    if set(credential) != {'format','app_id','authorization'} or type(credential['format']) is not int or credential['format'] != 1:
        raise Refused('control_incompatible')
    value = {'api_version':VERSION,'request_id':request_id or str(uuid.uuid4()),'app_id':credential['app_id'],
             'authorization':credential['authorization'],'operation':operation,'params':params or {}}
    request(value)
    path = control/'engine.sock'; info = path.lstat()
    if not stat.S_ISSOCK(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077: raise Refused('unsafe_socket')
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as connection:
        connection.settimeout(55); connection.connect(str(path))
        _, uid, _ = struct.unpack('3i', connection.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,struct.calcsize('3i')))
        if uid != os.getuid(): raise Refused('application_unauthorized')
        connection.sendall(canonical(value)+b'\n')
        with connection.makefile('rb') as stream: raw = stream.readline(65537)
    if not raw.endswith(b'\n') or len(raw)>65536: raise Refused('invalid_response')
    # Responses may exceed request bound due approved-volume status.
    result=json.loads(raw)
    if type(result) is not dict or type(result.get('api_version')) is not int or result['api_version']!=VERSION:
        raise Refused('invalid_response')
    return result
