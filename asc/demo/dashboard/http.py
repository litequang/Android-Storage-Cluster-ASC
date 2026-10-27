"""Same-origin owner-session browser API, reusing pinned Core transfer clients."""
from contextlib import contextmanager
import hashlib
from http.cookies import SimpleCookie, CookieError
import json
from pathlib import Path
import re
import shutil
import socket
import sqlite3
import tempfile
import threading
import time
from urllib.parse import urlsplit
import uuid
from ...catalog.common import identifier, logical_path, content, key
from ...client import ClientError
from ...server import Handler, PayloadTooLarge
from ...storage.errors import StorageError
from ...storage.volumes import no_links
from .assets import ASSETS
from .auth import COOKIE, SESSION_TTL, GRANT_TTL, Sessions
from .views import Views
from ..pairing import Pairings, PairingError

CSP = "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'; object-src 'none'; manifest-src 'self'; worker-src 'self'"
ERRORS = {'no_eligible_storage': 'insufficient_capacity', 'logical_version_exists': 'file_exists',
          'idempotency_conflict': 'idempotency_conflict', 'file_not_found': 'not_found',
          'no_available_replica': 'replica_unavailable'}


class Rejected(Exception):
    def __init__(self, status, code):
        self.status, self.code = status, code


class DashboardAPI:
    mode = 'single-writer-demo'
    def __init__(self, root, cfg, service, client, cluster_name):
        self.root, self.cfg, self.service, self.client = Path(root), cfg, service, client
        self.origin = f"https://{cfg['host']}:{cfg['port']}"
        self.sessions = Sessions()
        self.views = Views(service, cluster_name)
        self.pairings = Pairings(root,service,client)
        self.lock = threading.Lock()
        self.tickets = {}
        self.transfers = threading.BoundedSemaphore(1)

    @contextmanager
    def transfer(self):
        if not self.transfers.acquire(blocking=False):
            raise Rejected(429, 'transfer_busy')
        try:
            spool = self.root / 'dashboard/spool'
            no_links(spool)
            if not spool.is_dir():
                raise Rejected(503, 'spool_unavailable')
            yield spool
        finally:
            self.transfers.release()

    def ticket(self, ticket_id, identity):
        identifier(ticket_id)
        with self.lock:
            ticket = self.tickets.get(ticket_id)
            if not ticket or ticket['owner'] != identity or ticket['expires'] <= time.monotonic():
                raise Rejected(404, 'transfer_not_found')
            return dict(ticket)

    def update(self, ticket_id, **fields):
        with self.lock:
            self.tickets[ticket_id].update(fields)

    def progress(self, ticket_id, identity):
        ticket = self.ticket(ticket_id, identity)
        result = {k: ticket[k] for k in ('transfer_id', 'size', 'received_bytes', 'checksum_verified_bytes', 'status', 'file_id', 'error')}
        result['protected'] = self.views.file(ticket['file_id'])['protected']
        return result

    def prepare(self, obj, identity):
        if set(obj) != {'logical_path', 'size', 'sha256', 'idempotency_key'}:
            raise Rejected(400, 'bad_request')
        logical_path(obj['logical_path']); content(obj['size'], obj['sha256']); key(obj['idempotency_key'])
        if obj['size'] > self.cfg['max_upload_bytes']:
            raise Rejected(413, 'upload_too_large')
        with self.lock:
            self.tickets = {k: v for k, v in self.tickets.items() if v['expires'] > time.monotonic()}
            if len(self.tickets) >= 16 or sum(v['owner'] == identity for v in self.tickets.values()) >= 4:
                raise Rejected(429, 'transfer_limit')
        # Core owns placement, stable jobs, generations and idempotency. Never return its plan/grants.
        plan = self.client.request('POST', 'uploads', dict(obj, policy='replicated_2'))
        file_id = plan['file']['file']['file_id']
        if plan['completed']:
            return {'completed': True, 'file': self.views.file(file_id)}
        ticket_id = str(uuid.uuid4())
        ticket = dict(obj, owner=identity, expires=time.monotonic() + 600,
                      transfer_id=ticket_id, received_bytes=0, checksum_verified_bytes=None,
                      status='ready', file_id=file_id, error=None)
        with self.lock:
            # Recheck after Core IO; bounded maps never silently evict live transfers.
            if len(self.tickets) >= 16 or sum(v['owner'] == identity for v in self.tickets.values()) >= 4:
                raise Rejected(429, 'transfer_limit')
            self.tickets[ticket_id] = ticket
        return {'completed': False, 'transfer_id': ticket_id, 'file': self.views.file(file_id),
                'max_upload_bytes': self.cfg['max_upload_bytes']}

    def close(self):
        self.sessions.close()
        self.pairings.close()
        with self.lock:
            self.tickets.clear()


