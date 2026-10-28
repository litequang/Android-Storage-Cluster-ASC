"""Exact published 0.4.3 snapshots: live TLS/bytes/pending and code-only rollback."""
import contextlib
import hashlib
import http.client
from http.cookies import SimpleCookie
import json
import sqlite3
import ssl
import subprocess
import tarfile

from asc.demo import STATE_FORMATS
from asc.demo.package import verify
from tests import test_demo_release_upgrade as published
from tests import test_demo_upgrade as installed
from tests import test_quick_join as quick


class SnapshotUpgradeFixture(published.PublishedUpgradeFixture):
    proxy = quick.QuickJoinTests.proxy
    quick_join = quick.QuickJoinTests.join

    def extract_exact(self, name, checksum, label):
        archive = self.repo/'candidates'/name
        self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), checksum)
        with tarfile.open(archive) as saved:
            self.assertTrue(all(m.isfile() and m.name.startswith('asc-demo-alpha/')
                                and '..' not in m.name.split('/') for m in saved.getmembers()))
            saved.extractall(self.root/label, filter='data')
        root = self.root/label/'asc-demo-alpha'
        return root, verify(root)

    def command_result(self, root, *args, input=None):
        if not hasattr(self, 'old_source'):
            self.old_source, self.old_release = self.extract_exact(
                self.old_archive, self.old_sha, 'exact-old')
            self.new_source, self.new_release = self.extract_exact(
                'asc-demo-alpha-0.4.3-core-decode-internal-source.tar.gz',
                '6a60bd4180bc338d8c62eff4ef1347082a0e6c0ce36e06143ff53baa791b9d57',
                'exact-new')
            for manifest in (self.old_release, self.new_release):
                self.assertEqual(manifest['version'], '0.4.3-dev')
                self.assertEqual(manifest['state_formats'], STATE_FORMATS)
            self.assertNotEqual(self.old_release['release_id'], self.new_release['release_id'])
            self.source = self.old_source  # BEFORE first install or identity creation.
        return installed.DemoUpgradeTests.command_result(self, root, *args, input=input)

    def identities_equal(self, root, expected):
        # Do not include private key/token bytes in assertion failure output.
        self.assertTrue(self.identity_bytes(root) == expected, 'identity or credential bytes changed')

    def bridge_status(self, control):
        process = subprocess.Popen(
            ['sh', str(self.prefix_for(self.bphone)/'bin/asc-demo'), '--state',
             str(self.bphone), 'bridge-run', '--control', str(control)],
            cwd=self.root, env=self.env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.addCleanup(self.stop, process)
        self.wait_for(lambda: (control/'engine.sock').exists())
        status = self.command(self.bphone, 'bridge-status', '--control', str(control))
        self.assertTrue(status['ok'])
        self.assertTrue(status['result']['node']['identity_present'])
        self.assertIsNone(status['result']['volumes'][0]['writable'])
        self.stop(process)

    def web_download(self, entry, expected):
        origin = 'https://127.0.0.1:'+str(self.dashboard_port)
        trust = ssl.create_default_context(cafile=str(self.controller/'dashboard/ca.crt'))
        def request(method, path, obj=None, cookie=None, csrf=None):
            connection = http.client.HTTPSConnection('127.0.0.1', self.dashboard_port,
                                                     context=trust, timeout=30)
            headers = {'Origin': origin}
            if obj is not None: headers['Content-Type'] = 'application/json'
            if cookie: headers['Cookie'] = cookie
            if csrf: headers['X-ASC-CSRF'] = csrf
            try:
                connection.request(method, path, json.dumps(obj) if obj is not None else None, headers)
                reply = connection.getresponse()
                return reply.status, dict(reply.getheaders()), reply.read()
            finally:
                connection.close()
        fid = entry['file']['file_id']
        self.assertEqual(request('GET', '/api/files/'+fid+'/content')[0], 401)
        code = self.command(self.controller, 'dashboard-code')['code']
        status, headers, body = request('POST', '/api/login', {'code': code})
        self.assertEqual(status, 200)
        cookie = SimpleCookie(headers['Set-Cookie'])['__Host-ASC-Demo'].value
        csrf = json.loads(body)['csrf']
        status, headers, body = request('GET', '/api/files/'+fid+'/content',
                                       cookie='__Host-ASC-Demo='+cookie, csrf=csrf)
        self.assertEqual(status, 200)
        self.assertTrue(body == expected, 'HTTPS download differs from committed bytes')
        self.assertEqual(headers['X-ASC-SHA256'], hashlib.sha256(expected).hexdigest())

    def exercise_snapshot(self):
        old_file = self.upload()
        pending_root = self.home/'old-pending'
        self.command(pending_root, 'init', '--role', 'node', '--host', '127.0.0.1')
        code = self.command(self.controller, 'pair')['code']
        proxy, proxy_origin = self.proxy(drop=True)
        lost = self.command_result(pending_root, 'join', '--controller', proxy_origin,
            '--pin', self.pin, '--name', 'snapshot pending', input=code+'\n')
        self.assertNotEqual(lost.returncode, 0)
        self.assertTrue(proxy.dropped, 'must lose an actual successful TLS join ACK')
        pending_bytes = (pending_root/'node/enrollment_pending.json').read_bytes()
        pending = json.loads(pending_bytes)
        self.assertFalse((pending_root/'node/node.json').exists())
        pair = {'controller': proxy_origin, 'pin': self.pin,
                'cluster_id': pending['expected_cluster_id'], 'code': code}
        control = self.home/'private-application-control'
        self.command(self.bphone, 'bridge-provision', '--control', str(control))
        self.bridge_status(control)  # BOTH old043 and new043 support the same bridge.
        controls = {p.name: p.read_bytes() for p in control.iterdir() if p.is_file()}
        roots = [self.controller, self.bphone, pending_root]
        identities = {str(root): self.identity_bytes(root) for root in roots}
        media = {str(node['root']): (node['root']/'node/data').stat() for node in self.nodes}
        self.stop_all()
        self.dashboard_port = self.free_port()
        self.command(self.controller, 'dashboard-init', '--port', str(self.dashboard_port))
        browser = {p.name: p.read_bytes() for p in (self.controller/'dashboard').iterdir() if p.is_file()}
        for root in roots:
            backup = self.home/(root.name+'-before-upgrade')
            self.command(root, 'backup', str(backup))
            self.command(root, 'verify-backup', str(backup))
            self.command(root, 'stage', str(self.new_source))
            self.assertTrue(self.command(root, 'upgrade-preflight', self.new_release['release_id'])['compatible'])
            activated = self.command(root, 'upgrade', self.new_release['release_id'],
                '--backup', str(self.home/(root.name+'-activation-backup')))
            self.assertFalse(activated['schema_migration'])
            self.assertEqual(activated['previous_release_id'], self.old_release['release_id'])
            self.command(root, 'verify-backup', str(self.home/(root.name+'-activation-backup')))
            self.identities_equal(root, identities[str(root)])
        self.assertTrue((pending_root/'node/enrollment_pending.json').read_bytes() == pending_bytes)
        self.assertTrue({p.name: p.read_bytes() for p in control.iterdir() if p.is_file()} == controls)
        self.source = self.new_source
        self.browser_enabled = True
        self.restart_cluster()
        self.wait_for(lambda: self.command(self.controller, 'replicas', old_file['file']['file_id'])['available_replicas'] == 2)
        self.web_download(old_file, self.data)
        self.bridge_status(control)
        self.assertEqual(self.quick_join(pending_root, pair).returncode, 0)
        cfg = json.loads((pending_root/'node/node.json').read_bytes())
        self.assertTrue(cfg['token'] == pending['payload']['enrollment_token'])
        self.assertEqual(proxy.join_calls, 2)
        self.assertFalse((pending_root/'node/storage.json').exists())
        identities[str(pending_root)] = self.identity_bytes(pending_root)
        new_data = self.data+b'new bytes after exact snapshot upgrade'
        self.payload.write_bytes(new_data)
        new_file = self.upload('snapshot_new_file_key', 'demo/new-snapshot.bin')
        self.assertEqual(new_file['verified_replicas'], 2)
        reverse_root = self.home/'new-pending'
        self.command(reverse_root, 'init', '--role', 'node', '--host', '127.0.0.1')
        pair['code'] = self.command(self.controller, 'pair')['code']
        proxy.drop, proxy.dropped = True, False
        self.assertNotEqual(self.quick_join(reverse_root, pair).returncode, 0)
        self.assertTrue(proxy.dropped)
        reverse_bytes = (reverse_root/'node/enrollment_pending.json').read_bytes()
        reverse = json.loads(reverse_bytes)
        roots.append(reverse_root)
        identities[str(reverse_root)] = self.identity_bytes(reverse_root)
        self.stop_all()
        controls = {p.name: p.read_bytes() for p in control.iterdir() if p.is_file()}
        for root in roots:
            self.command(root, 'stage', str(self.old_source))
            backup = self.home/(root.name+'-NEW-state-code-rollback')
            rolled = self.command(root, 'rollback', self.old_release['release_id'], '--backup', str(backup))
            self.assertFalse(rolled['schema_migration'])
            self.command(root, 'verify-backup', str(backup))
            self.identities_equal(root, identities[str(root)])
        self.assertTrue((reverse_root/'node/enrollment_pending.json').read_bytes() == reverse_bytes)
        self.assertTrue({p.name: p.read_bytes() for p in control.iterdir() if p.is_file()} == controls)
        self.assertTrue({p.name: p.read_bytes() for p in (self.controller/'dashboard').iterdir() if p.is_file()} == browser)
        for node in self.nodes:
            medium = (node['root']/'node/data').stat()
            saved = media[str(node['root'])]
            self.assertEqual((medium.st_dev, medium.st_ino), (saved.st_dev, saved.st_ino))
        self.source = self.old_source
        self.restart_cluster()
        self.bridge_status(control)  # Old043 bridge stays supported after rollback.
        self.assertEqual(self.quick_join(reverse_root, pair).returncode, 0)
        joined = json.loads((reverse_root/'node/node.json').read_bytes())
        self.assertTrue(joined['token'] == reverse['payload']['enrollment_token'])
        self.assertFalse((reverse_root/'node/storage.json').exists())
        for entry, expected in ((old_file, self.data), (new_file, new_data)):
            fid = entry['file']['file_id']
            self.wait_for(lambda: self.command(self.controller, 'replicas', fid)['available_replicas'] == 2)
            output = self.home/('rollback-download-'+fid)
            self.command(self.controller, 'download', fid, str(output))
            self.assertTrue(output.read_bytes() == expected, 'code rollback lost old or newly committed bytes')
            self.web_download(entry, expected)
        with contextlib.closing(sqlite3.connect(self.controller/'controller/registry.sqlite3')) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM catalog_files').fetchone()[0], 2)
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0], 4)
            for root, original in ((pending_root, pending), (reverse_root, reverse)):
                node = json.loads((root/'node/node.json').read_bytes())
                row = db.execute('SELECT node_id FROM enrollments WHERE enrollment_hash=?',
                    (hashlib.sha256(original['payload']['enrollment_id'].encode()).hexdigest(),)).fetchone()
                self.assertEqual(row[0], node['node_id'])
                self.assertEqual(db.execute('SELECT COUNT(*) FROM catalog_nodes WHERE node_id=?', (node['node_id'],)).fetchone()[0], 0)


class NativeNodeSnapshotUpgradeTests(SnapshotUpgradeFixture):
    old_archive = 'asc-demo-alpha-0.4.3-native-node-internal-source.tar.gz'
    old_sha = '9dbd9007058a6a43f075c1924f4014faa7060ef6667e014bbc28a91be070ad59'

    def test_published_native_node_snapshot_to_core_decode_and_new_state_rollback(self):
        self.exercise_snapshot()


class PwaSnapshotUpgradeTests(SnapshotUpgradeFixture):
    old_archive = 'asc-demo-alpha-0.4.3-native-pwa-internal-source.tar.gz'
    old_sha = 'c726bd36f107335452da5e59b87614052608ffa92816df727728c9eec4f027fc'

    def test_published_pwa_snapshot_to_core_decode_and_new_state_rollback(self):
        self.exercise_snapshot()
