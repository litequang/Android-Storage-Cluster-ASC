"""Actual existing gateway TLS/session/recovery and Core quorum native client gates."""
import copy
import json
import os
from unittest import mock
import unittest

from asc.identity import fingerprint_from_pem
from asc.catalog.common import CatalogError
from asc.observability import gateway
from asc.observability.native import NativeObserver, ObserverRefused
from asc.observability.core import unavailable
from asc.external.recovery import stage
from tests import test_observer_gateway as fixtures
from tests import test_external as external


class NativeRecoveryObserverTests(unittest.TestCase):
    setUp = external.ExternalBackupTests.setUp
    port = staticmethod(fixtures.GatewayFixture.port)

    def setup_gateway(self):
        backup = self.engine.create(self.source, self.roots)
        self.stage = self.base / 'native-recovery'; self.stage.mkdir(mode=0o700)
        stage(self.store, backup['backup_id'], backup['manifest_sha256'], self.stage,
              self.roots, self.source.doc['cluster_id'], 100)
        self.root = self.base / 'native-gateway'; self.gateway_port = self.port()
        with mock.patch.dict(os.environ, {'HOME': str(self.base)}):
            gateway.init(self.root, '127.0.0.1', self.gateway_port, self.source.doc['cluster_id'],
                         self.source.doc['epoch'], recovery={'root': str(self.stage), 'anchor': backup['manifest_sha256']},
                         source_roots=self.roots, minimum_index=100)
        self.config = dict(endpoint='https://127.0.0.1:' + str(self.gateway_port),
                           pin=fingerprint_from_pem(self.root / 'dashboard/server.crt'),
                           cluster_id=self.source.doc['cluster_id'], epoch=self.source.doc['epoch'],
                           mode='recovery-read-only', minimum_index=100)

    def runtime(self):
        # Existing gateway host policy: temporary operator-private Linux HOME only.
        env = mock.patch.dict(os.environ, {'HOME': str(self.base)})
        env.start(); self.addCleanup(env.stop)
        return gateway.Runtime(self.root)

    def test_actual_tls_owner_session_full_byte_recovery_logout_and_no_disk_state(self):
        self.setup_gateway()
        before = {p.relative_to(self.stage): p.read_bytes() for p in self.stage.rglob('*') if p.is_file()}
        client = NativeObserver(**self.config)
        with self.runtime() as runtime:
            code = runtime.api.sessions.issue()
            view = client.login(code)
            self.assertEqual(view['runtime']['state'], 'RECOVERY READ-ONLY')
            self.assertFalse(view['writer_authority'])
            self.assertFalse(view['backup']['recovery']['credentials_restored'])
            self.assertEqual(view['native_observer']['session_persistence'], 'RAM_ONLY')
            for secret in (code, client.cookie, client.csrf):
                self.assertNotIn(secret, json.dumps(view))
            self.assertEqual(client.state()['backup']['recovery']['objects'], 2)
            self.assertEqual(client.floor, 100)
            client.close()
            self.assertEqual(client.state()['runtime']['state'], 'UNKNOWN')
            self.assertIsNone(client.state()['counts']['files'])
            self.assertIsNone(client.cookie)
        self.assertEqual(before, {p.relative_to(self.stage): p.read_bytes() for p in self.stage.rglob('*') if p.is_file()})
        self.assertFalse((self.stage / 'controller.json').exists())
        self.assertFalse((self.stage / 'registry.sqlite3').exists())

    def test_wrong_pin_and_mode_refuse_before_consuming_grant(self):
        self.setup_gateway()
        with self.runtime() as runtime:
            code = runtime.api.sessions.issue(); grant = copy.deepcopy(runtime.api.sessions.grant)
            for changes in ({'pin': '0' * 64}, {'mode': 'core-quorum'}):
                client = NativeObserver(**dict(self.config, **changes))
                with self.assertRaises(ObserverRefused): client.login(code)
                self.assertIsNone(client.cookie)
                self.assertEqual(runtime.api.sessions.grant, grant)
            actual = NativeObserver(**self.config); actual.login(code); actual.close()

    def test_cluster_epoch_and_checkpoint_mismatch_never_publish_view(self):
        self.setup_gateway()
        with self.runtime() as runtime:
            for changes in ({'cluster_id': 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'},
                            {'epoch': 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb'}, {'minimum_index': 101}):
                client = NativeObserver(**dict(self.config, **changes))
                with self.assertRaises(ObserverRefused): client.login(runtime.api.sessions.issue())
                self.assertIsNone(client.cookie)

    def test_offline_reconnect_process_session_loss_and_server_restart(self):
        self.setup_gateway(); client = NativeObserver(**self.config)
        with self.runtime() as runtime:
            code = runtime.api.sessions.issue(); client.login(code)
            restarted_process = NativeObserver(**self.config)
            self.assertEqual(restarted_process.state()['runtime']['state'], 'UNKNOWN')
            self.assertIsNone(restarted_process.state()['counts']['files'])
            with self.assertRaises(ObserverRefused): restarted_process.login(code)
        offline = client.state()
        self.assertEqual(offline['runtime']['state'], 'UNKNOWN')
        self.assertIsNone(offline['capacity']['available_bytes'])
        with self.runtime() as runtime:
            self.assertEqual(client.state()['native_observer']['error'], 'observer_login_required')
            self.assertIsNone(client.cookie)
            self.assertEqual(client.login(runtime.api.sessions.issue())['runtime']['state'], 'RECOVERY READ-ONLY')
            client.close()

    def test_corrupt_stage_never_becomes_healthy_and_original_bytes_retained(self):
        self.setup_gateway(); client = NativeObserver(**self.config)
        with self.runtime() as runtime:
            client.login(runtime.api.sessions.issue())
            body = next((self.stage / 'objects').glob('*.blob'))
            body.write_bytes(b'actual synthetic corruption')
            state = client.state()
            self.assertEqual(state['runtime']['state'], 'UNKNOWN')
            self.assertIsNone(state['backup']['recovery']['verified_at'])
            self.assertIsNone(state['counts']['files'])
            self.assertFalse(state['writer_authority'])
            self.assertEqual(body.read_bytes(), b'actual synthetic corruption')
            client.close()


class NativeObserverContractTests(unittest.TestCase):
    cluster = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'
    epoch = 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb'

    def client(self, **changes):
        return NativeObserver(**dict(dict(endpoint='https://127.0.0.1:8445', pin='a' * 64,
                                          cluster_id=self.cluster, epoch=self.epoch, mode='core-quorum'), **changes))

    def test_invalid_bindings_and_no_arbitrary_path_or_writer_methods(self):
        for change in ({'mode': 'single-writer-demo'}, {'mode': 'shell'}, {'minimum_index': True},
                       {'endpoint': 'http://127.0.0.1:8445'}, {'endpoint': 'https://8.8.8.8:8445'},
                       {'endpoint': 'https://127.0.0.1:8445/api/state'}, {'pin': 'invalid'}):
            with self.assertRaises((ValueError, CatalogError)):
                self.client(**change)
        client = self.client()
        for method in ('upload', 'download', 'approve', 'start', 'promote', 'gc', 'activate', 'join'):
            self.assertFalse(hasattr(client, method))
        with self.assertRaises(KeyError): client._request('promote')

    def test_leader_flag_alone_is_downgraded_and_checkpoint_floor_never_regresses(self):
        client = self.client()
        value = unavailable(cluster_id=self.cluster, epoch=self.epoch)
        value['runtime'].update(state='ONLINE', leader_confirmed=True, leader_id='old-leader',
                                 checkpoint={'index': 10, 'term': 2, 'document_sha256': 'a' * 64})
        with mock.patch.object(client, '_request', return_value=(value, [])):
            result = client._state()
            self.assertEqual(result['runtime']['state'], 'UNKNOWN')
            self.assertFalse(result['runtime']['leader_confirmed'])
            self.assertFalse(result['writer_authority'])
            value['runtime']['checkpoint']['index'] = 9
            with self.assertRaises(ObserverRefused): client._state()
            self.assertEqual(client.floor, 10)


class NativeCoreObserverTests(fixtures.GatewayFixture):
    def test_actual_core_tls_quorum_partition_stale_leader_controller_loss_and_reconnect(self):
        leader = self.make_cluster()
        with mock.patch.dict(os.environ, {'HOME': str(self.base)}):
            self.setup_gateway()
            client = NativeObserver(self.origin_browser, fingerprint_from_pem(self.gateway_root/'dashboard/server.crt'),
                                    self.cluster, self.epoch, 'core-quorum')
            with gateway.Runtime(self.gateway_root) as runtime:
                view = client.login(runtime.api.sessions.issue())
                self.assertTrue(view['runtime']['quorum_available'])
                self.assertFalse(view['writer_authority']); self.assertEqual(len(view['nodes']), 3)
                self.partition(leader, True); replacement = self.wait_ready(exclude=(leader,))
                view = client.state()
                self.assertTrue(view['runtime']['quorum_available'])
                self.assertEqual(view['runtime']['leader_id'], self.endpoints[replacement]['node_id'])
                old = next(c for c in view['runtime']['controllers'] if c['node_id'] == self.endpoints[leader]['node_id'])
                self.assertFalse(old['leader_confirmed'])
                self.split([{0}, {1}, {2}])
                lost = client.state()
                self.assertEqual(lost['runtime']['state'], 'QUORUM UNAVAILABLE')
                self.assertIsNone(lost['capacity']['available_bytes'])
                self.assertFalse(lost['writer_authority'])
                self.split([set(range(3))]); recovered = self.wait_ready()
                self.assertTrue(client.state()['runtime']['quorum_available'])
                self.kill_python(recovered); self.stop(recovered, crash=True); self.wait_ready(exclude=(recovered,))
                down = client.state()
                self.assertEqual(down['runtime']['state'], 'DEGRADED')
                self.assertEqual(next(c for c in down['runtime']['controllers'] if c['node_id'] == self.endpoints[recovered]['node_id'])['state'], 'OFFLINE')
                self.start(recovered); self.launch_python(recovered); self.wait_ready()
                self.assertTrue(client.state()['runtime']['strong_read_confirmed'])
                client.close()
