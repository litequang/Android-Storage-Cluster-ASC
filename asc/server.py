"""HTTPS lifecycle API for a single-writer private LAN development registry."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import hmac
import json
import sqlite3
import ssl
import threading
import time
from urllib.parse import urlsplit
from . import validation as valid
from .store import SCHEMA_VERSION
from . import __version__

MAX_JSON = valid.MAX_JSON


class RateLimiter:
    """Fixed windows, bounded memory, no forwarded-IP trust. Restart resets counters."""
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.lock = threading.Lock()
        self.entries = {}
        self.limits = {'join': (8, 60), 'auth': (12, 120)}

    def _keys(self, group, ip):
        return ((group, '*'), (group, ip))

    def blocked(self, group, ip, consume=False):
        now = self.clock()
        with self.lock:
            self.entries = {k: v for k, v in self.entries.items() if now - v[0] < 60}
            keys = self._keys(group, ip)
            local_limit, global_limit = self.limits[group]
            if (self.entries.get(keys[0], (now, 0))[1] >= global_limit or
                    self.entries.get(keys[1], (now, 0))[1] >= local_limit or
                    (keys[1] not in self.entries and len(self.entries) >= 1024)):
                return True
            if consume:
                for key in keys:
                    started, count = self.entries.get(key, (now, 0))
                    self.entries[key] = (started, count + 1)
            return False


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, registry, admin_token, handler=None, catalog=None, *, bind_and_activate=True):
        self.catalog = catalog
        self.registry = registry
        self.admin_hash = hashlib.sha256(admin_token.encode()).hexdigest()
        self.limiter = RateLimiter()
        self.slots = threading.BoundedSemaphore(32)
        self.tls_context = None
        super().__init__(address, handler or Handler, bind_and_activate=bind_and_activate)

    def get_request(self):
        sock, address = super().get_request()
        sock.settimeout(12)
        return sock, address

    def process_request(self, request, client_address):
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self.slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            if self.tls_context is not None:
                request = self.tls_context.wrap_socket(request, server_side=True)
            super().process_request_thread(request, client_address)
        except (OSError, ssl.SSLError):
            self.shutdown_request(request)
        finally:
            self.slots.release()

    def handle_error(self, request, client_address):
        # Never dump request objects, headers, payloads or exception text.
        print('ASC request failed; sensitive details suppressed', flush=True)


class PayloadTooLarge(ValueError):
    pass


def _unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError('duplicate JSON key')
        obj[key] = value
    return obj


class Handler(BaseHTTPRequestHandler):
    server_version = 'ASC-LAN/' + __version__
    sys_version = ''

    def log_message(self, fmt, *args):
        # BaseHTTPRequestHandler also uses this for malformed request lines.
        pass

    def send_error(self, code, message=None, explain=None):
        self.close_connection = True
        self._json(code, {'error': 'bad_request'})

    def _json(self, status, data):
        self.close_connection = True
        raw = json.dumps({'protocol_version': 1, **data}, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Connection', 'close')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        if status == 429:
            self.send_header('Retry-After', '60')
        self.end_headers()
        self.wfile.write(raw)

    def _read_json(self):
        if self.headers.get('Content-Type', '').split(';')[0].strip() != 'application/json':
            raise ValueError('expected application/json')
        lengths = self.headers.get_all('Content-Length', [])
        if len(lengths) != 1 or self.headers.get('Transfer-Encoding'):
            raise ValueError('invalid framing')
        length = int(lengths[0])
        if length > MAX_JSON:
            # Windows can reset TLS while the peer is still sending a small oversized body.
            # Bounded discard only: never parse it, allocate by its length or drain an arbitrary stream.
            if length <= MAX_JSON * 2:
                timeout = self.connection.gettimeout()
                deadline, remaining = time.monotonic() + 2, length
                try:
                    self.connection.settimeout(1)
                    while remaining and time.monotonic() < deadline:
                        chunk = self.rfile.read1(min(65536, remaining))
                        if not chunk:
                            break
                        remaining -= len(chunk)
                except OSError:
                    pass
                finally:
                    self.connection.settimeout(timeout)
            raise PayloadTooLarge()
        if length < 1:
            raise ValueError('invalid content length')
        raw = self.rfile.read(length)
        if len(raw) != length:
            raise ValueError('incomplete body')
        obj = json.loads(raw, object_pairs_hook=_unique_object,
                         parse_constant=lambda _: (_ for _ in ()).throw(ValueError('invalid number')))
        if not isinstance(obj, dict):
            raise ValueError('expected object')
        return obj

    def _bearer(self):
        values = self.headers.get_all('Authorization', [])
        if len(values) != 1:
            return ''
        raw = values[0]
        return raw[7:] if raw.startswith('Bearer ') and len(raw) <= 135 else ''

    def _rate(self, group, consume=False):
        if self.server.limiter.blocked(group, self.client_address[0], consume):
            self._json(429, {'error': 'rate_limited'})
            return True
        return False

    def _admin(self):
        if self._rate('auth'):
            return False
        token = self._bearer()
        if not token or not hmac.compare_digest(hashlib.sha256(token.encode()).hexdigest(), self.server.admin_hash):
            self.server.limiter.blocked('auth', self.client_address[0], consume=True)
            self._json(401, {'error': 'unauthorized'})
            return False
        return True

    def do_GET(self):
        try:
            path = urlsplit(self.path).path
            if path.startswith('/catalog/v1/'):
                from .catalog.http import handle
                return handle(self)
            if path == '/api/v1/info':
                if getattr(self.server.catalog, 'distributed', False):
                    return self._json(200, {'cluster_id': self.server.registry.cluster_id(),
                        'mode': 'metadata-consensus-development', 'schema_version': SCHEMA_VERSION,
                        'features': ['metadata-consensus-v1'], 'raft_enabled': True,
                        'automatic_failover': False, 'file_storage_enabled': False,
                        'global_file_catalog_enabled': True})
                return self._json(200, {'cluster_id': self.server.registry.cluster_id(),
                                       'mode': 'single-writer-development', 'schema_version': SCHEMA_VERSION,
                                       'features': ['node-lifecycle-v1', 'retry-safe-enrollment-v1', 'local-storage-v1', 'file-scoped-transfers-v1'] +
                                                   (['global-catalog-v1','metadata-replication-v1'] if self.server.catalog else []),
                                       'raft_enabled': False, 'file_storage_enabled': True,
                                       'storage_mode': 'node-local-opt-in', 'global_file_catalog_enabled': self.server.catalog is not None})
            if path == '/api/v1/nodes' or path.startswith('/api/v1/nodes/'):
                if not self._admin():
                    return
                if path == '/api/v1/nodes':
                    return self._json(200, self.server.registry.snapshot())
                node = self.server.registry.detail(path.removeprefix('/api/v1/nodes/'))
                return self._json(200, {'node': node}) if node else self._json(404, {'error': 'not_found'})
            return self._json(404, {'error': 'not_found'})
        except ValueError:
            return self._json(400, {'error': 'bad_request'})
        except sqlite3.Error:
            return self._json(503, {'error': 'registry_unavailable'})

    def do_POST(self):
        path = urlsplit(self.path).path
        if path.startswith('/catalog/v1/'):
            from .catalog.http import handle
            return handle(self)
        admin_paths = ('/api/v1/admin/pair', '/api/v1/admin/rename', '/api/v1/admin/revoke', '/api/v1/admin/storage-grant')
        if path not in ('/api/v1/join', '/api/v1/heartbeat', '/api/v1/storage/authorize') + admin_paths:
            return self._json(404, {'error': 'not_found'})
        if path in admin_paths and not self._admin():
            return
        if path == '/api/v1/join' and self._rate('join', consume=True):
            return
        if path in ('/api/v1/heartbeat', '/api/v1/storage/authorize') and self._rate('auth'):
            return
        try:
            obj = self._read_json()
            reg = self.server.registry
            if path == '/api/v1/admin/storage-grant':
                valid.payload(obj, ('node_id', 'volume_id', 'operations'), ('ttl',))
                return self._json(201, reg.storage_grant(obj['node_id'], obj['volume_id'],
                                                        obj['operations'], obj.get('ttl', 300)))
            if path == '/api/v1/storage/authorize':
                valid.payload(obj, ('node_id', 'grant', 'volume_id', 'operation'), ('scope',))
                reply = reg.storage_authorize(obj['node_id'], self._bearer(), obj['grant'],
                                              obj['volume_id'], obj['operation'], obj.get('scope'))
                if reply is None:
                    self.server.limiter.blocked('auth', self.client_address[0], consume=True)
                    return self._json(403, {'error': 'unauthorized'})
                return self._json(200, reply)
            if path == '/api/v1/join':
                valid.payload(obj, ('code', 'name', 'profile'), ('enrollment_id', 'enrollment_token', 'node_id'))
                if 'enrollment_id' in obj or 'enrollment_token' in obj:
                    valid.secret(obj.get('enrollment_id'))
                    valid.secret(obj.get('enrollment_token'))
                if 'node_id' in obj:
                    valid.node_id(obj['node_id'])
                reply = reg.join(obj['code'], obj['name'], obj['profile'],
                                 obj.get('enrollment_id'), obj.get('enrollment_token'), obj.get('node_id'))
                if reply is None:
                    return self._json(403, {'error': 'invalid_or_expired_code'})
                return self._json(201, {'cluster_id': reg.cluster_id(), **reply, 'mode': 'single-writer-development'})
            if path == '/api/v1/heartbeat':
                valid.payload(obj, ('node_id', 'profile'))
                if not reg.heartbeat(obj['node_id'], self._bearer(), obj['profile']):
                    self.server.limiter.blocked('auth', self.client_address[0], consume=True)
                    return self._json(401, {'error': 'credential_rejected_repair_required'})
                return self._json(200, {**reg.snapshot(),'catalog_metadata_enabled': self.server.catalog is not None})
            if path == '/api/v1/admin/pair':
                valid.payload(obj, (), ('ttl', 'node_id'))
                ttl = obj.get('ttl', 600)
                if type(ttl) is not int or not 60 <= ttl <= 1800:
                    raise ValueError('invalid TTL')
                code = reg.add_pair_code(ttl, obj.get('node_id'))
                return self._json(201, {'code': code, 'ttl': ttl, 'node_id': obj.get('node_id')})
            if path == '/api/v1/admin/rename':
                valid.payload(obj, ('node_id', 'name'))
                ok = reg.rename(obj['node_id'], obj['name'])
            else:
                valid.payload(obj, ('node_id',))
                ok = reg.revoke(obj['node_id'])
            return self._json(200, {'ok': True}) if ok else self._json(404, {'error': 'not_found'})
        except PayloadTooLarge:
            return self._json(413, {'error': 'payload_too_large'})
        except (ValueError, UnicodeError, RecursionError, OverflowError):
            return self._json(400, {'error': 'bad_request'})
        except sqlite3.Error:
            return self._json(503, {'error': 'registry_unavailable'})


def serve(host, port, registry, admin_token, cert, key, catalog=None):
    httpd = Server((host, port), registry, admin_token, catalog=catalog)
    try:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(certfile=str(cert), keyfile=str(key))
        # Handshake happens in bounded workers, not in the accept loop.
        httpd.tls_context = context
        mode = 'metadata consensus; storage automation disabled' if getattr(catalog, 'distributed', False) else 'single-writer; no Raft'
        print(f'ASC development HTTPS on {host}:{port}; {mode}. Ctrl+C to stop.', flush=True)
        httpd.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
