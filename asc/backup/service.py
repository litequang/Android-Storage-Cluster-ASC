"""Quorum-committed backup scheduler and safe restore, reusing Catalog/Storage IO."""
import copy
import threading

from . import state
from ..catalog.common import CatalogError, POLICIES, digest, identifier, key, logical_path, now, uid
from ..catalog.placement import active_nodes, readable
from ..catalog.transport import source_stream
from ..client import ClientError
from ..storage.client import StorageClient


class Backups:
    def __init__(self, service):
        self.service, self.runtime = service, service.runtime
        self._tick = threading.Lock()
        self._last_retention = 0

    def _edit(self, action, obj, change, enable=False):
        """Prepare from a strong committed view; ACK only after existing Go CAS apply."""
        request = obj.get('request_id')
        if request is not None:
            key(request)
        intent = digest({'action': action, 'payload': obj})
        with self.runtime.lock, self.runtime.operation() as view:
            doc = copy.deepcopy(view['document'])
            if 'backup' not in doc:
                if not enable:
                    raise CatalogError('phase3a_not_enabled', 409)
                doc['backup'] = state.empty()
            backup = doc['backup']
            if request in backup['requests']:
                previous = backup['requests'][request]
                if previous['intent'] != intent:
                    raise CatalogError('request_id_conflict', 409)
                return copy.deepcopy(previous['result'])
            result = change(doc, backup, view)
            if request is not None:
                backup['requests'][request] = {'intent': intent, 'result': result}
            if doc == view['document']:
                return result
            doc['revision'] += 1
            self.runtime.commit(view, doc, 'backup-'+digest(request) if request else None, intent)
            return result

    def enable(self, obj):
        return self._edit('enable', obj, lambda d, b, v: {'enabled': True, 'backup_schema': 1}, enable=True)

    @staticmethod
    def _job(kind, stamp, snapshot_id=None, source=None, version=None, copies=2):
        return {'kind': kind, 'state': 'PENDING', 'snapshot_id': snapshot_id,
                'source_file_id': source, 'target_version': version, 'target_file_id': None,
                'copies': copies, 'cursor': 0, 'proofs': [], 'attempts': 0,
                'next_attempt_at': stamp, 'run_token': None, 'lease_until': None,
                'last_error': None, 'created_at': stamp, 'updated_at': stamp}

    def _snapshot(self, backup, view, stamp, retention, copies):
        state.integer(retention, 60, 315360000); state.integer(copies, 1, 3)
        snapshot_id, job_id = uid(), uid()
        backup['snapshots'][snapshot_id] = state.capture(view, backup, stamp, retention)
        backup['jobs'][job_id] = self._job('BACKUP', stamp, snapshot_id=snapshot_id, copies=copies)
        return {'snapshot_id': snapshot_id, 'job_id': job_id}

    def snapshot(self, obj):
        return self._edit('snapshot', obj, lambda d, b, v: self._snapshot(
            b, v, now(), obj.get('retention_seconds', 604800), obj.get('copies', 2)))

    @staticmethod
    def _source(doc, backup, file_id, snapshot_id=None):
        identifier(file_id)
        file = next((f for f in doc['catalog']['files'] if f['file_id'] == file_id), None)
        if file is None:
            raise CatalogError('file_not_found', 404)
        if snapshot_id is not None:
            identifier(snapshot_id)
            snapshot = backup['snapshots'].get(snapshot_id)
            if not snapshot or snapshot['state'] == 'EXPIRED' or file_id not in {f['file_id'] for f in snapshot['files']}:
                raise CatalogError('snapshot_not_retained', 409)
        elif state.status(backup, file_id) == 'EXPIRED':
            raise CatalogError('version_expired', 409)
        return file

    def _restore_job(self, doc, backup, file, stamp):
        path = file['logical_path']
        versions = [f['version'] for f in doc['catalog']['files'] if f['logical_path'] == path]
        versions += [j['target_version'] for j in backup['jobs'].values() if j['kind'] == 'RESTORE' and
                     next(f for f in doc['catalog']['files'] if f['file_id'] == j['source_file_id'])['logical_path'] == path]
        version = max(versions, default=0) + 1
        state.integer(version, 1, 1000000)
        job_id = uid()
        backup['jobs'][job_id] = self._job('RESTORE', stamp, source=file['file_id'], version=version, copies=1)
        return {'job_id': job_id, 'target_version': version}

    def restore(self, obj):
        def change(doc, backup, view):
            file = self._source(doc, backup, obj['file_id'], obj.get('snapshot_id'))
            return self._restore_job(doc, backup, file, now())
        return self._edit('restore', obj, change)

    def restore_snapshot(self, snapshot_id, obj):
        identifier(snapshot_id)
        def change(doc, backup, view):
            snapshot = backup['snapshots'].get(snapshot_id)
            if not snapshot or snapshot['state'] == 'EXPIRED':
                raise CatalogError('snapshot_not_retained', 409)
            return {'jobs': [self._restore_job(doc, backup, self._source(doc, backup, f['file_id'], snapshot_id), now())
                             for f in snapshot['files']]}
        return self._edit('restore_snapshot', {**obj, 'snapshot_id': snapshot_id}, change)

    def delete(self, obj):
        file_id = identifier(obj['file_id'])
        def change(doc, backup, view):
            self._source(doc, backup, file_id)
            file = next(f for f in doc['catalog']['files'] if f['file_id'] == file_id)
            stamp = now()
            if state.status(backup, file_id) == 'LIVE':
                seconds = backup['policies'].get(file['logical_path'], {}).get('trash_seconds', 604800)
                backup['files'][file_id] = {'state': 'TRASH', 'changed_at': stamp, 'retain_until': stamp + seconds}
            return {'file_id': file_id, 'state': state.status(backup, file_id)}
        return self._edit('delete', obj, change)

    def policy(self, obj):
        path = logical_path(obj['logical_path'])
        row = {k: obj[k] for k in ('keep_last', 'max_age_seconds', 'trash_seconds')}
        state.integer(row['keep_last'], 1, 256)
        state.integer(row['max_age_seconds'], 60, 315360000)
        state.integer(row['trash_seconds'], 60, 315360000)
        def change(doc, backup, view):
            backup['policies'][path] = row
            return {'logical_path': path, 'policy': row}
        return self._edit('retention_policy', obj, change)

    def retention(self, obj):
        def change(doc, backup, view):
            stamp, expired = now(), []
            active_snapshots = {j['snapshot_id'] for j in backup['jobs'].values() if j['kind'] == 'BACKUP' and j['state'] not in ('COMPLETED', 'FAILED')}
            for snapshot_id, snapshot in backup['snapshots'].items():
                if snapshot['retain_until'] <= stamp and snapshot_id not in active_snapshots:
                    snapshot['state'] = 'EXPIRED'
            pins = state.pinned(backup)
            verified = {r['file_id'] for r in doc['catalog']['replicas'] if r['state'] == 'VERIFIED'}
            latest = {f['file_id'] for f in state.heads(doc['catalog'])}
            latest.update(f['file_id'] for f in state.heads({'files': [f for f in doc['catalog']['files'] if f['file_id'] in verified]}))
            for file in doc['catalog']['files']:
                file_id = file['file_id']
                if file_id in pins or state.status(backup, file_id) == 'EXPIRED':
                    continue
                row = backup['files'].get(file_id)
                expire = row and row['state'] == 'TRASH' and row['retain_until'] <= stamp
                policy = backup['policies'].get(file['logical_path'])
                if not row and policy and file_id not in latest:
                    newer = sum(f['file_id'] in verified and f['logical_path'] == file['logical_path'] and f['version'] > file['version'] for f in doc['catalog']['files'])
                    expire = newer >= policy['keep_last'] and file['created_at'] + policy['max_age_seconds'] <= stamp
                if expire:
                    backup['files'][file_id] = {'state': 'EXPIRED', 'changed_at': stamp, 'retain_until': stamp}
                    expired.append(file_id)
            return {'expired_versions': expired, 'physical_deletions': 0}
        return self._edit('retention_run', obj, change)

    def schedule(self, obj):
        state.integer(obj['interval_seconds'], 60, 86400)
        state.integer(obj.get('retention_seconds', 604800), 60, 315360000)
        state.integer(obj.get('copies', 2), 1, 3)
        def change(doc, backup, view):
            schedule_id = uid()
            backup['schedules'][schedule_id] = {'interval_seconds': obj['interval_seconds'],
                'retention_seconds': obj.get('retention_seconds', 604800), 'copies': obj.get('copies', 2),
                'next_run_at': now(), 'enabled': True, 'last_error': None}
            return {'schedule_id': schedule_id}
        return self._edit('schedule', obj, change)

    def configure_schedule(self, schedule_id, obj):
        identifier(schedule_id)
        if type(obj['enabled']) is not bool:
            raise ValueError()
        def change(doc, backup, view):
            if schedule_id not in backup['schedules']:
                raise CatalogError('schedule_not_found', 404)
            backup['schedules'][schedule_id]['enabled'] = obj['enabled']
            return {'schedule_id': schedule_id, 'enabled': obj['enabled']}
        return self._edit('configure_schedule', {**obj, 'schedule_id': schedule_id}, change)

    def retry(self, job_id, obj):
        identifier(job_id)
        def change(doc, backup, view):
            job = backup['jobs'].get(job_id)
            if not job or job['state'] not in ('FAILED', 'RETRY'):
                raise CatalogError('backup_job_state_conflict', 409)
            if job['kind'] == 'BACKUP' and backup['snapshots'][job['snapshot_id']]['state'] == 'EXPIRED':
                raise CatalogError('snapshot_not_retained', 409)
            if job['kind'] == 'RESTORE' and state.status(backup, job['source_file_id']) == 'EXPIRED':
                raise CatalogError('version_expired', 409)
            job.update(state='RETRY', attempts=0, cursor=0, proofs=[], next_attempt_at=0,
                       run_token=None, lease_until=None, last_error=None)
            return {'job_id': job_id}
        return self._edit('retry', {**obj, 'job_id': job_id}, change)

    def inspect(self, kind, path=None):
        view = self.runtime.view()
        backup = view['document'].get('backup')
        if backup is None:
            return {'enabled': False}
        if kind == 'history':
            logical_path(path)
            files = sorted((f for f in view['document']['catalog']['files'] if f['logical_path'] == path), key=lambda f: f['version'], reverse=True)
            pins = state.pinned(backup)
            return {'versions': [{'file': {k: v for k, v in f.items() if k not in ('upload_key', 'upload_policy')},
                                  'state': state.status(backup, f['file_id']), 'pinned': f['file_id'] in pins} for f in files]}
        if kind == 'trash':
            return {'trash': {f: r for f, r in backup['files'].items() if r['state'] == 'TRASH'}}
        if kind == 'jobs':
            return {'jobs': {j: {k: v for k, v in row.items() if k not in ('run_token', 'lease_until')}
                             for j, row in backup['jobs'].items()}}
        if kind in ('snapshots', 'schedules', 'policies'):
            return {kind: copy.deepcopy(backup[kind])}
        return {'enabled': True, 'backup_schema': 1, 'physical_gc': False,
                'counts': {k: len(backup[k]) for k in state.LIMITS}}

    def _scheduled(self):
        def change(doc, backup, view):
            stamp = now()
            for schedule in backup['schedules'].values():
                if schedule['enabled'] and schedule['next_run_at'] <= stamp:
                    if (len(backup['snapshots']) >= state.LIMITS['snapshots'] or
                            len(backup['jobs']) >= state.LIMITS['jobs']):
                        schedule.update(next_run_at=stamp+schedule['interval_seconds'], last_error='backup_limit')
                        return {'deferred': True}
                    try:
                        result = self._snapshot(backup, view, stamp, schedule['retention_seconds'], schedule['copies'])
                    except CatalogError as exc:
                        if exc.code != 'snapshot_unverified_head':
                            raise
                        schedule.update(next_run_at=stamp+60, last_error='snapshot_unverified_head')
                        return {'deferred': True}
                    schedule.update(next_run_at=stamp+schedule['interval_seconds'], last_error=None)
                    return result
            return {}
        return self._edit('scheduler', {}, change)

    def _claim(self, job_id=None):
        def change(doc, backup, view):
            stamp = now()
            for jid, job in backup['jobs'].items():
                if job_id is not None and jid != job_id:
                    continue
                if job['state'] == 'RUNNING' and job['lease_until'] <= stamp:
                    job.update(state='RETRY', run_token=None, lease_until=None, cursor=0,
                               proofs=[], next_attempt_at=stamp, last_error='lease_expired')
                if job['state'] in ('PENDING', 'RETRY') and job['next_attempt_at'] <= stamp:
                    job.update(state='RUNNING', run_token=uid(), lease_until=stamp + self.service.timeout, updated_at=stamp)
                    return {'job_id': jid, **copy.deepcopy(job)}
            return {}
        return self._edit('claim', {}, change)

    def _checkpoint(self, job, update):
        def change(doc, backup, view):
            current = backup['jobs'][job['job_id']]
            if current['state'] != 'RUNNING' or current['run_token'] != job['run_token'] or current['lease_until'] <= now():
                raise CatalogError('stale_backup_lease', 409)
            current.update(update, updated_at=now(), run_token=None, lease_until=None)
            if current['state'] == 'COMPLETED' and job['kind'] == 'BACKUP':
                backup['snapshots'][job['snapshot_id']].update(state='VERIFIED', verified_at=now())
            return {'job_id': job['job_id'], 'state': current['state']}
        return self._edit('checkpoint', {}, change)

    def _verify(self, file_id, copies=1):
        entry = self.service.catalog.file(file_id)
        with self.service.registry.connect() as db:
            nodes = {n['node_id']: n for n in active_nodes(db)}
        domains, source = [], None
        for replica in entry['replicas']:
            node = nodes.get(replica['node_id'])
            if replica['state'] != 'VERIFIED' or not node or not readable(node, replica['volume_id']) or node['device_id'] in domains:
                continue
            try:
                client = self.service._client(replica['node_id'], replica['volume_id'], 'audit', replica['local_file_id'])
                self.service._proof(client, replica['local_file_id'], replica['volume_id'],
                    '_asc-global/'+file_id+'/'+replica['replica_id'], entry['file'])
                domains.append(node['device_id'])
                source = source or (client, replica)
                if len(domains) >= copies:
                    return {'file_id': file_id, 'sha256': entry['file']['sha256'], 'size': entry['file']['size'],
                            'domains': domains, 'verified_at': now()}, source
            except (OSError, ValueError, CatalogError, ClientError) as exc:
                self.service._bad_replica(replica, exc)
        raise CatalogError('backup_unavailable', 503)

    def _backup(self, job):
        view = self.runtime.view()
        snapshot = view['document']['backup']['snapshots'][job['snapshot_id']]
        if job['cursor'] == len(snapshot['files']):
            return self._checkpoint(job, {'state': 'COMPLETED', 'last_error': None})
        file_id = snapshot['files'][job['cursor']]['file_id']
        entry = self.service.catalog.file(file_id)
        if POLICIES[entry['file']['policy']] < job['copies']:
            self.service.catalog.mutate('POLICY', {'file_id': file_id, 'policy': {1: 'single', 2: 'replicated_2', 3: 'replicated_3'}[job['copies']]})
        self.service.catalog.schedule(file_id)
        # Waiting for ordinary durable COPY jobs is not a failed physical read.
        if entry['available_replicas'] < job['copies']:
            return self._checkpoint(job, {'state': 'RETRY', 'next_attempt_at': now()+2, 'last_error': 'copies_pending'})
        proof, _ = self._verify(file_id, job['copies'])
        return self._checkpoint(job, {'state': 'RETRY', 'cursor': job['cursor']+1,
                                     'proofs': job['proofs']+[proof], 'next_attempt_at': 0, 'last_error': None})

    def _restore(self, job):
        view = self.runtime.view()
        file = next(f for f in view['document']['catalog']['files'] if f['file_id'] == job['source_file_id'])
        plan = self.service.upload_plan({'idempotency_key': 'restore-'+job['job_id'], 'logical_path': file['logical_path'],
            'size': file['size'], 'sha256': file['sha256'], 'policy': file['policy'], 'version': job['target_version']})
        target_file = plan['file']['file']['file_id']
        if not plan['completed']:
            target = plan['target']
            client = StorageClient(target['origin'], target['pin'], target['grant'], target['volume_id'], timeout=self.service.timeout)
            session = client.initiate(plan['idempotency_key'], plan['local_logical_path'], file['size'], file['sha256'])
            if session['state'] == 'NEEDS_REVIEW':
                client.commit(session['session_id']); session['state'] = 'COMMITTED'
            if session['state'] not in ('READY', 'COMMITTED'):
                _, (source, replica) = self._verify(file['file_id'])
                with source_stream(source, replica['local_file_id'], file['size'], file['sha256'], self.service.rate,
                                   job['lease_until']) as reader:
                    client.upload(session['session_id'], reader, file['size'])
            if session['state'] != 'COMMITTED':
                client.commit(session['session_id'])
            result = self.service.confirm_upload(plan['job_id'], session['session_id'], session['file_id'])
            if result['job_state'] != 'COMPLETED':
                return self._checkpoint(job, {'state': 'RETRY', 'next_attempt_at': now()+2, 'target_file_id': target_file,
                                             'last_error': 'copies_pending'})
        proof, _ = self._verify(target_file)
        return self._checkpoint(job, {'state': 'COMPLETED', 'target_file_id': target_file, 'proofs': [proof], 'last_error': None})

    def tick(self, job_id=None):
        if not self._tick.acquire(blocking=False):
            return {'busy': True}
        job = None
        try:
            if 'backup' not in self.runtime.view()['document']:
                return None
            with self.runtime.operation():
                if now()-self._last_retention >= 60:
                    self.retention({})
                    self._last_retention = now()
                self._scheduled()
                job = self._claim(job_id)
                if not job:
                    return None
                self.service.refresh()
                return self._backup(job) if job['kind'] == 'BACKUP' else self._restore(job)
        except (CatalogError, ClientError, OSError, ValueError):
            if job:
                attempts = job['attempts']+1
                return self._checkpoint(job, {'state': 'FAILED' if attempts >= 5 else 'RETRY', 'attempts': attempts,
                    'next_attempt_at': now()+min(300, 2**attempts),
                    'last_error': 'backup_unavailable' if job['kind'] == 'BACKUP' else 'restore_unavailable'})
            raise
        finally:
            self._tick.release()
