"""Actual private POSIX I/O; missing metadata must never become a new manifest."""
import hashlib
from contextlib import closing
import io
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from asc.storage.engine import StorageEngine
from asc.storage.errors import StorageError
from asc.storage.manifest import Manifest, existing_identity


@unittest.skipUnless(os.name == 'posix', 'existing-only private metadata provider is POSIX-only')
class ExistingStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.home = self.root / 'metadata'; self.data = self.root / 'volume'
        self.actor = 'existing-storage-contract'; self.body = bytes(range(256)) * 512
        self.sha = hashlib.sha256(self.body).hexdigest()
        with StorageEngine(self.home, self.actor) as engine:
            self.volume = engine.volumes.register(self.data, quota=1024**2, reserve=0)['volume_id']
            row = engine.initiate('fixture-owner', self.volume, 'existing_storage_1', 'old/file.bin', len(self.body), self.sha)
            engine.upload(row['session_id'], 'fixture-owner', self.volume, io.BytesIO(self.body), len(self.body))
            self.saved = engine.commit(row['session_id'], 'fixture-owner', self.volume)
        self.path = self.home / 'manifest.sqlite3'; self.identity = existing_identity(self.path)
        self.marker = (self.data / '.asc-volume.json').read_bytes()

    def reopen(self, **kwargs):
        return StorageEngine(self.home, self.actor, existing_only=True, manifest_identity=self.identity, **kwargs)

    def test_existing_bytes_ids_sha_and_marker_survive_actual_reopen(self):
        with self.reopen() as engine:
            self.assertEqual(engine.manifest.expected_file, self.identity)
            self.assertEqual(engine.volumes.get(self.volume).record['node_id'], self.actor)
            with engine.download(self.saved['file_id'], self.volume) as (metadata, stream):
                self.assertEqual(stream.read(), self.body); self.assertEqual(metadata['sha256'], self.sha)
            self.assertEqual(engine.verify(self.saved['file_id'], self.volume)['state'], 'COMMITTED')
        self.assertEqual(self.marker, (self.data / '.asc-volume.json').read_bytes())
        self.assertEqual(existing_identity(self.path), self.identity)

    def test_missing_manifest_home_or_expected_identity_never_create_or_adopt(self):
        missing = self.root / 'missing'
        with self.assertRaises((OSError, ValueError)):
            StorageEngine(missing, self.actor, existing_only=True)
        self.assertFalse(missing.exists())
        held = self.home / 'held.sqlite3'; self.path.rename(held)
        before = set(p.name for p in self.home.iterdir())
        with self.assertRaises((OSError, ValueError)): self.reopen()
        self.assertFalse(self.path.exists()); self.assertEqual(before, set(p.name for p in self.home.iterdir()))
        held.rename(self.path)
        with self.assertRaises(ValueError):
            StorageEngine(self.home, self.actor, existing_only=True, manifest_identity=[0, 0])
        self.assertEqual(self.marker, (self.data / '.asc-volume.json').read_bytes())

    def test_replaced_manifest_symlink_and_hardlink_refuse_without_modifying_target(self):
        original = self.home / 'original.sqlite3'; self.path.rename(original)
        target = self.root / 'other.sqlite3'; shutil.copy2(original, target)
        before = target.read_bytes()
        self.path.symlink_to(target)
        with self.assertRaises(StorageError) as result: self.reopen()
        self.assertEqual(result.exception.code, 'unsafe_path')
        self.assertEqual(before, target.read_bytes()); self.path.unlink()
        os.link(target, self.path)
        with self.assertRaises(ValueError): self.reopen()
        self.assertEqual(before, target.read_bytes()); self.path.unlink()
        shutil.copy2(original, self.path)
        with self.assertRaises(ValueError): self.reopen()  # Valid schema, different inode still refuses.
        self.assertEqual(before, target.read_bytes())

    def test_empty_future_schema_or_missing_identity_are_never_initialized(self):
        for fault in ('empty', 'future', 'missing-node', 'missing-index', 'missing-table'):
            with self.subTest(fault=fault):
                folder = self.root / fault; folder.mkdir(mode=0o700)
                path = folder / 'manifest.sqlite3'
                if fault == 'empty': path.touch()
                else:
                    shutil.copy2(self.path, path)
                    with closing(sqlite3.connect(path)) as db, db:
                        if fault == 'future': db.execute('PRAGMA user_version=99')
                        if fault == 'missing-node': db.execute("DELETE FROM settings WHERE key='node_id'")
                        if fault == 'missing-index': db.execute('DROP INDEX upload_path')
                        if fault == 'missing-table': db.execute('DROP TABLE uploads')
                before = path.read_bytes()
                with self.assertRaises((sqlite3.Error, ValueError)):
                    Manifest(path, self.actor, existing_only=True)
                self.assertEqual(before, path.read_bytes())
                self.assertEqual(self.marker, (self.data / '.asc-volume.json').read_bytes())

    def test_wrong_actor_cannot_insert_identity_or_access_existing_bytes(self):
        before = self.path.read_bytes()
        with self.assertRaises(ValueError):
            StorageEngine(self.home, 'another-actor', existing_only=True)
        self.assertEqual(before, self.path.read_bytes())
        self.assertEqual(self.marker, (self.data / '.asc-volume.json').read_bytes())

    def test_mode_rw_refuses_delete_between_check_and_connect_or_after_open(self):
        transport = sqlite3.connect; held = self.home / 'race-held.sqlite3'
        def delete_before_open(path, *args, **kwargs):
            self.path.rename(held)
            return transport(path, *args, **kwargs)
        with patch('asc.storage.manifest.sqlite3.connect', side_effect=delete_before_open):
            with self.assertRaises(sqlite3.OperationalError):
                Manifest(self.path, self.actor, existing_only=True, expected_file=self.identity)
        self.assertFalse(self.path.exists()); held.rename(self.path)
        manifest = Manifest(self.path, self.actor, existing_only=True, expected_file=self.identity)
        self.path.rename(held)
        with self.assertRaises(OSError):
            with manifest.connect(): self.fail('must not yield a recreated metadata connection')
        self.assertFalse(self.path.exists()); self.assertEqual(existing_identity(held), self.identity)

    def test_schema_validation_accepts_legacy_ddl_whitespace_without_rewriting(self):
        # Canonical format1 DDL used to be indented inside __init__; execute the
        # SAME statements via trace as a fixture with additional whitespace.
        statements = []
        db = sqlite3.connect(':memory:'); db.row_factory = sqlite3.Row
        db.set_trace_callback(statements.append)
        try: Manifest._initialize(db, self.actor)
        finally: db.close()
        path = self.root / 'legacy-whitespace.sqlite3'
        with closing(sqlite3.connect(path)) as legacy, legacy:
            for statement in statements:
                if statement.startswith(('BEGIN', 'SELECT')): continue
                legacy.execute(statement.replace('\n', '\n    '))
        before = path.read_bytes()
        Manifest(path, self.actor, existing_only=True)
        self.assertEqual(before, path.read_bytes())

    def test_unapproved_directory_mode_and_replacement_after_connect_refuse(self):
        os.chmod(self.home, 0o755)
        with self.assertRaises(ValueError): self.reopen()
        self.assertEqual(self.home.stat().st_mode & 0o777, 0o755)  # No chmod repair.
        os.chmod(self.home, 0o700)
        transport = sqlite3.connect; held = self.home / 'after-open-held.sqlite3'
        def replace_after_open(path, *args, **kwargs):
            db = transport(path, *args, **kwargs)
            self.path.rename(held); shutil.copy2(held, self.path)
            return db
        before = self.path.read_bytes()
        with patch('asc.storage.manifest.sqlite3.connect', side_effect=replace_after_open):
            with self.assertRaises(ValueError):
                Manifest(self.path, self.actor, existing_only=True, expected_file=self.identity)
        self.assertEqual(before, held.read_bytes()); self.assertEqual(before, self.path.read_bytes())
