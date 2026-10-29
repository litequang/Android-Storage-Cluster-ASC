"""Single-writer development registry; NOT distributed consensus."""
import hashlib
from contextlib import contextmanager
import hmac
import json
import secrets
import sqlite3
import time
import uuid
from pathlib import Path
from .planner import recommend
from . import validation as valid

SCHEMA_VERSION = 4


class NodeStateChanged(ValueError):
    """A conditional owner operation cannot target a newer credential/state."""


def check_node_generation(row, expected):
    if expected is None:
        return
    if type(expected) is not int or expected < 1:
        raise ValueError('invalid expected generation')
    if (row is None or row['state'] != 'active' or row['token_version'] != expected
            or row['node_id'] == 'local-controller' or json.loads(row['profile']).get('protected') is True):
        raise NodeStateChanged('node_state_changed')


def _digest(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


class Registry:
    def __init__(self, path):
        self.path = Path(path)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        db.create_function('asc_consensus_apply', 0, lambda: 0)
        try:
            has_settings = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='settings'").fetchone()
            distributed = has_settings and db.execute(
                "SELECT 1 FROM settings WHERE key='consensus_mode' AND value='metadata-v1'").fetchone()
            if distributed:
                # Persistent triggers also stop raw/older SQLite writers. This
                # authorizer prevents normal internal connections removing them.
                writes = {sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE,
                          sqlite3.SQLITE_CREATE_TABLE, sqlite3.SQLITE_DROP_TABLE,
                          sqlite3.SQLITE_CREATE_TRIGGER, sqlite3.SQLITE_DROP_TRIGGER,
                          sqlite3.SQLITE_ALTER_TABLE, sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH}
                db.set_authorizer(lambda action, arg1, arg2, database, source:
                                  sqlite3.SQLITE_DENY if action in writes else sqlite3.SQLITE_OK)
            with db:
                yield db
        finally:
            db.close()

    def initialize(self, cluster_id, *, initial_catalog_epoch=None):
        """Transactional additive v0.4/v0.4.1 -> schema 4; never replace identity or rows."""
        with self.connect() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('BEGIN IMMEDIATE')
            version = db.execute('PRAGMA user_version').fetchone()[0]
            if version not in (0, 2, 3, SCHEMA_VERSION):
                raise ValueError('unsupported registry schema; use matching release')
            if version == SCHEMA_VERSION:
                distributed = db.execute("SELECT value FROM settings WHERE key='consensus_mode'").fetchone()
                if distributed:
                    if distributed[0] != 'metadata-v1' or self.cluster_id() != cluster_id:
                        raise ValueError('unsupported consensus identity/mode')
                    from .catalog.schema import validate_existing
                    validate_existing(db)
                    return  # No legacy migration/write path in distributed mode.
            db.execute('CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL)')
            existing = db.execute("SELECT value FROM settings WHERE key='cluster_id'").fetchone()
            if existing and existing['value'] != cluster_id:
                raise ValueError('cluster identity mismatch; refusing migration')
            db.execute('''CREATE TABLE IF NOT EXISTS nodes(
                node_id TEXT PRIMARY KEY, name TEXT NOT NULL, token_hash TEXT NOT NULL,
                profile TEXT NOT NULL, last_seen INTEGER NOT NULL, joined_at INTEGER NOT NULL)''')
            db.execute('''CREATE TABLE IF NOT EXISTS join_codes(
                code_hash TEXT PRIMARY KEY, expires_at INTEGER NOT NULL, used INTEGER NOT NULL DEFAULT 0)''')
            db.execute('''CREATE TABLE IF NOT EXISTS enrollments(
                enrollment_hash TEXT PRIMARY KEY, node_id TEXT NOT NULL)''')
            additions = {
                'nodes': [('state', "TEXT NOT NULL DEFAULT 'active'"),
                          ('token_version', 'INTEGER NOT NULL DEFAULT 1'), ('revoked_at', 'INTEGER')],
                'join_codes': [('target_node_id', 'TEXT'), ('enrollment_hash', 'TEXT'), ('node_id', 'TEXT')],
            }
            for table, columns in additions.items():
                present = {r['name'] for r in db.execute(f'PRAGMA table_info({table})')}
                for column, definition in columns:
                    if column not in present:
                        db.execute(f'ALTER TABLE {table} ADD COLUMN {column} {definition}')
            db.execute('INSERT OR IGNORE INTO settings(key,value) VALUES (?,?)', ('cluster_id', cluster_id))
            db.execute('''CREATE TABLE IF NOT EXISTS storage_grants(
                grant_hash TEXT PRIMARY KEY,node_id TEXT NOT NULL,volume_id TEXT NOT NULL,
                token_version INTEGER NOT NULL,principal TEXT NOT NULL,operations TEXT NOT NULL,
                expires_at INTEGER NOT NULL)''')
            from .catalog.schema import migrate, validate_existing
            if version==SCHEMA_VERSION:
                validate_existing(db)
            if initial_catalog_epoch is not None:
                from .catalog.common import identifier
                identifier(initial_catalog_epoch)
                migrate(db, initial_catalog_epoch)
            else:
                migrate(db)
            db.execute(f'PRAGMA user_version={SCHEMA_VERSION}')

    def consensus_enabled(self):
        with self.connect() as db:
            row = db.execute("SELECT value FROM settings WHERE key='consensus_mode'").fetchone()
        return row is not None and row[0] == 'metadata-v1'

    def cluster_id(self):
        with self.connect() as db:
            row = db.execute('SELECT value FROM settings WHERE key=?', ('cluster_id',)).fetchone()
            return row['value'] if row else None

    def add_pair_code(self, ttl=600, target_node_id=None):
        ttl = max(60, min(1800, ttl))
        if target_node_id is not None:
            valid.node_id(target_node_id)
        code = secrets.token_hex(6).upper()
        now = int(time.time())
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if target_node_id:
                row = db.execute('SELECT node_id FROM nodes WHERE node_id=?', (target_node_id,)).fetchone()
                if row is None or target_node_id == 'local-controller':
                    raise ValueError('node not found or protected local controller')
                db.execute('DELETE FROM join_codes WHERE target_node_id=?', (target_node_id,))
            db.execute('DELETE FROM join_codes WHERE expires_at<?', (now - 86400,))
            db.execute('INSERT INTO join_codes(code_hash,expires_at,target_node_id) VALUES (?,?,?)',
                       (_digest(code), now + ttl, target_node_id))
        return code

    def join(self, code, name, profile, enrollment_id=None, enrollment_token=None, node_id=None):
        code, name, profile = valid.code(code), valid.name(name), valid.profile(profile)
        modern = enrollment_id is not None or enrollment_token is not None
        if modern:
            valid.secret(enrollment_id)
            valid.secret(enrollment_token)
        if node_id is not None:
            valid.node_id(node_id)
            if not modern:
                raise ValueError('re-pair requires retry-safe enrollment')
        now = int(time.time())
        token = enrollment_token if modern else secrets.token_urlsafe(32)
        code_hash = _digest(code)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM join_codes WHERE code_hash=?', (code_hash,)).fetchone()
            if not row or row['target_node_id'] != node_id:
                return None
            prior = (db.execute('SELECT node_id FROM enrollments WHERE enrollment_hash=?',
                                (_digest(enrollment_id),)).fetchone() if modern else None)
            if prior:
                saved = db.execute('SELECT * FROM nodes WHERE node_id=?', (prior['node_id'],)).fetchone()
                if (not saved or saved['state'] != 'active' or
                        (node_id is not None and node_id != saved['node_id']) or
                        not hmac.compare_digest(saved['token_hash'], _digest(token))):
                    return None
                if row['used']:
                    if (row['enrollment_hash'] != _digest(enrollment_id) or
                            row['node_id'] != saved['node_id'] or row['expires_at'] < now - 86400):
                        return None
                else:
                    if row['expires_at'] <= now:
                        return None
                    db.execute('UPDATE join_codes SET used=1,enrollment_hash=?,node_id=? WHERE code_hash=?',
                               (_digest(enrollment_id), saved['node_id'], code_hash))
                return {'node_id': saved['node_id'], 'token': token, 'token_version': saved['token_version']}
            if row['used']:
                return None
            if row['expires_at'] <= now:
                return None
            if node_id:
                saved = db.execute('SELECT * FROM nodes WHERE node_id=?', (node_id,)).fetchone()
                if saved is None or node_id == 'local-controller':
                    return None
                db.execute("UPDATE nodes SET token_hash=?,profile=?,last_seen=?,state='active',"
                           'revoked_at=NULL,token_version=token_version+1 WHERE node_id=?',
                           (_digest(token), json.dumps(profile), now, node_id))
                version = saved['token_version'] + 1
            else:
                node_id, version = str(uuid.uuid4()), 1
                db.execute('INSERT INTO nodes(node_id,name,token_hash,profile,last_seen,joined_at) VALUES(?,?,?,?,?,?)',
                           (node_id, name, _digest(token), json.dumps(profile), now, now))
            db.execute('UPDATE join_codes SET used=1,enrollment_hash=?,node_id=? WHERE code_hash=?',
                       (_digest(enrollment_id) if modern else None, node_id, code_hash))
            if modern:
                db.execute('INSERT INTO enrollments(enrollment_hash,node_id) VALUES (?,?)',
                           (_digest(enrollment_id), node_id))
        return {'node_id': node_id, 'token': token, 'token_version': version}

    def heartbeat(self, node_id, token, profile):
        valid.node_id(node_id)
        valid.profile(profile)
        if not isinstance(token, str) or not 1 <= len(token) <= 128:
            return False
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT token_hash,state FROM nodes WHERE node_id=?', (node_id,)).fetchone()
            if row is None or row['state'] != 'active' or not hmac.compare_digest(row['token_hash'], _digest(token)):
                return False
            db.execute('UPDATE nodes SET profile=?,last_seen=? WHERE node_id=?',
                       (json.dumps(profile), int(time.time()), node_id))
        return True

    def rename(self, node_id, name, *, expected_generation=None):
        valid.node_id(node_id)
        valid.name(name)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM nodes WHERE node_id=?', (node_id,)).fetchone()
            check_node_generation(row, expected_generation)
            return db.execute('UPDATE nodes SET name=? WHERE node_id=?', (name, node_id)).rowcount == 1

    def revoke(self, node_id, *, expected_generation=None):
        valid.node_id(node_id)
        if node_id == 'local-controller':
            raise ValueError('cannot revoke local controller')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            exists = db.execute('SELECT * FROM nodes WHERE node_id=?', (node_id,)).fetchone()
            check_node_generation(exists, expected_generation)
            if not exists:
                return False
            db.execute("UPDATE nodes SET state='revoked',token_hash='<revoked>',revoked_at=?,"
                       "token_version=token_version+1 WHERE node_id=? AND state!='revoked'",
                       (int(time.time()), node_id))
            db.execute('DELETE FROM join_codes WHERE target_node_id=?', (node_id,))
        return True

    def seed_self(self, name, profile):
        valid.name(name)
        valid.profile(profile)
        now = int(time.time())
        with self.connect() as db:
            db.execute('INSERT OR IGNORE INTO nodes(node_id,name,token_hash,profile,last_seen,joined_at) VALUES(?,?,?,?,?,?)',
                       ('local-controller', name, '<local>', json.dumps(profile), now, now))
        return 'local-controller'

    def update_self(self, profile):
        valid.profile(profile)
        with self.connect() as db:
            db.execute('UPDATE nodes SET profile=?,last_seen=? WHERE node_id=?',
                       (json.dumps(profile), int(time.time()), 'local-controller'))

    @staticmethod
    def _public(row, now):
        return dict(node_id=row['node_id'], name=row['name'], profile=json.loads(row['profile']),
                    state=row['state'], token_version=row['token_version'], revoked_at=row['revoked_at'],
                    joined_at=row['joined_at'], last_seen=row['last_seen'],
                    online=(row['state'] == 'active' and now - row['last_seen'] < 100))

    def detail(self, node_id):
        valid.node_id(node_id)
        with self.connect() as db:
            row = db.execute('SELECT * FROM nodes WHERE node_id=?', (node_id,)).fetchone()
        return self._public(row, int(time.time())) if row else None

    def snapshot(self):
        now = int(time.time())
        with self.connect() as db:
            rows = db.execute('SELECT * FROM nodes ORDER BY joined_at,node_id').fetchall()
        nodes = [self._public(row, now) for row in rows]
        return {'protocol_version': 1, 'schema_version': SCHEMA_VERSION,
                'cluster_id': self.cluster_id(), 'snapshot_at': now,
                'consensus_status': 'NOT_IMPLEMENTED_SINGLE_WRITER',
                'nodes': nodes, 'advisory_role_plan': recommend(nodes)}

    def storage_grant(self, node_id, volume_id, operations, ttl=300):
        """Owner delegation; a node bearer never grants user data access."""
        valid.node_id(node_id)
        if not isinstance(volume_id, str) or str(uuid.UUID(volume_id)) != volume_id:
            raise ValueError('invalid volume ID')
        allowed = {'read', 'write', 'list', 'verify'}
        if (not isinstance(operations, list) or not operations or
                any(not isinstance(op, str) or op not in allowed for op in operations) or
                len(operations) > 4 or type(ttl) is not int or not 30 <= ttl <= 900):
            raise ValueError('invalid storage grant')
        token, now = secrets.token_urlsafe(32), int(time.time())
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            node = db.execute('SELECT * FROM nodes WHERE node_id=?', (node_id,)).fetchone()
            if (not node or node['state'] != 'active' or node_id == 'local-controller' or
                    json.loads(node['profile']).get('protected') is True):
                raise ValueError('node unavailable or protected')
            db.execute('DELETE FROM storage_grants WHERE expires_at<=?', (now,))
            if db.execute('SELECT COUNT(*) FROM storage_grants').fetchone()[0] >= 1024:
                raise ValueError('too many active storage grants')
            db.execute('INSERT INTO storage_grants VALUES (?,?,?,?,?,?,?)',
                       (_digest(token), node_id, volume_id, node['token_version'], 'local-admin',
                        json.dumps(sorted(set(operations))), now + ttl))
        return {'grant': token, 'node_id': node_id, 'volume_id': volume_id,
                'operations': sorted(set(operations)), 'expires_at': now + ttl, 'principal': 'local-admin'}

    def storage_authorize(self, node_id, node_token, grant, volume_id, operation, scope=None):
        if self.consensus_enabled():
            return None  # Old grants cannot revive physical writes after attachment.
        valid.node_id(node_id)
        valid.secret(grant)
        valid.secret(node_token)
        if not isinstance(volume_id, str) or str(uuid.UUID(volume_id)) != volume_id or operation not in ('read', 'write', 'list', 'verify'):
            raise ValueError('invalid storage authorization')
        with self.connect() as db:
            node = db.execute('SELECT * FROM nodes WHERE node_id=?', (node_id,)).fetchone()
            row = db.execute('SELECT * FROM storage_grants WHERE grant_hash=?', (_digest(grant),)).fetchone()
        if (not node or node['state'] != 'active' or
                not hmac.compare_digest(node['token_hash'], _digest(node_token)) or
                json.loads(node['profile']).get('protected') is True):
            return None
        if row is None:
            from .catalog.grants import authorize
            with self.connect() as db:
                return authorize(db, node, _digest(grant), volume_id, operation, scope)
        if (not node or node['state'] != 'active' or
                not hmac.compare_digest(node['token_hash'], _digest(node_token)) or
                json.loads(node['profile']).get('protected') is True or not row or
                row['node_id'] != node_id or row['volume_id'] != volume_id or
                row['token_version'] != node['token_version'] or row['expires_at'] <= int(time.time()) or
                operation not in json.loads(row['operations'])):
            return None
        return {'principal': row['principal'], 'expires_at': row['expires_at']}

    def authenticate_node(self, node_id, token):
        valid.node_id(node_id)
        if not isinstance(token,str) or not 1 <= len(token) <= 128:
            return False
        with self.connect() as db:
            row=db.execute('SELECT state,token_hash FROM nodes WHERE node_id=?',(node_id,)).fetchone()
        return bool(row and row['state']=='active' and hmac.compare_digest(row['token_hash'],_digest(token)))
