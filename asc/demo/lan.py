"""Restricted single-writer Demo runtime reusing Core TLS, Catalog and Storage engine."""
from contextlib import ExitStack
import os
from pathlib import Path
import ssl
import sqlite3
import subprocess
import sys
import threading
import time
from urllib.parse import urlsplit
from ..catalog.client import ClusterClient
from ..catalog.common import CatalogError
from ..catalog.placement import candidates
from ..catalog.service import CatalogService
from ..client import ClientError, request_json
from ..identity import fingerprint_from_pem
from ..probe import inspect
from .locks import private_lock as foreground_lock
from ..server import Handler, Server
from ..store import Registry
from .installer import guard
from .state import inspect_state, lan_host, lan_origin, read_json


def core_call(home, command):
    # Import-time Core HOME is isolated in a child; never patch globals in running threads.
    env = dict(os.environ, ASC_HOME=str(home), PYTHONDONTWRITEBYTECODE='1')
    result = subprocess.run([sys.executable, '-B', '-m', 'asc.cli', *command], env=env,
                            cwd=Path(__file__).resolve().parents[2])
    if result.returncode:
        raise ValueError('Core operation refused; identity retained')


def owner(root):
    marker = inspect_state(root)
    if marker['role'] != 'controller':
        raise ValueError('owner credential remains on Controller')
    home = Path(root) / 'controller'
    cfg = read_json(home / 'controller.json')
    if cfg['listen_port'] != marker['port']:
        raise ValueError('Controller port mismatch')
    return ClusterClient(f"https://{marker['host']}:{marker['port']}",
                         fingerprint_from_pem(home / 'server.crt'), cfg['admin_token'])


def lifecycle_request(client, method, path, value=None):
    return request_json(client.origin, client.pin, method, '/api/v1/' + path, value, client.token)


class DemoCatalog(CatalogService):
    def register(self, node_id, endpoint, pin, device_id, volume_ids, metadata_allowed=True, storage_allowed=True):
        if storage_allowed:
            lan_origin(endpoint)
        return super().register(node_id, endpoint, pin, device_id, volume_ids, metadata_allowed, storage_allowed)

    def upload_plan(self, obj):
        if obj.get('policy') != 'replicated_2':
            raise CatalogError('invalid_policy', 400)
        self.refresh()
        with self.registry.connect() as db:
            existing = db.execute('SELECT 1 FROM catalog_files WHERE upload_key=?', (obj.get('idempotency_key'),)).fetchone()
            if not existing:
                size = obj.get('size')
                if type(size) is not int or size < 0:
                    raise CatalogError('invalid_content', 400)
                if len({r['device_id'] for r in candidates(db, size)}) < 2:
                    raise CatalogError('no_eligible_storage', 507)
        return super().upload_plan(obj)


class DemoHandler(Handler):
    """Do not expose policy changes, whole-volume grants, Core extensions or deletion."""
    def allowed(self):
        path = urlsplit(self.path).path
        parts = path.strip('/').split('/')
        if self.command == 'GET':
            return (path in ('/api/v1/info', '/api/v1/nodes') or path.startswith('/api/v1/nodes/')
                    or parts[:2] == ['catalog', 'v1'] and (parts[2:] in (['files'], ['jobs'], ['nodes'], ['metadata', 'status'], ['metadata', 'snapshot'], ['metadata', 'changes'])
                        or len(parts) == 4 and parts[2] in ('files', 'jobs')
                        or len(parts) == 5 and parts[2] == 'files' and parts[4] == 'replicas'))
        if path in ('/api/v1/join', '/api/v1/heartbeat', '/api/v1/storage/authorize',
                    '/api/v1/admin/pair', '/api/v1/admin/rename', '/api/v1/admin/revoke'):
            return True
        if parts[:2] != ['catalog', 'v1']:
            return False
        tail = parts[2:]
        return (tail in (['nodes', 'register'], ['uploads'], ['metadata', 'ack'], ['reconcile'], ['jobs', 'run'])
                or len(tail) == 3 and (tail[0] == 'uploads' and tail[2] == 'complete'
                    or tail[0] == 'files' and tail[2] == 'download'
                    or tail[0] == 'jobs' and tail[2] == 'retry'))

    def do_GET(self):
        if not self.allowed():
            return self._json(404, {'error': 'not_found'})
        return super().do_GET()

    def do_POST(self):
        if not self.allowed():
            return self._json(404, {'error': 'not_found'})
        return super().do_POST()


