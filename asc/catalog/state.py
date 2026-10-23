"""Single catalog mutation boundary. No network caller can submit a verification proof."""
import json
import sqlite3
from .common import (CatalogError, POLICIES, ZERO, canonical, content, digest, identifier,
                     key, logical_path, now, policy, uid)
from .placement import active_nodes, candidates, eligible, readable


def insert(db, table, fields):
    columns = ','.join(fields)
    db.execute(f"INSERT INTO {table}({columns}) VALUES({','.join('?' for _ in fields)})", tuple(fields.values()))


class Catalog:
    def __init__(self, registry):
        self.registry = registry

    @staticmethod
    def _state(db):
        return dict(db.execute('SELECT * FROM catalog_state WHERE singleton=1').fetchone())

    @staticmethod
    def _file(db, file_id):
        row = db.execute('SELECT * FROM catalog_files WHERE file_id=?', (file_id,)).fetchone()
        if row is None:
            raise CatalogError('file_not_found', 404)
        fields = ('file_id','logical_path','version','size','sha256','policy','created_at','updated_at','revision')
        return {field: row[field] for field in fields}

    def _aggregate(self, db, file_id):
        return {'file': self._file(db, file_id),
                'replicas': [dict(r) for r in db.execute(
                    'SELECT * FROM catalog_replicas WHERE file_id=? ORDER BY replica_id', (file_id,))]}

    def _event(self, db, file_id):
        state, stamp = self._state(db), now()
        revision = state['revision'] + 1
        db.execute('UPDATE catalog_files SET revision=?,updated_at=? WHERE file_id=?', (revision, stamp, file_id))
        payload = self._aggregate(db, file_id)
        event = {'epoch': state['epoch'], 'revision': revision,
                 'previous_digest': state['head_digest'], 'payload': payload, 'created_at': stamp}
        event_hash = digest(event)
        insert(db, 'catalog_events', {**event, 'payload': canonical(payload).decode(), 'digest': event_hash})
        db.execute('UPDATE catalog_state SET revision=?,head_digest=? WHERE singleton=1', (revision, event_hash))
        db.execute('DELETE FROM catalog_events WHERE revision<=?', (revision - 1024,))

    @staticmethod
    def _history(db, job_id, state, error=None):
        insert(db, 'catalog_job_history', {'job_id': job_id, 'state': state, 'error': error, 'created_at': now()})

    def _new_job(self, db, file_id, target, kind='COPY', source=None):
        if db.execute('SELECT COUNT(*) FROM catalog_jobs').fetchone()[0] >= 2048:
            raise CatalogError('job_limit', 409)
        job_id, replica_id, stamp = uid(), uid(), now()
        insert(db, 'catalog_jobs', {'job_id': job_id, 'file_id': file_id, 'replica_id': replica_id,
            'kind': kind, 'state': 'PENDING', 'idempotency_key': job_id,
            'source_replica_id': source, 'target_node_id': target['node_id'],
            'target_volume_id': target['volume_id'], 'logical_path': '_asc-global/' + file_id + '/' + replica_id,
            'next_attempt_at': stamp, 'created_at': stamp, 'updated_at': stamp})
        self._history(db, job_id, 'PENDING')
        return job_id

    def mutate(self, command, data):
        """Single-writer command boundary: transaction + materialization + ordered event; not a Raft apply."""
        if self.registry.consensus_enabled():
            raise CatalogError('consensus_required', 503)
        with self.registry.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            changed = True
            if command == 'CREATE':
                path, size, sha = logical_path(data['logical_path']), data['size'], data['sha256']
                content(size, sha); policy(data['policy']); key(data['idempotency_key'])
                version = data.get('version', 1)
                if type(version) is not int or not 1 <= version <= 1000000:
                    raise CatalogError('invalid_file_version', 400)
                old = db.execute('SELECT * FROM catalog_files WHERE upload_key=?', (data['idempotency_key'],)).fetchone()
                if old:
                    if (old['logical_path'],old['version'],old['size'],old['sha256'],old['upload_policy']) != (
                            path,version,size,sha,data['policy']):
                        raise CatalogError('idempotency_conflict', 409)
                    return self._aggregate(db, old['file_id'])
                if db.execute('SELECT COUNT(*) FROM catalog_files').fetchone()[0] >= 256:
                    raise CatalogError('catalog_limit', 409)
                targets = candidates(db, size)
                if not targets:
                    raise CatalogError('no_eligible_storage', 507)
                file_id, stamp = uid(), now()
                try:
                    insert(db, 'catalog_files', {'file_id':file_id,'logical_path':path,'version':version,'size':size,
                        'sha256':sha,'policy':data['policy'],'created_at':stamp,'updated_at':stamp,
                        'revision':0,'upload_key':data['idempotency_key'],'upload_policy':data['policy']})
                except sqlite3.IntegrityError:
                    raise CatalogError('logical_version_exists', 409) from None
                self._new_job(db, file_id, targets[0], 'UPLOAD')
            elif command == 'POLICY':
                file_id = identifier(data['file_id']); current = self._file(db, file_id)
                value = policy(data['policy'])
                changed = current['policy'] != value
                db.execute('UPDATE catalog_files SET policy=? WHERE file_id=?', (value, file_id))
            elif command == 'COMPLETE':
                job = db.execute('SELECT * FROM catalog_jobs WHERE job_id=?', (data['job_id'],)).fetchone()
                if not job:
                    raise CatalogError('job_not_found', 404)
                file_id, proof = job['file_id'], data['proof']
                file = self._file(db, file_id)
                if (proof.get('file_id') != job['target_local_file_id'] or proof.get('logical_path') != job['logical_path'] or
                        proof.get('volume_id') != job['target_volume_id'] or proof.get('state') != 'COMMITTED' or
                        proof.get('size') != file['size'] or proof.get('sha256') != file['sha256'] or
                        proof.get('physically_verified') is not True):
                    raise CatalogError('verification_required', 409)
                if job['state'] == 'COMPLETED':
                    return self._aggregate(db, file_id)
                if (job['state'] != 'RUNNING' or job['run_token'] != data['run_token'] or
                        job['lease_until'] <= now()):
                    raise CatalogError('stale_job_lease', 409)
                target = db.execute('SELECT * FROM nodes WHERE node_id=?', (job['target_node_id'],)).fetchone()
                approval=db.execute('SELECT * FROM catalog_nodes WHERE node_id=?',(job['target_node_id'],)).fetchone()
                if (not target or target['state'] != 'active' or target['token_version'] != job['target_generation'] or
                        json.loads(target['profile']).get('protected') is True or not approval or not approval['storage_allowed'] or
                        approval['approved_generation']!=target['token_version'] or
                        job['target_volume_id'] not in json.loads(approval['volume_ids'])):
                    raise CatalogError('node_credential_changed', 403)
                if job['source_replica_id']:
                    source = db.execute('SELECT n.* FROM nodes n JOIN catalog_replicas r USING(node_id) WHERE r.replica_id=?',
                                        (job['source_replica_id'],)).fetchone()
                    if not source or source['state'] != 'active' or source['token_version'] != job['source_generation']:
                        raise CatalogError('node_credential_changed', 403)
                stamp = now()
                insert(db, 'catalog_replicas', {'replica_id':job['replica_id'],'file_id':file_id,
                    'node_id':job['target_node_id'],'volume_id':job['target_volume_id'],
                    'local_file_id':job['target_local_file_id'],'state':'VERIFIED',
                    'created_at':stamp,'updated_at':stamp,'verified_at':stamp})
                db.execute("UPDATE catalog_jobs SET state='COMPLETED',updated_at=?,last_error=NULL WHERE job_id=?",
                           (stamp, job['job_id']))
                self._history(db, job['job_id'], 'COMPLETED')
            elif command == 'REPLICA_STATE':
                row = db.execute('SELECT * FROM catalog_replicas WHERE replica_id=?', (data['replica_id'],)).fetchone()
                if not row:
                    raise CatalogError('replica_not_found', 404)
                file_id, value = row['file_id'], data['state']
                if value not in ('MISSING','CORRUPT','UNAVAILABLE','METADATA_CONFLICT'):
                    raise CatalogError('verification_required', 409)
                changed = row['state'] != value
                if changed:
                    db.execute('UPDATE catalog_replicas SET state=?,updated_at=? WHERE replica_id=?',
                               (value, now(), row['replica_id']))
            elif command == 'REVERIFY':
                row = db.execute('SELECT * FROM catalog_replicas WHERE replica_id=?', (data['replica_id'],)).fetchone()
                if not row or data.get('physically_verified') is not True:
                    raise CatalogError('verification_required', 409)
                file_id = row['file_id']
                db.execute("UPDATE catalog_replicas SET state='VERIFIED',updated_at=?,verified_at=? WHERE replica_id=?",
                           (now(), now(), row['replica_id']))
            else:
                raise CatalogError('unknown_catalog_command', 400)
            if changed:
                self._event(db, file_id)
            return self._aggregate(db, file_id)

    def file(self, file_id):
        identifier(file_id)
        with self.registry.connect() as db:
            db.execute('BEGIN')
            result = self._aggregate(db, file_id)
            nodes = {n['node_id']: n for n in active_nodes(db)}
        verified, available = set(), set()
        for replica in result['replicas']:
            node = nodes.get(replica['node_id'])
            if replica['state'] != 'VERIFIED' or not node:
                continue
            verified.add(node['device_id'])
            volumes = json.loads(node['capabilities'] or '{}').get('volumes', [])
            if eligible(node) and any(v.get('volume_id') == replica['volume_id'] and v.get('state') == 'online'
                                      and v.get('readable') is True for v in volumes):
                available.add(node['device_id'])
        desired = POLICIES[result['file']['policy']]
        result.update(desired_replicas=desired, verified_replicas=len(verified), available_replicas=len(available),
                      state='UPLOADING' if not result['replicas'] else 'UNDER_REPLICATED' if len(verified)<desired else 'REPLICATED',
                      availability='AVAILABLE' if available else 'UNAVAILABLE',
                      protection='SATISFIED' if len(available)>=desired else 'DEGRADED')
        return result

    def files(self, offset=0):
        if type(offset) is not int or not 0 <= offset <= 10000:
            raise CatalogError('invalid_offset', 400)
        with self.registry.connect() as db:
            ids = [r[0] for r in db.execute('SELECT file_id FROM catalog_files ORDER BY created_at,file_id LIMIT 51 OFFSET ?', (offset,))]
        return {'files':[self.file(i) for i in ids[:50]],'next_offset':offset+50 if len(ids)>50 else None}

    def schedule(self, file_id):
        """Persistent repair scheduling; pending jobs reserve target/device capacity."""
        identifier(file_id)
        with self.registry.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            file = self._file(db, file_id)
            nodes = {n['node_id']: n for n in active_nodes(db)}
            rows = db.execute("SELECT * FROM catalog_replicas WHERE file_id=? AND state='VERIFIED'", (file_id,)).fetchall()
            sources = [r for r in rows if r['node_id'] in nodes and readable(nodes[r['node_id']],r['volume_id'])]
            if not sources:
                return []
            occupied = {nodes[r['node_id']]['device_id'] for r in rows if r['node_id'] in nodes}
            available = {nodes[r['node_id']]['device_id'] for r in sources}
            pending = db.execute("SELECT target_node_id FROM catalog_jobs WHERE file_id=? AND state IN ('PENDING','RUNNING','RETRY')",
                                 (file_id,)).fetchall()
            planned = {nodes[r[0]]['device_id'] for r in pending if r[0] in nodes}
            failed=db.execute("SELECT target_node_id FROM catalog_jobs WHERE file_id=? AND state='FAILED'",(file_id,)).fetchall()
            blocked={nodes[r[0]]['device_id'] for r in failed if r[0] in nodes}
            needed = max(0, POLICIES[file['policy']] - len(available | planned))
            jobs=[]
            for target in candidates(db, file['size'], occupied | planned | blocked):
                if needed <= 0:
                    break
                if target['device_id'] in planned:
                    continue
                jobs.append(self._new_job(db, file_id, target, source=sources[0]['replica_id']))
                planned.add(target['device_id']); needed -= 1
            return jobs
