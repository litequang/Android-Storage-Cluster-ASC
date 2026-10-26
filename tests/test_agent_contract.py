"""Actual Core Registry/pinned TLS heartbeat; no native Agent/FGS claim."""
import copy
import json
from pathlib import Path
import secrets
import ssl
import tempfile
import threading
import unittest
import uuid

from asc.agent import heartbeat
from asc.client import ClientError
from asc.identity import make_cert, fingerprint_from_pem
from asc.server import Server
from asc.store import Registry


class AgentContractTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.cluster = str(uuid.uuid4()); self.registry = Registry(self.root / 'registry.sqlite3')
        self.registry.initialize(self.cluster)
        node = self.registry.join(self.registry.add_pair_code(), 'explicit agent fixture', {'protected': False})
        make_cert(self.root / 'fixture.crt', self.root / 'fixture.key')
        self.pin = fingerprint_from_pem(self.root / 'fixture.crt').lower()
        self.tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); self.tls.minimum_version = ssl.TLSVersion.TLSv1_2
        self.tls.load_cert_chain(self.root / 'fixture.crt', self.root / 'fixture.key')
        self.owner = secrets.token_urlsafe(32)
        self.start_server()
        self.config = dict(node, cluster_id=self.cluster, controller=self.origin, pin=self.pin)

    def start_server(self, port=0):
        server = Server(('127.0.0.1', port), self.registry, self.owner); server.tls_context = self.tls
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        self.addCleanup(lambda: (server.shutdown(), server.server_close(), thread.join()))
        self.server, self.thread = server, thread
        self.origin = 'https://127.0.0.1:' + str(server.server_address[1])

    def test_actual_pinned_heartbeat_preserves_unknown_profile_and_private_identity(self):
        config = copy.deepcopy(self.config)
        profile = {'protected': False, 'model': 'explicit synthetic provider', 'memory_mb': None}
        before = copy.deepcopy(profile)
        reply = heartbeat(self.config, profile)
        self.assertEqual(reply['cluster_id'], self.cluster)
        node = next(n for n in reply['nodes'] if n['node_id'] == self.config['node_id'])
        self.assertEqual(node['profile'], profile); self.assertIsNone(node['profile']['memory_mb'])
        for secret in (self.config['token'], self.owner): self.assertNotIn(secret, json.dumps(reply))
        self.assertEqual(config, self.config); self.assertEqual(profile, before)
        self.assertFalse((self.root / 'node.json').exists())
        with self.registry.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM catalog_nodes').fetchone()[0], 0)

    def test_wrong_pin_never_updates_profile_or_regenerates_credentials(self):
        def persisted():
            with self.registry.connect() as db:
                return [tuple(row) for row in db.execute('SELECT * FROM nodes ORDER BY node_id')]
        before = persisted(); config = dict(self.config, pin='0' * 64)
        with self.assertRaises(ClientError): heartbeat(config, {'model': 'must not reach server'})
        self.assertEqual(before, persisted())
        self.assertTrue(self.registry.authenticate_node(self.config['node_id'], self.config['token']))

    def test_authenticated_cluster_mismatch_refuses_snapshot(self):
        before = copy.deepcopy(self.config)
        with self.assertRaisesRegex(ClientError, 'Cluster ID mismatch'):
            heartbeat(dict(self.config, cluster_id=str(uuid.uuid4())), {'protected': False})
        self.assertEqual(before, self.config)
        self.assertEqual(len(self.registry.snapshot()['nodes']), 1)

    def test_revoked_token_fails_without_repair_or_state_publication(self):
        before = copy.deepcopy(self.config); self.registry.revoke(self.config['node_id'])
        with self.assertRaises(ClientError) as result: heartbeat(self.config, {'protected': False})
        self.assertEqual(result.exception.status, 401)
        self.assertEqual(result.exception.code, 'credential_rejected_repair_required')
        self.assertEqual(before, self.config); self.assertFalse((self.root / 'agent_state.json').exists())
        self.assertFalse(self.registry.authenticate_node(self.config['node_id'], self.config['token']))

    def test_actual_disconnect_reconnect_keeps_same_node_config(self):
        before = copy.deepcopy(self.config); port = self.server.server_address[1]
        heartbeat(self.config, {'protected': False})
        self.server.shutdown(); self.server.server_close(); self.thread.join()
        with self.assertRaises(OSError): heartbeat(self.config, {'protected': False})
        self.assertEqual(before, self.config)
        self.start_server(port)
        reply = heartbeat(self.config, {'protected': False})
        self.assertEqual(reply['cluster_id'], self.cluster)
        self.assertEqual(len(reply['nodes']), 1)
        self.assertEqual(reply['nodes'][0]['node_id'], self.config['node_id'])
        self.assertEqual(before, self.config)
