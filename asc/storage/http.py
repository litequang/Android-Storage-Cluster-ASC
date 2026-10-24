"""Versioned node-local HTTPS storage; every operation is introspected at the controller."""
import json
import sqlite3
import ssl
import time
import uuid
import hashlib
from urllib.parse import urlsplit, parse_qs
from .. import validation as valid
from ..client import ClientError, request_json
from ..server import Handler, Server, PayloadTooLarge
from .errors import StorageError
from .volumes import CHUNK, identifier


class UploadBody:
    def __init__(self, stream, budget):
        self.stream = stream
        self.deadline = time.monotonic() + budget

    def read(self, size):
        if time.monotonic() > self.deadline:
            raise StorageError('upload_deadline', 408)
        chunk = self.stream.read1(size)  # Return available bytes, avoiding endless buffered trickle reads.
        if time.monotonic() > self.deadline:
            raise StorageError('upload_deadline', 408)
        return chunk


class StorageServer(Server):
    def __init__(self, address, engine, node_config):
        self.engine, self.node_config = engine, dict(node_config)
        self.discovery = None
        self.gc_executors = {}  # Only an in-process synthetic fixture may attach issued executors.
        if 'controllers' in node_config:
            from ..failover.discovery import Discovery
            if not node_config.get('cluster_epoch'):
                raise ValueError('distributed storage requires pinned cluster epoch')
            self.discovery = Discovery(node_config['cluster_id'], node_config['controllers'], node_config['token'])
        super().__init__(address, None, '', StorageHandler)


