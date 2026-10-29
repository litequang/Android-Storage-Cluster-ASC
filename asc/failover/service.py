"""Leader-only existing Catalog worker and explicit stale read/lifecycle API."""
import hashlib
import hmac
import json
import sqlite3
import threading
import time
from urllib.parse import urlsplit, parse_qs

from ..catalog.common import CatalogError
from ..catalog.service import CatalogService
from ..catalog.metadata import FILE_FIELDS
from ..catalog.placement import active_nodes, readable
from ..client import ClientError
from ..runtime import foreground_lock
from ..server import Handler, PayloadTooLarge
from .. import validation as valid


class Service(CatalogService):
    failover = True

    def __init__(self, runtime, rate=4*1024**2, timeout=300):
        self.runtime = runtime
        self._refresh_lock = threading.Lock()
        self._refreshed = None
        super().__init__(runtime.registry, rate, timeout)
        from ..backup.service import Backups
        self.backups = Backups(self)
        from ..nodes.service import Insights
        self.insights = Insights(self)
        from ..replication.service import Replication
        self.replication = Replication(self)
        self.gc_test_context = None
        from ..replication.gc import GarbageCollection
        self.gc = GarbageCollection(self.replication)
        runtime.gc_authorizer = self.gc
        from ..backup.catalog import VersionedCatalog
        self.catalog = VersionedCatalog(runtime.registry)
        self.queue.catalog = self.catalog

    def refresh(self):
        # Coalesce worker/owner probes within the same activation. A takeover
        # changes term and invalidates replicated probe freshness independently.
        with self._refresh_lock:
            term = getattr(self.runtime.local, 'term', None)
            if self._refreshed and self._refreshed[0] == term and time.monotonic()-self._refreshed[1] < 10:
                return
            super().refresh()
            self.insights.capture()
            self._refreshed = (term, time.monotonic())

    def status(self):
        result = super().status()
        view = self.runtime.view()
        return {**result, 'writer': self.runtime.node_id, 'raft_enabled': True,
                'automatic_failover': True, 'applied_index': view['state']['index'],
                'term': view['document']['authority']['term']}

    def _bad_replica(self, replica, exc):
        # Failed permission/quorum is not evidence of missing/corrupt bytes.
        if (getattr(exc, 'status', None) in (401, 403, 429) or
                getattr(exc, 'code', None) in {'authorization_unavailable', 'stale_authority',
                    'controller_not_ready', 'quorum_read_unavailable', 'commit_unconfirmed'}):
            return
        return super()._bad_replica(replica, exc)

    def upload_plan(self, obj):
        view = self.runtime.view()
        backup = view['document'].get('backup')
        if backup:
            files = {f['file_id']: f for f in view['document']['catalog']['files']}
            for job_id, job in backup['jobs'].items():
                if (job['kind'] == 'RESTORE' and files[job['source_file_id']]['logical_path'] == obj['logical_path'] and
                        job['target_version'] == obj.get('version', 1) and obj['idempotency_key'] != 'restore-'+job_id):
                    raise CatalogError('restore_version_reserved', 409)
        return super().upload_plan(obj)

    def download_plan(self, file_id):
        from ..backup.state import status
        backup = self.runtime.view()['document'].get('backup')
        if backup and status(backup, file_id) != 'LIVE':
            raise CatalogError('version_not_live', 409)
        self.refresh()
        entry = self.catalog.file(file_id)
        with self.registry.connect() as db:
            nodes = {n['node_id']: n for n in active_nodes(db)}
        checked = 0
        for replica in entry['replicas']:
            node = nodes.get(replica['node_id'])
            if replica['state'] != 'UNAVAILABLE' or not node or not readable(node, replica['volume_id']) or checked >= 3:
                continue
            checked += 1
            try:
                audit = self._client(replica['node_id'], replica['volume_id'], 'audit', replica['local_file_id'])
                self._proof(audit, replica['local_file_id'], replica['volume_id'],
                    '_asc-global/'+file_id+'/'+replica['replica_id'], entry['file'])
                self.catalog.mutate('REVERIFY', {'replica_id': replica['replica_id'], 'physically_verified': True})
            except (ClientError, CatalogError, OSError, ValueError) as exc:
                self._bad_replica(replica, exc)
        return super().download_plan(file_id)

    def start(self, background=True):
        owner = foreground_lock(self.registry.path.parent, 'catalog-worker')
        owner.__enter__(); self._owner = owner
        if background:
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()
            self.runtime.worker = self._thread
        return self

    def _loop(self):
        last_reconcile = 0
        while not self._stop.is_set():
            try:
                with self.runtime.operation():
                    # Takeover has already durably fenced leases and grants.
                    # Pending/recovered work takes priority over background
                    # audits; a multi-replica audit must not starve owner ACKs.
                    job = self.run_one()
                    self.backups.tick()
                    self.replication.tick()
                    if job is None and time.monotonic()-last_reconcile >= 30:
                        self.reconcile(); last_reconcile = time.monotonic()
            except (CatalogError, ClientError, sqlite3.Error, OSError, ValueError):
                pass
            self._stop.wait(1)

    def reconcile(self, max_verify=1):
        return super().reconcile(max_verify=max_verify)


