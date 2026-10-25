"""Android-like root-open denial; actual private Linux IO/faults, never Android PASS."""
from contextlib import contextmanager
import errno
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest import mock
from asc.storage.engine import StorageEngine
from asc.storage.errors import StorageError
from asc.storage.volumes import LocalVolume


@contextmanager
def deny_filesystem_root():
    original = os.open
    denied = []
    def opened(path, flags, mode=0o777, *, dir_fd=None):
        if dir_fd is None and os.fspath(path) == '/':
            denied.append('/')
            raise PermissionError(errno.EACCES, 'synthetic Android root denial')
        return original(path, flags, mode, dir_fd=dir_fd)
    with mock.patch('os.open', side_effect=opened):
        yield denied


@unittest.skipUnless(os.name == 'posix', 'POSIX/Android descriptor regression; Windows has its separate handle adapter')
class AndroidVolumeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.engine = StorageEngine(self.base / 'private', 'existing-node')
        self.addCleanup(lambda: self.engine.close())
        self.record = self.engine.volumes.register(self.base / 'app/data', 'internal', 1024**2, 0)
        self.volume = LocalVolume(self.record)
        self.root = self.volume.root
        self.marker = (self.root / '.asc-volume.json').read_bytes()
        self.data = b'Android root denied, private directory allowed\x00' * 128
        self.sha = hashlib.sha256(self.data).hexdigest()

    def test_root_open_denied_private_probe_rehash_fsync_cleanup_and_identity(self):
        keep = self.root / 'staging/keep.part'; keep.write_bytes(b'other pending bytes')
        with deny_filesystem_root() as attempts, mock.patch('os.fsync', wraps=os.fsync) as synced:
            report = self.engine.capabilities()
            row = report['volumes'][0]
            self.assertTrue(row['writable'], row)
            self.assertTrue(row['fsync_tested'], row)
            self.assertTrue(row['readable'])
            self.assertEqual(report['recommended_storage_role'], 'Storage')
            self.assertEqual(row['state'], 'online'); self.assertIsNone(row['last_error'])
            self.assertGreater(synced.call_count, 0)
            self.assertTrue(self.volume.sync_directory('staging'))
            with self.volume.open('staging/manual.probe', create=True) as stream:
                stream.write(self.data); stream.flush(); os.fsync(stream.fileno())
            with self.volume.open('staging/manual.probe') as stream:
                self.assertEqual(hashlib.sha256(stream.read()).hexdigest(), self.sha)
            self.volume.remove_staging('staging/manual.probe')
            self.assertEqual(attempts, [], 'Adapter must never attempt to open filesystem root')
        self.assertEqual(list((self.root / 'staging').iterdir()), [keep])
        self.assertEqual(keep.read_bytes(), b'other pending bytes')
        self.assertEqual((self.root / '.asc-volume.json').read_bytes(), self.marker)
        self.assertEqual(self.engine.volumes.records(), [self.record])

    def test_root_denial_actual_upload_commit_download_verify_and_restart(self):
        with deny_filesystem_root() as attempts:
            row = self.engine.initiate('owner', self.record['volume_id'], 'android_root_001', 'demo.bin', len(self.data), self.sha)
            self.engine.upload(row['session_id'], 'owner', self.record['volume_id'], io.BytesIO(self.data), len(self.data))
            file = self.engine.commit(row['session_id'], 'owner', self.record['volume_id'])
            self.assertEqual(self.engine.verify(file['file_id'], self.record['volume_id'])['state'], 'COMMITTED')
            self.engine.close(); self.engine = StorageEngine(self.base / 'private', 'existing-node')
            with self.engine.download(file['file_id'], self.record['volume_id']) as (metadata, stream):
                self.assertEqual(hashlib.sha256(stream.read()).hexdigest(), self.sha)
                self.assertEqual(metadata['sha256'], self.sha)
            self.assertEqual(attempts, [])
        self.assertEqual((self.root / '.asc-volume.json').read_bytes(), self.marker)
        self.assertEqual(self.engine.volumes.records(), [self.record])

    def test_real_private_staging_permission_denial_never_reports_writable(self):
        # Actual EACCES from the OS on this fixture-owned directory, not a fake probe.
        self.assertNotEqual(os.geteuid(), 0, 'Run this gate as an unprivileged test user')
        stage = self.root / 'staging'; stage.chmod(0o500)
        try:
            with self.assertRaises(PermissionError):
                fd = os.open(stage / 'permission.probe', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                os.close(fd)
            with deny_filesystem_root():
                row = self.engine.capabilities()['volumes'][0]
            self.assertTrue(row['readable']); self.assertFalse(row['writable'])
            self.assertIsNone(row['fsync_tested']); self.assertEqual(row['last_error'], 'write_denied')
            self.assertFalse((stage / 'permission.probe').exists())
        finally:
            stage.chmod(0o700)

    def swap_on_open(self, name, callback, operation):
        original = os.open; swapped = []
        def opened(path, flags, mode=0o777, *, dir_fd=None):
            if os.fspath(path) == name and not swapped:
                swapped.append(True); callback()
            return original(path, flags, mode, dir_fd=dir_fd)
        with mock.patch('os.open', side_effect=opened):
            with self.assertRaises((StorageError, OSError)):
                operation()
        self.assertTrue(swapped)

    def create_probe(self):
        with self.volume.open('staging/race.probe', create=True) as stream:
            stream.write(b'never outside approved volume')

    def test_symlink_swap_before_descriptor_open_never_touches_outside(self):
        outside = self.base / 'outside'; outside.mkdir(); keep = outside / 'race.probe'; keep.write_bytes(b'keep')
        stage = self.root / 'staging'
        def swap():
            stage.rename(self.root / 'old-staging'); stage.symlink_to(outside, target_is_directory=True)
        self.swap_on_open('staging', swap, self.create_probe)
        self.assertEqual(keep.read_bytes(), b'keep')
        self.assertEqual(list(outside.iterdir()), [keep])

    def test_real_directory_swap_before_open_is_not_adopted(self):
        stage = self.root / 'staging'
        def swap():
            stage.rename(self.root / 'old-staging'); stage.mkdir()
        self.swap_on_open('staging', swap, self.create_probe)
        self.assertEqual(list(stage.iterdir()), [])
        self.assertEqual(list((self.root / 'old-staging').iterdir()), [])

    def test_root_replacement_with_cloned_marker_fails_before_body_io(self):
        original_root = self.root.parent / 'original-root'
        def swap():
            self.root.rename(original_root); self.root.mkdir()
            (self.root / '.asc-volume.json').write_bytes(self.marker)
            (self.root / 'staging').mkdir(); (self.root / 'objects').mkdir()
        self.swap_on_open(str(self.root), swap, self.create_probe)
        self.assertEqual(list((self.root / 'staging').iterdir()), [])
        self.assertEqual(list((original_root / 'staging').iterdir()), [])
        self.assertNotEqual(f'{self.root.stat().st_dev}:{self.root.stat().st_ino}', self.record['medium'])

    def test_replacement_during_io_is_detected_before_success_and_preserves_both_roots(self):
        original = self.root.parent / 'original-root'
        with self.assertRaises(StorageError):
            with self.volume.open('staging/held.probe', create=True) as stream:
                self.root.rename(original); self.root.mkdir()
                (self.root / '.asc-volume.json').write_bytes(self.marker)
                (self.root / 'staging').mkdir(); (self.root / 'objects').mkdir()
                stream.write(self.data)
        self.assertEqual((original / 'staging/held.probe').read_bytes(), self.data)
        self.assertFalse((self.root / 'staging/held.probe').exists())

    def test_marker_mismatch_link_and_race_never_recreate_or_adopt_marker(self):
        marker = self.root / '.asc-volume.json'
        wrong = json.loads(self.marker); wrong['node_id'] = 'other-node'
        marker.write_text(json.dumps(wrong)); changed = marker.read_bytes()
        with self.assertRaises(StorageError): self.volume.check()
        self.assertEqual(marker.read_bytes(), changed)
        marker.write_bytes(self.marker)
        def swap():
            marker.rename(self.root / 'old-marker'); marker.write_bytes(self.marker)
        self.swap_on_open('.asc-volume.json', swap, self.volume.check)
        marker.unlink(); outside = self.base / 'outside-marker'; outside.write_bytes(self.marker); marker.symlink_to(outside)
        with self.assertRaises(StorageError): self.volume.check()
        self.assertTrue(marker.is_symlink()); self.assertEqual(outside.read_bytes(), self.marker)

    def test_cleanup_refuses_final_hardlinked_and_symlink_files_and_sync_traversal(self):
        outside = self.base / 'keep'; outside.write_bytes(b'keep')
        for relative in ('objects/x.blob', '../keep', 'staging/../keep'):
            with self.assertRaises(StorageError): self.volume.remove_staging(relative)
        for folder in ('../', '/', 'staging/../../outside'):
            with self.assertRaises(StorageError): self.volume.sync_directory(folder)
        stage = self.root / 'staging/race.probe'
        os.link(outside, stage)
        with self.assertRaises(StorageError): self.volume.remove_staging('staging/race.probe')
        self.assertTrue(stage.exists()); stage.unlink(); stage.symlink_to(outside)
        with self.assertRaises(StorageError): self.volume.remove_staging('staging/race.probe')
        self.assertTrue(stage.is_symlink()); self.assertEqual(outside.read_bytes(), b'keep')

    def test_missing_marker_is_not_reported_as_missing_body_or_recreated(self):
        marker = self.root / '.asc-volume.json'; marker.unlink()
        with self.assertRaises(StorageError) as held: self.volume.check()
        self.assertEqual(held.exception.code, 'volume_identity_changed')
        self.assertFalse(marker.exists())

    def test_probe_collision_or_replaced_regular_file_never_deletes_unowned_bytes(self):
        import uuid
        fixed = uuid.UUID('11111111-1111-4111-8111-111111111111')
        path = self.root / 'staging' / (str(fixed) + '.probe')
        path.write_bytes(b'existing staging must survive')
        with mock.patch('asc.storage.volumes.uuid.uuid4', return_value=fixed):
            row = self.engine.capabilities()['volumes'][0]
        self.assertIsNot(row['writable'], True)
        self.assertEqual(path.read_bytes(), b'existing staging must survive')
        original = path.stat(); identity = original.st_dev, original.st_ino
        path.rename(path.with_name('original.probe')); path.write_bytes(b'replacement must survive')
        with self.assertRaises(StorageError):
            self.volume.remove_staging('staging/' + path.name, expected_identity=identity)
        self.assertEqual(path.read_bytes(), b'replacement must survive')

    def test_missing_safe_posix_primitives_fail_closed_without_absolute_file_fallback(self):
        with mock.patch('asc.storage.volumes.POSIX_FD_SUPPORTED', False):
            with self.assertRaises(StorageError) as held: self.create_probe()
        self.assertEqual(held.exception.code, 'safe_volume_access_unavailable')
        self.assertFalse((self.root / 'staging/race.probe').exists())

    def test_probe_fsync_failure_never_reports_success(self):
        with mock.patch('os.fsync', side_effect=OSError(errno.EIO, 'test-owned fsync failure')):
            report = self.engine.capabilities()['volumes'][0]
        self.assertIsNot(report['writable'], True)
        self.assertIsNot(report['fsync_tested'], True)
        self.assertIsNotNone(report['last_error'])
        self.assertEqual(list((self.root / 'staging').iterdir()), [])


if __name__ == '__main__':
    unittest.main()
