"""Registry schema-4 additive catalog tables, installed in its identity transaction."""
from .common import uid, ZERO


def migrate(db):
    db.execute('''CREATE TABLE IF NOT EXISTS catalog_state(
        singleton INTEGER PRIMARY KEY CHECK(singleton=1),epoch TEXT NOT NULL,
        revision INTEGER NOT NULL,head_digest TEXT NOT NULL)''')
    db.execute('INSERT OR IGNORE INTO catalog_state VALUES(1,?,0,?)', (uid(), ZERO))
    db.execute('''CREATE TABLE IF NOT EXISTS catalog_nodes(
        node_id TEXT PRIMARY KEY,origin TEXT NOT NULL,pin TEXT NOT NULL,device_id TEXT NOT NULL,
        metadata_allowed INTEGER NOT NULL,storage_allowed INTEGER NOT NULL,
        approved_generation INTEGER NOT NULL,volume_ids TEXT NOT NULL,capabilities TEXT,checked_at INTEGER,last_error TEXT,
        metadata_revision INTEGER,metadata_digest TEXT,metadata_synced_at INTEGER)''')
    db.execute('''CREATE TABLE IF NOT EXISTS catalog_files(
        file_id TEXT PRIMARY KEY,logical_path TEXT NOT NULL,version INTEGER NOT NULL,
        size INTEGER NOT NULL,sha256 TEXT NOT NULL,policy TEXT NOT NULL,created_at INTEGER NOT NULL,
        updated_at INTEGER NOT NULL,revision INTEGER NOT NULL,upload_key TEXT UNIQUE NOT NULL,upload_policy TEXT NOT NULL,
        UNIQUE(logical_path,version))''')
    db.execute('''CREATE TABLE IF NOT EXISTS catalog_replicas(
        replica_id TEXT PRIMARY KEY,file_id TEXT NOT NULL,node_id TEXT NOT NULL,
        volume_id TEXT NOT NULL,local_file_id TEXT NOT NULL,state TEXT NOT NULL,
        created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL,verified_at INTEGER,
        UNIQUE(node_id,volume_id,local_file_id))''')
    db.execute('''CREATE TABLE IF NOT EXISTS catalog_events(
        revision INTEGER PRIMARY KEY,epoch TEXT NOT NULL,previous_digest TEXT NOT NULL,
        digest TEXT NOT NULL,payload TEXT NOT NULL,created_at INTEGER NOT NULL)''')
    db.execute('''CREATE TABLE IF NOT EXISTS catalog_jobs(
        job_id TEXT PRIMARY KEY,file_id TEXT NOT NULL,replica_id TEXT NOT NULL,kind TEXT NOT NULL,
        state TEXT NOT NULL,idempotency_key TEXT UNIQUE NOT NULL,
        source_replica_id TEXT,target_node_id TEXT NOT NULL,target_volume_id TEXT NOT NULL,
        target_local_file_id TEXT,target_session_id TEXT,logical_path TEXT NOT NULL,
        attempts INTEGER NOT NULL DEFAULT 0,next_attempt_at INTEGER NOT NULL,
        run_token TEXT,lease_until INTEGER,source_generation INTEGER,target_generation INTEGER,
        last_error TEXT,created_at INTEGER NOT NULL,updated_at INTEGER NOT NULL)''')
    db.execute("CREATE UNIQUE INDEX IF NOT EXISTS active_copy ON catalog_jobs(file_id,target_node_id) WHERE state IN ('PENDING','RUNNING','RETRY')")
    db.execute('''CREATE TABLE IF NOT EXISTS catalog_job_history(
        sequence INTEGER PRIMARY KEY AUTOINCREMENT,job_id TEXT NOT NULL,state TEXT NOT NULL,
        error TEXT,created_at INTEGER NOT NULL)''')
    db.execute('''CREATE TABLE IF NOT EXISTS transfer_grants(
        grant_hash TEXT PRIMARY KEY,node_id TEXT NOT NULL,volume_id TEXT NOT NULL,
        node_generation INTEGER NOT NULL,job_id TEXT,side TEXT NOT NULL,
        run_token TEXT,local_file_id TEXT,expires_at INTEGER NOT NULL)''')

def validate_existing(db):
    required={'catalog_state','catalog_nodes','catalog_files','catalog_replicas','catalog_events',
              'catalog_jobs','catalog_job_history','transfer_grants'}
    tables={row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if not required<=tables:
        raise ValueError('catalog state missing; restore complete stopped-state backup')
    row=db.execute('SELECT epoch,revision,head_digest FROM catalog_state WHERE singleton=1').fetchone()
    if row is None:
        raise ValueError('catalog epoch missing; restore backup instead of recreating authority')
    from .common import identifier
    identifier(row['epoch'])
    if (type(row['revision']) is not int or row['revision']<0 or not isinstance(row['head_digest'],str) or
            len(row['head_digest'])!=64 or any(c not in '0123456789abcdef' for c in row['head_digest'])):
        raise ValueError('invalid catalog checkpoint; restore reviewed backup')
