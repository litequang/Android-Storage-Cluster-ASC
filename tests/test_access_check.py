"""Operator checker: actual TLS/owner services, no account or live-provider access."""
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from asc.access.gateway import initialize
from asc.bridge import private
from tests import test_access_gateway as private_fixture
from tools import check_access as checker


def snapshot(root):
    return {str(p.relative_to(root)): (p.stat().st_ino, p.stat().st_mode,
            hashlib.sha256(p.read_bytes()).hexdigest())
            for p in root.rglob('*') if p.is_file()}


class LocalAccessCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='.asc-access-check-', dir=Path.home())
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'gateway'
        self.cfg = dict(format=1, mode='private-gateway', frontend_origin='https://127.0.0.1:19443',
                        upstream_origin='https://127.0.0.1:18443', upstream_pin='a'*64,
                        upstream_mode='single-writer-demo', max_body_bytes=1024**2)
        initialize(self.root, self.cfg)

    def test_default_is_offline_and_changes_no_private_files_or_identity(self):
        before = snapshot(self.root)
        with patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')):
            result = checker.check(self.root)
        self.assertEqual(result['state'], 'CHECKS_PASSED')
        self.assertEqual(result['checks']['upstream_mode'], 'NOT_REQUESTED')
        self.assertEqual(result['checks']['anonymous_gate'], 'NOT_REQUESTED')
        self.assertEqual(result['remote_reachability'], 'UNKNOWN')
        self.assertEqual(result['quorum_status'], 'UNKNOWN')
        self.assertFalse(result['writer_authority'])
        self.assertFalse(result['live_deployment_accepted'])
        self.assertEqual(snapshot(self.root), before)
        self.assertEqual({p.name for p in self.root.iterdir()}, {'dashboard', 'gateway.json'})

    def test_existing_engine_recovery_markers_links_and_permissions_refuse_before_network(self):
        with patch.object(checker, 'request_json', side_effect=AssertionError('must not probe')):
            for marker in ('demo.json', 'RECOVERY_READ_ONLY.json', '.asc-volume.json'):
                with self.subTest(marker=marker):
                    path = self.root / marker
                    path.write_text('{}'); path.chmod(0o600)
                    before = snapshot(self.root)
                    self.assertEqual(checker.check(self.root, probe_upstream=True)['state'], 'BLOCKED')
                    self.assertEqual(snapshot(self.root), before)
                    path.unlink()  # Only this test's own synthetic refusal marker.
            profile = self.root / 'gateway.json'
            profile.chmod(0o644)
            self.assertEqual(checker.check(self.root)['checks']['profile'], 'BLOCKED')
            profile.chmod(0o600)
            link = self.base / 'linked'; link.symlink_to(self.root, target_is_directory=True)
            self.assertEqual(checker.check(link)['checks']['profile'], 'BLOCKED')

    def test_mismatched_key_fails_without_probe_or_recreation(self):
        other = self.base / 'other'; initialize(other, self.cfg)
        key = self.root / 'dashboard/server.key'
        key.write_bytes((other / 'dashboard/server.key').read_bytes())
        before = snapshot(self.root)
        with patch.object(checker, 'request_json', side_effect=AssertionError('must not probe')):
            result = checker.check(self.root, probe_upstream=True, probe_listener=True)
        self.assertEqual(result['checks']['profile'], 'VERIFIED')
        self.assertEqual(result['checks']['tls_identity'], 'BLOCKED')
        self.assertEqual(snapshot(self.root), before)

    def test_cli_missing_root_no_creation_and_no_sensitive_error_reflection(self):
        path = self.base / 'secret-looking-missing-root'
        cmd = [sys.executable, '-I', '-B', str(checker.ROOT/'tools/check_access.py'), '--root', str(path)]
        run = subprocess.run(cmd, cwd=self.base, capture_output=True, text=True, timeout=30)
        self.assertEqual(run.returncode, 1, run.stderr)
        self.assertEqual(json.loads(run.stdout)['checks']['profile'], 'BLOCKED')
        self.assertEqual(run.stderr, '')
        self.assertNotIn(str(path), run.stdout)
        self.assertFalse(path.exists())
        bad = subprocess.run(cmd + ['--token', 'synthetic-secret'], capture_output=True, text=True, timeout=30)
        self.assertEqual(bad.returncode, 2)
        self.assertNotIn('synthetic-secret', bad.stderr)

    def test_unknown_format_and_missing_certificate_are_not_repaired(self):
        profile = self.root / 'gateway.json'
        profile.write_text(json.dumps(dict(self.cfg, format=99)))
        before = snapshot(self.root)
        self.assertEqual(checker.check(self.root)['checks']['profile'], 'BLOCKED')
        self.assertEqual(snapshot(self.root), before)
        profile.write_text(json.dumps(self.cfg))
        (self.root / 'dashboard/server.crt').unlink()  # Only this fixture's disposable identity.
        before = snapshot(self.root)
        self.assertEqual(checker.check(self.root)['state'], 'BLOCKED')
        self.assertEqual(snapshot(self.root), before)


