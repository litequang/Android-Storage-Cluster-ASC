"""Real Core Registry/TLS with explicit native-context CAS adapter on Linux.

MemoryCredentials is test-only, NOT Keystore evidence; Android wiring is g.2b.
"""
import hashlib
import http.server
import json
from pathlib import Path
import secrets
import ssl
import tempfile
import threading
import unittest
from unittest.mock import patch
import uuid

from asc.client import ClientError
from asc.identity import make_cert
from asc.node.context import NodeContext, ContextLocked
from asc.node.enrollment import NativeEnrollment, EnrollmentRefused, public_request
from asc.server import Server
from asc.store import Registry
from test_native_context import MemoryCredentials, synthetic_build
from test_quick_join import JoinProxy


class NativeEnrollmentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.cluster = str(uuid.uuid4())
        self.reg = Registry(self.root / 'registry.sqlite3'); self.reg.initialize(self.cluster)
        make_cert(self.root / 'fixture.crt', self.root / 'fixture.key')
        cert = (self.root / 'fixture.crt').read_text()
        self.pin = hashlib.sha256(ssl.PEM_cert_to_DER_cert(cert)).hexdigest()
        self.tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.tls.load_cert_chain(self.root / 'fixture.crt', self.root / 'fixture.key')
        self.server = Server(('127.0.0.1', 0), self.reg, secrets.token_urlsafe(32)); self.server.tls_context = self.tls
        thread = threading.Thread(target=self.server.serve_forever, daemon=True); thread.start()
        self.addCleanup(lambda: (self.server.shutdown(), self.server.server_close(), thread.join()))
        self.origin = 'https://127.0.0.1:' + str(self.server.server_address[1])
        self.parent = self.root / 'private'; self.parent.mkdir(mode=0o700)
        self.store = MemoryCredentials(); self.app = str(uuid.uuid4())
        self.context = NodeContext(self.parent, self.store, self.app, synthetic_build()); self.context.initialize()
        class Certificate:
            def generate(_):
                return json.dumps({'format': 1, 'certificate': cert,
                    'private_key': (self.root / 'fixture.key').read_text(), 'pin': self.pin})
        self.context.prepare_tls(Certificate())
        self.client = NativeEnrollment(self.context)
        self.id = str(uuid.uuid4()); self.code = self.reg.add_pair_code()
        self.profile = {'protected': False, 'model': 'synthetic native context', 'memory_mb': None}

    def join(self, **change):
        arguments = dict(request_id=self.id, origin=self.origin, pin=self.pin, cluster=self.cluster,
                         name='Native context fixture', code=self.code, profile=self.profile)
        arguments.update(change)
        return self.client.join(**arguments)

    def proxy(self, drop=False, override=None, port=0):
        server = http.server.ThreadingHTTPServer(('127.0.0.1', port), JoinProxy)
        server.origin, server.pin, server.drop, server.dropped = self.origin, self.pin, drop, False
        server.override, server.join_calls = override, 0
        server.socket = self.tls.wrap_socket(server.socket, server_side=True)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        self.addCleanup(lambda: (server.shutdown(), server.server_close(), thread.join()))
        return server, thread, 'https://127.0.0.1:' + str(server.server_address[1])

    def test_real_join_identity_is_private_pending_approval_and_retry_is_read_only(self):
        first = self.join(); node = self.context.load()['node']
        self.assertEqual(first['enrollment'], 'ENROLLED_PENDING_APPROVAL')
        self.assertEqual(first['node_id'], node['node_id']); self.assertEqual(first['cluster_id'], self.cluster)
        self.assertIsNone(first['storage_approved']); self.assertIsNone(first['failure_domain_approved'])
        self.assertFalse(first['runtime_start_supported']); self.assertFalse(first['writer_authority'])
        self.assertNotIn(node['token'], json.dumps(first)); self.assertNotIn(self.code, json.dumps(first))
        self.assertIsNone(self.context.load()['pending'])
        raw = self.store.raw
        with patch('asc.node.enrollment.request_json', side_effect=AssertionError('no reinstall network')):
            self.assertEqual(self.join(), first)
        self.assertEqual(raw, self.store.raw)
        self.assertTrue(self.reg.heartbeat(node['node_id'], node['token'], self.profile))
        with self.reg.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM catalog_nodes').fetchone()[0], 0)
        self.assertFalse((self.context.home / 'node.json').exists())

    def test_actual_successful_tls_ack_loss_resume_keeps_operation_token_and_node(self):
        proxy, _, origin = self.proxy(drop=True)
        with self.assertRaises((OSError, ClientError)):
            self.join(origin=origin)
        self.assertTrue(proxy.dropped); self.assertEqual(proxy.join_calls, 1)
        saved = self.context.load()['pending']; token = saved['operation']['payload']['enrollment_token']
        self.assertEqual(len(self.reg.snapshot()['nodes']), 1)
        public = self.context.public_status()
        self.assertEqual(public['enrollment'], 'PENDING_RECEIPT'); self.assertNotIn(token, json.dumps(public))
        restarted = NodeContext(self.parent, self.store, self.app, synthetic_build())
        result = NativeEnrollment(restarted).resume()
        self.assertEqual(result['enrollment'], 'ENROLLED_PENDING_APPROVAL')
        self.assertEqual(restarted.load()['node']['token'], token)
        self.assertEqual(result['node_id'], self.reg.snapshot()['nodes'][0]['node_id'])
        self.assertEqual(len(self.reg.snapshot()['nodes']), 1)

    def test_expired_code_replacement_retains_original_private_operation(self):
        with self.reg.connect() as db:
            db.execute('UPDATE join_codes SET expires_at=0')
        with self.assertRaises(ClientError): self.join()
        before = self.context.load()['pending']['operation']['payload'].copy()
        code = self.reg.add_pair_code()
        result = self.client.replace_code(code)
        self.assertEqual(result['enrollment'], 'ENROLLED_PENDING_APPROVAL')
        self.assertEqual(self.context.load()['node']['token'], before['enrollment_token'])
        self.assertEqual(len(self.reg.snapshot()['nodes']), 1)

    def test_actual_controller_disconnect_and_reconnect_preserve_pending(self):
        proxy, thread, origin = self.proxy(drop=True)
        with self.assertRaises((OSError, ClientError)): self.join(origin=origin)
        saved = self.store.raw
        port = proxy.server_address[1]
        proxy.shutdown(); proxy.server_close(); thread.join()
        with self.assertRaises((OSError, ClientError)): self.client.resume()
        self.assertEqual(self.store.raw, saved)
        self.proxy(port=port)
        restarted = NodeContext(self.parent, self.store, self.app, synthetic_build())
        result = NativeEnrollment(restarted).resume()
        self.assertEqual(result['enrollment'], 'ENROLLED_PENDING_APPROVAL')
        self.assertEqual(len(self.reg.snapshot()['nodes']), 1)
        self.assertEqual(restarted.load()['node']['token'],
                         json.loads(saved)['pending']['operation']['payload']['enrollment_token'])

    def test_wrong_pin_cluster_runtime_and_protected_profile_never_create_pending(self):
        original = self.store.raw
        for args in ({'pin': '0' * 64}, {'cluster': str(uuid.uuid4())}, {'profile': {'protected': True}}):
            with self.assertRaises((ClientError, EnrollmentRefused)): self.join(**args)
            self.assertEqual(self.store.raw, original)
        _, _, origin = self.proxy(override={'mode': 'core-quorum', 'raft_enabled': True})
        with self.assertRaises(EnrollmentRefused): self.join(origin=origin)
        self.assertEqual(self.store.raw, original); self.assertEqual(len(self.reg.snapshot()['nodes']), 0)

    def test_pending_conflict_and_missing_or_corrupt_state_hold_original_operation(self):
        proxy, _, origin = self.proxy(drop=True)
        with self.assertRaises((OSError, ClientError)): self.join(origin=origin)
        original = self.store.raw
        for change in ({'request_id': str(uuid.uuid4())}, {'name': 'different'}, {'code': secrets.token_hex(6)}):
            with self.assertRaises(EnrollmentRefused): self.join(origin=origin, **change)
            self.assertEqual(self.store.raw, original)
        self.assertEqual(proxy.join_calls, 1)
        for value in (None, '{}'):
            self.store.raw = value
            with self.assertRaises(ContextLocked): self.client.resume()
            self.assertEqual(self.store.raw, value)
        self.store.raw = original
        self.assertEqual(self.client.resume()['enrollment'], 'ENROLLED_PENDING_APPROVAL')

    def test_node_publication_failure_replays_same_committed_server_identity(self):
        publish = self.store.compare_exchange
        def fail_node(expected, replacement):
            if json.loads(replacement)['node'] is not None:
                raise OSError('injected lost private publication')
            return publish(expected, replacement)
        with patch.object(self.store, 'compare_exchange', side_effect=fail_node):
            with self.assertRaises(OSError): self.join()
        self.assertEqual(len(self.reg.snapshot()['nodes']), 1)
        token = self.context.load()['pending']['operation']['payload']['enrollment_token']
        self.assertEqual(self.client.resume()['enrollment'], 'ENROLLED_PENDING_APPROVAL')
        self.assertEqual(self.context.load()['node']['token'], token)
        self.assertEqual(len(self.reg.snapshot()['nodes']), 1)

    def test_authenticated_reply_corruption_cannot_publish_identity(self):
        from asc.node import enrollment
        transport = enrollment.request_json
        def wrong_reply(origin, pin, method, path, *args, **kwargs):
            reply = transport(origin, pin, method, path, *args, **kwargs)
            if path == '/api/v1/join':
                return dict(reply, token=secrets.token_urlsafe(32))
            return reply
        with patch('asc.node.enrollment.request_json', side_effect=wrong_reply):
            with self.assertRaises(ClientError): self.join()
        self.assertIsNone(self.context.load()['node'])
        self.assertIsNotNone(self.context.load()['pending'])
        self.assertEqual(len(self.reg.snapshot()['nodes']), 1)
        self.assertEqual(self.client.resume()['enrollment'], 'ENROLLED_PENDING_APPROVAL')
        self.assertEqual(len(self.reg.snapshot()['nodes']), 1)

    def test_unconfigured_tls_and_stale_enrollment_never_reinitialize_or_repair(self):
        parent = self.root / 'no-tls'; parent.mkdir(mode=0o700)
        store = MemoryCredentials(); context = NodeContext(parent, store, str(uuid.uuid4()), synthetic_build())
        context.initialize()
        with self.assertRaises(EnrollmentRefused):
            NativeEnrollment(context).join(self.id, self.origin, self.pin, self.cluster,
                'native fixture', self.code, self.profile)
        self.assertIsNone(context.load()['pending']); self.assertEqual(len(self.reg.snapshot()['nodes']), 0)
        result = self.join(); node = self.context.load()['node']; self.reg.revoke(node['node_id'])
        before = self.store.raw
        self.assertEqual(self.join()['controller_confirmation'], 'HISTORICAL_JOIN_RECEIPT')
        self.assertEqual(self.store.raw, before); self.assertEqual(result['node_id'], node['node_id'])
        with self.assertRaises(EnrollmentRefused): self.join(cluster=str(uuid.uuid4()))
        self.assertFalse(self.reg.heartbeat(node['node_id'], node['token'], self.profile))

    def test_public_native_boundary_redacts_failures_and_never_claims_success(self):
        self.assertEqual(public_request(self.context, 'shell')['error'], 'invalid_request')
        with self.reg.connect() as db:
            db.execute('UPDATE join_codes SET expires_at=0')
        result = public_request(self.context, 'join', self.id, self.origin, self.pin,
                                self.cluster, 'native fixture', self.code, self.profile)
        self.assertFalse(result['ok']); self.assertEqual(result['error'], 'invalid_or_expired_code')
        self.assertEqual(result['enrollment'], 'PENDING_RECEIPT')
        private = self.context.load()['pending']['operation']['payload']
        for secret in (self.code, private['enrollment_token'], private['enrollment_id']):
            self.assertNotIn(secret, json.dumps(result))
        before = self.store.raw
        with patch('asc.node.enrollment.request_json', side_effect=OSError('sensitive injected exception')):
            failure = public_request(self.context, 'resume')
        self.assertFalse(failure['ok']); self.assertEqual(failure['error'], 'enrollment_unconfirmed')
        self.assertNotIn('sensitive', json.dumps(failure)); self.assertEqual(before, self.store.raw)
        success = public_request(self.context, 'replace_code', self.reg.add_pair_code())
        self.assertTrue(success['ok']); self.assertEqual(success['enrollment'], 'ENROLLED_PENDING_APPROVAL')
        self.store.raw = '{}'
        held = public_request(self.context, 'resume')
        self.assertFalse(held['ok']); self.assertEqual(held['error'], 'native_context_locked')
        self.assertEqual(held['enrollment'], 'UNKNOWN'); self.assertEqual(self.store.raw, '{}')
