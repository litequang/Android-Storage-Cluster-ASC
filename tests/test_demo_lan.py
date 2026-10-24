"""Owner CLI and actual TLS/bytes on Linux synthetic phones, including cohosted ZTE."""
import contextlib
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import sqlite3
import subprocess
import time
import unittest
from asc.client import ClientError, request_json
from asc.storage.client import StorageClient
from tests import test_demo_installer as installer_fixtures


class DemoLANTests(unittest.TestCase):
    script = installer_fixtures.DemoInstallerTests.script
    run_cli = installer_fixtures.DemoInstallerTests.run_cli

    def setUp(self):
        installer_fixtures.DemoInstallerTests.setUp(self)
        self.controller = self.home / 'zte-demo'
        self.bphone = self.home / 'bphone-demo'
        self.port = self.free_port()
        self.command(self.controller, 'init', '--role', 'controller', '--host', '127.0.0.1', '--port', str(self.port))
        self.origin = 'https://127.0.0.1:' + str(self.port)
        self.controller_process = self.start(self.controller, 'run-controller')
        from asc.identity import fingerprint_from_pem
        self.pin = fingerprint_from_pem(self.controller / 'controller/server.crt')
        self.wait_for(lambda: request_json(self.origin, self.pin, 'GET', '/api/v1/info'))
        self.nodes = []
        for index, root in enumerate((self.controller, self.bphone)):
            if root != self.controller:
                self.command(root, 'init', '--role', 'node', '--host', '127.0.0.1')
            pair = self.command(self.controller, 'pair')
            self.command(root, 'join', '--controller', self.origin, '--pin', self.pin,
                         '--name', 'synthetic-phone-' + str(index), input=pair['code'] + '\n')
            port = self.free_port()
            storage = self.command(root, 'storage-init', '--host', '127.0.0.1', '--port', str(port),
                                   '--quota', str(8 * 1024**2), '--reserve', '0')
            cfg = json.loads((root / 'node/node.json').read_text())
            process = self.start(root, 'run-node')
            self.wait_for(lambda: request_json(self.origin, self.pin, 'GET', '/api/v1/nodes',
                        token=self.admin())['nodes'] if self.seen(cfg['node_id']) else False)
            self.command(self.controller, 'approve', '--node-id', cfg['node_id'], '--volume-id', storage['volume_id'],
                         '--origin', 'https://127.0.0.1:' + str(port), '--pin', storage['pin'], '--domain', 'phone-' + str(index))
            self.nodes.append({'root': root, 'cfg': cfg, 'process': process, 'port': port,
                               'volume': storage['volume_id'], 'pin': storage['pin']})
        self.data = b'Demo real TLS synthetic file\x00' * 8192
        self.payload = self.home / 'input.bin'
        self.payload.write_bytes(self.data)

    @staticmethod
    def free_port():
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            return sock.getsockname()[1]

    def admin(self):
        return json.loads((self.controller / 'controller/controller.json').read_text())['admin_token']

    def seen(self, node_id):
        with contextlib.closing(sqlite3.connect(self.controller / 'controller/registry.sqlite3')) as db:
            row = db.execute('SELECT profile FROM nodes WHERE node_id=?', (node_id,)).fetchone()
        return row and 'storage' in json.loads(row[0])

    def command_result(self, root, *args, input=None):
        return self.run_cli('--state', str(root), *args) if input is None else subprocess.run(
            ['sh', str(self.source / 'scripts/demo-alpha.sh'), '--state', str(root), *args],
            cwd=self.root, env=self.env, input=input, capture_output=True, text=True, timeout=45)

    def command(self, root, *args, input=None):
        result = self.command_result(root, *args, input=input)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout[result.stdout.index('{'):])

    def start(self, root, command):
        # Logs stay in the private synthetic fixture and are not committed/returned.
        log = (self.root / ('process-' + str(time.monotonic_ns()))).open('w+')
        self.addCleanup(log.close)
        process = subprocess.Popen(['sh', str(self.source / 'scripts/demo-alpha.sh'), '--state', str(root), command],
                                   cwd=self.root, env=self.env, stdout=log, stderr=log, text=True)
        self.addCleanup(self.stop, process)
        return process

    def stop(self, process):
        if process.poll() is None:
            process.send_signal(signal.SIGINT)
            try:
                process.wait(timeout=25)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
                self.fail('synthetic runtime failed safe foreground shutdown')

    def wait_for(self, callback):
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            try:
                result = callback()
                if result:
                    return result
            except (OSError, ClientError):
                pass
            time.sleep(0.1)
        self.fail('synthetic TLS runtime readiness deadline')

    def upload(self, key='demo_upload_key_01', path='demo/real.bin'):
        return self.command(self.controller, 'upload', str(self.payload), path, '--key', key, '--wait', '20')['file']

    def test_cli_two_verified_physical_copies_and_offline_fallback_no_unsafe_new_upload(self):
        entry = self.upload()
        self.assertEqual((entry['verified_replicas'], entry['available_replicas']), (2, 2))
        self.assertEqual(len({r['node_id'] for r in entry['replicas']}), 2)
        for replica in entry['replicas']:
            node = next(n for n in self.nodes if n['cfg']['node_id'] == replica['node_id'])
            body = node['root'] / 'node/data/objects' / (replica['local_file_id'] + '.blob')
            self.assertEqual(hashlib.sha256(body.read_bytes()).hexdigest(), hashlib.sha256(self.data).hexdigest())
        again = self.upload()
        self.assertEqual(again['file']['file_id'], entry['file']['file_id'])
        first = entry['replicas'][0]['node_id']
        stopped = next(n for n in self.nodes if n['cfg']['node_id'] == first)
        self.stop(stopped['process'])
        output = self.home / 'fallback.bin'
        result = self.command(self.controller, 'download', entry['file']['file_id'], str(output))
        self.assertNotEqual(result['node_id'], first)
        self.assertEqual(output.read_bytes(), self.data)
        degraded = self.command(self.controller, 'replicas', entry['file']['file_id'])
        self.assertEqual(degraded['available_replicas'], 1)
        self.assertEqual(degraded['protection'], 'DEGRADED')
        denied = self.command_result(self.controller, 'upload', str(self.payload), 'new.bin', '--key', 'unsafe_new_upload')
        self.assertNotEqual(denied.returncode, 0)
        with contextlib.closing(sqlite3.connect(self.controller / 'controller/registry.sqlite3')) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM catalog_files').fetchone()[0], 1)
        self.assertNotEqual(self.command_result(self.controller, 'download', entry['file']['file_id'], str(output)).returncode, 0)
        self.assertEqual(output.read_bytes(), self.data)

    def test_missing_volume_capacity_domain_pinning_controller_loss_and_locked_surfaces(self):
        node = self.nodes[1]
        # Two node identities on the same physical device do not satisfy placement.
        self.command(self.controller, 'approve', '--node-id', node['cfg']['node_id'], '--volume-id', node['volume'],
                     '--origin', 'https://127.0.0.1:' + str(node['port']), '--pin', node['pin'], '--domain', 'phone-0')
        denied = self.command_result(self.controller, 'upload', str(self.payload), 'same-phone.bin', '--key', 'same_phone_key')
        self.assertNotEqual(denied.returncode, 0)
        self.command(self.controller, 'approve', '--node-id', node['cfg']['node_id'], '--volume-id', node['volume'],
                     '--origin', 'https://127.0.0.1:' + str(node['port']), '--pin', node['pin'], '--domain', 'phone-1')
        # Actual missing approved medium, not a simulated successful probe.
        volume = node['root'] / 'node/data'
        volume.rename(node['root'] / 'node/missing-test-volume')
        self.assertNotEqual(self.command_result(self.controller, 'upload', str(self.payload), 'missing.bin', '--key', 'missing_volume_key').returncode, 0)
        (node['root'] / 'node/missing-test-volume').rename(volume)
        with self.assertRaises(ClientError):
            request_json(self.origin, '0' * 64, 'GET', '/api/v1/info')
        with self.assertRaises(ClientError) as err:
            request_json(self.origin, self.pin, 'GET', '/catalog/v1/files')
        self.assertEqual(err.exception.status, 401)
        for path, payload in (('/api/v1/admin/storage-grant', {}), ('/catalog/v1/files/id/policy', {'policy': 'single'}),
                              ('/catalog/v1/replication/gc/plan', {}), ('/catalog/v1/backup/enable', {})):
            with self.subTest(path=path), self.assertRaises(ClientError) as err:
                request_json(self.origin, self.pin, 'POST', path, payload, self.admin())
            self.assertEqual(err.exception.status, 404)
        with self.assertRaises(ClientError) as err:
            request_json('https://127.0.0.1:' + str(node['port']), node['pin'], 'POST', '/storage/v1/gc/11111111-1111-4111-8111-111111111111', {})
        self.assertEqual(err.exception.status, 403)
        # Measured double-copy quota refusal occurs before metadata creation.
        with self.assertRaises(ClientError) as capacity:
            request_json(self.origin, self.pin, 'POST', '/catalog/v1/uploads',
                {'idempotency_key': 'exceeds_capacity_key', 'logical_path': 'too-big.bin',
                 'size': 5 * 1024**2, 'sha256': '0' * 64, 'policy': 'replicated_2'}, self.admin())
        self.assertEqual(capacity.exception.status, 507)
        entry = self.upload()
        # Hold a real scoped upload grant, then remove the Controller. Node must deny it.
        plan = request_json(self.origin, self.pin, 'POST', '/catalog/v1/uploads',
            {'idempotency_key': 'outage_lease_key', 'logical_path': 'leased.bin',
             'size': len(self.data), 'sha256': hashlib.sha256(self.data).hexdigest(),
             'policy': 'replicated_2'}, self.admin())
        target = plan['target']
        leased = StorageClient(target['origin'], target['pin'], target['grant'], target['volume_id'])
        cfg = self.nodes[0]['cfg']
        self.stop(self.controller_process)
        with self.assertRaises(ClientError):
            leased.initiate(plan['idempotency_key'], plan['local_logical_path'], len(self.data), hashlib.sha256(self.data).hexdigest())
        failed = self.command_result(self.controller, 'upload', str(self.payload), 'controller-down.bin', '--key', 'controller_down_key')
        self.assertNotEqual(failed.returncode, 0)
        with self.assertRaises((ClientError, OSError)):
            request_json(cfg['controller'], cfg['pin'], 'POST', '/api/v1/heartbeat',
                         {'node_id': cfg['node_id'], 'profile': {}}, cfg['token'])
        for n in self.nodes:
            self.assertIsNone(n['process'].poll())
            self.assertFalse((n['root'] / 'node/controller.json').exists())
        self.assertEqual(entry['verified_replicas'], 2)

    def test_unknown_schema_raft_state_and_protected_runtime_refused_without_recreation(self):
        for node in self.nodes:
            self.stop(node['process'])
        self.stop(self.controller_process)
        original = (self.controller / 'demo.json').read_bytes()
        marker = json.loads(original)
        marker['format'] = 2
        (self.controller / 'demo.json').write_text(json.dumps(marker))
        self.assertNotEqual(self.command_result(self.controller, 'run-controller').returncode, 0)
        self.assertEqual(json.loads((self.controller / 'demo.json').read_text())['format'], 2)
        (self.controller / 'demo.json').write_bytes(original)
        registry = self.controller / 'controller/registry.sqlite3'
        with contextlib.closing(sqlite3.connect(registry)) as db, db:
            db.execute('PRAGMA user_version=99')
        self.assertNotEqual(self.command_result(self.controller, 'run-controller').returncode, 0)
        with contextlib.closing(sqlite3.connect(registry)) as db, db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0], 99)
            db.execute('PRAGMA user_version=4')
            db.execute("INSERT INTO settings VALUES ('consensus_mode','metadata-v1')")
        self.assertNotEqual(self.command_result(self.controller, 'run-controller').returncode, 0)
        with contextlib.closing(sqlite3.connect(registry)) as db, db:
            self.assertEqual(db.execute("SELECT value FROM settings WHERE key='consensus_mode'").fetchone()[0], 'metadata-v1')
            db.execute("DELETE FROM settings WHERE key='consensus_mode'")
        for model in ('SM-M515F', 'unknown'):
            self.env['ASC_TEST_MODEL'] = model
            for root, command in ((self.controller, 'run-controller'), (self.bphone, 'run-node')):
                self.assertNotEqual(self.command_result(root, command).returncode, 0)
            new = self.home / ('blocked-' + model)
            self.assertNotEqual(self.command_result(new, 'init', '--role', 'controller', '--host', '127.0.0.1').returncode, 0)
            self.assertFalse(new.exists())
        self.env['ASC_TEST_MODEL'] = 'ZTE V40'
        for host in ('0.0.0.0', '8.8.8.8', '169.254.1.1', 'localhost'):
            new = self.home / 'invalid-bind'
            self.assertNotEqual(self.command_result(new, 'init', '--role', 'controller', '--host', host).returncode, 0)
            self.assertFalse(new.exists())


if __name__ == '__main__':
    unittest.main()