class DashboardHandler(Handler):
    server_version = 'ASC-Demo-Dashboard'

    def _headers(self, status, mime, length, extra=()):
        self.close_connection = True
        self.send_response(status)
        for k, v in (('Content-Type', mime), ('Content-Length', str(length)), ('Cache-Control', 'no-store'),
                     ('X-Content-Type-Options', 'nosniff'), ('Referrer-Policy', 'no-referrer'),
                     ('X-Frame-Options', 'DENY'), ('Content-Security-Policy', CSP),
                     ('Cross-Origin-Resource-Policy', 'same-origin'),
                     ('Permissions-Policy', 'camera=(), microphone=(), geolocation=()'),
                     ('Connection', 'close'), *extra):
            self.send_header(k, v)
        self.end_headers()
        self._response_started = True

    def _json(self, status, obj, extra=()):
        raw = json.dumps(obj, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')
        if len(raw) > 2 * 1024**2:
            status, raw = 503, b'{"error":"view_too_large"}'
        self._headers(status, 'application/json; charset=utf-8', len(raw), extra)
        self.wfile.write(raw)

    def browser_origin(self, mutation=False):
        api = self.server.api
        hosts = self.headers.get_all('Host', [])
        origins = self.headers.get_all('Origin', [])
        if (hosts != [urlsplit(api.origin).netloc] or len(origins) > 1
                or origins and origins != [api.origin] or mutation and origins != [api.origin]
                or self.headers.get('Sec-Fetch-Site', 'same-origin') not in ('same-origin', 'none')):
            raise Rejected(403, 'origin_rejected')

    def auth(self, csrf=True):
        if self._rate('auth'):
            return None
        cookie_name = getattr(self.server.api,'cookie_name',COOKIE)
        headers = self.headers.get_all('Cookie', [])
        if len(headers) != 1 or len(headers[0]) > 4096 or len(re.findall(r'(?:^|;)\s*' + re.escape(cookie_name) + '=', headers[0])) != 1:
            self.server.limiter.blocked('auth', self.client_address[0], consume=True)
            raise Rejected(401, 'login_required')
        parsed = SimpleCookie()
        try:
            parsed.load(headers[0])
        except CookieError:
            self.server.limiter.blocked('auth', self.client_address[0], consume=True)
            raise Rejected(401, 'login_required') from None
        cookie = parsed[cookie_name].value if cookie_name in parsed else ''
        values = self.headers.get_all('X-ASC-CSRF', [])
        if csrf and len(values) != 1:
            self.server.limiter.blocked('auth', self.client_address[0], consume=True)
            raise Rejected(403, 'csrf_required')
        result = self.server.api.sessions.authenticate(cookie, values[0] if csrf else None)
        if result is None:
            self.server.limiter.blocked('auth', self.client_address[0], consume=True)
            raise Rejected(401, 'login_required')
        return cookie, result[0], result[1]

    def body_json(self):
        values = self.headers.get_all('Content-Length', [])
        if len(values) == 1 and values[0].isdigit() and int(values[0]) > 8192:
            raise Rejected(413, 'metadata_too_large')
        return super()._read_json()

    def _upload(self, ticket_id, auth):
        api = self.server.api
        cookie, identity, session = auth
        ticket = api.ticket(ticket_id, identity)
        lengths = self.headers.get_all('Content-Length', [])
        if (lengths != [str(ticket['size'])] or self.headers.get('Transfer-Encoding')
                or self.headers.get('Content-Type') != 'application/octet-stream'):
            raise Rejected(400, 'invalid_upload_framing')
        with api.transfer() as directory:
            if shutil.disk_usage(directory).free < ticket['size'] + 8 * 1024**2:
                raise Rejected(507, 'insufficient_spool_space')
            api.update(ticket_id, status='receiving', received_bytes=0, checksum_verified_bytes=None, error=None)
            try:
                with tempfile.TemporaryFile(dir=directory) as stream:
                    remaining, sha = ticket['size'], hashlib.sha256()
                    deadline = time.monotonic() + 60 + ticket['size'] / (1024**2)
                    while remaining:
                        if time.monotonic() > deadline:
                            raise Rejected(408, 'upload_timeout')
                        chunk = self.rfile.read1(min(65536, remaining))
                        if not chunk:
                            raise Rejected(400, 'upload_incomplete')
                        stream.write(chunk); sha.update(chunk); remaining -= len(chunk)
                        api.update(ticket_id, received_bytes=ticket['size'] - remaining)
                    stream.flush()
                    import os
                    os.fsync(stream.fileno())
                    if sha.hexdigest() != ticket['sha256']:
                        raise Rejected(422, 'checksum_mismatch')
                    if api.sessions.authenticate(cookie, session['csrf']) is None:
                        raise Rejected(401, 'login_required')
                    api.update(ticket_id, status='forwarding', checksum_verified_bytes=ticket['size'])
                    api.client.upload(stream, ticket['logical_path'], ticket['idempotency_key'])
                    file = api.views.file(ticket['file_id'])
                    api.update(ticket_id, status='protected' if file['protected'] else 'replicating')
                return self._json(200 if file['protected'] else 202, {'file': file, 'transfer_id': ticket_id})
            except BaseException:
                api.update(ticket_id, status='retry_required', error='transfer_unconfirmed')
                raise

    def _download(self, file_id, auth):
        api = self.server.api
        file = api.views.file(file_id)
        if file['size'] > api.cfg['max_upload_bytes']:
            raise Rejected(413, 'browser_download_too_large')
        with api.transfer() as directory:
            if shutil.disk_usage(directory).free < file['size'] + 8 * 1024**2:
                raise Rejected(507, 'insufficient_spool_space')
            with tempfile.TemporaryFile(dir=directory) as stream:
                result = api.client.download(file_id, stream)  # Existing seekable-output SHA + fallback.
                if api.sessions.authenticate(auth[0], auth[2]['csrf']) is None:
                    raise Rejected(401, 'login_required')
                stream.seek(0)
                sha = hashlib.sha256()
                while chunk := stream.read(65536):
                    sha.update(chunk)
                if stream.tell() != file['size'] or sha.hexdigest() != file['sha256']:
                    raise Rejected(422, 'checksum_mismatch')
                stream.seek(0)
                self._headers(200, 'application/octet-stream', file['size'],
                              (('Content-Disposition', 'attachment; filename="ASC-' + file_id + '.bin"'),
                               ('X-ASC-SHA256', file['sha256']), ('X-ASC-Replica-Node', result['node_id'])))
                shutil.copyfileobj(stream, self.wfile, 65536)

    def _route(self):
        api = self.server.api
        cookie_name = getattr(api,'cookie_name',COOKIE)
        if api.mode not in ('single-writer-demo','core-quorum','recovery-read-only'):raise Rejected(503,'unsupported_runtime')
        parsed = urlsplit(self.path)
        if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment or '%' in parsed.path or '\\' in parsed.path or any(p == '..' for p in parsed.path.split('/')):
            raise Rejected(400, 'bad_request')
        self.browser_origin(self.command != 'GET')
        path, method = parsed.path, self.command
        if path == '/api/login' and method == 'POST':
            if self._rate('join', consume=True):
                return
            obj = self.body_json()
            if set(obj) != {'code'}:
                raise Rejected(400, 'bad_request')
            result = api.sessions.login(obj['code'])
            if result is None:
                raise Rejected(401, 'login_rejected')
            cookie, session = result
            return self._json(200, {'authenticated': True, 'csrf': session['csrf'], 'expires_in': SESSION_TTL},
                              (('Set-Cookie', cookie_name + '=' + cookie + '; Secure; HttpOnly; SameSite=Strict; Path=/; Max-Age=' + str(SESSION_TTL)),))
        # Fixed, public, local assets only. No filesystem path is derived from the request.
        assets = ASSETS
        if method == 'GET' and path == '/favicon.ico':
            self._headers(204, 'image/x-icon', 0)
            return
        if method == 'GET' and path in assets:
            name, mime = assets[path]
            target = Path(__file__).parent / 'web' / name
            no_links(target)
            if not target.is_file():
                raise Rejected(404, 'frontend_not_installed')
            raw = target.read_bytes()
            self._headers(200, mime, len(raw)); self.wfile.write(raw)
            return
        if path == '/api/mode' and method == 'GET':
            return self._json(200,{'mode':api.mode,'read_only':api.mode!='single-writer-demo'})
        if path == '/api/session' and method == 'GET':
            authenticated = self.auth(csrf=False)
            if authenticated is None:
                return
            return self._json(200, {'authenticated': True, 'csrf': authenticated[2]['csrf'], 'max_upload_bytes': api.cfg['max_upload_bytes'],'mode':api.mode,'read_only':api.mode!='single-writer-demo'})
        authenticated = self.auth()
        if authenticated is None:
            return
        if path == '/api/logout' and method == 'POST':
            if self.body_json() != {}:
                raise Rejected(400, 'bad_request')
            if api.pairings is not None:api.pairings.forget(authenticated[1])
            api.sessions.logout(authenticated[0])
            return self._json(200, {'authenticated': False},
                              (('Set-Cookie', cookie_name + '=; Secure; HttpOnly; SameSite=Strict; Path=/; Max-Age=0'),))
        if api.mode != 'single-writer-demo':
            if path=='/api/state' and method=='GET':return self._json(200,api.views.state())
            pieces=path.strip('/').split('/')
            if method=='GET' and len(pieces)==3 and pieces[:2]==['api','files']:
                return self._json(200,api.views.file(pieces[2]))
            raise Rejected(403,'read_only_mode')
        if path == '/api/v1/quick-join/pairings' and method == 'POST':
            if self.body_json() != {}:raise Rejected(400,'bad_request')
            return self._json(201,api.pairings.create(authenticated[1],authenticated[2]['expires']))
        if path.startswith('/api/v1/quick-join/pairings/') and method == 'GET':
            pairing_id=path.removeprefix('/api/v1/quick-join/pairings/')
            return self._json(200,api.pairings.status(pairing_id,authenticated[1]))
        if path == '/api/state' and method == 'GET':
            return self._json(200, api.views.state())
        if path == '/api/refresh' and method == 'POST':
            if self.body_json() != {}:
                raise Rejected(400, 'bad_request')
            api.client.request('POST', 'reconcile', {})
            return self._json(200, api.views.state())
        if path == '/api/uploads' and method == 'POST':
            return self._json(200, api.prepare(self.body_json(), authenticated[1]))
        parts = path.strip('/').split('/')
        if len(parts) == 3 and parts[:2] == ['api', 'uploads']:
            if method == 'GET':
                return self._json(200, api.progress(parts[2], authenticated[1]))
            if method == 'PUT':
                return self._upload(parts[2], authenticated)
        if len(parts) == 3 and parts[:2] == ['api', 'files'] and method == 'GET':
            identifier(parts[2])
            return self._json(200, api.views.file(parts[2]))
        if len(parts) == 4 and parts[:2] == ['api', 'files'] and parts[3] == 'content' and method == 'GET':
            identifier(parts[2])
            return self._download(parts[2], authenticated)
        if len(parts) == 3 and parts[:2] == ['api', 'nodes'] and method == 'GET':
            matches = [n for n in api.views.state()['nodes'] if n['node_id'] == parts[2]]
            if matches:
                return self._json(200, {'node': matches[0]})
        raise Rejected(404, 'not_found')

    def _dispatch(self):
        self._response_started = False
        try:
            self._route()
        except (Rejected,PairingError) as exc:
            if not self._response_started:
                self._json(exc.status, {'error': exc.code})
        except ClientError as exc:
            if not self._response_started:
                self._json(exc.status if exc.status in (400, 403, 409, 413, 422, 429, 507) else 503,
                           {'error': 'insufficient_capacity' if exc.status == 507 else ERRORS.get(exc.code, 'core_unavailable')})
        except PayloadTooLarge:
            if not self._response_started:
                self._json(413, {'error': 'metadata_too_large'})
        except (ValueError, KeyError, TypeError, UnicodeError, RecursionError, OverflowError):
            if not self._response_started:
                self._json(400, {'error': 'bad_request'})
        except StorageError as exc:
            if not self._response_started:
                self._json(exc.status if exc.status in (400, 403, 404, 409, 413, 422, 429, 507) else 503,
                           {'error': 'not_found' if exc.status == 404 else 'storage_unavailable'})
        except (OSError, sqlite3.Error):
            if not self._response_started:
                self._json(503, {'error': 'core_unavailable'})

    do_GET = do_POST = do_PUT = _dispatch
