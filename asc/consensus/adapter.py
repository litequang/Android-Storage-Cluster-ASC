"""Transactional projection/checkpoint/receipt installation, with durable writer fencing."""
import base64
from contextlib import closing
import hashlib
import json
import sqlite3
import threading

from .client import Client
from .projection import PRIMARY, TABLES, export, prepare, validate
from ..catalog.common import CatalogError, canonical, digest, key, now, uid


def enabled(db):
    row = db.execute("SELECT value FROM settings WHERE key='consensus_mode'").fetchone()
    return row is not None and row[0] == 'metadata-v1'


def writer(db):
    db.create_function('asc_consensus_apply', 0, lambda: 1)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA synchronous=FULL')
    db.execute('BEGIN IMMEDIATE')


def import_seed(registry, raw):
    """Explicit new-voter metadata import only; never overwrite an existing history."""
    doc = validate(json.loads(raw))
    if canonical(doc) != raw:
        raise CatalogError('noncanonical_consensus_seed', 409)
    with registry.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        current = export(db)
        if (enabled(db) or current['cluster_id'] != doc['cluster_id'] or current['revision'] or
                current['files'] or current['replicas'] or db.execute('SELECT COUNT(*) FROM catalog_jobs').fetchone()[0]):
            raise CatalogError('consensus_import_refused', 409)
        db.execute('UPDATE catalog_state SET epoch=?,revision=?,head_digest=? WHERE singleton=1',
                   (doc['epoch'], doc['revision'], doc['head_digest']))
        for field, table in TABLES.items():
            for row in doc[field]:
                row = dict(row)
                if field == 'events':
                    row['payload'] = canonical(row['payload']).decode()
                db.execute(f"INSERT INTO {table}({','.join(row)}) VALUES({','.join('?' for _ in row)})", tuple(row.values()))