class ControllerRuntime:
    def __init__(self, root):
        self.root = Path(root)

    def __enter__(self):
        guard()
        self.stack = ExitStack()
        try:
            with foreground_lock(self.root, 'demo-operation'):
                marker = inspect_state(self.root)
                if os.environ.get('ASC_DEMO_PREFIX'):
                    from .upgrade import startup_check
                    startup_check(os.environ['ASC_DEMO_PREFIX'], self.root)
                if marker['role'] != 'controller':
                    raise ValueError('not a Controller')
                home = self.root / 'controller'
                self.stack.enter_context(foreground_lock(home, 'controller'))
                cfg = read_json(home / 'controller.json')
                if cfg['listen_port'] != marker['port']:
                    raise ValueError('Controller port mismatch')
                self.registry = Registry(home / 'registry.sqlite3')
                if self.registry.consensus_enabled():
                    raise ValueError('no single-writer fallback for Raft')
                self.registry.update_self(inspect())
                self.service = DemoCatalog(self.registry).start(background=True)
                self.stack.callback(self.service.close)
                self.server = Server((lan_host(marker['host']), marker['port']), self.registry,
                                     cfg['admin_token'], handler=DemoHandler, catalog=self.service)
                self.stack.callback(self.server.server_close)
                self.server.daemon_threads = False
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                context.minimum_version = ssl.TLSVersion.TLSv1_2
                context.load_cert_chain(home / 'server.crt', home / 'server.key')
                self.server.tls_context = context
                self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
                self.thread.start()
                self.stack.callback(self.thread.join)
                self.stack.callback(self.server.shutdown)
                profile_stop = threading.Event()
                def refresh_profile():
                    while not profile_stop.wait(30):
                        try:
                            self.registry.update_self(inspect())
                        except (OSError, ValueError, sqlite3.Error):
                            pass
                profile_thread = threading.Thread(target=refresh_profile, daemon=True)
                profile_thread.start()
                self.stack.callback(profile_thread.join)
                self.stack.callback(profile_stop.set)
            return self
        except BaseException:
            self.stack.close()
            raise

    def __exit__(self, *_):
        self.stack.close()


def run_node(root, interval=10, once=False):
    guard()
    root = Path(root)
    if not 5 <= interval <= 3600:
        raise ValueError('invalid heartbeat interval')
    # Own child process, Core HOME was set BEFORE import (see cli run-node dispatch).
    from .. import cli as core
    if core.HOME != root / 'node':
        raise ValueError('node process private HOME mismatch')
    from ..storage.runtime import StorageRuntime, load_config
    with ExitStack() as stack:
        with foreground_lock(root, 'demo-operation'):
            inspect_state(root)
            if os.environ.get('ASC_DEMO_PREFIX'):
                from .upgrade import startup_check
                startup_check(os.environ['ASC_DEMO_PREFIX'], root)
            home = root / 'node'
            if (home / 'enrollment_pending.json').exists():
                raise ValueError('complete enrollment first')
            stack.enter_context(foreground_lock(home, 'agent'))
            cfg = read_json(home / 'node.json')
            lan_origin(cfg['controller'])
            lan_host(load_config(home)['host'])
            runtime = stack.enter_context(StorageRuntime(home, cfg))
            if runtime.server.gc_executors:
                raise ValueError('physical GC must remain locked')
        print('Demo node foreground; Ctrl+C stops safely. Controller outage grants no writes.', flush=True)
        while True:
            try:
                core.agent_once(cfg, storage_engine=runtime.engine)
                print('Heartbeat OK', flush=True)
            except (ClientError, OSError, ValueError):
                if once:
                    raise
                print('Heartbeat unavailable; state retained; no Controller promotion.', flush=True)
            if once:
                break
            time.sleep(interval)


def upload(client, source, logical_path, key, wait=120):
    if not 1 <= wait <= 900:
        raise ValueError('invalid bounded replication wait')
    with Path(source).open('rb') as stream:
        reply = client.upload(stream, logical_path, key)
    file_id = reply['file']['file']['file_id']
    deadline = time.monotonic() + wait
    while True:
        entry = client.request('GET', 'files/' + file_id)
        if entry['verified_replicas'] >= 2 and entry['available_replicas'] >= 2:
            return {'protected': True, 'file': entry, 'android_qualified': False}
        if time.monotonic() >= deadline:
            return {'protected': False, 'file': entry, 'retry_same_key': True,
                    'reason': 'replication incomplete; bytes/jobs retained'}
        time.sleep(0.5)