class RuntimeHandler(Handler):
    def _json(self, status, data):
        runtime = self.server.catalog.runtime
        # MetadataSource already owns a versioned, digest-bound envelope. Adding
        # fields or replacing its revision would invalidate every node import.
        metadata_envelope = urlsplit(getattr(self, 'path', '')).path in (
            '/catalog/v1/metadata/snapshot', '/catalog/v1/metadata/changes')
        if status < 300 and getattr(runtime.local, 'term', None) is not None and not metadata_envelope:
            view = runtime.view()
            data = {**data, 'cluster_id': runtime.cluster, 'epoch': runtime.epoch,
                    'revision': view['document']['catalog']['revision'],
                    'control_revision': view['document']['revision'], 'applied_index': view['state']['index'],
                    'term': view['document']['authority']['term'], 'stale': False,
                    'read_only': self.command == 'GET'}
            if data.get('mode') == 'single-writer-development':
                data['mode'] = 'distributed-runtime-development'
        return super()._json(status, data)

    def _discovery_auth(self, view):
        if self._rate('auth'):
            return False
        token_hash = hashlib.sha256(self._bearer().encode()).hexdigest()
        allowed = hmac.compare_digest(token_hash, self.server.admin_hash) or any(
            n['state'] == 'active' and hmac.compare_digest(token_hash, n['token_hash'])
            for n in view['document']['tables']['nodes'])
        if not allowed:
            self.server.limiter.blocked('auth', self.client_address[0], consume=True)
            self._json(401, {'error': 'unauthorized'})
        return allowed

    def _runtime_dispatch(self):
        runtime = self.server.catalog.runtime
        parsed = urlsplit(self.path)
        try:
            from ..observability.http import handle as observe_handle
            if observe_handle(self, parsed):
                return
            from ..external.http import handle as external_handle
            if external_handle(self, parsed):
                return
            if self.command == 'GET' and parsed.path == '/cluster/v1/leader':
                if parsed.query or parsed.fragment:
                    raise ValueError()
                view = runtime.view()
                if not self._discovery_auth(view):
                    return
                ready = False
                try:
                    runtime.ensure_ready(); ready = True
                except CatalogError:
                    pass
                return self._json(200, {'cluster_id': runtime.cluster, 'node_id': runtime.node_id,
                    'mode': runtime.mode, 'write_ready': ready, 'term': runtime.term,
                    'automatic_failover': True})
            if self.command == 'GET' and parsed.path == '/api/v1/info':
                try:
                    routing_hint = runtime.client.status()['role'] == 'Leader'
                except CatalogError:
                    routing_hint = False
                return self._json(200, {'cluster_id': runtime.cluster, 'mode': 'distributed-runtime-development',
                    'node_id': runtime.node_id, 'leader_hint': routing_hint, 'routing_hint_only': True,
                    'raft_enabled': True, 'automatic_failover': True, 'file_storage_enabled': True,
                    'global_file_catalog_enabled': True, 'schema_version': 4,
                    'features': ['controller-failover-v1', 'node-lifecycle-v1', 'retry-safe-enrollment-v1',
                                 'global-catalog-v1', 'metadata-replication-v1', 'file-scoped-transfers-v1',
                                 'backup-versioning-v1', 'node-insights-v1', 'replica-reduction-preview-v1']})
            if (self.command == 'GET' and parsed.path.startswith('/catalog/v1/files/') and
                    parsed.path.endswith('/reduction-preview')):
                query = parse_qs(parsed.query, strict_parsing=True)
                parts = parsed.path.split('/')
                if (len(parts) != 6 or set(query)-{'consistency'} or parsed.fragment or
                        any(len(v) != 1 for v in query.values()) or
                        query.get('consistency', ['local'])[0] not in ('local','strong')):
                    raise ValueError()
                if not self._admin(): return
                from ..nodes.reduction import preview
                from ..catalog.common import now
                view = runtime.view(strong=query.get('consistency') == ['strong'])
                return self._json(200, preview(view, parts[4], now()))
            if self.command == 'GET' and (parsed.path == '/catalog/v1/nodes/scores' or
                    parsed.path.startswith('/catalog/v1/nodes/') and parsed.path.endswith('/history')):
                query = parse_qs(parsed.query, strict_parsing=True)
                if (set(query) - {'consistency', 'window'} or parsed.fragment or
                        any(len(v) != 1 for v in query.values()) or
                        query.get('consistency', ['local'])[0] not in ('local', 'strong')):
                    raise ValueError()
                if not self._admin():
                    return
                from ..nodes.view import scores
                from ..catalog.common import now
                view = runtime.view(strong=query.get('consistency') == ['strong'])
                result = scores(view, now())
                if parsed.path.endswith('/history'):
                    from ..nodes.history import summary, empty, WINDOWS
                    parts = parsed.path.split('/')
                    window = query.get('window', ['24h'])[0]
                    if len(parts) != 6 or window not in WINDOWS:
                        raise ValueError()
                    node_id = valid.node_id(parts[4])
                    if node_id not in {n['node_id'] for n in view['document']['tables']['nodes']}:
                        raise CatalogError('node_not_found', 404)
                    result = {k:v for k,v in result.items() if k != 'nodes'}
                    result.update(node_id=node_id, **summary(view['document'].get('insights', empty()), node_id, window, now()))
                elif 'window' in query:
                    raise ValueError()
                return self._json(200, result)
            if self.command == 'GET' and parsed.path.startswith('/catalog/v1/'):
                query = parse_qs(parsed.query, strict_parsing=True)
                if any(len(v) != 1 for v in query.values()) or parsed.fragment:
                    raise ValueError()
                consistency = query.get('consistency', ['local'])[0]
                if consistency not in ('local', 'strong'):
                    raise ValueError()
                parts = parsed.path.removeprefix('/catalog/v1/').split('/')
                if consistency == 'local' and (parts == ['files'] or len(parts) == 2 and parts[0] == 'files' or
                                                parts == ['metadata', 'status']):
                    if set(query) - {'consistency'}:
                        raise ValueError()
                    if not self._admin():
                        return
                    view = runtime.view(); doc = view['document']['catalog']
                    common = {'cluster_id': runtime.cluster, 'epoch': runtime.epoch,
                        'revision': doc['revision'], 'control_revision': view['document']['revision'],
                        'applied_index': view['state']['index'], 'stale': True, 'read_only': True,
                        'automatic_failover': True, 'available_replicas': None, 'availability': 'UNKNOWN'}
                    if parts == ['metadata', 'status']:
                        return self._json(200, {**common, 'mode': runtime.mode})
                    def public(f):
                        return {'file': {k: f[k] for k in FILE_FIELDS}, 'replicas': [r for r in doc['replicas']
                            if r['file_id'] == f['file_id']], **common}
                    backup = view['document'].get('backup')
                    if backup:
                        from ..backup.state import heads, status
                        original_public = public
                        def public(f):
                            return {**original_public(f), 'version_state': status(backup, f['file_id'])}
                    if parts == ['files']:
                        visible = doc['files']
                        if backup:
                            visible = [f for f in heads(doc) if status(backup, f['file_id']) == 'LIVE']
                        return self._json(200, {'files': [public(f) for f in visible], **common})
                    file = next((f for f in doc['files'] if f['file_id'] == parts[1]), None)
                    if file is None:
                        raise CatalogError('file_not_found', 404)
                    return self._json(200, public(file))
                # Existing route parser has no consistency parameter. Strong
                # reads below enter the same quorum/term gate as mutations.
                if 'consistency' in query:
                    if set(query) != {'consistency'}:
                        raise ValueError()
                    self.path = parsed.path
            if self.command == 'POST' and parsed.path == '/api/v1/storage/authorize':
                if parsed.query or parsed.fragment:
                    raise ValueError()
                if self._rate('auth'):
                    return
                obj = self._read_json()
                valid.payload(obj, ('node_id', 'grant', 'volume_id', 'operation', 'scope', 'nonce'))
                reply = runtime.registry.storage_authorize(obj['node_id'], self._bearer(), obj['grant'],
                    obj['volume_id'], obj['operation'], obj['scope'], obj['nonce'])
                if reply is None:
                    self.server.limiter.blocked('auth', self.client_address[0], consume=True)
                    return self._json(403, {'error': 'unauthorized'})
                return self._json(200, reply)
            with runtime.operation():
                return super().do_GET() if self.command == 'GET' else super().do_POST()
        except CatalogError as exc:
            return self._json(exc.status, {'error': exc.code})
        except PayloadTooLarge:
            return self._json(413, {'error': 'payload_too_large'})
        except (ValueError, KeyError, TypeError, UnicodeError, RecursionError, OverflowError):
            return self._json(400, {'error': 'bad_request'})
        except (sqlite3.Error, OSError):
            return self._json(503, {'error': 'runtime_unavailable'})

    do_GET = do_POST = _runtime_dispatch
