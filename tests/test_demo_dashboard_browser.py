"""Real Chromium UI / CA trust / TLS storage. Requires local Node Playwright/certutil."""
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import contextlib
import subprocess
import time
import unittest
from tests import test_demo_dashboard as fixture


class DashboardBrowserTests(unittest.TestCase):
    script = fixture.DashboardAPITests.script
    run_cli = fixture.DashboardAPITests.run_cli
    free_port = staticmethod(fixture.DashboardAPITests.free_port)
    command_result = fixture.DashboardAPITests.command_result
    command = fixture.DashboardAPITests.command
    stop = fixture.DashboardAPITests.stop
    wait_for = fixture.DashboardAPITests.wait_for
    seen = fixture.DashboardAPITests.seen
    admin = fixture.DashboardAPITests.admin
    upload = fixture.DashboardAPITests.upload
    start = fixture.DashboardAPITests.start
    login = fixture.DashboardAPITests.login
    http = fixture.DashboardAPITests.http

    def setUp(self):
        for executable in ('node', 'chromium', 'certutil'):
            if shutil.which(executable) is None:
                self.fail('Browser regression requires local Node/Chromium/certutil; see DEMO4-PLAN; never skip TLS/browser gates')
        fixture.DashboardAPITests.setUp(self)

    def test_real_browser_trusted_tls_upload_replicas_sha_mobile_xss_node_and_controller_offline(self):
        output = self.root / 'browser-artifacts'
        output.mkdir(mode=0o700)
        grant = self.command(self.controller, 'dashboard-code')
        config = {'origin': self.browser_origin, 'code': grant['code'], 'ca': str(self.controller / 'dashboard/ca.crt'),
                  'payload': str(self.payload), 'sha': hashlib.sha256(self.data).hexdigest(), 'output': str(output),
                  'logical': 'browser/<img src=x onerror=globalThis.dashboardXss=1>.bin'}
        script = self.repo / 'tests/browser/demo_dashboard.cjs'
        process = subprocess.Popen(['node', str(script)], cwd=self.repo, env=self.env,
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        process.stdin.write(json.dumps(config))
        process.stdin.close()
        self.addCleanup(lambda: process.kill() if process.poll() is None else None)
        stopped = False
        deadline = time.monotonic() + 150
        while process.poll() is None and time.monotonic() < deadline:
            signal = output / 'stop-node.json'
            if signal.exists() and not stopped:
                requested = json.loads(signal.read_text())['node_id']
                node = next(n for n in self.nodes if n['cfg']['node_id'] == requested)
                self.stop(node['process'])
                (output / 'node-stopped').write_text('actual synthetic process stopped')
                stopped = True
            time.sleep(0.1)
        if process.poll() is None:
            process.kill()
        process.wait(timeout=10)
        stdout, stderr = process.stdout.read(), process.stderr.read()
        process.stdout.close(); process.stderr.close()
        # Failure output is deliberately fixed, never includes the one-use input grant.
        self.assertEqual(process.returncode, 0, stderr)
        result = json.loads(stdout)
        self.assertTrue(result['passed'])
        self.assertTrue(stopped)
        self.assertEqual(result['replicas'], 2)
        self.assertEqual(result['sha256'], hashlib.sha256(self.data).hexdigest())
        self.assertEqual((output / 'downloaded-after-node-offline.bin').read_bytes(), self.data)
        with contextlib.closing(sqlite3.connect(self.controller / 'controller/registry.sqlite3')) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM catalog_files').fetchone()[0], 1)
            replicas = db.execute('SELECT node_id,local_file_id FROM catalog_replicas').fetchall()
        self.assertEqual(len({r[0] for r in replicas}), 2)
        for node_id, local_file in replicas:
            root = next(n['root'] for n in self.nodes if n['cfg']['node_id'] == node_id)
            self.assertEqual(hashlib.sha256((root / 'node/data/objects' / (local_file + '.blob')).read_bytes()).hexdigest(), result['sha256'])
        # Keep only screenshots as local review artifacts, never private profile/log/state.
        artifacts = Path('/workspace/work/demo4-browser')
        artifacts.mkdir(parents=True, exist_ok=True)
        for name in ('dashboard-desktop.png', 'dashboard-mobile.png'):
            shutil.copyfile(output / name, artifacts / name)


if __name__ == '__main__':
    unittest.main()
