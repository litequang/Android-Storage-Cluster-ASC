"""Actual CA-verified browser API and existing two-node TLS storage, Linux synthetic."""
import contextlib
import hashlib
import http.client
from http.cookies import SimpleCookie
import json
from pathlib import Path
import secrets
import ssl
import sqlite3
import subprocess
import time
import unittest
from asc.client import ClientError, request_json
from asc.demo.dashboard.auth import Sessions, COOKIE, SESSION_TTL, GRANT_TTL
from tests import test_demo_lan as fixture


class DashboardSessionTests(unittest.TestCase):
    def test_one_use_expiry_rotation_bounds_and_csrf(self):
        now = [100.0]
        sessions = Sessions(clock=lambda: now[0])
        old = sessions.issue()
        code = sessions.issue()
        self.assertIsNone(sessions.login(old))
        cookie, session = sessions.login(code)
        self.assertIsNone(sessions.login(code))
        self.assertIsNone(sessions.authenticate(cookie, 'incorrect-csrf'))
        self.assertIsNotNone(sessions.authenticate(cookie, session['csrf']))
        for _ in range(7):
            self.assertIsNotNone(sessions.login(sessions.issue()))
        self.assertIsNone(sessions.login(sessions.issue()))
        now[0] += SESSION_TTL
        self.assertIsNone(sessions.authenticate(cookie))
        code = sessions.issue()
        now[0] += GRANT_TTL
        self.assertIsNone(sessions.login(code))
        cookie, _ = sessions.login(sessions.issue())
        sessions.logout(cookie)
        self.assertIsNone(sessions.authenticate(cookie))
        self.assertIsNone(sessions.login('<invalid>'))


