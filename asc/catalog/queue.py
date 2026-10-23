"""Durable lease-fenced job queue. Retry never deletes source/target objects."""
from .common import CatalogError, identifier, now, uid
from .state import insert


class JobQueue:
    def __init__(self, catalog, timeout=300, max_attempts=5):
        if type(timeout) is not int or not 30 <= timeout <= 900:
            raise ValueError('invalid job timeout')
        self.catalog, self.registry = catalog, catalog.registry
        self.timeout, self.max_attempts = timeout, max_attempts

    def get(self, job_id):
        identifier(job_id)
        with self.registry.connect() as db:
            row = db.execute('SELECT * FROM catalog_jobs WHERE job_id=?', (job_id,)).fetchone()
        if not row:
            raise CatalogError('job_not_found', 404)
        return dict(row)

    def list(self, offset=0):
        if type(offset) is not int or not 0 <= offset <= 10000:
            raise CatalogError('invalid_offset', 400)
        with self.registry.connect() as db:
            rows = db.execute('SELECT * FROM catalog_jobs ORDER BY created_at,job_id LIMIT 101 OFFSET ?', (offset,)).fetchall()
        public = ('job_id','file_id','replica_id','kind','state','source_replica_id','target_node_id',
                  'target_volume_id','attempts','next_attempt_at','last_error','created_at','updated_at')
        return {'jobs':[{k:r[k] for k in public} for r in rows[:100]],
                'next_offset':offset+100 if len(rows)>100 else None}

    def recover(self):
        """Only call after acquiring the controller's OS-held catalog-worker lock."""
        with self.registry.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            for row in db.execute("SELECT job_id FROM catalog_jobs WHERE state='RUNNING'").fetchall():
                db.execute("UPDATE catalog_jobs SET state='RETRY',run_token=NULL,lease_until=NULL,"
                           "next_attempt_at=?,updated_at=?,last_error='controller_restart' WHERE job_id=?",
                           (now(),now(),row['job_id']))
                self.catalog._history(db,row['job_id'],'RETRY','controller_restart')

    def claim(self, job_id=None):
        if job_id is not None:identifier(job_id)
        with self.registry.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            for row in db.execute("SELECT job_id FROM catalog_jobs WHERE state='RUNNING' AND lease_until<=?", (now(),)).fetchall():
                db.execute("UPDATE catalog_jobs SET state='RETRY',run_token=NULL,next_attempt_at=?,last_error='job_timeout' WHERE job_id=?",
                           (now()+2,row['job_id']))
                self.catalog._history(db,row['job_id'],'RETRY','job_timeout')
            rows = db.execute("SELECT * FROM catalog_jobs WHERE state IN ('PENDING','RETRY') AND next_attempt_at<=? "
                              "AND (kind='COPY' OR target_local_file_id IS NOT NULL) AND (? IS NULL OR job_id=?) ORDER BY created_at,job_id", (now(),job_id,job_id)).fetchall()
            for row in rows:
                source = db.execute('SELECT node_id FROM catalog_replicas WHERE replica_id=?', (row['source_replica_id'],)).fetchone()
                nodes = {row['target_node_id']}
                if source:
                    nodes.add(source[0])
                busy = db.execute("SELECT j.target_node_id,r.node_id AS source FROM catalog_jobs j "
                                  "LEFT JOIN catalog_replicas r ON j.source_replica_id=r.replica_id WHERE j.state='RUNNING'").fetchall()
                if any(b['target_node_id'] in nodes or b['source'] in nodes for b in busy):
                    continue
                target = db.execute('SELECT token_version FROM nodes WHERE node_id=?', (row['target_node_id'],)).fetchone()
                generation = db.execute('SELECT n.token_version FROM nodes n JOIN catalog_replicas r USING(node_id) WHERE r.replica_id=?',
                                        (row['source_replica_id'],)).fetchone()
                token = uid()
                db.execute("UPDATE catalog_jobs SET state='RUNNING',attempts=attempts+1,run_token=?,lease_until=?,"
                           "target_generation=?,source_generation=?,updated_at=? WHERE job_id=?",
                           (token,now()+self.timeout,target[0] if target else -1,generation[0] if generation else None,now(),row['job_id']))
                self.catalog._history(db,row['job_id'],'RUNNING')
                job_id=row['job_id']
                break
            else:
                return None
        return self.get(job_id)

    def checkpoint(self, job, session_id, local_file_id):
        identifier(session_id);identifier(local_file_id)
        with self.registry.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            current = db.execute('SELECT * FROM catalog_jobs WHERE job_id=?',(job['job_id'],)).fetchone()
            if (not current or current['state']!='RUNNING' or current['run_token']!=job['run_token'] or
                    current['lease_until']<=now()):
                raise CatalogError('stale_job_lease',409)
            if current['target_local_file_id'] and (current['target_local_file_id'],current['target_session_id'])!=(local_file_id,session_id):
                raise CatalogError('job_object_conflict',409)
            db.execute('UPDATE catalog_jobs SET target_session_id=?,target_local_file_id=?,updated_at=? WHERE job_id=?',
                       (session_id,local_file_id,now(),job['job_id']))
        return self.get(job['job_id'])

    def upload_lease(self, job_id):
        with self.registry.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            job = db.execute('SELECT * FROM catalog_jobs WHERE job_id=?',(job_id,)).fetchone()
            if not job or job['kind']!='UPLOAD' or job['state'] not in ('PENDING','RETRY'):
                raise CatalogError('upload_state_conflict',409)
            target = db.execute('SELECT state,token_version FROM nodes WHERE node_id=?',(job['target_node_id'],)).fetchone()
            if not target or target['state']!='active':
                raise CatalogError('node_credential_changed',403)
            db.execute('UPDATE catalog_jobs SET run_token=?,lease_until=?,target_generation=?,updated_at=? WHERE job_id=?',
                       (uid(),now()+900,target['token_version'],now(),job_id))
        return self.get(job_id)

    def ack_upload(self, job_id, session_id, local_file_id):
        identifier(session_id);identifier(local_file_id)
        with self.registry.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            job = db.execute('SELECT * FROM catalog_jobs WHERE job_id=?',(identifier(job_id),)).fetchone()
            if not job or job['kind']!='UPLOAD':
                raise CatalogError('job_not_found',404)
            if job['target_local_file_id'] and (job['target_session_id'],job['target_local_file_id'])!=(session_id,local_file_id):
                raise CatalogError('job_object_conflict',409)
            db.execute('UPDATE catalog_jobs SET target_session_id=?,target_local_file_id=?,next_attempt_at=? WHERE job_id=?',
                       (session_id,local_file_id,now(),job_id))
        return self.get(job_id)

    def failed_attempt(self, job, error):
        with self.registry.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT state,run_token,attempts FROM catalog_jobs WHERE job_id=?',(job['job_id'],)).fetchone()
            if not row or row['state']!='RUNNING' or row['run_token']!=job['run_token']:
                return
            state = 'FAILED' if row['attempts']>=self.max_attempts else 'RETRY'
            delay = min(300,2**min(row['attempts'],8))
            db.execute('UPDATE catalog_jobs SET state=?,last_error=?,next_attempt_at=?,run_token=NULL,lease_until=NULL,updated_at=? WHERE job_id=?',
                       (state,error,now()+delay,now(),job['job_id']))
            self.catalog._history(db,job['job_id'],state,error)

    def retry(self, job_id):
        with self.registry.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT * FROM catalog_jobs WHERE job_id=?',(identifier(job_id),)).fetchone()
            if not row or row['state'] not in ('FAILED','RETRY'):
                raise CatalogError('job_state_conflict',409)
            db.execute("UPDATE catalog_jobs SET state='RETRY',attempts=0,next_attempt_at=?,run_token=NULL,lease_until=NULL WHERE job_id=?",
                       (now(),job_id))
            self.catalog._history(db,job_id,'RETRY','owner_retry')
        return self.get(job_id)

    def source(self,job,replica_id):
        with self.registry.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            source=db.execute('SELECT r.*,n.token_version FROM catalog_replicas r JOIN nodes n USING(node_id) WHERE replica_id=?',
                              (identifier(replica_id),)).fetchone()
            if not source or source['file_id']!=job['file_id'] or source['state']!='VERIFIED':
                raise CatalogError('no_verified_source',503)
            result=db.execute('UPDATE catalog_jobs SET source_replica_id=?,source_generation=? WHERE job_id=? '
                              "AND state='RUNNING' AND run_token=? AND lease_until>?",
                              (replica_id,source['token_version'],job['job_id'],job['run_token'],now()))
            if result.rowcount!=1:raise CatalogError('stale_job_lease',409)
        return self.get(job['job_id'])
