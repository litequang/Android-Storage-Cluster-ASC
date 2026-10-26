"""Immutable node-local objects, bounded streaming and conservative crash recovery."""
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import re
import sqlite3
import stat
import threading
import time
import uuid
from .errors import StorageError
from .manifest import Manifest, existing_identity
from .volumes import CHUNK, VolumeManager, identifier, logical_path, no_links
from ..identity import ensure_private_home
from ..runtime import foreground_lock


class StorageEngine:
    def __init__(self, home, node_id, max_upload=64 * 1024**2, bytes_per_second=8 * 1024**2,
                 *, existing_only=False, manifest_identity=None):
        if type(max_upload) is not int or not 1 <= max_upload <= 1024**3:
            raise ValueError('invalid upload limit')
        if type(bytes_per_second) is not int or not 1 <= bytes_per_second <= 64 * 1024**2:
            raise ValueError('invalid transfer rate')
        if type(existing_only) is not bool or not existing_only and manifest_identity is not None:
            raise ValueError('invalid storage open mode')
        if existing_only:
            self.home = Path(home)
            if os.name != 'posix' or not self.home.is_absolute() or '..' in self.home.parts:
                raise ValueError('existing private storage provider not qualified')
            source = Path(__file__).resolve().parents[2]
            shared = (Path('/storage'), Path('/sdcard'), Path('/mnt/media_rw'))
            if (self.home == source or source in self.home.parents or
                    any(self.home == root or root in self.home.parents for root in shared)):
                raise ValueError('private storage outside source/shared roots required')
            no_links(self.home)
            info = self.home.lstat()
            if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
                raise ValueError('private existing storage required')
            # BEFORE a lifecycle lock or Engine can create any path.
            manifest_identity = existing_identity(self.home / 'manifest.sqlite3', manifest_identity)
        else:
            self.home = ensure_private_home(home)
        self.node_id, self.max_upload, self.rate = node_id, max_upload, bytes_per_second
        self._owner = foreground_lock(self.home, 'storage-engine')
        self._owner.__enter__()
        self._closed = False
        self._mutex = threading.RLock()
        self._transfer = threading.BoundedSemaphore(1)
        try:
            self.manifest = Manifest(self.home / 'manifest.sqlite3', node_id,
                                     existing_only=existing_only, expected_file=manifest_identity)
            self.volumes = VolumeManager(self.manifest, node_id)
            self.recover()
        except BaseException:
            self.close()
            raise

    def close(self):
        if not self._closed:
            self._closed = True
            self._owner.__exit__(None, None, None)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    @contextmanager
    def transfer(self):
        if self._closed:
            raise StorageError('storage_stopped', 503)
        if not self._transfer.acquire(blocking=False):
            raise StorageError('storage_busy', 429)
        try:
            with self._mutex:
                yield
        finally:
            self._transfer.release()

    def _pace(self, count, started):
        delay = count / self.rate - (time.monotonic() - started)
        if delay > 0:
            time.sleep(min(delay, CHUNK / self.rate))

    def _hash(self, stream):
        digest, size, started = hashlib.sha256(), 0, time.monotonic()
        while True:
            chunk = stream.read(CHUNK)
            if not chunk:
                return size, digest.hexdigest()
            digest.update(chunk); size += len(chunk)
            self._pace(size, started)

    @staticmethod
    def _stage(row):
        return 'staging/' + identifier(row['session_id']) + '.part'

    @staticmethod
    def _object(row):
        return 'objects/' + identifier(row['file_id']) + '.blob'

    def session(self, session_id, principal, volume_id):
        identifier(session_id)
        with self.manifest.connect() as db:
            row = db.execute('SELECT * FROM uploads WHERE session_id=?', (session_id,)).fetchone()
        if row is None:
            raise StorageError('session_not_found', 404)
        if row['principal'] != principal or row['volume_id'] != volume_id:
            raise StorageError('forbidden', 403)
        return dict(row)

    def _state(self, session_id, state):
        with self.manifest.connect() as db:
            db.execute('UPDATE uploads SET state=?,updated_at=? WHERE session_id=?',
                       (state, int(time.time()), session_id))

    def _space(self, volume, required):
        volume.check()
        import shutil
        try:
            free = volume.disk_usage().free
        except OSError:
            raise StorageError('volume_unavailable', 503) from None
        if free - volume.record['reserve'] < required:
            raise StorageError('insufficient_space', 507)

    def _quota_usage(self, volume):
        physical = volume.allocated_files()
        charge = 0
        with self.manifest.connect() as db:
            uploads = db.execute('SELECT * FROM uploads WHERE volume_id=?', (volume.record['volume_id'],)).fetchall()
            files = db.execute('SELECT * FROM files WHERE volume_id=?', (volume.record['volume_id'],)).fetchall()
        for row in uploads:
            if row['state'] not in ('COMMITTED', 'EXPIRED'):
                present = physical.pop(self._stage(row), 0) + physical.pop(self._object(row), 0)
                charge += max(row['size'] * 2, present)
        for row in files:
            charge += max(row['size'], physical.pop(self._object(row), 0))
        return charge + sum(physical.values())  # Orphans and retained committed staging stay charged.

    def initiate(self, principal, volume_id, key, path, size, sha256):
        logical_path(path)
        if not isinstance(principal, str) or not 1 <= len(principal) <= 64:
            raise StorageError('invalid_principal', 400)
        if not isinstance(key, str) or not re.fullmatch(r'[A-Za-z0-9_-]{8,128}', key):
            raise StorageError('invalid_idempotency_key', 400)
        if type(size) is not int or not 0 <= size <= self.max_upload:
            raise StorageError('upload_too_large', 413)
        if not isinstance(sha256, str) or not re.fullmatch(r'[a-f0-9]{64}', sha256):
            raise StorageError('invalid_sha256', 400)
        with self._mutex:
            volume = self.volumes.get(volume_id)
            volume.check()
            with self.manifest.connect() as db:
                db.execute('BEGIN IMMEDIATE')
                old = db.execute('SELECT * FROM uploads WHERE principal=? AND idempotency_key=?',
                                 (principal, key)).fetchone()
                if old:
                    if (old['volume_id'], old['logical_path'], old['size'], old['sha256']) != (volume_id, path, size, sha256):
                        raise StorageError('idempotency_conflict', 409)
                    return dict(old)
                if (db.execute("SELECT COUNT(*) FROM uploads WHERE state NOT IN ('EXPIRED','COMMITTED')").fetchone()[0] >= 128 or
                        db.execute('SELECT COUNT(*) FROM files').fetchone()[0] >= 10000):
                    raise StorageError('manifest_limit', 409)
                # Reserve a full staging + final copy until commit (portable on exFAT).
                usage = self._quota_usage(volume)
                if usage + size * 2 > volume.record['quota']:
                    raise StorageError('quota_exceeded', 507)
                self._space(volume, size * 2)
                now, session_id, file_id = int(time.time()), str(uuid.uuid4()), str(uuid.uuid4())
                try:
                    db.execute('''INSERT INTO uploads(session_id,file_id,principal,idempotency_key,logical_path,
                        volume_id,size,sha256,state,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)''',
                        (session_id, file_id, principal, key, path, volume_id, size, sha256, 'INITIATED', now, now))
                except sqlite3.IntegrityError:
                    raise StorageError('logical_path_exists', 409) from None
        return self.session(session_id, principal, volume_id)

    def upload(self, session_id, principal, volume_id, source, length):
        with self.transfer():
            row = self.session(session_id, principal, volume_id)
            if type(length) is not int or length != row['size']:
                raise StorageError('size_mismatch', 400)
            if row['state'] in ('COMMITTED', 'EXPIRED', 'NEEDS_REVIEW', 'COMMITTING'):
                raise StorageError('session_state_conflict', 409)
            volume = self.volumes.get(volume_id)
            self._space(volume, row['size'] * 2)
            if row['state'] == 'READY':
                # Duplicate body is verified, but the existing staging file is never truncated.
                size, digest, started = 0, hashlib.sha256(), time.monotonic()
                while size < length:
                    chunk = source.read(min(CHUNK, length - size))
                    if not chunk:
                        raise StorageError('upload_interrupted', 400)
                    digest.update(chunk); size += len(chunk); self._pace(size, started)
                if digest.hexdigest() != row['sha256']:
                    raise StorageError('checksum_mismatch', 422)
                return row
            volume.remove_staging(self._stage(row))
            self._state(session_id, 'WRITING')
            count, digest, started = 0, hashlib.sha256(), time.monotonic()
            try:
                with volume.open(self._stage(row), create=True) as output:
                    while count < length:
                        chunk = source.read(min(CHUNK, length - count))
                        if not chunk:
                            raise StorageError('upload_interrupted', 400)
                        output.write(chunk); digest.update(chunk); count += len(chunk)
                        self._pace(count, started)
                    output.flush(); os.fsync(output.fileno())
                volume.check()
                if digest.hexdigest() != row['sha256']:
                    self._state(session_id, 'FAILED')
                    raise StorageError('checksum_mismatch', 422)
                self._state(session_id, 'READY')
            except BaseException:
                current = self.session(session_id, principal, volume_id)
                if current['state'] == 'WRITING':
                    self._state(session_id, 'INTERRUPTED')
                raise
        return self.session(session_id, principal, volume_id)

    def _verified(self, volume, relative, row):
        with volume.open(relative) as stream:
            size, digest = self._hash(stream)
        return size == row['size'] and digest == row['sha256']

    def commit(self, session_id, principal, volume_id, reauthorize=None, *, resume_verified=False):
        with self.transfer():
            row = self.session(session_id, principal, volume_id)
            volume = self.volumes.get(volume_id)
            volume.check()
            if row['state'] == 'COMMITTED':
                return self.file(row['file_id'], volume_id)
            if row['state'] == 'NEEDS_REVIEW' and resume_verified and reauthorize is not None and principal.startswith('job:'):
                # Distributed failover may revoke authority after a complete
                # immutable copy. Only a freshly scoped job can resume the SAME
                # session, after independently rehashing BOTH retained bodies.
                # Missing/mismatched/unknown bodies remain held, never deleted.
                try:
                    matched = self._verified(volume, self._stage(row), row) and self._verified(volume, self._object(row), row)
                except (OSError, StorageError):
                    matched = False
                if not matched:
                    raise StorageError('object_requires_review', 409)
                reauthorize()
                self._state(session_id, 'READY')
                row['state'] = 'READY'
            if row['state'] != 'READY':
                raise StorageError('session_not_ready', 409)
            if not self._verified(volume, self._stage(row), row):
                self._state(session_id, 'NEEDS_REVIEW')
                raise StorageError('checksum_mismatch', 422)
            self._space(volume, row['size'])
            self._state(session_id, 'COMMITTING')
            try:
                try:
                    with volume.open(self._object(row), create=True) as output:
                        with volume.open(self._stage(row)) as source:
                            count, started = 0, time.monotonic()
                            while True:
                                chunk = source.read(CHUNK)
                                if not chunk:
                                    break
                                output.write(chunk); count += len(chunk); self._pace(count, started)
                        output.flush(); os.fsync(output.fileno())
                except FileExistsError:
                    # Crash after exclusive creation: only adopt a fully matching object.
                    pass
                if not self._verified(volume, self._object(row), row):
                    raise StorageError('object_conflict', 409)
                volume.sync_directory('objects')
                if reauthorize is not None:
                    reauthorize()  # Fail closed if grant/node was revoked while copying.
                now = int(time.time())
                with self.manifest.connect() as db:
                    db.execute('BEGIN IMMEDIATE')
                    db.execute('INSERT INTO files VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                               (row['file_id'], row['logical_path'], volume_id, self._object(row),
                                row['size'], row['sha256'], row['version'], 'COMMITTED',
                                now, now, now))
                    db.execute("UPDATE uploads SET state='COMMITTED',updated_at=? WHERE session_id=?",
                               (now, session_id))
            except BaseException:
                self._state(session_id, 'NEEDS_REVIEW')
                raise
            # A committed copy is never deleted. Cleanup failure retains extra staging.
            try:
                volume.remove_staging(self._stage(row))
            except (OSError, StorageError):
                pass
        return self.file(row['file_id'], volume_id)

    def file(self, file_id, volume_id):
        identifier(file_id)
        with self.manifest.connect() as db:
            row = db.execute('SELECT * FROM files WHERE file_id=?', (file_id,)).fetchone()
            upload = db.execute('SELECT * FROM uploads WHERE file_id=?', (file_id,)).fetchone()
        if row is None:
            raise StorageError('file_not_found', 404)
        row = dict(row)
        if row['volume_id'] != volume_id:
            raise StorageError('forbidden', 403)
        if (not upload or row['relative_path'] != self._object(row) or
                any(row[key] != upload[key] for key in ('volume_id', 'size', 'sha256', 'version', 'logical_path'))):
            raise StorageError('metadata_conflict', 409)
        return row

    def verify(self, file_id, volume_id):
        with self._mutex:
            row = self.file(file_id, volume_id)
            volume = self.volumes.get(volume_id)
            state, error = 'COMMITTED', None
            try:
                if not self._verified(volume, self._object(row), row):
                    state, error = 'CORRUPT', 'checksum_mismatch'
            except FileNotFoundError:
                state, error = 'MISSING', 'file_missing'
            except (OSError, StorageError) as exc:
                state, error = 'VOLUME_UNAVAILABLE', getattr(exc, 'code', 'volume_io_error')
            now = int(time.time())
            with self.manifest.connect() as db:
                db.execute('UPDATE files SET state=?,updated_at=?,last_verified_at=? WHERE file_id=?',
                           (state, now, now if state == 'COMMITTED' else None, file_id))
            return {'file_id': file_id, 'state': state, 'error': error, 'verified_at': now if not error else None}

    @contextmanager
    def download(self, file_id, volume_id):
        with self.transfer():
            row = self.file(file_id, volume_id)
            volume = self.volumes.get(volume_id)
            with volume.open(self._object(row)) as stream:
                size, digest = self._hash(stream)
                if (size, digest) != (row['size'], row['sha256']):
                    self.verify(file_id, volume_id)
                    raise StorageError('checksum_mismatch', 422)
                stream.seek(0)
                yield row, stream

    def list_files(self, volume_id, offset=0):
        self.volumes.get(volume_id).check()
        if type(offset) is not int or not 0 <= offset <= 1000000:
            raise StorageError('invalid_offset', 400)
        with self.manifest.connect() as db:
            rows = db.execute('SELECT * FROM files WHERE volume_id=? ORDER BY created_at,file_id LIMIT 201 OFFSET ?',
                              (volume_id, offset)).fetchall()
        return {'files': [dict(r) for r in rows[:200]], 'next_offset': offset + 200 if len(rows) > 200 else None}

    def recover(self):
        """Never publish an incomplete/uncommitted object automatically after a crash."""
        with self._mutex:
            with self.manifest.connect() as db:
                db.execute("UPDATE uploads SET state='INTERRUPTED' WHERE state='WRITING'")
                rows = db.execute("SELECT * FROM uploads WHERE state='COMMITTING'").fetchall()
            for row in rows:
                try:
                    volume = self.volumes.get(row['volume_id'])
                    valid = self._verified(volume, self._stage(row), row) and self._verified(volume, self._object(row), row)
                    self._state(row['session_id'], 'READY' if valid else 'NEEDS_REVIEW')
                except (OSError, StorageError):
                    self._state(row['session_id'], 'NEEDS_REVIEW')
            with self.manifest.connect() as db:
                files = db.execute('SELECT file_id,volume_id FROM files').fetchall()
            for row in files:
                try:
                    self.verify(row['file_id'], row['volume_id'])
                except StorageError:
                    # Metadata conflicts require operator attention; do not invent a repair.
                    with self.manifest.connect() as db:
                        db.execute("UPDATE files SET state='METADATA_CONFLICT',last_verified_at=NULL WHERE file_id=?",
                                   (row['file_id'],))

    def cleanup(self, older_than=86400, dry_run=True):
        if type(older_than) is not int or older_than < 60:
            raise StorageError('invalid_expiry', 400)
        with self._mutex:
            with self.manifest.connect() as db:
                rows = db.execute("SELECT * FROM uploads WHERE state IN ('INITIATED','INTERRUPTED','FAILED','READY') AND updated_at<?",
                                  (int(time.time()) - older_than,)).fetchall()
            result = []
            for row in rows:
                item = {'session_id': row['session_id'], 'removed': False}
                if not dry_run:
                    # Generated staging path only. Objects/last verified copies are never GC'd.
                    try:
                        volume = self.volumes.get(row['volume_id'])
                        # A final object means a crash/metadata issue; preserve both copies.
                        try:
                            with volume.open(self._object(row)):
                                item['error'] = 'object_requires_review'
                                result.append(item); continue
                        except FileNotFoundError:
                            pass
                        volume.remove_staging(self._stage(row))
                        self._state(row['session_id'], 'EXPIRED')
                        item['removed'] = True
                    except (OSError, StorageError):
                        item['error'] = 'volume_unavailable'
                result.append(item)
            return result

    def capabilities(self, probe=True):
        volumes = self.volumes.inspect(probe=probe)
        writable = any(v['writable'] is True and v['state'] == 'online' for v in volumes)
        readable = any(v['readable'] is True and v['state'] == 'online' for v in volumes)
        return {'storage_version': 1, 'manifest_schema': 1, 'volumes': volumes,
                'recommended_storage_role': 'Storage' if writable else 'Backup' if readable else 'Metadata-only',
                'max_upload_bytes': self.max_upload, 'max_concurrent_transfers': 1,
                'bytes_per_second': self.rate, 'resumable_upload': False}

    def inventory(self, limit=1000, volume_id=None):
        """Bounded local audit. Unreferenced objects are reported, never adopted/deleted."""
        result = []
        for record in self.volumes.records():
            if volume_id is not None and record['volume_id']!=volume_id:
                continue
            item = {'volume_id': record['volume_id'], 'unreferenced_objects': [], 'truncated': False}
            try:
                volume = self.volumes.get(record['volume_id'])
                volume.check()
                with self.manifest.connect() as db:
                    known = {row[0] for row in db.execute('SELECT relative_path FROM files WHERE volume_id=?',
                                                        (record['volume_id'],))}
                    pending = {self._object(row) for row in db.execute('SELECT * FROM uploads WHERE volume_id=?',
                                                                      (record['volume_id'],))}
                # Scandir does not follow child symlinks; names alone are diagnostic.
                with volume.entries('objects') as entries:
                    for index, entry in enumerate(entries):
                        if index >= limit:
                            item['truncated'] = True
                            break
                        relative = 'objects/' + entry.name
                        if relative not in known:
                            item['unreferenced_objects'].append(
                                {'name': entry.name, 'pending_session': relative in pending})
            except (OSError, StorageError):
                item['error'] = 'volume_unavailable'
            result.append(item)
        return result

    def placement_status(self, volume_id):
        with self._mutex:
            volume=self.volumes.get(volume_id)
            rows=self.volumes.inspect(probe=True,volume_id=volume_id)
            for row in rows:
                try:
                    row['used_bytes']=self._quota_usage(volume)
                except (OSError,StorageError):
                    row.update(used_bytes=None,state='unavailable',last_error='usage_unavailable')
            return {'node_id':self.node_id,'storage_version':1,'volumes':rows,
                    'max_upload_bytes':self.max_upload,'bytes_per_second':self.rate,
                    'max_concurrent_transfers':1,'external_load':None}

    def reconciliation_inventory(self,volume_id,offset=0):
        result=self.list_files(volume_id,offset)
        with self.manifest.connect() as db:
            for row in result['files']:
                upload=db.execute('SELECT session_id,principal,idempotency_key FROM uploads WHERE file_id=?',(row['file_id'],)).fetchone()
                row['upload']=dict(upload) if upload else None
        result['objects']=self.inventory(volume_id=volume_id) if offset==0 else []
        return result