class DashboardAPITests(unittest.TestCase):
    script = fixture.DemoLANTests.script
    run_cli = fixture.DemoLANTests.run_cli
    free_port = staticmethod(fixture.DemoLANTests.free_port)
    command_result = fixture.DemoLANTests.command_result
    command = fixture.DemoLANTests.command
    stop = fixture.DemoLANTests.stop
    wait_for = fixture.DemoLANTests.wait_for
    seen = fixture.DemoLANTests.seen
    admin = fixture.DemoLANTests.admin
    upload = fixture.DemoLANTests.upload

    def start(self, root, command):
        if command != 'run-controller':
            return fixture.DemoLANTests.start(self, root, command)
        if not hasattr(self, 'dashboard_port'):
            self.dashboard_port = self.free_port()
            while self.dashboard_port == self.port:
                self.dashboard_port = self.free_port()
            self.command(root, 'dashboard-init', '--port', str(self.dashboard_port))
        log = (self.root / ('dashboard-controller-' + str(time.monotonic_ns()))).open('w+')
        self.addCleanup(log.close)
        process = subprocess.Popen(['sh', str(self.source / 'scripts/demo-alpha.sh'), '--state', str(root), command, '--dashboard'],
                                   env=self.env, cwd=self.root, stdout=log, stderr=log, text=True)
        self.addCleanup(self.stop, process)
        # Controller API readiness does not imply this separate TLS listener is up.
        # Probe ONLY a CA-verified handshake before the first HTTP/session assertion;
        # never retry/consume an old cookie or accept a transient HTTP200 as readiness.
        context = ssl.create_default_context(cafile=str(root / 'dashboard/ca.crt'))
        def dashboard_tls_ready():
            if process.poll() is not None:
                self.fail('synthetic dashboard exited before TLS readiness')
            connection = http.client.HTTPSConnection('127.0.0.1', self.dashboard_port,
                                                     context=context, timeout=1)
            try:
                connection.connect()
                return True
            finally:
                connection.close()
        self.wait_for(dashboard_tls_ready)
        return process

    def setUp(self):
        fixture.DemoLANTests.setUp(self)
        self.browser_origin = 'https://127.0.0.1:' + str(self.dashboard_port)
        self.context = ssl.create_default_context(cafile=str(self.controller / 'dashboard/ca.crt'))
        self.cookie, self.csrf = '', ''
        self.login()

    def http(self, method, path, obj=None, *, body=None, authenticated=True, headers=None, json_response=True):
        data = json.dumps(obj).encode() if obj is not None else body
        sent = {'Origin': self.browser_origin}
        if obj is not None:
            sent['Content-Type'] = 'application/json'
        if authenticated and self.cookie:
            sent.update(Cookie=self.cookie, **{'X-ASC-CSRF': self.csrf})
        if headers:
            sent.update(headers)
        conn = http.client.HTTPSConnection('127.0.0.1', self.dashboard_port, context=self.context, timeout=30)
        try:
            conn.request(method, path, data, sent)
            response = conn.getresponse()
            raw = response.read()
            return response.status, dict(response.getheaders()), json.loads(raw) if json_response and raw else raw
        finally:
            conn.close()

    def login(self):
        grant = self.command(self.controller, 'dashboard-code')
        status, headers, reply = self.http('POST', '/api/login', {'code': grant['code']}, authenticated=False)
        self.assertEqual(status, 200, reply)
        parsed = SimpleCookie(headers['Set-Cookie'])
        self.cookie = COOKIE + '=' + parsed[COOKIE].value
        self.csrf = reply['csrf']
        return grant['code'], headers

    def prepare(self, key='dashboard_upload_01', name='dashboard/real.bin'):
        status, _, reply = self.http('POST', '/api/uploads', {'logical_path': name, 'size': len(self.data),
                                      'sha256': hashlib.sha256(self.data).hexdigest(), 'idempotency_key': key})
        self.assertEqual(status, 200, reply)
        return reply

    def send_file(self, key='dashboard_upload_01', name='dashboard/real.bin'):
        plan = self.prepare(key, name)
        if plan['completed']:
            return plan['file']
        status, _, reply = self.http('PUT', '/api/uploads/' + plan['transfer_id'], body=self.data,
                                    headers={'Content-Type': 'application/octet-stream'})
        self.assertIn(status, (200, 202), reply)
        file_id = reply['file']['file_id']
        def ready():
            status, _, entry = self.http('GET', '/api/files/' + file_id)
            self.assertEqual(status, 200, entry)
            return entry if entry['protected'] else False
        return self.wait_for(ready)

    def test_ca_trust_san_owner_login_cookie_csrf_origin_and_no_secret_views(self):
        with self.assertRaises(ssl.SSLCertVerificationError):
            conn = http.client.HTTPSConnection('127.0.0.1', self.dashboard_port, context=ssl.create_default_context(), timeout=5)
            try: conn.request('GET', '/api/session')
            finally: conn.close()
        with self.assertRaises(ssl.SSLCertVerificationError):
            conn = http.client.HTTPSConnection('localhost', self.dashboard_port, context=self.context, timeout=5)
            try: conn.request('GET', '/api/session')
            finally: conn.close()
        code, headers = self.login()
        for flag in ('Secure', 'HttpOnly', 'SameSite=Strict', 'Path=/'):
            self.assertIn(flag, headers['Set-Cookie'])
        self.assertEqual(self.http('POST', '/api/login', {'code': code}, authenticated=False)[0], 401)
        self.assertEqual(self.http('GET', '/api/state', authenticated=False)[0], 401)
        self.assertEqual(self.http('GET', '/api/state', headers={'X-ASC-CSRF': ''})[0], 401)
        self.assertEqual(self.http('POST', '/api/refresh', {}, headers={'Origin': 'https://attacker.invalid'})[0], 403)
        self.assertEqual(self.http('GET', '/api/state', headers={'Host': 'attacker.invalid'})[0], 403)
        status, response_headers, state = self.http('POST', '/api/refresh', {})
        self.assertEqual(status, 200, state)
        self.assertEqual(state['counts']['paired_nodes'], 2)
        self.assertEqual(state['counts']['online'], 2)
        serialized = json.dumps(state)
        for value in (self.admin(), self.pin, self.nodes[0]['cfg']['token'], str(self.controller)):
            self.assertNotIn(value, serialized)
        self.assertIn("frame-ancestors 'none'", response_headers['Content-Security-Policy'])
        self.assertEqual(response_headers['Cache-Control'], 'no-store')
        with self.assertRaises(ClientError) as denied:
            request_json(self.origin, self.pin, 'POST', '/demo/v1/dashboard/code', {}, self.nodes[0]['cfg']['token'])
        self.assertEqual(denied.exception.status, 401)
        self.assertEqual(self.http('POST', '/api/logout', {})[0], 200)
        self.assertEqual(self.http('GET', '/api/state')[0], 401)

    def test_actual_upload_two_domains_sha_fallback_and_idempotency(self):
        entry = self.send_file()
        self.assertEqual(entry['verified_replicas'], 2)
        self.assertEqual(entry['available_replicas'], 2)
        self.assertEqual(len({r['node_id'] for r in entry['replicas']}), 2)
        again = self.send_file()
        self.assertEqual(again['file_id'], entry['file_id'])
        status, headers, content = self.http('GET', '/api/files/' + entry['file_id'] + '/content', json_response=False)
        self.assertEqual(status, 200)
        self.assertEqual(content, self.data)
        self.assertEqual(headers['X-ASC-SHA256'], hashlib.sha256(content).hexdigest())
        stopped = next(n for n in self.nodes if n['cfg']['node_id'] == entry['replicas'][0]['node_id'])
        self.stop(stopped['process'])
        status, _, content = self.http('GET', '/api/files/' + entry['file_id'] + '/content', json_response=False)
        self.assertEqual((status, content), (200, self.data))
        status, _, state = self.http('POST', '/api/refresh', {})
        self.assertEqual(status, 200)
        self.assertFalse(state['files'][0]['protected'])
        denied = self.http('POST', '/api/uploads', {'logical_path': 'unsafe.bin', 'size': len(self.data),
                           'sha256': hashlib.sha256(self.data).hexdigest(), 'idempotency_key': 'dashboard_unsafe_new'})
        self.assertEqual(denied[0], 507)
        with contextlib.closing(sqlite3.connect(self.controller / 'controller/registry.sqlite3')) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM catalog_files').fetchone()[0], 1)

    def test_bounded_body_bad_sha_ticket_scope_traversal_and_disabled_mutations(self):
        plan = self.prepare()
        path = '/api/uploads/' + plan['transfer_id']
        status, _, _ = self.http('PUT', path, body=b'x' * len(self.data), headers={'Content-Type': 'application/octet-stream'})
        self.assertEqual(status, 422)
        status, _, progress = self.http('GET', path)
        self.assertEqual(status, 200)
        self.assertEqual(progress['received_bytes'], len(self.data))
        self.assertIsNone(progress['checksum_verified_bytes'])
        self.assertFalse(progress['protected'])
        old_cookie, old_csrf = self.cookie, self.csrf
        self.login()
        self.assertEqual(self.http('GET', path)[0], 404)  # Ticket is bound to its original session.
        self.cookie, self.csrf = old_cookie, old_csrf
        self.assertEqual(self.http('GET', '/api/files/11111111-1111-4111-8111-111111111111/content', authenticated=False)[0], 401)
        for invalid in ('/../controller/controller.json', '/%2e%2e/server.key', '/api/state?token=not-a-real-secret', 'https://attacker.invalid/api/state'):
            self.assertEqual(self.http('GET', invalid)[0], 400)
        for invalid in ('/api/approve', '/api/gc', '/api/replication/policy'):
            self.assertEqual(self.http('POST', invalid, {})[0], 404)
        status, _, _ = self.http('POST', '/api/uploads', {'logical_path': 'large.bin', 'size': 32 * 1024**2 + 1,
                  'sha256': '0' * 64, 'idempotency_key': 'dashboard_large_upload'})
        self.assertEqual(status, 413)
        self.assertEqual(list((self.controller / 'dashboard/spool').iterdir()), [])

    def test_unknown_capacity_and_restart_invalidate_browser_sessions(self):
        self.http('POST', '/api/refresh', {})
        with contextlib.closing(sqlite3.connect(self.controller / 'controller/registry.sqlite3')) as db, db:
            db.execute("UPDATE catalog_nodes SET checked_at=0,capabilities='{}'")
        status, _, view = self.http('GET', '/api/state')
        self.assertEqual(status, 200)
        for name in ('approved_quota_bytes', 'used_bytes', 'available_bytes'):
            self.assertIsNone(view['capacity'][name])
        self.assertTrue(all(len(n['volumes']) == 1 for n in view['nodes']))
        self.assertTrue(all(v['free_bytes'] is None for n in view['nodes'] for v in n['volumes']))
        before = {p.name: p.read_bytes() for p in (self.controller / 'dashboard').glob('*.key')}
        self.stop(self.controller_process)
        for node in self.nodes:
            self.stop(node['process'])
        self.controller_process = self.start(self.controller, 'run-controller')
        self.wait_for(lambda: request_json(self.origin, self.pin, 'GET', '/api/v1/info'))
        self.assertEqual(self.http('GET', '/api/state')[0], 401)
        self.assertEqual(before, {p.name: p.read_bytes() for p in (self.controller / 'dashboard').glob('*.key')})
        self.stop(self.controller_process)
        setup = self.command(self.controller, 'dashboard-init', '--port', str(self.dashboard_port))
        self.assertEqual(setup['url'], self.browser_origin)
        self.assertEqual(before, {p.name: p.read_bytes() for p in (self.controller / 'dashboard').glob('*.key')})

    def test_same_failure_domain_never_reports_two_copies_and_limits_precede_body(self):
        entry = self.send_file()
        node = self.nodes[1]
        self.command(self.controller, 'approve', '--node-id', node['cfg']['node_id'], '--volume-id', node['volume'],
                     '--origin', 'https://127.0.0.1:' + str(node['port']), '--pin', node['pin'], '--domain', 'phone-0')
        status, _, state = self.http('POST', '/api/refresh', {})
        self.assertEqual(status, 200, state)
        self.assertFalse(state['files'][0]['protected'])
        self.assertEqual(state['files'][0]['verified_replicas'], 1)
        self.assertIsNone(state['capacity']['available_bytes'])
        self.assertEqual(self.http('POST', '/api/uploads', {'logical_path': 'no-domain.bin', 'size': len(self.data),
                  'sha256': hashlib.sha256(self.data).hexdigest(), 'idempotency_key': 'dashboard_same_domain'})[0], 507)
        # Declare oversized JSON but transmit no body: early refusal, no blocking read/mutation.
        conn = http.client.HTTPSConnection('127.0.0.1', self.dashboard_port, context=self.context, timeout=5)
        try:
            conn.putrequest('POST', '/api/uploads')
            for k, v in {'Origin': self.browser_origin, 'Cookie': self.cookie, 'X-ASC-CSRF': self.csrf,
                         'Content-Type': 'application/json', 'Content-Length': '8193'}.items():
                conn.putheader(k, v)
            conn.endheaders()
            reply = conn.getresponse()
            self.assertEqual(reply.status, 413)
            reply.read()
        finally:
            conn.close()
        self.assertEqual(self.http('GET', '/api/state', headers={'Cookie': COOKIE + '=broken; bad[=x'})[0], 401)
        ca = self.home / 'exported-public-ca.crt'
        self.command(self.controller, 'dashboard-trust', '--out', str(ca))
        self.assertEqual(ca.read_bytes(), (self.controller / 'dashboard/ca.crt').read_bytes())
        self.assertNotIn(b'PRIVATE', ca.read_bytes())
        self.assertNotEqual(self.command_result(self.controller, 'dashboard-trust', '--out', str(ca)).returncode, 0)
        self.assertNotEqual(self.command_result(self.controller, 'dashboard-init', '--port', str(self.dashboard_port)).returncode, 0)
        self.assertEqual(entry['verified_replicas'], 2)  # Historical observation before domain reapproval.


    def test_public_pwa_assets_are_fixed_network_only_and_never_auth_data(self):
        from asc.demo.dashboard.assets import ASSETS
        import struct
        for route, (name, mime) in ASSETS.items():
            status, headers, raw = self.http('GET', route, authenticated=False, json_response=False)
            self.assertEqual(status, 200, route)
            self.assertEqual(headers['Content-Type'], mime)
            self.assertEqual(headers['Cache-Control'], 'no-store')
            self.assertNotIn('Set-Cookie', headers)
            self.assertIn("worker-src 'self'", headers['Content-Security-Policy'])
            self.assertIn("manifest-src 'self'", headers['Content-Security-Policy'])
            if name.endswith('.png'):
                self.assertTrue(raw.startswith(b'\x89PNG\r\n\x1a\n'))
                width,height=struct.unpack('>II',raw[16:24])
                self.assertEqual((width,height),(192,192) if '192' in name else (512,512))
        status, _, manifest = self.http('GET','/manifest.webmanifest',authenticated=False)
        self.assertEqual(status,200)
        self.assertEqual((manifest['id'],manifest['start_url'],manifest['scope']),('/','/','/'))
        self.assertEqual(manifest['display'],'standalone')
        self.assertEqual(len(manifest['icons']),2)
        self.assertEqual(self.http('GET','/assets/private.key',authenticated=False)[0],401)
        self.assertEqual(self.http('GET','/assets/%2e%2e/state',authenticated=False)[0],400)
        self.assertEqual(self.http('GET','/api/state',authenticated=False)[0],401)


if __name__ == '__main__':
    unittest.main()