class StorageHandler(Handler):
    server_version = 'ASC-Storage/0.6.0'

    def _json(self, status, data):
        try:
            super()._json(status, data)
        except (BrokenPipeError, ConnectionResetError, ssl.SSLError):
            self.close_connection = True  # An interrupted peer cannot receive the JSON rejection.

    def _authorize(self, operation):
        if self.server.limiter.blocked('auth', self.client_address[0]):
            raise StorageError('rate_limited', 429)
        grants = self.headers.get_all('Authorization', [])
        volumes = self.headers.get_all('X-ASC-Volume-ID', [])
        grant = self._bearer()
        try:
            valid.secret(grant)
            if len(grants) != 1 or len(volumes) != 1:
                raise ValueError()
            volume = identifier(volumes[0])
        except (ValueError, StorageError):
            self.server.limiter.blocked('auth', self.client_address[0], consume=True)
            raise StorageError('unauthorized', 401) from None
        cfg = self.server.node_config
        obj={'node_id':cfg['node_id'],'grant':grant,'volume_id':volume,'operation':operation,
             'scope':{'method':self.command,'resource':urlsplit(self.path).path.removeprefix('/storage/v1/')}}
        try:
            if self.server.discovery is not None:
                from ..catalog.common import digest
                nonce = uuid.uuid4().hex
                obj['nonce'] = nonce
                reply = self.server.discovery.request('POST', '/api/v1/storage/authorize', obj)
                proof = reply.get('authority', {})
                expected = digest({'node_id': cfg['node_id'], 'grant_sha256': hashlib.sha256(grant.encode()).hexdigest(),
                    'volume_id': volume, 'operation': operation, 'scope': obj['scope'], 'nonce': nonce})
                if (proof.get('cluster_id') != cfg['cluster_id'] or proof.get('epoch') != cfg['cluster_epoch'] or
                        proof.get('nonce') != nonce or proof.get('intent_sha256') != expected or
                        type(proof.get('term')) is not int or proof['term'] < 1 or
                        type(proof.get('index')) is not int or proof['index'] < 1):
                    raise ClientError('invalid committed operation authority', 403)
            else:
                try:
                    reply=request_json(cfg['controller'],cfg['pin'],'POST','/api/v1/storage/authorize',obj,cfg['token'])
                except ClientError as exc:
                    if exc.status!=400:raise
                    # v0.5 rejects scope. The same pinned authority must approve this request;
                    # only a legacy whole-volume grant can succeed without scope.
                    legacy={k:v for k,v in obj.items() if k!='scope'}
                    reply=request_json(cfg['controller'],cfg['pin'],'POST','/api/v1/storage/authorize',legacy,cfg['token'])
        except ClientError as exc:
            if exc.status in (400, 401, 403):
                self.server.limiter.blocked('auth', self.client_address[0], consume=True)
                raise StorageError('forbidden', 403) from None
            raise StorageError('authorization_unavailable', 503) from None
        except (OSError, ValueError):
            raise StorageError('authorization_unavailable', 503) from None
        self._constraints = reply.get('constraints')
        self._authority_reply = reply
        return reply['principal'], volume

    def _route(self):
        parsed = urlsplit(self.path)
        parts = parsed.path.split('/')
        if (parsed.fragment or len(parts) < 4 or parts[:3] != ['', 'storage', 'v1'] or
                any(not p for p in parts[3:])):
            raise StorageError('not_found', 404)
        resource = parts[3]
        extra = parts[4:]
        method = self.command
        if resource == 'gc':
            if method != 'POST' or len(extra) != 1 or parsed.query:
                raise StorageError('not_found', 404)
            identifier(extra[0])
            if self.server.discovery is None or not self.server.gc_executors:
                raise StorageError('physical_gc_locked', 403)
            principal, volume = self._authorize('gc')
            from ..replication.sandbox import Executor
            executor = self.server.gc_executors.get(volume)
            if type(executor) is not Executor or executor.engine is not self.server.engine:
                raise StorageError('physical_gc_locked', 403)
            executor.capability.validate(self.server.engine)
            exact = self._constraints
            if not exact or exact.get('gc_job_id') != extra[0]:
                raise StorageError('forbidden', 403)
            valid.payload(self._read_json(), ())
            def fresh():
                self._authorize('gc')  # New nonce/actual-term commit; no cached reply or fallback.
                return self._authority_reply
            return self._json(200, executor.execute(exact, fresh))
        operation = 'write' if resource == 'uploads' else 'verify' if extra[-1:] == ['verify'] else 'list' if resource in ('volumes','status','inventory') or resource == 'files' and not extra else 'read'
        if (resource not in ('uploads', 'files', 'volumes','status','inventory') or
                method not in ('GET', 'POST', 'PUT')):
            raise StorageError('not_found', 404)
        principal, volume = self._authorize(operation)
        engine = self.server.engine
        constraints = self._constraints
        if constraints and constraints.get('kind')=='target' and resource=='uploads' and extra:
            session=engine.session(extra[0],principal,volume)
            if (any(session[field]!=constraints[field] for field in ('idempotency_key','logical_path','size','sha256')) or
                    constraints['session_id'] and constraints['session_id']!=extra[0] or
                    constraints['local_file_id'] and constraints['local_file_id']!=session['file_id']):
                raise StorageError('forbidden',403)
        if parsed.query and not (method == 'GET' and resource in ('files','inventory') and not extra):
            raise StorageError('bad_request', 400)
        if method == 'GET':
            if resource=='inventory' and not extra:
                query=parse_qs(parsed.query,strict_parsing=True)
                if set(query)-{'offset'} or any(len(v)!=1 for v in query.values()):
                    raise ValueError()
                return self._json(200,engine.reconciliation_inventory(volume,int(query.get('offset',['0'])[0])))
            if resource=='status' and not extra:
                return self._json(200,engine.placement_status(volume))
            if resource == 'volumes' and not extra:
                items = engine.volumes.inspect()
                return self._json(200, {'volumes': [v for v in items if v['volume_id'] == volume]})
            if resource == 'uploads' and len(extra) == 1:
                return self._json(200, {'session': engine.session(extra[0], principal, volume)})
            if resource == 'files' and not extra:
                query = parse_qs(parsed.query, strict_parsing=True)
                if set(query) - {'offset'} or any(len(v) != 1 for v in query.values()):
                    raise ValueError()
                return self._json(200, engine.list_files(volume, int(query.get('offset', ['0'])[0])))
            if resource == 'files' and len(extra) == 1:
                return self._json(200, {'file': engine.file(extra[0], volume)})
            if resource == 'files' and len(extra) == 2 and extra[1] == 'content':
                with engine.download(extra[0], volume) as (row, stream):
                    self.close_connection = True
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/octet-stream')
                    self.send_header('Content-Length', str(row['size']))
                    self.send_header('X-ASC-SHA256', row['sha256'])
                    self.send_header('Cache-Control', 'no-store')
                    self.send_header('Connection', 'close')
                    self.end_headers()
                    self._started = True
                    count, started = 0, time.monotonic()
                    while True:
                        chunk = stream.read(CHUNK)
                        if not chunk:
                            break
                        self.wfile.write(chunk); count += len(chunk); engine._pace(count, started)
                return
        if method == 'POST':
            obj = self._read_json()
            if resource == 'uploads' and not extra:
                valid.payload(obj, ('idempotency_key', 'logical_path', 'size', 'sha256'))
                if constraints and constraints.get('kind')=='target' and any(obj[field]!=constraints[field] for field in ('idempotency_key','logical_path','size','sha256')):
                    raise StorageError('forbidden',403)
                row = engine.initiate(principal, volume, obj['idempotency_key'], obj['logical_path'], obj['size'], obj['sha256'])
                return self._json(201, {'session': row})
            if resource == 'uploads' and len(extra) == 2 and extra[1] == 'commit':
                valid.payload(obj, ())
                resume = self.server.discovery is not None and constraints and constraints.get('kind') == 'target'
                if resume:
                    row = engine.commit(extra[0], principal, volume, lambda: self._authorize('write'), resume_verified=True)
                else:
                    row = engine.commit(extra[0], principal, volume, lambda: self._authorize('write'))
                return self._json(200, {'file': row})
            if resource == 'files' and len(extra) == 2 and extra[1] == 'verify':
                valid.payload(obj, ())
                return self._json(200, engine.verify(extra[0], volume))
        if method == 'PUT' and resource == 'uploads' and len(extra) == 1:
            lengths = self.headers.get_all('Content-Length', [])
            if (len(lengths) != 1 or self.headers.get('Transfer-Encoding') or
                    self.headers.get('Content-Type') != 'application/octet-stream' or
                    not lengths[0].isdigit()):
                raise StorageError('bad_request', 400)
            length = int(lengths[0])
            body = UploadBody(self.rfile, 60 + min(length, engine.max_upload) / engine.rate)
            row = engine.upload(extra[0], principal, volume, body, length)
            return self._json(200, {'session': row})
        raise StorageError('not_found', 404)

    def _dispatch(self):
        self._started = False
        try:
            self._route()
        except StorageError as exc:
            if not self._started:
                self._json(exc.status, {'error': exc.code})
        except PayloadTooLarge:
            self._json(413, {'error': 'payload_too_large'})
        except (ValueError, UnicodeError, RecursionError, OverflowError):
            self._json(400, {'error': 'bad_request'})
        except sqlite3.Error:
            self._json(503, {'error': 'manifest_unavailable'})
        except OSError as exc:
            if not self._started:
                try:
                    self._json(507 if exc.errno == 28 else 503,
                               {'error': 'insufficient_space' if exc.errno == 28 else 'storage_io_error'})
                except OSError:
                    pass

    do_GET = do_POST = do_PUT = _dispatch
