"""Quorum-gated Controller lifecycle and prepared SQL transactions."""
import base64
from contextlib import contextmanager, closing
import hashlib
import hmac
import json
from pathlib import Path
import sqlite3
import threading

from . import state as projection
from ..catalog.common import CatalogError, canonical, digest, key, uid
from ..consensus.client import Client
from ..store import Registry, _digest
from ..catalog import grants
from .. import validation as valid


class Runtime:
    def __init__(self, config, cache):
        self.client = Client.from_config(config)
        cfg = json.loads(Path(config).read_bytes())
        self.node_id, self.cluster, self.epoch = cfg['node_id'], cfg['cluster_id'], cfg['epoch']
        self.path = Path(cache)
        if not self.path.is_absolute() or any((p/'.git').exists() for p in self.path.parents):
            raise ValueError('runtime cache must be private and outside source')
        self.lock = threading.RLock()
        self.local = threading.local()
        self.mode, self.term = 'Recovery', None
        self.fatal = False
        self.cache_schema = None
        self.stop = threading.Event()
        self.heartbeat = None
        self.worker = None
        self.registry = RuntimeRegistry(self)

    def start(self):
        self.client.request('POST', '/v1/runtime/heartbeat', {})
        self.heartbeat = threading.Thread(target=self._heartbeat, daemon=True)
        self.heartbeat.start()
        return self

    def _heartbeat(self):
        while not self.stop.wait(1):
            if self.fatal or self.worker is not None and not self.worker.is_alive():
                self.mode, self.term = 'Recovery', None
                continue  # Withdraw unhealthy Python through the armed watchdog.
            try:
                self.client.request('POST', '/v1/runtime/heartbeat', {})
            except CatalogError:
                self.mode, self.term = 'Recovery', None

    def close(self):
        self.stop.set()
        if self.heartbeat:
            self.heartbeat.join(timeout=20)

    def _cached(self):
        if not self.path.exists():
            return None
        with closing(sqlite3.connect(self.path, timeout=15)) as db:
            self.cache_schema = db.execute('PRAGMA user_version').fetchone()[0]
            if self.cache_schema not in (0, 1):
                raise CatalogError('runtime_cache_quarantined', 409)
            row = db.execute('SELECT data,sha256 FROM projection WHERE singleton=1').fetchone()
        if row is None or hashlib.sha256(row[0]).hexdigest() != row[1]:
            raise CatalogError('runtime_cache_quarantined', 409)
        result = json.loads(row[0]); projection.validate(result['document'])
        return result

    def view(self, strong=False):
        with self.lock:
            try:
                cached = self._cached()
            except (CatalogError, sqlite3.Error, ValueError, TypeError, KeyError):
                self.fatal = True
                raise CatalogError('runtime_cache_quarantined', 409) from None
            try:
                result = self.client.state(strong)
            except CatalogError:
                if strong or cached is None:
                    raise
                return {**cached, 'stale': True, 'read_only': True}
            try:
                state = result['state']; raw = base64.b64decode(state['document'], validate=True)
                if cached and state['index'] < cached['state']['index']:
                    if not strong:
                        return {**cached, 'stale': True, 'read_only': True}
                    raise CatalogError('runtime_recovering', 503)
                doc = projection.validate(json.loads(raw))
                if (canonical(doc) != raw or hashlib.sha256(raw).hexdigest() != state['document_sha256'] or
                        (state['cluster_id'], state['epoch']) != (self.cluster, self.epoch) or
                        (doc['cluster_id'], doc['epoch']) != (self.cluster, self.epoch) or
                        type(state['index']) is not int or state['index'] < 0):
                    raise ValueError()
            except (ValueError, TypeError, KeyError):
                raise CatalogError('invalid_runtime_state', 409) from None
            current = {'state': state, 'document': doc}
            if cached:
                old = cached['state']
                if (state['index'] < old['index']):
                    if not strong:
                        return {**cached, 'stale': True, 'read_only': True}
                    raise CatalogError('runtime_recovering', 503)
                if (doc['revision'] < cached['document']['revision'] or
                        state['term'] < old['term'] or
                        state['index'] == old['index'] and state['document_sha256'] != old['document_sha256']):
                    raise CatalogError('runtime_cache_quarantined', 409)
            if cached != current or self.cache_schema != 1:
                data = canonical(current)
                with closing(sqlite3.connect(self.path, timeout=15)) as db, db:
                    db.execute('PRAGMA synchronous=FULL')
                    db.execute('CREATE TABLE IF NOT EXISTS projection(singleton INTEGER PRIMARY KEY CHECK(singleton=1),data BLOB NOT NULL,sha256 TEXT NOT NULL)')
                    db.execute('INSERT OR REPLACE INTO projection VALUES(1,?,?)', (data, hashlib.sha256(data).hexdigest()))
                    # Keep ordinary Registry.initialize from interpreting this
                    # separate cache as an empty legacy authority database.
                    db.execute('PRAGMA user_version=1')
                    self.cache_schema = 1
            return {**current, 'stale': not strong, 'read_only': True}

    def commit(self, view, document, request_id=None, intent=None):
        from ..replication.state import transition
        transition(view['document'], document)
        request_id = request_id or uid()
        key(request_id); projection.validate(document)
        receipt = self.client.submit({'schema': 1, 'cluster_id': self.cluster, 'epoch': self.epoch,
            'request_id': request_id, 'intent_sha256': intent or digest(document),
            'expected_sha256': view['state']['document_sha256'],
            'authority_term': document['authority']['term'],
            'document': base64.b64encode(canonical(document)).decode()})
        # ApplyFuture has already established quorum commit and FSM application.
        # Verify its exact receipt locally; a second Barrier adds no authority.
        applied = self.view()
        if applied['state']['receipts'].get(request_id) != receipt:
            raise CatalogError('runtime_recovering', 503)
        return receipt

    def ensure_ready(self):
        with self.lock:
            if self.fatal:
                raise CatalogError('runtime_cache_quarantined', 409)
            try:
                status = self.client.status()
                if status['role'] != 'Leader' or status['quarantined']:
                    self.mode, self.term = 'Follower', None
                    raise CatalogError('controller_not_ready', 503)
                term = int(status['term'])
                view = self.view(strong=True)
                if view['document']['authority'] != {'node_id': self.node_id, 'term': term}:
                    self.mode, self.term = 'Recovery', None
                    self.commit(view, projection.takeover(view['document'], self.node_id, term))
                    view = self.view(strong=True)
                # Never report ready from only a cached role or document.
                status = self.client.status()
                if status['role'] != 'Leader' or int(status['term']) != term:
                    raise CatalogError('controller_not_ready', 503)
                self.mode, self.term = 'Leader', term
                return view
            except CatalogError:
                self.term = None
                if self.mode == 'Leader':
                    self.mode = 'Recovery'
                raise

    @contextmanager
    def operation(self):
        previous = getattr(self.local, 'term', None)
        view = self.ensure_ready()
        term = view['document']['authority']['term']
        if previous is not None and previous != term:
            raise CatalogError('stale_authority', 409)
        self.local.term = term
        try:
            yield view
        finally:
            self.local.term = previous