class Adapter:
    def __init__(self, registry, client):
        self.registry, self.client = registry, client
        self.lock = threading.RLock()
        self.fault_hook = None  # Test-only crash boundaries, never remotely configurable.

    def _fault(self, point):
        if self.fault_hook:
            self.fault_hook(point)

    def activate(self):
        result = self.client.state()
        state, doc, raw = self._decode(result)
        with self.lock, closing(sqlite3.connect(self.registry.path, timeout=15)) as db, db:
            writer(db)
            if enabled(db):
                row = db.execute('SELECT cluster_id,epoch FROM consensus_checkpoint WHERE singleton=1').fetchone()
                if row is None or (row['cluster_id'], row['epoch']) != (state['cluster_id'], state['epoch']):
                    raise CatalogError('consensus_identity_mismatch', 409)
                tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
                expected = {f'consensus_guard_{table}_{action}' for table in tables for action in ('INSERT', 'UPDATE', 'DELETE')}
                actual = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE 'consensus_guard_%'")}
                if expected != actual:
                    raise CatalogError('consensus_guards_missing', 409)
                return self
            # Explicit attachment requires an EXACT stopped-state metadata import.
            # Independently initialized epochs cannot silently become one history.
            if canonical(export(db)) != raw:
                raise CatalogError('consensus_seed_mismatch', 409)
            db.execute('''CREATE TABLE consensus_checkpoint(singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                schema INTEGER NOT NULL,cluster_id TEXT NOT NULL,epoch TEXT NOT NULL,
                applied_index INTEGER NOT NULL,applied_term INTEGER NOT NULL,document_sha256 TEXT NOT NULL)''')
            db.execute('CREATE TABLE consensus_receipts(request_id TEXT PRIMARY KEY,data TEXT NOT NULL)')
            db.execute("INSERT INTO settings VALUES('consensus_mode','metadata-v1')")
            db.execute('INSERT INTO consensus_checkpoint VALUES(1,1,?,?,?,?,?)',
                       (state['cluster_id'], state['epoch'], state['index'], state['term'], state['document_sha256']))
            for request_id, receipt in state['receipts'].items():
                db.execute('INSERT INTO consensus_receipts VALUES(?,?)', (request_id, canonical(receipt).decode()))
            tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
            for table in tables:
                if not table.replace('_', '').isalnum():
                    raise CatalogError('unsupported_registry_table', 409)
                for action in ('INSERT', 'UPDATE', 'DELETE'):
                    db.execute(f'''CREATE TRIGGER consensus_guard_{table}_{action} BEFORE {action} ON {table}
                        WHEN asc_consensus_apply()!=1 BEGIN SELECT RAISE(ABORT,'consensus_required'); END''')
        return self

    @staticmethod
    def _decode(result):
        try:
            state = result['state']; raw = base64.b64decode(state['document'], validate=True)
            if (state['schema'] != 1 or len(raw) > 2*1024**2 or hashlib.sha256(raw).hexdigest() != state['document_sha256'] or
                    type(state['index']) is not int or not 0 <= state['index'] < 2**63 or
                    type(state['term']) is not int or not 0 <= state['term'] < 2**63 or
                    not isinstance(state['receipts'], dict) or len(state['receipts']) > 4096):
                raise ValueError()
            doc = validate(json.loads(raw))
            if (doc['cluster_id'], doc['epoch']) != (state['cluster_id'], state['epoch']) or canonical(doc) != raw:
                raise ValueError()
            for request_id, receipt in state['receipts'].items():
                key(request_id)
                if (not 0 < receipt['index'] <= state['index'] or not 0 < receipt['term'] <= state['term'] or
                        len(receipt['command_sha256']) != 64 or len(receipt['document_sha256']) != 64 or
                        len(receipt['intent_sha256']) != 64):
                    raise ValueError()
            return state, doc, raw
        except (ValueError, TypeError, KeyError, OverflowError):
            raise CatalogError('invalid_consensus_state', 409) from None

    def sync(self, strong=False):
        with self.lock:
            result = self.client.state(strong=strong)
            state, doc, raw = self._decode(result)
            self._fault('committed_before_python_apply')
            changed = False
            with closing(sqlite3.connect(self.registry.path, timeout=15)) as db, db:
                writer(db)
                saved = db.execute('SELECT * FROM consensus_checkpoint WHERE singleton=1').fetchone()
                if not enabled(db) or saved is None:
                    raise CatalogError('consensus_not_attached', 409)
                cached = export(db)
                if (not strong and state['index'] < saved['applied_index'] and
                        (saved['cluster_id'], saved['epoch']) == (state['cluster_id'], state['epoch']) and
                        digest(cached) == saved['document_sha256']):
                    # A just-restarted Go FSM may await a quorum commit before
                    # replay catches up. Preserve the last verified Python
                    # projection as explicitly stale, never install a rollback.
                    receipts = {r['request_id']: json.loads(r['data']) for r in db.execute('SELECT * FROM consensus_receipts')}
                    local = {'schema': 1, 'cluster_id': saved['cluster_id'], 'epoch': saved['epoch'],
                             'index': saved['applied_index'], 'term': saved['applied_term'],
                             'document_sha256': saved['document_sha256'], 'receipts': receipts,
                             'document': base64.b64encode(canonical(cached)).decode()}
                    return {'state': local, 'document': cached, 'stale': True, 'read_only': True,
                            'recovering': True, 'revision': cached['revision'],
                            'applied_index': saved['applied_index'], 'metadata_only': True}
                if ((saved['cluster_id'], saved['epoch']) != (state['cluster_id'], state['epoch']) or
                        state['index'] < saved['applied_index'] or state['term'] < saved['applied_term'] or
                        digest(cached) != saved['document_sha256'] or
                        state['index'] == saved['applied_index'] and state['document_sha256'] != saved['document_sha256']):
                    raise CatalogError('consensus_projection_quarantined', 409)
                if state['index'] > saved['applied_index']:
                    changed = True
                    db.execute('UPDATE catalog_state SET epoch=?,revision=?,head_digest=? WHERE singleton=1',
                               (doc['epoch'], doc['revision'], doc['head_digest']))
                    for table in ('catalog_replicas', 'catalog_files', 'catalog_events', 'consensus_receipts'):
                        db.execute(f'DELETE FROM {table}')
                    for field, table in TABLES.items():
                        for row in doc[field]:
                            row = dict(row)
                            if field == 'events':
                                row['payload'] = canonical(row['payload']).decode()
                            fields = list(row)
                            db.execute(f"INSERT INTO {table}({','.join(fields)}) VALUES({','.join('?' for _ in fields)})", tuple(row.values()))
                    for request_id, receipt in state['receipts'].items():
                        db.execute('INSERT INTO consensus_receipts VALUES(?,?)', (request_id, canonical(receipt).decode()))
                    db.execute('UPDATE consensus_checkpoint SET applied_index=?,applied_term=?,document_sha256=? WHERE singleton=1',
                               (state['index'], state['term'], state['document_sha256']))
                    self._fault('inside_python_apply_transaction')
            if changed:
                self._fault('python_applied_before_ack')
            return {'state': state, 'document': doc, 'stale': result['stale'], 'read_only': True,
                    'revision': doc['revision'], 'applied_index': state['index'], 'metadata_only': True}

    def submit(self, operation, data, request_id):
        key(request_id); intent = digest({'operation': operation, 'data': data})
        with self.lock:
            view = self.sync(strong=True); state = view['state']
            previous = state['receipts'].get(request_id)
            if previous:
                if previous['intent_sha256'] != intent:
                    raise CatalogError('request_id_conflict', 409)
                if previous.get('error'):
                    raise CatalogError(previous['error'], 409)
                return {'receipt': previous, **self.sync(strong=True)}
            prepared = prepare(view['document'], operation, data, request_id, uid(), now())
            command = {'schema': 1, 'cluster_id': state['cluster_id'], 'epoch': state['epoch'],
                       'request_id': request_id, 'intent_sha256': intent,
                       'expected_sha256': state['document_sha256'],
                       'document': base64.b64encode(canonical(prepared)).decode()}
            receipt = self.client.submit(command)
            self._fault('raft_committed_before_sync')
            return {'receipt': receipt, **self.sync(strong=True)}
