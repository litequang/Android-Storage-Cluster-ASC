"""Private, node-local manifest. Versions are independent of the registry schema."""
from contextlib import contextmanager
from functools import lru_cache
import os
import sqlite3
import stat
from pathlib import Path
from .volumes import no_links

SCHEMA_VERSION = 1


def existing_identity(path, expected=None):
    """POSIX app-private metadata only, never adopt an untrusted shared path.

    URI mode=rw prevents missing-file recreation; inode/namespace checks detect
    replacement. Not an fd-pinned SQLite VFS against a compromised same-UID host.
    Native callers must supply a private approved root and retain this receipt.
    """
    if os.name != 'posix':
        raise ValueError('existing manifest provider not qualified on this platform')
    if expected is not None and (not isinstance(expected, (tuple, list)) or len(expected) != 2 or
            any(type(value) is not int or value < 0 for value in expected)):
        raise ValueError('invalid manifest identity')
    path = Path(path)
    if not path.is_absolute() or '..' in path.parts:
        raise ValueError('absolute private manifest required')
    no_links(path)
    info = path.lstat()
    identity = (info.st_dev, info.st_ino)
    if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid() or
            expected is not None and tuple(expected) != identity):
        raise ValueError('manifest identity changed')
    return identity


class Manifest:
    def __init__(self, path, node_id, *, existing_only=False, expected_file=None):
        self.path = Path(path)
        if type(existing_only) is not bool or not existing_only and expected_file is not None:
            raise ValueError('invalid manifest open mode')
        self.existing_only = existing_only
        self.expected_file = existing_identity(self.path, expected_file) if existing_only else None
        if existing_only:
            with self.connect() as db:
                if db.execute('PRAGMA user_version').fetchone()[0] != SCHEMA_VERSION:
                    raise ValueError('unsupported existing local manifest schema')
                row = db.execute("SELECT value FROM settings WHERE key='node_id'").fetchone()
                if row is None or row['value'] != node_id:
                    raise ValueError('manifest node identity mismatch')
                if self._schema(db) != self._expected_schema():
                    raise ValueError('unsupported existing manifest structure')
                if db.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                    raise ValueError('manifest integrity check failed')
            return  # No DDL, schema update, identity insertion or chmod/mkdir.
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('PRAGMA journal_mode=WAL')
            self._initialize(db, node_id)

    @staticmethod
    def _initialize(db, node_id):
        db.execute('BEGIN IMMEDIATE')
        version = db.execute('PRAGMA user_version').fetchone()[0]
        if version not in (0, SCHEMA_VERSION):
            raise ValueError('unsupported local manifest schema')
        db.execute('CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL)')
        row = db.execute("SELECT value FROM settings WHERE key='node_id'").fetchone()
        if row and row['value'] != node_id:
            raise ValueError('manifest node identity mismatch')
        db.execute("INSERT OR IGNORE INTO settings VALUES ('node_id',?)", (node_id,))
        db.execute('''CREATE TABLE IF NOT EXISTS volumes(
            volume_id TEXT PRIMARY KEY,node_id TEXT NOT NULL,kind TEXT NOT NULL,
            root TEXT UNIQUE NOT NULL,medium TEXT NOT NULL,quota INTEGER NOT NULL,
            reserve INTEGER NOT NULL)''')
        db.execute('''CREATE TABLE IF NOT EXISTS uploads(
            session_id TEXT PRIMARY KEY,file_id TEXT UNIQUE NOT NULL,principal TEXT NOT NULL,
            idempotency_key TEXT NOT NULL,logical_path TEXT NOT NULL,volume_id TEXT NOT NULL,
            size INTEGER NOT NULL,sha256 TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1,
            state TEXT NOT NULL,created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL,
            UNIQUE(principal,idempotency_key))''')
        db.execute("CREATE UNIQUE INDEX IF NOT EXISTS upload_path ON uploads(volume_id,logical_path) WHERE state NOT IN ('EXPIRED')")
        db.execute('''CREATE TABLE IF NOT EXISTS files(
            file_id TEXT PRIMARY KEY,logical_path TEXT NOT NULL,volume_id TEXT NOT NULL,
            relative_path TEXT NOT NULL,size INTEGER NOT NULL,sha256 TEXT NOT NULL,
            version INTEGER NOT NULL,state TEXT NOT NULL,created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,last_verified_at INTEGER,
            UNIQUE(volume_id,logical_path))''')
        db.execute(f'PRAGMA user_version={SCHEMA_VERSION}')

    @staticmethod
    def _schema(db):
        # Moving canonical Python DDL indentation does not change format1.
        return tuple((row[0], row[1], row[2], ' '.join(row[3].split())) for row in db.execute(
            "SELECT type,name,tbl_name,sql FROM sqlite_master "
            "WHERE name NOT GLOB 'sqlite_*' ORDER BY type,name"))

    @staticmethod
    @lru_cache(maxsize=1)
    def _expected_schema():
        # SAME canonical DDL, isolated in RAM; no duplicate schema or data store.
        db = sqlite3.connect(':memory:')
        db.row_factory = sqlite3.Row
        try:
            Manifest._initialize(db, 'schema-template-only')
            return Manifest._schema(db)
        finally:
            db.close()

    @contextmanager
    def connect(self):
        if self.existing_only:
            existing_identity(self.path, self.expected_file)
            db = sqlite3.connect(self.path.as_uri() + '?mode=rw', uri=True, timeout=15)
        else:
            db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            if self.existing_only:
                existing_identity(self.path, self.expected_file)
            db.execute('PRAGMA synchronous=FULL')
            with db:
                yield db
                if self.existing_only:
                    existing_identity(self.path, self.expected_file)
        finally:
            db.close()
