"""Private, node-local manifest. Versions are independent of the registry schema."""
from contextlib import contextmanager
import sqlite3
from pathlib import Path

SCHEMA_VERSION = 1


class Manifest:
    def __init__(self, path, node_id):
        self.path = Path(path)
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('PRAGMA journal_mode=WAL')
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

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            db.execute('PRAGMA synchronous=FULL')
            with db:
                yield db
        finally:
            db.close()