class PrivateConnectivityCheckTests(unittest.TestCase):
    def setUp(self):
        self.f = private_fixture.PrivateGatewayTests()
        self.addCleanup(self.f.doCleanups); self.f.setUp()

    def test_actual_pinned_backend_trusted_listener_anonymous_gate_and_controller_loss(self):
        before = snapshot(self.f.root)
        result = checker.check(self.f.root, probe_upstream=True, probe_listener=True)
        self.assertEqual(set(result['checks'].values()), {'VERIFIED'}, result)
        self.assertEqual(result['state'], 'CHECKS_PASSED')
        self.assertEqual(result['authenticated_access'], 'NOT_TESTED')
        self.assertFalse(result['writer_authority'])
        self.assertEqual(result['remote_reachability'], 'UNKNOWN')
        self.assertEqual(snapshot(self.f.root), before)
        self.f.f.stop(self.f.f.controller_process)
        result = checker.check(self.f.root, probe_upstream=True, probe_listener=True)
        self.assertEqual(result['state'], 'BLOCKED')
        self.assertEqual(result['checks']['upstream_mode'], 'BLOCKED')
        self.assertEqual(result['checks']['listener_mode'], 'BLOCKED')

    def test_wrong_pin_wrong_mode_and_wrong_frontend_ca_never_fallback(self):
        base = Path(self.f.temp.name)
        for field, value in [('upstream_pin', 'b'*64), ('upstream_mode', 'recovery-read-only')]:
            with self.subTest(field=field):
                root = base / field
                initialize(root, dict(self.f.cfg, **{field: value}))
                result = checker.check(root, probe_upstream=True)
                self.assertEqual(result['checks']['upstream_mode'], 'BLOCKED')
                self.assertEqual(result['state'], 'BLOCKED')
                self.assertEqual(result['quorum_status'], 'UNKNOWN')
        # Same listener address but another profile CA/identity: refuse the actual server.
        root = base / 'other-ca'; initialize(root, self.f.cfg)
        result = checker.check(root, probe_listener=True)
        self.assertEqual(result['checks']['anonymous_gate'], 'BLOCKED')
        self.assertEqual(result['checks']['listener_mode'], 'BLOCKED')

    def test_stopped_listener_is_not_reported_ready_from_valid_local_profile(self):
        self.f.stop_gateway()
        result = checker.check(self.f.root, probe_listener=True)
        self.assertEqual(result['checks']['tls_identity'], 'VERIFIED')
        self.assertEqual(result['checks']['anonymous_gate'], 'BLOCKED')
        self.assertEqual(result['state'], 'BLOCKED')

    def test_tls_service_with_wrong_mode_and_open_anonymous_state_is_refused(self):
        self.f.stop_gateway()
        # Negative-only TLS fixture: a valid certificate is insufficient evidence
        # of the expected API mode or an owner authentication gate.
        class WrongService(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_GET(inner):
                value = ({'mode': 'single-writer-demo', 'read_only': 0}
                         if inner.path == '/api/mode' else {'nodes': []})
                raw = json.dumps(value).encode()
                inner.send_response(200); inner.send_header('Content-Length', str(len(raw)))
                inner.end_headers(); inner.wfile.write(raw)
        server = ThreadingHTTPServer(('127.0.0.1', self.f.port), WrongService)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(self.f.root/'dashboard/server.crt', self.f.root/'dashboard/server.key')
        server.socket = context.wrap_socket(server.socket, server_side=True)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            result = checker.check(self.f.root, probe_listener=True)
            self.assertEqual(result['checks']['tls_identity'], 'VERIFIED')
            self.assertEqual(result['checks']['listener_mode'], 'BLOCKED')
            self.assertEqual(result['checks']['anonymous_gate'], 'BLOCKED')
            self.assertEqual(result['state'], 'BLOCKED')
        finally:
            server.shutdown(); server.server_close(); thread.join()


class EdgeConnectivityCheckTests(unittest.TestCase):
    def test_actual_edge_anonymous_refusal_is_not_authenticated_provider_acceptance(self):
        from tests import test_access_cloudflare as edge_fixture
        f = edge_fixture.EdgeOriginTests(); self.addCleanup(f.doCleanups); f.setUp()
        before = snapshot(f.root)
        # No refresh/JWT/owner login is performed by the checker. Edge runtime's
        # existing real local HTTPS JWKS fixture was prepared independently.
        with patch.object(f.verifier, 'refresh', side_effect=AssertionError('no issuer probe')):
            result = checker.check(f.root, probe_upstream=True, probe_listener=True)
        self.assertEqual(result['state'], 'CHECKS_PASSED', result)
        self.assertEqual(result['checks']['anonymous_gate'], 'VERIFIED')
        self.assertEqual(result['checks']['listener_mode'], 'UNKNOWN')
        self.assertEqual(result['authenticated_access'], 'NOT_TESTED')
        self.assertFalse(result['live_deployment_accepted'])
        self.assertEqual(snapshot(f.root), before)


if __name__ == '__main__':
    unittest.main()