class RuntimeRegistry(Registry):
    """Run old transaction preparation on disposable SQL; only Go commits authority.

    No guarded/live registry connection is writable. Returning from a mutating
    context establishes majority commit, so callers cannot launch IO beforehand.
    """
    def __init__(self, runtime):
        self.runtime = runtime
        self.path = runtime.path

    def consensus_enabled(self):
        # This facade is a preparation workspace, not the guarded original DB.
        return False

    @contextmanager
    def connect(self):
        runtime = self.runtime
        with runtime.lock:
            active_term = getattr(runtime.local, 'term', None)
            if active_term is None:
                view = runtime.ensure_ready()
            else:
                view = runtime.view()
                status = runtime.client.status()
                if (status['role'] != 'Leader' or int(status['term']) != active_term or
                        view['document']['authority'] != {'node_id': runtime.node_id, 'term': active_term}):
                    raise CatalogError('stale_authority', 409)
            term = view['document']['authority']['term']
            if getattr(runtime.local, 'term', term) not in (None, term):
                raise CatalogError('stale_authority', 409)
            reg = projection.prepare_registry(view['document'])
            try:
                yield reg.db
                reg.db.commit()
                prepared = projection.export(reg.db, view['document']['revision'], view['document']['authority'])
                if prepared != view['document']:
                    prepared['revision'] += 1
                    runtime.commit(view, prepared)
            finally:
                reg.db.close()

    def initialize(self, cluster):
        raise CatalogError('runtime_initialization_refused', 409)

    def storage_grant(self, *args, **kwargs):
        raise CatalogError('file_scoped_authority_required', 403)

    def seed_self(self, *args, **kwargs):
        raise CatalogError('runtime_initialization_refused', 409)

    update_self = seed_self

    def snapshot(self):
        result = super().snapshot()
        result['consensus_status'] = 'RAFT_CONTROLLER_RUNTIME'
        result['automatic_failover'] = True
        return result

    def join(self, code, name, profile, enrollment_id=None, enrollment_token=None, node_id=None):
        if enrollment_id is None or enrollment_token is None:
            raise CatalogError('retry_safe_enrollment_required', 409)
        return super().join(code, name, profile, enrollment_id, enrollment_token, node_id)

    def storage_authorize(self, node_id, node_token, grant, volume_id, operation, scope=None, nonce=None):
        valid.secret(node_token); valid.secret(grant); key(nonce)
        runtime = self.runtime
        if operation == 'gc':
            authorizer = getattr(runtime, 'gc_authorizer', None)
            if authorizer is None:
                raise CatalogError('physical_gc_locked', 403)
            return authorizer.authorize(node_id, node_token, grant, volume_id, scope, nonce)
        with runtime.operation(), runtime.lock:
            view = runtime.view()
            if view['document']['authority'] != {'node_id': runtime.node_id, 'term': runtime.local.term}:
                raise CatalogError('stale_authority', 409)
            reg = projection.prepare_registry(view['document'])
            try:
                node = reg.db.execute('SELECT * FROM nodes WHERE node_id=?', (node_id,)).fetchone()
                if (not node or node['state'] != 'active' or json.loads(node['profile']).get('protected') is True or
                        not hmac.compare_digest(node['token_hash'], _digest(node_token))):
                    return None
                reply = grants.authorize(reg.db, node, _digest(grant), volume_id, operation, scope)
                if reply is None:
                    return None
            finally:
                reg.db.close()
            # A fresh authenticated request commits a no-op receipt in the actual
            # activation term. No raw credentials are persisted in this evidence.
            intent = digest({'node_id': node_id, 'grant_sha256': _digest(grant), 'volume_id': volume_id,
                             'operation': operation, 'scope': scope, 'nonce': nonce})
            receipt = runtime.commit(view, view['document'], 'authorize-'+nonce, intent)
            return {**reply, 'authority': {'cluster_id': runtime.cluster, 'epoch': runtime.epoch,
                    'term': receipt['term'], 'index': receipt['index'], 'nonce': nonce,
                    'intent_sha256': intent}}
