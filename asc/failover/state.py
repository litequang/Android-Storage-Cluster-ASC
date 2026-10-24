"""Bounded runtime projection and isolated SQL preparation, never a live DB copy."""
from contextlib import contextmanager, closing
import copy
import json
import re
import sqlite3
from pathlib import Path

from ..catalog.common import CatalogError, canonical, identifier, key, digest
from ..consensus.projection import export as catalog_export, validate as catalog_validate, TABLES
from ..store import Registry
from .. import validation as valid

# A code-owned schema/column allowlist; no SQL, paths, keys or raw bearer tokens
# are accepted from the replicated document. Lease IDs are public non-bearer IDs.
SHARED = {'nodes': 64, 'join_codes': 256, 'enrollments': 1024,
          'catalog_nodes': 16, 'catalog_jobs': 2048,
          'catalog_job_history': 8192, 'transfer_grants': 4096}


class MemoryRegistry(Registry):
    def __init__(self, cluster):
        self.path = Path(':memory:')
        self.db = sqlite3.connect(':memory:')
        self.db.row_factory = sqlite3.Row
        # Validation/installation never samples a clock or random source. This
        # placeholder has no authority and is replaced by the validated epoch.
        self.initialize(cluster, initial_catalog_epoch='00000000-0000-0000-0000-000000000000')

    @contextmanager
    def connect(self):
        with self.db:
            yield self.db


def rows(db, table):
    fields = [r['name'] for r in db.execute(f'PRAGMA table_info({table})')]
    primary = [r['name'] for r in db.execute(f'PRAGMA table_info({table})') if r['pk']]
    return [dict(r) for r in db.execute(f'SELECT * FROM {table} ORDER BY {",".join(primary or fields)}')]


def export(db, revision, authority):
    result = {'schema': 2, 'cluster_id': db.execute("SELECT value FROM settings WHERE key='cluster_id'").fetchone()[0],
            'epoch': db.execute('SELECT epoch FROM catalog_state').fetchone()[0],
            'revision': revision, 'authority': authority,
            'catalog': catalog_export(db), 'tables': {t: rows(db, t) for t in SHARED},
            'inventory_cursor': (lambda r: r[0] if r else None)(db.execute(
                "SELECT value FROM settings WHERE key='catalog_inventory_cursor'").fetchone())}
    backup = db.execute("SELECT value FROM settings WHERE key='phase3a_backup'").fetchone()
    if backup:
        result['backup'] = json.loads(backup[0])
    insights = db.execute("SELECT value FROM settings WHERE key='phase3b_insights'").fetchone()
    if insights:
        result['insights'] = json.loads(insights[0])
    replication = db.execute("SELECT value FROM settings WHERE key='phase3c_replication'").fetchone()
    if replication:
        result['replication'] = json.loads(replication[0])
    return result


def _install(db, doc):
    db.execute("DELETE FROM settings WHERE key='phase3c_replication'")
    if 'replication' in doc:
        db.execute("INSERT INTO settings VALUES('phase3c_replication',?)", (canonical(doc['replication']).decode(),))
    db.execute("DELETE FROM settings WHERE key='phase3b_insights'")
    if 'insights' in doc:
        db.execute("INSERT INTO settings VALUES('phase3b_insights',?)", (canonical(doc['insights']).decode(),))
    db.execute("DELETE FROM settings WHERE key='phase3a_backup'")
    if 'backup' in doc:
        db.execute("INSERT INTO settings VALUES('phase3a_backup',?)", (canonical(doc['backup']).decode(),))
    for table in [*SHARED, *TABLES.values(), 'storage_grants']:
        db.execute(f'DELETE FROM {table}')
    db.execute('UPDATE catalog_state SET epoch=?,revision=?,head_digest=? WHERE singleton=1',
               tuple(doc['catalog'][k] for k in ('epoch', 'revision', 'head_digest')))
    for table, records in [*( (t, doc['tables'][t]) for t in SHARED),
                            *((t, doc['catalog'][f]) for f, t in TABLES.items())]:
        columns = {r['name'] for r in db.execute(f'PRAGMA table_info({table})')}
        for record in records:
            if not isinstance(record, dict) or set(record) != columns:
                raise CatalogError('invalid_runtime_columns', 409)
            row = dict(record)
            if table == 'catalog_events':
                row['payload'] = canonical(row['payload']).decode()
            db.execute(f'INSERT INTO {table}({",".join(row)}) VALUES({",".join("?" for _ in row)})', tuple(row.values()))
    if doc['inventory_cursor'] is not None:
        db.execute("INSERT OR REPLACE INTO settings VALUES('catalog_inventory_cursor',?)", (doc['inventory_cursor'],))


