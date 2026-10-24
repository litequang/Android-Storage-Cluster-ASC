"""Node-local storage fault injection. All state stays under TemporaryDirectory."""
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
import uuid
from unittest import mock
from asc.storage.engine import StorageEngine
from asc.storage.errors import StorageError
from asc.storage.manifest import Manifest
from asc.storage.volumes import LocalVolume


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.engine = StorageEngine(self.base / 'private', 'node-test')
        self.addCleanup(lambda: self.engine.close())
        self.volume = self.engine.volumes.register(self.base / 'data', quota=1024**2, reserve=0)['volume_id']
        self.data = b'ASC storage\x00' * 1000
        self.digest = hashlib.sha256(self.data).hexdigest()

    def initiate(self, key='request_0001', path='folder/test.bin', size=None, digest=None):
        return self.engine.initiate('owner', self.volume, key, path,
                                    len(self.data) if size is None else size, digest or self.digest)

    def ready(self, **kw):
        row = self.initiate(**kw)
        self.engine.upload(row['session_id'], 'owner', self.volume, io.BytesIO(self.data), len(self.data))
        return row

    def committed(self):
        row = self.ready()
        return self.engine.commit(row['session_id'], 'owner', self.volume)

    def assert_code(self, code, call):
        with self.assertRaises(StorageError) as caught:
            call()
        self.assertEqual(caught.exception.code, code)

    def test_stream_commit_idempotency_restart_and_sqlite_release(self):
        row = self.ready()
        self.assertEqual(self.initiate()['session_id'], row['session_id'])
        self.assertEqual(self.engine.list_files(self.volume)['files'], [])
        file = self.engine.commit(row['session_id'], 'owner', self.volume)
        self.assertEqual(self.engine.commit(row['session_id'], 'owner', self.volume)['file_id'], file['file_id'])
        self.engine.close()
        self.engine = StorageEngine(self.base / 'private', 'node-test')
        with self.engine.download(file['file_id'], self.volume) as (metadata, stream):
            self.assertEqual(stream.read(), self.data)
            self.assertEqual(metadata['sha256'], self.digest)
        self.assertEqual(self.engine.verify(file['file_id'], self.volume)['state'], 'COMMITTED')
        self.engine.close()
        path = self.base / 'private' / 'manifest.sqlite3'
        moved = path.with_suffix('.closed')
        path.rename(moved); moved.unlink()

    def test_fenced_job_resume_requires_fresh_authority_and_two_matching_retained_bodies(self):
        principal = 'job:'+str(uuid.uuid4())
        def revoked():
            raise StorageError('forbidden', 403)
        for index in range(2):
            row = self.engine.initiate(principal, self.volume, 'fenced_job_'+str(index), 'recovery/'+str(index), len(self.data), self.digest)
            self.engine.upload(row['session_id'], principal, self.volume, io.BytesIO(self.data), len(self.data))
            self.assert_code('forbidden', lambda: self.engine.commit(row['session_id'], principal, self.volume, revoked))
            self.assert_code('session_not_ready', lambda: self.engine.commit(row['session_id'], principal, self.volume))
            final = self.base/'data'/'objects'/(row['file_id']+'.blob')
            staging = self.base/'data'/'staging'/(row['session_id']+'.part')
            self.assertEqual(final.read_bytes(), self.data)
            self.assertEqual(staging.read_bytes(), self.data)
            if index == 0:
                self.assert_code('forbidden', lambda: self.engine.commit(row['session_id'], principal, self.volume, revoked, resume_verified=True))
                self.assertEqual(self.engine.session(row['session_id'], principal, self.volume)['state'], 'NEEDS_REVIEW')
                proof = self.engine.commit(row['session_id'], principal, self.volume, lambda: None, resume_verified=True)
                self.assertEqual(proof['file_id'], row['file_id'])
                self.assertEqual(final.read_bytes(), self.data)
            else:
                final.write_bytes(b'X'+self.data[1:])
                self.assert_code('object_requires_review', lambda: self.engine.commit(row['session_id'], principal, self.volume, lambda: None, resume_verified=True))
                self.assertEqual(self.engine.session(row['session_id'], principal, self.volume)['state'], 'NEEDS_REVIEW')
                self.assertTrue(final.exists()); self.assertTrue(staging.exists())

    def test_conflicting_requests_and_bounded_concurrency(self):
        row = self.initiate()
        self.assert_code('idempotency_conflict', lambda: self.initiate(path='other'))
        self.assert_code('logical_path_exists', lambda: self.initiate(key='request_0002'))
        with self.engine.transfer():
            self.assert_code('storage_busy', lambda: self.engine.upload(row['session_id'], 'owner', self.volume, io.BytesIO(self.data), len(self.data)))
        self.assert_code('forbidden', lambda: self.engine.session(row['session_id'], 'another', self.volume))

    def test_disconnect_restart_full_body_retry_and_wrong_checksum(self):
        row = self.initiate()
        self.assert_code('upload_interrupted', lambda: self.engine.upload(row['session_id'], 'owner', self.volume, io.BytesIO(self.data[:100]), len(self.data)))
        self.assertEqual(self.engine.session(row['session_id'], 'owner', self.volume)['state'], 'INTERRUPTED')
        with self.engine.manifest.connect() as db:
            db.execute("UPDATE uploads SET state='WRITING'")
        self.engine.close()
        self.engine = StorageEngine(self.base / 'private', 'node-test')
        self.assertEqual(self.engine.session(row['session_id'], 'owner', self.volume)['state'], 'INTERRUPTED')
        self.assert_code('checksum_mismatch', lambda: self.engine.upload(row['session_id'], 'owner', self.volume, io.BytesIO(b'x' * len(self.data)), len(self.data)))
        self.engine.upload(row['session_id'], 'owner', self.volume, io.BytesIO(self.data), len(self.data))
        self.engine.upload(row['session_id'], 'owner', self.volume, io.BytesIO(self.data), len(self.data))
        self.engine.commit(row['session_id'], 'owner', self.volume)

    def test_quota_disk_full_and_fsync_failure_do_not_publish(self):
        self.assert_code('quota_exceeded', lambda: self.initiate(size=600000))
        row = self.initiate()
        with mock.patch('asc.storage.engine.os.fsync', side_effect=OSError(28, 'injected full disk')):
            with self.assertRaises(OSError):
                self.engine.upload(row['session_id'], 'owner', self.volume, io.BytesIO(self.data), len(self.data))
        self.assertEqual(self.engine.list_files(self.volume)['files'], [])
        self.assertEqual(self.engine.session(row['session_id'], 'owner', self.volume)['state'], 'INTERRUPTED')
        with mock.patch('shutil.disk_usage', return_value=type('Disk', (), {'free': 0})()):
            self.assert_code('insufficient_space', lambda: self.initiate(key='request_0002', path='other'))

    def test_revoke_during_commit_preserves_copies_without_visibility(self):
        row = self.ready()
        def revoked():
            raise StorageError('forbidden', 403)
        self.assert_code('forbidden', lambda: self.engine.commit(row['session_id'], 'owner', self.volume, revoked))
        self.assertEqual(self.engine.list_files(self.volume)['files'], [])
        self.assertTrue((self.base / 'data' / 'objects' / (row['file_id'] + '.blob')).exists())
        self.assertEqual(self.engine.session(row['session_id'], 'owner', self.volume)['state'], 'NEEDS_REVIEW')

    def test_crash_after_final_copy_requires_explicit_reauthorized_commit(self):
        row = self.ready()
        volume = self.engine.volumes.get(self.volume)
        with volume.open(self.engine._object(row), create=True) as out:
            out.write(self.data)
        self.engine._state(row['session_id'], 'COMMITTING')
        self.engine.close()
        self.engine = StorageEngine(self.base / 'private', 'node-test')
        self.assertEqual(self.engine.list_files(self.volume)['files'], [])
        self.assertEqual(self.engine.session(row['session_id'], 'owner', self.volume)['state'], 'READY')
        self.engine.commit(row['session_id'], 'owner', self.volume)

    def test_integrity_metadata_conflict_and_missing_copy_are_preserved(self):
        file = self.committed()
        physical = self.base / 'data' / file['relative_path']
        physical.write_bytes(b'corrupt')
        self.assertEqual(self.engine.verify(file['file_id'], self.volume)['state'], 'CORRUPT')
        self.assert_code('checksum_mismatch', lambda: self._download(file))
        self.assertTrue(physical.exists())
        with self.engine.manifest.connect() as db:
            db.execute("UPDATE files SET relative_path='../outside'")
        self.assert_code('metadata_conflict', lambda: self.engine.file(file['file_id'], self.volume))
        self.engine.recover()
        with self.engine.manifest.connect() as db:
            self.assertEqual(db.execute('SELECT state FROM files').fetchone()[0], 'METADATA_CONFLICT')
        self.assertTrue(physical.exists())

    def _download(self, file):
        with self.engine.download(file['file_id'], self.volume):
            pass

    def test_removed_or_replaced_medium_fails_closed(self):
        root = self.base / 'data'
        removed = self.base / 'removed'
        root.rename(removed)
        self.assert_code('volume_unavailable', lambda: self.initiate())
        root.mkdir()
        (root / '.asc-volume.json').write_text((removed / '.asc-volume.json').read_text())
        (root / 'staging').mkdir(); (root / 'objects').mkdir()
        self.assert_code('volume_identity_changed', lambda: self.initiate())
        self.assertEqual(self.engine.volumes.inspect()[0]['state'], 'unavailable')

    def test_path_traversal_hardlink_escape_and_staging_expiry(self):
        for path in ('../a', '/a', 'a\\b', 'a//b', 'a/%2e', 'C:foo', 'a/..', 'a.'):
            with self.subTest(path=path):
                self.assert_code('invalid_logical_path', lambda: self.initiate(path=path))
        row = self.initiate()
        outside = self.base / 'keep.bin'; outside.write_bytes(b'keep')
        stage = self.base / 'data' / self.engine._stage(row)
        os.link(outside, stage)
        self.assert_code('unsafe_path', lambda: self.engine.volumes.get(self.volume).open(self.engine._stage(row)).__enter__())
        self.assertEqual(outside.read_bytes(), b'keep')
        stage.unlink()
        self.ready()
        with self.engine.manifest.connect() as db:
            db.execute('UPDATE uploads SET updated_at=1')
        self.assertFalse(self.engine.cleanup(60)[0]['removed'])
        self.assertTrue(self.engine.cleanup(60, dry_run=False)[0]['removed'])
        self.assertEqual(outside.read_bytes(), b'keep')

    def test_probe_schema_identity_and_future_version_rejection(self):
        report = self.engine.capabilities()
        self.assertEqual(report['recommended_storage_role'], 'Storage')
        self.assertTrue(report['volumes'][0]['writable'])
        self.assertTrue(report['volumes'][0]['fsync_tested'])
        self.assertNotIn('root', report['volumes'][0])
        with self.assertRaises(ValueError):
            Manifest(self.base / 'private' / 'manifest.sqlite3', 'different-node')
        with self.engine.manifest.connect() as db:
            db.execute('PRAGMA user_version=99')
        with self.assertRaises(ValueError):
            Manifest(self.base / 'private' / 'manifest.sqlite3', 'node-test')

    def test_junction_or_symlink_escape_is_rejected(self):
        outside = self.base / 'outside'; outside.mkdir()
        sentinel = outside / 'keep'; sentinel.write_bytes(b'keep')
        root = self.base / 'data'
        (root / 'staging').rmdir()
        if os.name == 'nt':
            import subprocess
            result = subprocess.run(['cmd.exe', '/c', 'mklink', '/J', str(root / 'staging'), str(outside)],
                                    capture_output=True)
            self.assertEqual(result.returncode, 0, 'local junction fixture must be created')
            self.addCleanup(lambda: os.rmdir(root / 'staging'))
        else:
            (root / 'staging').symlink_to(outside, target_is_directory=True)
        self.assert_code('unsafe_path', lambda: self.initiate())
        self.assertEqual(sentinel.read_bytes(), b'keep')

    def test_orphans_retained_staging_and_future_reservations_count_toward_quota(self):
        row = self.ready()
        volume = self.engine.volumes.get(self.volume)
        orphan = 'objects/' + 'a' * 32 + '.blob'
        with volume.open(orphan, create=True) as stream:
            stream.write(b'x' * 10000)
        usage = self.engine._quota_usage(volume)
        self.assertEqual(usage, 2 * len(self.data) + 10000)
        with mock.patch.object(LocalVolume, 'remove_staging', side_effect=OSError('injected cleanup failure')):
            self.engine.commit(row['session_id'], 'owner', self.volume)
        self.assertEqual(self.engine._quota_usage(volume), 2 * len(self.data) + 10000)
        inventory = self.engine.inventory()[0]
        self.assertIn(orphan.split('/')[1], [r['name'] for r in inventory['unreferenced_objects']])
        self.assertTrue((self.base / 'data' / orphan).exists())

    def test_missing_file_is_reported_without_deleting_manifest_or_other_data(self):
        file = self.committed()
        (self.base / 'data' / file['relative_path']).unlink()  # Inject media data loss.
        self.engine.recover()
        self.assertEqual(self.engine.file(file['file_id'], self.volume)['state'], 'MISSING')
        self.assertEqual(len(self.engine.list_files(self.volume)['files']), 1)

    def test_read_only_probe_reports_measured_denial_and_advisory_backup(self):
        with mock.patch.object(LocalVolume, 'open', side_effect=PermissionError(13, 'injected read-only')):
            report = self.engine.capabilities()
        volume = report['volumes'][0]
        self.assertTrue(volume['readable'])
        self.assertFalse(volume['writable'])
        self.assertIsNone(volume['fsync_tested'])
        self.assertEqual(report['recommended_storage_role'], 'Backup')
        self.assertEqual(volume['last_error'], 'write_denied')

    def test_http_body_deadline_stops_a_trickling_peer(self):
        from asc.storage.http import UploadBody
        stream = io.BufferedReader(io.BytesIO(b'body'))
        body = UploadBody(stream, 0)
        body.deadline = -1
        self.assert_code('upload_deadline', lambda: body.read(4))

    def test_unknown_probe_and_unapproved_roots_fail_closed(self):
        with mock.patch('asc.storage.volumes.shutil.disk_usage', side_effect=OSError('unavailable')):
            report = self.engine.volumes.inspect(probe=True)[0]
        self.assertIsNone(report['free_bytes'])
        self.assertIsNone(report['writable'])
        self.assert_code('unsafe_storage_root', lambda: self.engine.volumes.register(self.base / 'x' / '..' / 'outside'))
        self.assert_code('unapproved_sd_root', lambda: self.engine.volumes.register(self.base / 'unapproved', kind='termux_sd'))
        with self.assertRaises(ValueError):
            StorageEngine(self.base / 'another', 'node', bytes_per_second=0)


if __name__ == '__main__':
    unittest.main()
