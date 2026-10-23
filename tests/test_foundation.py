import hashlib
import json
from pathlib import Path
import ssl
import tempfile
import threading
import time
import unittest
from unittest import mock

from asc import probe
from asc.planner import recommend
from asc.client import ClientError, request_json
from asc.identity import make_cert, fingerprint_from_pem
from asc.server import Server
from asc.store import Registry


class FoundationTests(unittest.TestCase):
    def test_registry_pair_is_one_time_and_token_works(self):
        with tempfile.TemporaryDirectory() as td:
            db = Registry(Path(td) / 'db.sqlite3')
            db.initialize('test-cluster')
            code = db.add_pair_code(120)
            joined = db.join(code, 'Bphone', {'recommended_role': 'backup-node'})
            self.assertIsNotNone(joined)
            self.assertIsNone(db.join(code, 'attacker', {}))
            self.assertFalse(db.heartbeat(joined['node_id'], 'incorrect', {}))
            self.assertTrue(db.heartbeat(joined['node_id'], joined['token'], {'model': 'A40'}))
            self.assertEqual(db.snapshot()['nodes'][0]['profile']['model'], 'A40')

    def test_cluster_role_planner_never_promotes_protected_or_offline(self):
        rows = [
            {'node_id': 'zte', 'name': 'ZTE', 'online': True,
             'profile': {'recommended_role': 'controller-candidate', 'readiness_score': 85}},
            {'node_id': 'm51', 'name': 'M51', 'online': True,
             'profile': {'recommended_role': 'production-protected', 'protected': True, 'readiness_score': 99}},
            {'node_id': 'xz3', 'name': 'Sony', 'online': False,
             'profile': {'recommended_role': 'storage-and-voter-candidate', 'readiness_score': 100}},
        ]
        plan = {x['node_id']: x['suggested_role'] for x in recommend(rows)}
        self.assertEqual(plan['zte'], 'preferred-controller-candidate')
        self.assertEqual(plan['m51'], 'hosting-protected-observer')
        self.assertEqual(plan['xz3'], 'standby-offline')

    def test_sd_probe_is_bounded_to_existing_app_directory(self):
        with tempfile.TemporaryDirectory() as td:
            candidate = {'app_dir': str(Path(td) / 'Android/data/com.termux/files')}
            self.assertEqual(probe.probe_sd_write(candidate)['status'], 'not_tested')
            Path(candidate['app_dir']).mkdir(parents=True)
            self.assertEqual(probe.probe_sd_write(candidate)['status'], 'pass')
            self.assertEqual(list(Path(candidate['app_dir']).iterdir()), [])

    def test_model_preset_and_protected_mode(self):
        with mock.patch.object(probe, '_cmd', side_effect=lambda *args: 'SM-M515F' if args[-1] == 'ro.product.model' else ('33' if args[-1] == 'ro.build.version.sdk' else 'unknown')):
            p = probe.inspect()
        self.assertTrue(p['protected'])
        self.assertEqual(p['recommended_role'], 'production-protected')

    def test_lan_tls_join_heartbeat_and_certificate_pin(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            cert, key = td / 'server.crt', td / 'server.key'
            make_cert(cert, key)
            pin = fingerprint_from_pem(cert)
            db = Registry(td / 'registry.sqlite3')
            db.initialize('cluster-test')
            server = Server(('127.0.0.1', 0), db, 'admin-secret')
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ctx.load_cert_chain(certfile=str(cert), keyfile=str(key))
            server.socket = ctx.wrap_socket(server.socket, server_side=True)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                origin = f'https://127.0.0.1:{server.server_address[1]}'
                info = request_json(origin, pin, 'GET', '/api/v1/info')
                self.assertEqual(info['raft_enabled'], False)
                with self.assertRaises(ClientError):
                    request_json(origin, 'A' * 64, 'GET', '/api/v1/info')
                code = db.add_pair_code(600)
                joined = request_json(origin, pin, 'POST', '/api/v1/join',
                                      {'code': code, 'name': 'sony-xz3', 'profile': {'model': 'XZ3'}})
                self.assertTrue(joined['token'])
                with self.assertRaises(ClientError):
                    request_json(origin, pin, 'POST', '/api/v1/join',
                                 {'code': code, 'name': 'replay', 'profile': {}})
                with self.assertRaises(ClientError):
                    request_json(origin, pin, 'GET', '/api/v1/nodes')
                snap = request_json(origin, pin, 'POST', '/api/v1/heartbeat',
                                    {'node_id': joined['node_id'], 'profile': {'model': 'XZ3'}},
                                    joined['token'])
                self.assertEqual(snap['nodes'][0]['name'], 'sony-xz3')
                nodeinfo = request_json(origin, pin, 'GET', '/api/v1/nodes', token='admin-secret')
                self.assertEqual(len(nodeinfo['nodes']), 1)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(3)

if __name__ == '__main__':
    unittest.main()