def validate(doc):
    try:
        if (not isinstance(doc, dict) or set(doc) - {'backup', 'insights', 'replication'} != {'schema', 'cluster_id', 'epoch', 'revision',
                'authority', 'catalog', 'tables', 'inventory_cursor'} or doc['schema'] != 2 or
                type(doc['revision']) is not int or not 0 < doc['revision'] < 2**63 or
                set(doc['tables']) != set(SHARED) or
                set(doc['authority']) != {'node_id', 'term'} or
                not isinstance(doc['authority']['node_id'], str) or not 1 <= len(doc['authority']['node_id']) <= 64 or
                type(doc['authority']['term']) is not int or not 0 < doc['authority']['term'] < 2**63):
            raise ValueError()
        catalog_validate(doc['catalog'])
        if 'backup' in doc:
            from ..backup.state import validate as validate_backup
            validate_backup(doc['backup'], doc['catalog'])
        if 'insights' in doc:
            from ..nodes.history import validate as validate_insights
            validate_insights(doc['insights'], doc['tables']['nodes'])
        if 'replication' in doc:
            from ..replication.state import validate as validate_replication
            validate_replication(doc['replication'],doc)
        if (doc['cluster_id'], doc['epoch']) != (doc['catalog']['cluster_id'], doc['catalog']['epoch']):
            raise ValueError()
        if len(canonical(doc)) > 2*1024**2:
            raise CatalogError('runtime_projection_limit', 409)
        for table, bound in SHARED.items():
            if not isinstance(doc['tables'][table], list) or len(doc['tables'][table]) > bound:
                raise CatalogError('runtime_projection_limit', 409)
        for node in doc['tables']['nodes']:
            valid.node_id(node['node_id']); valid.name(node['name']); valid.profile(json.loads(node['profile']))
            if (node['state'] not in ('active', 'revoked') or type(node['token_version']) is not int or
                    node['token_version'] < 1 or not isinstance(node['token_hash'], str) or
                    not (re.fullmatch('[0-9a-f]{64}', node['token_hash']) or
                         node['state'] == 'revoked' and node['token_hash'] == '<revoked>' or
                         node['node_id'] == 'local-controller' and node['token_hash'] == '<local>')):
                raise ValueError()
            for field in ('last_seen', 'joined_at'):
                if type(node[field]) is not int or not 0 <= node[field] < 2**63:
                    raise ValueError()
        node_ids = {n['node_id'] for n in doc['tables']['nodes']}
        file_ids = {f['file_id'] for f in doc['catalog']['files']}
        for row in doc['tables']['enrollments']:
            if row['node_id'] not in node_ids:
                raise ValueError()
        for row in doc['tables']['join_codes']:
            if (type(row['expires_at']) is not int or not 0 <= row['expires_at'] < 2**63 or
                    row['used'] not in (0, 1) or row['target_node_id'] is not None and row['target_node_id'] not in node_ids or
                    row['node_id'] is not None and row['node_id'] not in node_ids):
                raise ValueError()
        for row in doc['tables']['catalog_jobs']:
            identifier(row['job_id']); identifier(row['replica_id']); identifier(row['target_volume_id'])
            key(row['idempotency_key'])
            if (row['file_id'] not in file_ids or row['target_node_id'] not in node_ids or
                    row['kind'] not in ('UPLOAD', 'COPY') or row['state'] not in ('PENDING', 'RUNNING', 'COMPLETED', 'RETRY', 'FAILED') or
                    type(row['attempts']) is not int or not 0 <= row['attempts'] < 2**31):
                raise ValueError()
            for field in ('target_local_file_id', 'target_session_id', 'source_replica_id', 'run_token'):
                if row[field] is not None:
                    identifier(row[field])
        for row in doc['tables']['transfer_grants']:
            if row['node_id'] not in node_ids or row['side'] not in ('inspect', 'read', 'audit', 'source', 'target'):
                raise ValueError()
            identifier(row['volume_id'])
            for field in ('job_id', 'run_token', 'local_file_id'):
                if row[field] is not None:
                    identifier(row[field])
        if doc['inventory_cursor'] is not None:
            cursor = json.loads(doc['inventory_cursor'])
            if (set(cursor) != {'version', 'next_pair', 'offsets'} or cursor['version'] != 1 or
                    type(cursor['next_pair']) is not int or not 0 <= cursor['next_pair'] < 128 or
                    not isinstance(cursor['offsets'], dict) or len(cursor['offsets']) > 128):
                raise ValueError()
            for pair, offset in cursor['offsets'].items():
                node, volume = pair.split('/')
                valid.node_id(node); identifier(volume)
                if type(offset) is not int or not 0 <= offset <= 10000:
                    raise ValueError()
        for table, field in [('join_codes', 'code_hash'), ('enrollments', 'enrollment_hash'),
                              ('transfer_grants', 'grant_hash')]:
            for row in doc['tables'][table]:
                if not isinstance(row[field], str) or not re.fullmatch('[0-9a-f]{64}', row[field]):
                    raise ValueError()
        with closing(MemoryRegistry(doc['cluster_id']).db) as db, db:
            _install(db, doc)
            # Re-export also verifies canonical row order and exact schema fields.
            if export(db, doc['revision'], doc['authority']) != doc:
                raise ValueError()
        return doc
    except (ValueError, TypeError, KeyError, sqlite3.Error):
        raise CatalogError('invalid_runtime_projection', 409) from None


