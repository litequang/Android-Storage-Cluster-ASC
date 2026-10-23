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

SCHEMA_VERSION = 2


def _digest(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


class Registry:
    def __init__(self, path):
        self.path = Path(path)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def initialize(self, cluster_id):
        """Transactional additive v0.4 -> schema 2; never replace identity or rows."""
        with self.connect() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('BEGIN IMMEDIATE')
            version = db.execute('PRAGMA user_version').fetchone()[0]
            if version not in (0, SCHEMA_VERSION):
                raise ValueError('unsupported registry schema; use matching release')
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
            db.execute(f'PRAGMA user_version={SCHEMA_VERSION}')

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

    def rename(self, node_id, name):
        valid.node_id(node_id)
        valid.name(name)
        with self.connect() as db:
            return db.execute('UPDATE nodes SET name=? WHERE node_id=?', (name, node_id)).rowcount == 1

    def revoke(self, node_id):
        valid.node_id(node_id)
        if node_id == 'local-controller':
            raise ValueError('cannot revoke local controller')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            exists = db.execute('SELECT node_id FROM nodes WHERE node_id=?', (node_id,)).fetchone()
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
