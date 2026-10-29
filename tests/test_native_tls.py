"""Actual Linux TLS/sealed anonymous key loader; Android X.509 proof is separate."""
import hashlib
import json
import os
from pathlib import Path
import socket
import ssl
import subprocess
import tempfile
import threading
import types
import unittest
from unittest.mock import patch
import uuid

from asc.catalog.common import canonical
from asc.client import connect_pinned, ClientError
from asc.identity import make_cert
from asc.node.context import ContextLocked, NodeContext
from asc.node.tls import _sealed_bytes, server_context
from test_native_context import MemoryCredentials, synthetic_build


class NativeTLSTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        # Fixture generation uses the existing Linux development dependency; the
        # product loader never calls it. Android generates with actual BC/JCA.
        make_cert(self.root / 'fixture.crt', self.root / 'fixture.key')
        cert = (self.root / 'fixture.crt').read_text()
        self.identity = {'format': 1, 'certificate': cert,
                         'private_key': (self.root / 'fixture.key').read_text(),
                         'pin': hashlib.sha256(ssl.PEM_cert_to_DER_cert(cert)).hexdigest()}
        self.store = MemoryCredentials()
        self.app = str(uuid.uuid4())
        self.context = NodeContext(self.root, self.store, self.app, synthetic_build())
        self.context.initialize()
        identity = self.identity
        class FixtureCertificateProvider:
            calls = 0
            def generate(provider):
                provider.calls += 1
                return json.dumps(identity)
        self.certs = FixtureCertificateProvider()

    def test_prepare_repeat_and_restart_reuse_exact_certificate_and_key(self):
        before = self.context.load()
        with patch('subprocess.run', side_effect=AssertionError('no runtime OpenSSL')):
            state = self.context.prepare_tls(self.certs)
            ciphertext = self.store.raw
            self.assertEqual(state['tls'], 'IDENTITY_READY')
            self.assertEqual(state['tls_pin'], self.identity['pin'])
            self.assertEqual(state, self.context.prepare_tls(self.certs))
            restarted = NodeContext(self.root, self.store, self.app, synthetic_build())
            self.assertEqual(state, restarted.prepare_tls(self.certs))
            self.assertEqual(ciphertext, self.store.raw)
            self.assertEqual(self.certs.calls, 1)
            self.assertIsInstance(restarted.tls_context(), ssl.SSLContext)
        self.assertEqual(before['context_id'], self.context.load()['context_id'])
        self.assertEqual(self.context.load()['revision'], before['revision'] + 1)
        self.assertIsNone(state['node_id']); self.assertIsNone(state['cluster_id'])
        self.assertFalse(state['runtime_start_supported']); self.assertFalse(state['writer_authority'])
        self.assertNotIn('private_key', state); self.assertNotIn('certificate', state)
        self.assertEqual(sorted(p.name for p in self.context.home.iterdir()),
                         ['context.json', 'native-context.lock'])

    def test_actual_tls_correct_pin_and_sha_with_no_plaintext_before_pin(self):
        self.context.prepare_tls(self.certs)
        context = self.context.tls_context()
        listener = socket.socket(); self.addCleanup(listener.close)
        listener.bind(('127.0.0.1', 0)); listener.listen(2); listener.settimeout(10)
        received, errors = [], []
        def serve():
            try:
                for attempt in range(2):
                    raw, _ = listener.accept(); raw.settimeout(10)
                    try:
                        with context.wrap_socket(raw, server_side=True) as peer:
                            data = peer.recv(1024); received.append(data)
                            if data: peer.sendall(hashlib.sha256(data).hexdigest().encode())
                    except (BrokenPipeError, ConnectionResetError, ssl.SSLEOFError):
                        # Wrong-pin client deliberately closes after handshake;
                        # TLS1.3 ticket write can observe reset before application
                        # recv. Record that separately, never as a successful read.
                        if attempt != 0:
                            raise
                        received.append('CLOSED_BEFORE_DATA')
            except BaseException as exc:
                errors.append(type(exc).__name__)
        worker = threading.Thread(target=serve, daemon=True); worker.start()
        origin = 'https://127.0.0.1:' + str(listener.getsockname()[1])
        with self.assertRaises(ClientError):
            connect_pinned(origin, '0' * 64)
        conn = connect_pinned(origin, self.identity['pin'])
        try:
            body = b'actual Linux memfd TLS fixture'
            conn.sock.sendall(body)
            self.assertEqual(conn.sock.recv(1024), hashlib.sha256(body).hexdigest().encode())
        finally:
            conn.close()
        worker.join(12)
        self.assertFalse(worker.is_alive()); self.assertEqual(errors, [])
        self.assertEqual(len(received), 2)
        self.assertIn(received[0], [b'', 'CLOSED_BEFORE_DATA'])
        self.assertEqual(received[1], body)

    def test_anonymous_files_are_immutable_and_closed(self):
        with _sealed_bytes(b'owned synthetic fixture') as fd:
            self.assertEqual(os.pread(fd, 100, 0), b'owned synthetic fixture')
            with self.assertRaises(PermissionError):
                os.write(fd, b'not permitted')
        with self.assertRaises(OSError):
            os.fstat(fd)
        before = len(list(Path('/proc/self/fd').iterdir()))
        for _ in range(10):
            server_context(self.identity)
        self.assertEqual(len(list(Path('/proc/self/fd').iterdir())), before)

    def test_unsupported_anonymous_loader_has_no_disk_fallback(self):
        before = self.store.raw
        with patch('os.memfd_create', side_effect=PermissionError('synthetic SELinux denial')), \
                patch('ctypes.CDLL') as native:
            with self.assertRaises(ContextLocked):
                self.context.prepare_tls(self.certs)
            native.assert_not_called()
        self.assertEqual(self.store.raw, before)
        self.assertIsNone(self.context.load()['tls'])
        self.assertEqual(sorted(p.name for p in self.context.home.iterdir()),
                         ['context.json', 'native-context.lock'])

    def test_seal_failure_closes_fd_and_preserves_unconfigured_record(self):
        before = self.store.raw
        count = len(list(Path('/proc/self/fd').iterdir()))
        with patch('fcntl.fcntl', side_effect=PermissionError('injected seal denial')):
            with self.assertRaises(ContextLocked):
                self.context.prepare_tls(self.certs)
        self.assertEqual(count, len(list(Path('/proc/self/fd').iterdir())))
        self.assertEqual(self.store.raw, before)
        self.assertIsNone(self.context.load()['tls'])

    def test_reported_missing_seal_or_closexec_cannot_load_a_key(self):
        import fcntl
        real = fcntl.fcntl
        for operation in (fcntl.F_GET_SEALS, fcntl.F_GETFD):
            def fault(fd, command, *args):
                return 0 if command == operation else real(fd, command, *args)
            before = self.store.raw
            with patch('fcntl.fcntl', side_effect=fault):
                with self.assertRaises(ContextLocked):
                    self.context.prepare_tls(self.certs)
            self.assertEqual(self.store.raw, before)

    def test_native_loader_uses_sealed_readback_without_proc_reopen(self):
        # In-process provider-boundary unit test only, not Android TLS evidence.
        # Android integration separately requires the actual JSSE handshake.
        seen = []
        class Loader:
            def load(_, cert, key):
                seen.append((cert, key))
                return 'test-provider-not-runtime-proof'
        with patch('ssl.SSLContext.load_cert_chain', side_effect=AssertionError('no proc reopen')):
            server_context(self.identity, Loader())
        self.assertEqual(seen, [(self.identity['certificate'], self.identity['private_key'])])

    def test_corrupt_pin_key_certificate_and_alias_formats_refuse(self):
        for change in ({'pin': '0' * 64}, {'format': True}, {'format': 2},
                       {'private_key': 'invalid synthetic key'}, {'certificate': 'invalid fixture'},
                       {'unexpected': 'not a supported field'}):
            with self.assertRaises(ContextLocked) as refused:
                server_context(dict(self.identity, **change))
            self.assertEqual(str(refused.exception), 'native_context_locked')
        make_cert(self.root / 'other.crt', self.root / 'other.key')
        wrong = dict(self.identity, private_key=(self.root / 'other.key').read_text())
        with self.assertRaises(ContextLocked):
            server_context(wrong)
        self.context.prepare_tls(self.certs)
        raw = self.store.raw
        value = json.loads(raw); value['tls']['pin'] = '0' * 64
        self.store.raw = canonical(value).decode()
        with self.assertRaises(ContextLocked):
            self.context.prepare_tls(self.certs)
        self.assertEqual(self.certs.calls, 1)  # No automatic identity rotation on corruption.
        self.assertEqual(json.loads(self.store.raw)['tls']['pin'], '0' * 64)

    def test_exact_f1_source_refuses_new_tls_state_without_mutation(self):
        self.context.prepare_tls(self.certs)
        raw = self.store.raw
        source = subprocess.check_output(['git', 'show',
            '4df6ad6676de2a441991455c71d2e8e2d3aa2685:asc/node/context.py'], text=True,
            cwd=Path(__file__).resolve().parents[1])
        old = types.ModuleType('asc.node.qualification_f1')
        old.__package__ = 'asc.node'
        exec(compile(source, '<exact-published-f1-context>', 'exec'), old.__dict__)
        with self.assertRaises(old.ContextLocked):
            old.NodeContext(self.root, self.store, self.app, synthetic_build()).initialize()
        self.assertEqual(raw, self.store.raw)
