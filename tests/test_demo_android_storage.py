"""Actual Demo TLS runtime with test-only root denial, real private IO/restart."""
import contextlib
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import time
import unittest
from asc.client import request_json
from tests import test_demo_dashboard as fixture


class RootDeniedRuntimeFixture(unittest.TestCase):
    script = fixture.DashboardAPITests.script
    run_cli = fixture.DashboardAPITests.run_cli
    free_port = staticmethod(fixture.DashboardAPITests.free_port)
    command = fixture.DashboardAPITests.command
    stop = fixture.DashboardAPITests.stop
    wait_for = fixture.DashboardAPITests.wait_for
    seen = fixture.DashboardAPITests.seen
    admin = fixture.DashboardAPITests.admin
    login = fixture.DashboardAPITests.login
    http = fixture.DashboardAPITests.http
    prepare = fixture.DashboardAPITests.prepare
    send_file = fixture.DashboardAPITests.send_file

    def command_result(self, root, *args, input=None):
        return subprocess.run([sys.executable, '-I', '-B', str(self.repo / 'tests/android_root_denial.py'),
                               str(self.source), '--state', str(root), *args], env=self.env, input=input,
                              capture_output=True, text=True, timeout=45, cwd=self.root)

    def start(self, root, command):
        args = [command]
        if command == 'run-controller':
            if not hasattr(self, 'dashboard_port'):
                self.dashboard_port = self.free_port()
                while self.dashboard_port == self.port:
                    self.dashboard_port = self.free_port()
                self.command(root, 'dashboard-init', '--port', str(self.dashboard_port))
            args.append('--dashboard')
        env = dict(self.env)
        if command == 'run-node':
            env['ASC_HOME'] = str(root / 'node')  # Set before import; real product HOME guard remains.
        log = (self.root / ('android-root-denied-' + str(time.monotonic_ns()))).open('w+')
        self.addCleanup(log.close)
        child = subprocess.Popen([sys.executable, '-I', '-B', str(self.repo / 'tests/android_root_denial.py'),
                                  str(self.source), '--state', str(root), *args],
                                 env=env, cwd=self.root, stdout=log, stderr=log, text=True)
        self.addCleanup(self.stop, child)
        return child

    def setUp(self):
        fixture.DashboardAPITests.setUp(self)


class AndroidStorageRuntimeTests(RootDeniedRuntimeFixture):
    def test_root_denied_runtime_probe_two_copies_dashboard_fallback_and_restart(self):
        before = {str(n['root']): (n['root'] / 'node/node.json').read_bytes() for n in self.nodes}
        markers = {n['volume']: (n['root'] / 'node/data/.asc-volume.json').read_bytes() for n in self.nodes}
        status, _, state = self.http('POST', '/api/refresh', {})
        self.assertEqual(status, 200)
        self.assertEqual(state['counts']['paired_nodes'], 2)
        for n in state['nodes']:
            self.assertTrue(n['storage_approved'])
            self.assertTrue(n['volumes'][0]['writable'])
        topology = self.command(self.controller, 'nodes')['nodes']
        storage = [n['profile']['storage'] for n in topology if n['node_id'] != 'local-controller']
        self.assertEqual(len(storage), 2)
        for capability in storage:
            row = capability['volumes'][0]
            self.assertTrue(row['readable']); self.assertTrue(row['writable']); self.assertTrue(row['fsync_tested'])
            self.assertEqual(row['state'], 'online'); self.assertIsNone(row['last_error'])
        entry = self.send_file('android_runtime_key', 'android/real.bin')
        self.assertTrue(entry['protected'])
        self.assertEqual(entry['verified_replicas'], 2)
        self.assertEqual(len({r['node_id'] for r in entry['replicas']}), 2)
        file_id = entry['file_id']
        with contextlib.closing(sqlite3.connect(self.controller / 'controller/registry.sqlite3')) as db:
            records = db.execute('SELECT node_id,local_file_id FROM catalog_replicas WHERE file_id=?', (file_id,)).fetchall()
        for nid, local in records:
            node = next(n for n in self.nodes if n['cfg']['node_id'] == nid)
            self.assertEqual(hashlib.sha256((node['root'] / 'node/data/objects' / (local + '.blob')).read_bytes()).hexdigest(), entry['sha256'])
        self.assertNotEqual(self.command_result(self.controller, 'storage-status').returncode, 0, 'Live node ownership must block local probe')
        first = entry['replicas'][0]['node_id']
        stopped = next(n for n in self.nodes if n['cfg']['node_id'] == first)
        self.stop(stopped['process'])
        probe = self.command(stopped['root'], 'storage-status')['volumes'][0]
        self.assertTrue(probe['writable']); self.assertTrue(probe['fsync_tested'])
        try:
            for model in ('SM-M515F', 'unknown'):
                self.env['ASC_TEST_MODEL'] = model
                self.assertNotEqual(self.command_result(stopped['root'], 'storage-status').returncode, 0)
        finally:
            self.env['ASC_TEST_MODEL'] = 'ZTE V40'
        code, headers, content = self.http('GET', '/api/files/' + file_id + '/content', json_response=False)
        self.assertEqual((code, content), (200, self.data))
        self.assertNotEqual(headers['X-ASC-Replica-Node'], first)
        self.assertEqual(headers['X-ASC-SHA256'], hashlib.sha256(content).hexdigest())
        self.assertFalse(self.http('POST', '/api/refresh', {})[2]['files'][0]['protected'])
        stopped['process'] = self.start(stopped['root'], 'run-node')
        self.wait_for(lambda: self.command(self.controller, 'replicas', file_id)['available_replicas'] == 2)
        self.assertTrue(self.http('POST', '/api/refresh', {})[2]['files'][0]['protected'])
        self.assertEqual(self.http('GET', '/api/files/' + file_id + '/content', json_response=False)[2], self.data)
        for node in self.nodes:
            self.assertEqual((node['root'] / 'node/node.json').read_bytes(), before[str(node['root'])])
            self.assertEqual((node['root'] / 'node/data/.asc-volume.json').read_bytes(), markers[node['volume']])
            self.assertEqual(list((node['root'] / 'node/data/staging').iterdir()), [])


if __name__ == '__main__':
    unittest.main()
