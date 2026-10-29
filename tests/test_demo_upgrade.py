"""Installed final candidate, live TLS faults plus stopped upgrade/backup/recovery."""
import contextlib
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest
from unittest import mock
from asc.demo import package, upgrade
from asc.identity import replace_private
from tests import test_demo_lan as lan_fixtures


class DemoUpgradeTests(lan_fixtures.DemoLANTests):
    """Inherited LAN gates intentionally rerun through actual installed launchers."""
    def prefix_for(self, root):
        return self.home / (root.name + '-code')

    def command_result(self, root, *args, input=None):
        prefix = self.prefix_for(root)
        if not prefix.exists() and args[0] == 'init':
            installed = self.run_cli('install', '--prefix', str(prefix))
            if installed.returncode:
                return installed
        return subprocess.run(['sh', str(prefix / 'bin/asc-demo'), '--state', str(root), *args],
                              env=self.env, input=input, capture_output=True, text=True, timeout=45, cwd=self.root)

    def start(self, root, command):
        log = (self.root / ('installed-' + root.name + '-' + command)).open('w+')
        self.addCleanup(log.close)
        process = subprocess.Popen(['sh', str(self.prefix_for(root) / 'bin/asc-demo'), '--state', str(root), command],
                                   cwd=self.root, env=self.env, stdout=log, stderr=log, text=True)
        self.addCleanup(self.stop, process)
        return process

    def stop_all(self):
        for node in self.nodes:
            self.stop(node['process'])
        self.stop(self.controller_process)

    def candidate(self, name='candidate', **changes):
        target = self.root / name
        shutil.copytree(self.source, target)
        cli = target / 'asc/demo/cli.py'
        cli.write_bytes(cli.read_bytes() + b'\n# compatible synthetic patch candidate\n')
        manifest = json.loads((target / 'release.json').read_text())
        manifest['files']['asc/demo/cli.py'] = package.digest(cli.read_bytes())
        manifest.update(changes)
        body = {k: v for k, v in manifest.items() if k != 'release_id'}
        manifest['release_id'] = package.digest(package.encoded(body))
        (target / 'release.json').write_bytes(package.encoded(manifest))
        package.verify(target)
        return target, manifest['release_id']

    def identity_bytes(self, root):
        names = ('demo.json', 'controller/controller.json', 'controller/server.crt', 'controller/server.key',
                 'node/node.json', 'node/storage.json', 'node/storage.crt', 'node/storage.key', 'node/data/.asc-volume.json')
        return {name: (root / name).read_bytes() for name in names if (root / name).exists()}

    def test_installed_upgrade_rollback_preserves_files_ids_certs_pins_and_private_backup(self):
        entry = self.upload()
        prefix = self.prefix_for(self.controller)
        original_id = json.loads((prefix / 'install.json').read_text())['release_id']
        identity = self.identity_bytes(self.controller)
        # A source reinstall verifies bytes, while private identities and running agent survive.
        repeated = self.run_cli('install', '--prefix', str(prefix))
        self.assertEqual(repeated.returncode, 0, repeated.stderr)
        self.assertEqual(self.identity_bytes(self.controller), identity)
        source, release_id = self.candidate()
        staged = self.command(self.controller, 'stage', str(source))
        self.assertEqual(staged['release_id'], release_id)
        self.command(self.controller, 'upgrade-preflight', release_id)
        blocked = self.command_result(self.controller, 'upgrade', release_id, '--backup', str(self.home / 'running-backup'))
        self.assertNotEqual(blocked.returncode, 0)
        self.assertFalse((self.home / 'running-backup').exists())
        self.assertEqual(json.loads((prefix / 'install.json').read_text())['release_id'], original_id)
        self.stop_all()
        backup = self.home / 'before-upgrade'
        result = self.command(self.controller, 'upgrade', release_id, '--backup', str(backup))
        self.assertTrue(result['identity_preserved'])
        self.assertEqual(self.identity_bytes(self.controller), identity)
        self.assertEqual(json.loads((prefix / 'install.json').read_text())['release_id'], release_id)
        self.command(self.controller, 'verify-backup', str(backup))
        for path in backup.rglob('*'):
            if path.is_file():
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        saved = backup / 'state/node/data/objects'
        self.assertTrue((backup / 'state/node/data/staging').is_dir())
        self.assertEqual(len(list(saved.glob('*.blob'))), 1)
        self.assertEqual(hashlib.sha256(next(saved.glob('*.blob')).read_bytes()).hexdigest(), hashlib.sha256(self.data).hexdigest())
        self.command(self.controller, 'rollback', original_id, '--backup', str(self.home / 'before-rollback'))
        self.assertEqual(self.identity_bytes(self.controller), identity)
        self.assertEqual(json.loads((prefix / 'install.json').read_text())['release_id'], original_id)
        self.controller_process = self.start(self.controller, 'run-controller')
        from asc.client import request_json
        self.wait_for(lambda: request_json(self.origin, self.pin, 'GET', '/api/v1/info'))
        for node in self.nodes:
            node['process'] = self.start(node['root'], 'run-node')
        self.wait_for(lambda: self.command(self.controller, 'replicas', entry['file']['file_id'])['available_replicas'] == 2)
        output = self.home / 'after-upgrade.bin'
        self.command(self.controller, 'download', entry['file']['file_id'], str(output))
        self.assertEqual(output.read_bytes(), self.data)
        diagnostics = self.command(self.controller, 'diagnose')
        text = json.dumps(diagnostics)
        for private in (self.admin(), self.pin, self.origin, str(self.controller), 'demo/real.bin', self.nodes[0]['cfg']['token']):
            self.assertNotIn(private, text)

    def test_incompatible_candidate_missing_volume_and_corrupt_backup_refuse_without_state_changes(self):
        self.upload()
        self.stop_all()
        prefix = self.prefix_for(self.controller)
        old_pointer = (prefix / 'install.json').read_bytes()
        identity = self.identity_bytes(self.controller)
        source, release_id = self.candidate('future', state_formats=dict(package.STATE_FORMATS, registry=99))
        self.command(self.controller, 'stage', str(source))
        self.assertNotEqual(self.command_result(self.controller, 'upgrade', release_id, '--backup', str(self.home / 'blocked-future')).returncode, 0)
        self.assertFalse((self.home / 'blocked-future').exists())
        source, release_id = self.candidate('preview-only', capabilities=['installer'])
        self.command(self.controller, 'stage', str(source))
        self.assertNotEqual(self.command_result(self.controller, 'rollback', release_id, '--backup', str(self.home / 'blocked-preview')).returncode, 0)
        self.assertEqual((prefix / 'install.json').read_bytes(), old_pointer)
        self.assertEqual(self.identity_bytes(self.controller), identity)
        volume = self.controller / 'node/data'
        volume.rename(self.controller / 'node/volume-absent')
        missing = self.command_result(self.controller, 'backup', str(self.home / 'blocked-missing-volume'))
        self.assertNotEqual(missing.returncode, 0)
        self.assertFalse((self.home / 'blocked-missing-volume').exists())
        (self.controller / 'node/volume-absent').rename(volume)
        backup = self.home / 'verified-backup'
        self.command(self.controller, 'backup', str(backup))
        self.command(self.controller, 'verify-backup', str(backup))
        body = next((backup / 'state/node/data/objects').glob('*.blob'))
        body.write_bytes(b'corruption detected')
        self.assertNotEqual(self.command_result(self.controller, 'verify-backup', str(backup)).returncode, 0)
        self.assertEqual(self.identity_bytes(self.controller), identity)
        # A different state cannot bind the already installed code prefix.
        other = self.home / 'must-not-create-new-identity'
        result = subprocess.run(['sh', str(prefix / 'bin/asc-demo'), '--state', str(other), 'init', '--role', 'node', '--host', '127.0.0.1'],
                                env=self.env, capture_output=True, text=True, timeout=20)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(other.exists())

    def test_interrupted_activation_blocks_runtime_and_recovers_old_code_only(self):
        self.upload()
        self.stop_all()
        prefix = self.prefix_for(self.controller)
        identity = self.identity_bytes(self.controller)
        source, release_id = self.candidate()
        self.command(self.controller, 'stage', str(source))
        old_id = json.loads((prefix / 'install.json').read_text())['release_id']
        backup = self.home / 'interrupted-backup'
        real_write = upgrade.durable_json
        def fail_completion(path, value):
            if path.name == 'upgrade-journal.json' and value.get('status') == 'COMPLETED':
                raise OSError('synthetic crash after atomic pointer before completion')
            return real_write(path, value)
        # The fault is in actual pointer/journal transition; no fake TLS/success response.
        with mock.patch.dict(os.environ, self.env), mock.patch.object(upgrade, 'durable_json', side_effect=fail_completion):
            with self.assertRaises(OSError):
                upgrade.activate(self.controller, prefix, release_id, backup)
        self.assertEqual(json.loads((prefix / 'install.json').read_text())['release_id'], release_id)
        self.assertEqual(json.loads((prefix / 'upgrade-journal.json').read_text())['status'], 'PREPARED')
        self.assertNotEqual(self.command_result(self.controller, 'run-controller').returncode, 0)
        self.assertNotEqual(self.command_result(self.controller, 'run-node').returncode, 0)
        changed = self.controller / 'test-owned-stale-backup'
        changed.write_bytes(b'current state differs from backup')
        self.assertNotEqual(self.command_result(self.controller, 'recover-upgrade').returncode, 0)
        self.assertEqual(json.loads((prefix / 'upgrade-journal.json').read_text())['status'], 'PREPARED')
        changed.unlink()  # Only the sentinel created by this fault fixture.
        recovered = self.command(self.controller, 'recover-upgrade')
        self.assertEqual(recovered['release_id'], old_id)
        self.assertFalse(recovered['state_restored'])
        self.assertEqual(self.identity_bytes(self.controller), identity)
        # Private source backup checks reject links and insufficient space before completion.
        journal_path = prefix / 'upgrade-journal.json'
        valid = journal_path.read_bytes()
        future = json.loads(valid)
        future['format'] = 2
        journal_path.write_text(json.dumps(future))
        self.assertNotEqual(self.command_result(self.controller, 'run-controller').returncode, 0)
        journal_path.write_bytes(valid)
        linked = self.controller / 'unsafe-link'
        linked.symlink_to(self.payload)
        self.assertNotEqual(self.command_result(self.controller, 'backup', str(self.home / 'no-linked-backup')).returncode, 0)
        linked.unlink()
        with mock.patch.dict(os.environ, self.env), upgrade.stopped(self.controller), mock.patch.object(upgrade.shutil, 'disk_usage', return_value=shutil._ntuple_diskusage(1, 1, 0)):
            with self.assertRaises(ValueError):
                upgrade.backup_locked(self.controller, self.home / 'no-space-backup', prefix)
        self.assertFalse((self.home / 'no-space-backup').exists())

    def test_external_approved_volume_complete_backup_and_mutation_detection(self):
        self.stop_all()
        from asc.storage.engine import StorageEngine
        import io
        node = self.nodes[0]
        external = self.home / 'synthetic-external-app-folder/demo-owned'
        with mock.patch.dict(os.environ, self.env), StorageEngine(self.controller / 'node/storage', node['cfg']['node_id']) as engine:
            # Directory adapter is a Linux synthetic seam, not an Android SD permission claim.
            record = engine.volumes.register(external, 'directory', 1024**2, 0)
            row = engine.initiate('test-owned', record['volume_id'], 'external_backup_test', 'external.bin', len(self.data), hashlib.sha256(self.data).hexdigest())
            engine.upload(row['session_id'], 'test-owned', record['volume_id'], io.BytesIO(self.data), len(self.data))
            engine.commit(row['session_id'], 'test-owned', record['volume_id'])
        backup = self.home / 'external-complete'
        self.command(self.controller, 'backup', str(backup))
        self.command(self.controller, 'verify-backup', str(backup))
        copied = backup / ('volume-' + record['volume_id'])
        self.assertEqual((copied / 'objects' / (row['file_id'] + '.blob')).read_bytes(), self.data)
        self.assertTrue((copied / 'staging').is_dir())
        self.assertEqual((copied / '.asc-volume.json').read_bytes(), (external / '.asc-volume.json').read_bytes())
        sentinel = self.controller / 'test-owned-race'
        sentinel.write_bytes(b'before backup')
        original_copy = upgrade.shutil.copyfileobj
        changed = False
        def mutate_after_copy(source, target, length):
            nonlocal changed
            original_copy(source, target, length)
            if not changed:
                sentinel.write_bytes(b'changed during backup')
                changed = True
        failed = self.home / 'incomplete-race'
        with mock.patch.dict(os.environ, self.env), upgrade.stopped(self.controller), mock.patch.object(upgrade.shutil, 'copyfileobj', side_effect=mutate_after_copy):
            with self.assertRaises(ValueError):
                upgrade.backup_locked(self.controller, failed, self.prefix_for(self.controller))
        self.assertTrue(failed.exists())
        self.assertFalse((failed / 'backup-complete.json').exists())

    def test_linked_lifecycle_lock_refused_before_touching_outside_file(self):
        self.stop_all()
        outside = self.home / 'not-approved-test-owned-empty-file'
        outside.write_bytes(b'')
        for index, lock in enumerate((self.controller / 'demo-operation.lock',
                                     self.controller / 'controller/controller.lock',
                                     self.controller / 'node/agent.lock',
                                     self.controller / 'node/storage/storage-engine.lock',
                                     self.prefix_for(self.controller) / 'install.lock')):
            with self.subTest(lock=lock.name):
                old = lock.read_bytes()
                lock.unlink()  # Unheld file created solely by this synthetic fixture.
                lock.symlink_to(outside)
                destination = self.home / ('blocked-linked-lock-' + str(index))
                command = ('stage', str(self.source)) if lock.name == 'install.lock' else ('backup', str(destination))
                result = self.command_result(self.controller, *command)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(outside.read_bytes(), b'', 'refuse BEFORE any outside-file write')
                self.assertFalse(destination.exists())
                lock.unlink()  # Only the symlink created by this controlled fixture.
                lock.write_bytes(old)
        # Hardlinked coordination files are also rejected before open/write.
        lock = self.controller / 'demo-operation.lock'
        old = lock.read_bytes()
        lock.unlink()
        os.link(outside, lock)
        self.assertNotEqual(self.command_result(self.controller, 'backup', str(self.home / 'blocked-hardlink')).returncode, 0)
        self.assertEqual(outside.read_bytes(), b'')
        lock.unlink()
        lock.write_bytes(old)


if __name__ == '__main__':
    unittest.main()
