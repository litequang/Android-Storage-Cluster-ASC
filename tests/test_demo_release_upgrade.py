"""Exact published0.3/0.4 ->0.4.1 under root denial; old-code/new-state rollback."""
import contextlib
import hashlib
import http.client
from http.cookies import SimpleCookie
import json
import os
import sys
import sqlite3
import ssl
import subprocess
import tarfile
import time
import unittest
from asc.demo import STATE_FORMATS
from asc.demo.package import verify
from asc.client import request_json
from tests import test_demo_lan as lan
from tests import test_demo_upgrade as installed


class PublishedUpgradeFixture(unittest.TestCase):
    script = lan.DemoLANTests.script
    run_cli = lan.DemoLANTests.run_cli
    free_port = staticmethod(lan.DemoLANTests.free_port)
    command = lan.DemoLANTests.command
    stop = lan.DemoLANTests.stop
    wait_for = lan.DemoLANTests.wait_for
    seen = lan.DemoLANTests.seen
    admin = lan.DemoLANTests.admin
    upload = lan.DemoLANTests.upload
    prefix_for = installed.DemoUpgradeTests.prefix_for
    stop_all = installed.DemoUpgradeTests.stop_all
    identity_bytes = installed.DemoUpgradeTests.identity_bytes

    def command_result(self, root, *args, input=None):
        # First call is before old Controller/state creation. Both phones are
        # installed and populated by EXACT archived0.3/0.4 code, not a version label.
        if not hasattr(self, 'new_source'):
            self.new_source = self.source
            self.new_release = verify(self.new_source)
            archive = self.repo / ('releases/asc-demo-alpha-' + self.old_version + '.tar.gz')
            self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(),
                             self.old_sha)
            with tarfile.open(archive) as saved:
                self.assertTrue(all(m.isfile() and not m.name.startswith('/') and '..' not in m.name.split('/') for m in saved.getmembers()))
                saved.extractall(self.root / ('published-' + self.old_version), filter='data')
            self.source = self.root / ('published-' + self.old_version) / 'asc-demo-alpha'
            self.old_release = verify(self.source)
            self.assertEqual(self.old_release['version'], self.old_version + '-alpha')
        if getattr(self, 'deny_root', False):
            env = dict(self.env, ASC_HOME=str(root / 'node'))
            return subprocess.run([sys.executable, '-I', '-B', str(self.repo / 'tests/android_root_denial.py'),
                                   str(self.prefix_for(root) / 'launch.py'), str(self.prefix_for(root)),
                                   '--state', str(root), *args], env=env, input=input,
                                  capture_output=True, text=True, timeout=45, cwd=self.root)
        return installed.DemoUpgradeTests.command_result(self, root, *args, input=input)

    def start(self, root, command):
        args = [command]
        if command == 'run-controller' and getattr(self, 'browser_enabled', False):
            args.append('--dashboard')
        env = dict(self.env)
        if getattr(self, 'deny_root', False):
            if command == 'run-node':
                env['ASC_HOME'] = str(root / 'node')
            invocation = [sys.executable, '-I', '-B', str(self.repo / 'tests/android_root_denial.py'),
                          str(self.prefix_for(root) / 'launch.py'), str(self.prefix_for(root))]
        else:
            invocation = ['sh', str(self.prefix_for(root) / 'bin/asc-demo')]
        log = (self.root / ('release-runtime-' + str(time.monotonic_ns()))).open('w+')
        self.addCleanup(log.close)
        process = subprocess.Popen([*invocation, '--state', str(root), *args], env=env, cwd=self.root, stdout=log, stderr=log, text=True)
        self.addCleanup(self.stop, process)
        return process

    def setUp(self):
        lan.DemoLANTests.setUp(self)

    def restart_cluster(self):
        self.controller_process = self.start(self.controller, 'run-controller')
        self.wait_for(lambda: request_json(self.origin, self.pin, 'GET', '/api/v1/info'))
        for node in self.nodes:
            node['process'] = self.start(node['root'], 'run-node')

    def exercise_upgrade_and_rollback(self):
        entry = self.upload()
        file_id = entry['file']['file_id']
        roots = [self.controller, self.bphone]
        identities = {str(r): self.identity_bytes(r) for r in roots}
        with contextlib.closing(sqlite3.connect(self.controller / 'controller/registry.sqlite3')) as db:
            cluster = db.execute("SELECT value FROM settings WHERE key='cluster_id'").fetchone()[0]
        self.assertEqual(self.new_release['version'], '0.4.1-alpha')
        self.assertEqual(self.new_release['state_formats'], self.old_release['state_formats'])
        self.assertEqual(self.new_release['state_formats'], STATE_FORMATS)
        self.stop_all()
        port = self.free_port()
        while port in (self.port, *(node['port'] for node in self.nodes)):
            port = self.free_port()
        previous_browser = None
        if self.old_version == '0.4.0':
            self.command(self.controller, 'dashboard-init', '--port', str(port))
            previous_browser = {p.name: p.read_bytes() for p in (self.controller / 'dashboard').iterdir() if p.is_file()}
            for asset in ('index.html', 'app.js', 'style.css'):
                self.assertEqual((self.source / 'asc/demo/dashboard/web' / asset).read_bytes(),
                                 (self.new_source / 'asc/demo/dashboard/web' / asset).read_bytes())
        self.deny_root = True  # Old backup/stager and new runtime must work with root inaccessible.
        # Real OLD installed stage/compatibility/activation accepts new compatible
        # package; no installer overwrite, config editing or implicit migration.
        for root in roots:
            before = self.home / (root.name + '-explicit-before')
            self.command(root, 'backup', str(before)); self.command(root, 'verify-backup', str(before))
            self.assertEqual(self.command(root, 'stage', str(self.new_source))['release_id'], self.new_release['release_id'])
            self.assertTrue(self.command(root, 'upgrade-preflight', self.new_release['release_id'])['compatible'])
            updated = self.command(root, 'upgrade', self.new_release['release_id'], '--backup', str(self.home / (root.name + '-old-activation-backup')))
            self.assertFalse(updated['schema_migration'])
            self.assertEqual(updated['previous_release_id'], self.old_release['release_id'])
            self.assertEqual(self.identity_bytes(root), identities[str(root)])
            self.command(root, 'verify-backup', str(self.home / (root.name + '-old-activation-backup')))
            probe = self.command(root, 'storage-status')['volumes'][0]
            self.assertTrue(probe['writable']); self.assertTrue(probe['fsync_tested'])
        self.source = self.new_source
        setup = self.command(self.controller, 'dashboard-init', '--port', str(port))
        browser_files = {p.name: p.read_bytes() for p in (self.controller / 'dashboard').iterdir() if p.is_file()}
        if previous_browser is not None:
            self.assertEqual(browser_files, previous_browser)
        self.browser_enabled = True
        self.restart_cluster()
        self.wait_for(lambda: self.command(self.controller, 'replicas', file_id)['available_replicas'] == 2)
        origin = 'https://127.0.0.1:' + str(port)
        ctx = ssl.create_default_context(cafile=str(self.controller / 'dashboard/ca.crt'))
        def browser_request(method, path, obj=None, cookie=None, csrf=None):
            conn = http.client.HTTPSConnection('127.0.0.1', port, context=ctx, timeout=30)
            headers = {'Origin': origin}
            if obj is not None: headers['Content-Type'] = 'application/json'
            if cookie: headers['Cookie'] = cookie
            if csrf: headers['X-ASC-CSRF'] = csrf
            try:
                conn.request(method, path, json.dumps(obj) if obj is not None else None, headers)
                response = conn.getresponse()
                return response.status, dict(response.getheaders()), response.read()
            finally:
                conn.close()
        grant = self.command(self.controller, 'dashboard-code')
        status, headers, body = browser_request('POST', '/api/login', {'code': grant['code']})
        self.assertEqual(status, 200)
        cookie = SimpleCookie(headers['Set-Cookie'])['__Host-ASC-Demo'].value
        csrf = json.loads(body)['csrf']
        status, _, body = browser_request('GET', '/api/state', cookie='__Host-ASC-Demo=' + cookie, csrf=csrf)
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)['files'][0]['protected'])
        status, headers, body = browser_request('GET', '/api/files/' + file_id + '/content', cookie='__Host-ASC-Demo=' + cookie, csrf=csrf)
        self.assertEqual((status, body), (200, self.data))
        self.assertEqual(headers['X-ASC-SHA256'], hashlib.sha256(body).hexdigest())
        self.assertEqual(browser_request('GET', '/')[0], 200)
        # Write via actual0.4.1 root-denied code before rolling old code over the NEW actual state.
        second = self.upload('release041_new_key', 'demo/new-under-041.bin')
        self.assertEqual(second['verified_replicas'], 2)
        self.stop_all()
        for root in roots:
            backup = self.home / (root.name + '-041-before-rollback')
            rolled = self.command(root, 'rollback', self.old_release['release_id'], '--backup', str(backup))
            self.assertFalse(rolled['schema_migration'])
            self.assertEqual(self.identity_bytes(root), identities[str(root)])
            self.command(root, 'verify-backup', str(backup))
        self.assertEqual({p.name: p.read_bytes() for p in (self.controller / 'dashboard').iterdir() if p.is_file()}, browser_files)
        self.assertEqual((self.home / (self.controller.name + '-041-before-rollback') / 'state/dashboard/ca.key').read_bytes(), browser_files['ca.key'])
        self.browser_enabled = False
        self.restart_cluster()  # Real old source under root denial must still report original defect.
        def old_denied():
            rows = [n['profile'].get('storage', {}).get('volumes', []) for n in self.command(self.controller, 'nodes')['nodes'] if n['node_id'] != 'local-controller']
            return len(rows) == 2 and all(v and v[0]['writable'] is False and v[0]['fsync_tested'] is None for v in rows)
        self.wait_for(old_denied)
        self.assertNotEqual(self.command_result(self.controller, 'upload', str(self.payload), 'denied-rollback.bin', '--key', 'old_rollback_denied').returncode, 0)
        self.stop_all()
        # Baseline Linux privileges restored ONLY in test fixture to demonstrate
        # schema/code rollback compatibility; old Android storage is NOT declared fixed.
        self.deny_root = False
        self.restart_cluster()  # Runs exact old immutable compatible code; no DB restore.
        for saved in (entry, second):
            fid = saved['file']['file_id']
            self.wait_for(lambda: self.command(self.controller, 'replicas', fid)['available_replicas'] == 2)
            output = self.home / ('after-old-code-' + fid)
            self.command(self.controller, 'download', fid, str(output))
            self.assertEqual(output.read_bytes(), self.data)
        for root in roots:
            self.assertEqual(self.identity_bytes(root), identities[str(root)])
            self.assertEqual(json.loads((self.prefix_for(root) / 'install.json').read_text())['release_id'], self.old_release['release_id'])
        with contextlib.closing(sqlite3.connect(self.controller / 'controller/registry.sqlite3')) as db:
            self.assertEqual(db.execute("SELECT value FROM settings WHERE key='cluster_id'").fetchone()[0], cluster)
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0], 4)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM catalog_files').fetchone()[0], 2)
        self.assertEqual(self.command(self.controller, 'diagnose')['version'], self.old_version + '-alpha')


class Published03UpgradeTests(PublishedUpgradeFixture):
    old_version = '0.3.0'
    old_sha = '3bf81c5d94891fa064e2f05f99d60d620b4c5db71c87bb2ee6c89ac72b9a445a'

    def test_published03_to041_backup_stage_root_denied_upgrade_and_new_state_code_rollback(self):
        self.exercise_upgrade_and_rollback()


class Published04UpgradeTests(PublishedUpgradeFixture):
    old_version = '0.4.0'
    old_sha = 'b9e186589bb4f5c698c7df2250f94ec32ce1e6e2acb41cf3923ade9e706a29f1'

    def test_published04_to041_backup_stage_root_denied_upgrade_dashboard_identity_and_code_rollback(self):
        self.exercise_upgrade_and_rollback()


if __name__ == '__main__':
    unittest.main()