def prepare_registry(doc):
    """Create a disposable business-logic workspace, with no filesystem authority."""
    validate(doc)
    reg = MemoryRegistry(doc['cluster_id'])
    with reg.connect() as db:
        _install(db, doc)
    return reg


def takeover(doc, node_id, term):
    result = copy.deepcopy(doc)
    result['revision'] += 1
    result['authority'] = {'node_id': node_id, 'term': term}
    result['tables']['transfer_grants'] = []
    if 'backup' in result:
        from ..backup.state import takeover as backup_takeover
        result['backup'] = backup_takeover(result['backup'])
    if 'replication' in result:
        from ..replication.state import takeover as replication_takeover
        result['replication'] = replication_takeover(result['replication'])
    for job in result['tables']['catalog_jobs']:
        job.update(run_token=None, lease_until=None)
        if job['state'] == 'RUNNING':
            job.update(state='RETRY', next_attempt_at=0, last_error='controller_restart')
    # A probe is a time-bound observation, not a capability guarantee on takeover.
    for node in result['tables']['catalog_nodes']:
        node.update(checked_at=None, last_error='leader_recovery')
    return validate(result)


def verify_attachment(registry, view, voters):
    """Never silently abandon an independent Controller's private authority.

    The permanent upgrade receipt commits the initial full runtime SHA. Rebuild
    that exact deterministic preparation from the frozen local original and each
    configured possible owner. Only that source or an exact metadata-only fresh
    follower may attach; conflicting private histories require operator review.
    """
    if not registry.consensus_enabled():
        raise CatalogError('attached_registry_required', 409)
    with registry.connect() as db:
        source = catalog_export(db)
        source_sha = digest(source)
        receipt = view['state']['receipts'].get('runtime-upgrade-'+source_sha)
        if (not receipt or receipt.get('error') or receipt['intent_sha256'] != digest(
                {'upgrade': 2, 'expected_sha256': source_sha})):
            raise CatalogError('unmerged_controller_authority', 409)
        initial = export(db, source['revision'], {'node_id': voters[0], 'term': receipt['term']})
        fresh = (not any(records for table, records in initial['tables'].items() if table != 'nodes') and
                 all(n['node_id'] == 'local-controller' for n in initial['tables']['nodes']) and
                 not db.execute('SELECT COUNT(*) FROM storage_grants').fetchone()[0])
    for voter in voters:
        if digest(takeover(initial, voter, receipt['term'])) == receipt['document_sha256']:
            return 'primary-source'
    if fresh:
        return 'fresh-metadata-follower'
    raise CatalogError('unmerged_controller_authority', 409)
