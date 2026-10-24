"""Explicit terminal-job pointer release; immutable digest/history and replay remain."""
import json
from ..catalog.common import digest


def get(db,job_id):
    row=db.execute("SELECT value FROM settings WHERE key='phase3c_replication'").fetchone()
    archived=json.loads(row[0]).get('archived_jobs',{}) if row else {}
    record=archived.get(job_id)
    return {**record,'archived':True} if record else None


def completion(job):
    return digest({'session_id':job['target_session_id'],'local_file_id':job['target_local_file_id']})


def record(job,stamp):
    return {k:job[k] for k in ('job_id','file_id','kind','state','created_at','updated_at')}|{
        'archived_at':stamp,'original_sha256':digest(dict(job)),'completion_sha256':completion(job)}
