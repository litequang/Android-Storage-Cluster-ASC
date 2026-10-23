"""Phase 1.1 acceptance/regression cases. Written for the owner to run, never auto-run."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import contextlib
from contextlib import closing
import hashlib
import io
import json
from pathlib import Path
import secrets
import sqlite3
import ssl
import tempfile
import threading
import time
import unittest
from unittest import mock

from asc import cli, identity, probe
from asc.client import ClientError, request_json
from asc.identity import fingerprint_from_pem, make_cert, require_openssl, save_private
from asc.runtime import foreground_lock, running
from asc.planner import recommend
from asc.server import RateLimiter, Server
from asc.store import Registry
from asc import validation


class RegistryLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'registry.sqlite3'
        self.reg = Registry(self.path)
        self.reg.initialize('cluster')

    def modern(self, code, target=None, enrollment=None, token=None):
        return self.reg.join(code, 'Bphone', {'profile_version': 1},
                             enrollment or secrets.token_urlsafe(32),
                             token or secrets.token_urlsafe(32), target)

    def test_expired_reused_and_atomic_concurrent_code(self):
        expired = self.reg.add_pair_code()
        with self.reg.connect() as db:
            db.execute('UPDATE join_codes SET expires_at=?', (int(time.time()) - 1,))
        self.assertIsNone(self.reg.join(expired, 'expired', {}))
        code = self.reg.add_pair_code()
        with ThreadPoolExecutor(max_workers=4) as pool:
            replies = list(pool.map(lambda _: self.reg.join(code, 'node', {}), range(4)))
        self.assertEqual(sum(reply is not None for reply in replies), 1)
        self.assertEqual(len(self.reg.snapshot()['nodes']), 1)

    def test_retry_and_rotation_preserve_id_reject_old_credentials(self):
        code = self.reg.add_pair_code()
        enrollment, token = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        first = self.modern(code, enrollment=enrollment, token=token)
        self.assertEqual(first, self.modern(code, enrollment=enrollment, token=token))
        self.assertIsNone(self.modern(code))
        self.assertTrue(self.reg.rename(first['node_id'], "Phone '); SELECT 1; --"))
        target = first['node_id']
        pair = self.reg.add_pair_code(target_node_id=target)
        self.assertIsNone(self.modern(pair))  # A targeted code cannot create another node.
        replacement_id, replacement_token = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        replacement = self.modern(pair, target, replacement_id, replacement_token)
        self.assertEqual(target, replacement['node_id'])
        self.assertEqual(replacement['token_version'], 2)
        self.assertEqual(replacement, self.modern(pair, target, replacement_id, replacement_token))
        self.assertFalse(self.reg.heartbeat(target, token, {}))
        self.assertTrue(self.reg.heartbeat(target, replacement_token, {}))
        self.assertIsNone(self.modern(code, enrollment=enrollment, token=token))
        self.assertEqual(len(self.reg.snapshot()['nodes']), 1)
        self.assertIn('SELECT', self.reg.detail(target)['name'])
        self.assertNotIn('token_hash', self.reg.detail(target))

    def test_revoke_idempotent_and_only_targeted_repair_reactivates(self):
        joined = self.modern(self.reg.add_pair_code())
        target = joined['node_id']
        pending = self.reg.add_pair_code(target_node_id=target)
        self.assertTrue(self.reg.revoke(target))
        detail = self.reg.detail(target)
        self.assertTrue(self.reg.revoke(target))
        self.assertEqual(detail, self.reg.detail(target))
        self.assertFalse(self.reg.heartbeat(target, joined['token'], {}))
        self.assertFalse(detail['online'])
        self.assertEqual(self.reg.snapshot()['advisory_role_plan'][0]['suggested_role'], 'excluded-revoked')
        self.assertIsNone(self.modern(pending, target))
        new_code = self.reg.add_pair_code(target_node_id=target)
        repaired = self.modern(new_code, target)
        self.assertEqual(repaired['node_id'], target)
        self.assertTrue(self.reg.heartbeat(target, repaired['token'], {}))

    def test_replacement_generic_code_keeps_pending_identity(self):
        enrollment, token = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        first = self.modern(self.reg.add_pair_code(), enrollment=enrollment, token=token)
        replacement = self.modern(self.reg.add_pair_code(), enrollment=enrollment, token=token)
        self.assertEqual(first, replacement)
        self.assertEqual(len(self.reg.snapshot()['nodes']), 1)
        self.reg.revoke(first['node_id'])
        self.assertIsNone(self.modern(self.reg.add_pair_code(), enrollment=enrollment, token=token))

    def test_validation_does_not_consume_code(self):
        code = self.reg.add_pair_code()
        for name, profile in [('bad\nname', {}), ('x', {'readiness_score': '100'}),
                              ('x', {'protected': []}), ('x', {'profile_version': 2}),
                              ('x', {'memory_mb': -1}), ('x', {'model': []}),
                              ('x', {'sd_candidates': {}}), ('x', {'model': '\ud800'})]:
            with self.subTest(name=name, profile=repr(profile)):
                with self.assertRaises(ValueError):
                    self.reg.join(code, name, profile)
        self.assertIsNotNone(self.reg.join(code, 'valid', {}))

    def test_v04_migration_keeps_every_identity_and_code(self):
        legacy = Path(self.tmp.name) / 'legacy.sqlite3'
        token, code = secrets.token_urlsafe(32), '123456789ABC'
        digest = lambda text: hashlib.sha256(text.encode()).hexdigest()
        # sqlite3.Connection.__exit__ commits/rolls back; it does NOT close the handle.
        with closing(sqlite3.connect(legacy)) as db:
            with db:
                db.executescript('''
                    CREATE TABLE settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
                    CREATE TABLE nodes(node_id TEXT PRIMARY KEY,name TEXT NOT NULL,token_hash TEXT NOT NULL,
                        profile TEXT NOT NULL,last_seen INTEGER NOT NULL,joined_at INTEGER NOT NULL);
                    CREATE TABLE join_codes(code_hash TEXT PRIMARY KEY,expires_at INTEGER NOT NULL,used INTEGER NOT NULL DEFAULT 0);
                ''').close()
                db.execute('INSERT INTO settings VALUES (?,?)', ('cluster_id', 'old-cluster')).close()
                db.execute('INSERT INTO nodes VALUES (?,?,?,?,?,?)',
                           ('old-node', 'v0.4', digest(token), '{}', 12, 10)).close()
                db.execute('INSERT INTO join_codes VALUES (?,?,?)',
                           (digest(code), int(time.time()) + 600, 0)).close()
        with self.assertRaises(sqlite3.ProgrammingError):
            db.execute('SELECT 1')  # Legacy fixture is CLOSED before migration starts.
        reg = Registry(legacy)
        reg.initialize('old-cluster')
        reg.initialize('old-cluster')
        self.assertEqual(reg.cluster_id(), 'old-cluster')
        self.assertEqual(reg.detail('old-node')['joined_at'], 10)
        self.assertTrue(reg.heartbeat('old-node', token, {}))
        self.assertIsNotNone(reg.join(code, 'legacy-client', {}))
        with reg.connect() as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0], 2)
        with self.assertRaises(ValueError):
            reg.initialize('wrong-cluster')
        self.assertEqual(len(reg.snapshot()['nodes']), 2)
        # Registry context also releases while db still has a live Python reference.
        with self.assertRaises(sqlite3.ProgrammingError):
            db.execute('SELECT 1')
        moved = legacy.with_name('legacy-moved.sqlite3')
        legacy.rename(moved)
        moved.unlink()  # Windows refuses this if any SQLite handle still owns the file.

    def test_connection_context_closes_handles_and_rolls_back_on_error(self):
        with self.reg.connect() as db:
            db.execute('CREATE TABLE close_probe(value TEXT)').close()
            db.execute('INSERT INTO close_probe VALUES (?)', ('committed',)).close()
            with closing(db.execute('SELECT value FROM close_probe')) as cursor:
                self.assertEqual(cursor.fetchone()[0], 'committed')
        with self.assertRaises(sqlite3.ProgrammingError):
            db.execute('SELECT 1')
        with self.assertRaises(sqlite3.ProgrammingError):
            cursor.fetchone()
        with self.assertRaisesRegex(RuntimeError, 'rollback probe'):
            with self.reg.connect() as failed:
                failed.execute('INSERT INTO close_probe VALUES (?)', ('rolled-back',)).close()
                raise RuntimeError('rollback probe')
        with self.assertRaises(sqlite3.ProgrammingError):
            failed.execute('SELECT 1')
        with self.reg.connect() as check:
            with closing(check.execute('SELECT value FROM close_probe')) as rows:
                self.assertEqual([row[0] for row in rows], ['committed'])
        with self.assertRaises(sqlite3.ProgrammingError):
            check.execute('SELECT 1')
        moved = self.path.with_name('closed-registry.sqlite3')
        self.path.rename(moved)
        moved.unlink()

    def test_future_schema_is_not_downgraded(self):
        for version in (1, 99):
            with self.subTest(version=version):
                with self.reg.connect() as db:
                    db.execute(f'PRAGMA user_version={version}')
                with self.assertRaises(ValueError):
                    self.reg.initialize('cluster')
                with self.reg.connect() as db:
                    self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0], version)


class LifecycleHTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_openssl()  # Missing dependency is an ERROR, never SkipTest or fake PASS.
        cls.certdir = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.certdir.cleanup)
        cls.cert = Path(cls.certdir.name) / 'cert.pem'
        cls.key = Path(cls.certdir.name) / 'key.pem'
        make_cert(cls.cert, cls.key)
        cls.pin = fingerprint_from_pem(cls.cert)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.reg = Registry(Path(self.tmp.name) / 'db.sqlite3')
        self.reg.initialize('cluster')
        self.admin = secrets.token_urlsafe(40)
        self.server = Server(('127.0.0.1', 0), self.reg, self.admin)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(str(self.cert), str(self.key))
        self.server.tls_context = context
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.origin = f'https://127.0.0.1:{self.server.server_address[1]}'

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(3)
        self.tmp.cleanup()

    def call(self, method, path, obj=None, token=None):
        return request_json(self.origin, self.pin, method, path, obj, token)

    def failure(self, status, method, path, obj=None, token=None):
        with self.assertRaises(ClientError) as caught:
            self.call(method, path, obj, token)
        self.assertEqual(caught.exception.status, status)
        return caught.exception

    def test_admin_node_separation_rename_revoke_and_no_token_output(self):
        code = self.call('POST', '/api/v1/admin/pair', {}, self.admin)['code']
        payload = {'code': code, 'name': 'Bphone', 'profile': {}}
        joined = self.call('POST', '/api/v1/join', payload)
        node = joined['node_id']
        self.failure(401, 'GET', '/api/v1/nodes', token=joined['token'])
        self.failure(401, 'POST', '/api/v1/admin/pair', {}, joined['token'])
        self.failure(401, 'POST', '/api/v1/heartbeat', {'node_id': node, 'profile': {}}, self.admin)
        self.call('POST', '/api/v1/admin/rename', {'node_id': node, 'name': 'XZ3'}, self.admin)
        detail = self.call('GET', '/api/v1/nodes/' + node, token=self.admin)
        self.assertEqual(detail['node']['name'], 'XZ3')
        self.assertNotIn(joined['token'], json.dumps(detail))
        self.assertNotIn('token_hash', json.dumps(detail))
        self.call('POST', '/api/v1/admin/revoke', {'node_id': node}, self.admin)
        exc = self.failure(401, 'POST', '/api/v1/heartbeat', {'node_id': node, 'profile': {}}, joined['token'])
        self.assertEqual(exc.code, 'credential_rejected_repair_required')

    def test_join_bruteforce_rate_limit(self):
        for _ in range(8):
            self.failure(403, 'POST', '/api/v1/join', {'code': '000000000000', 'name': 'x', 'profile': {}})
        self.failure(429, 'POST', '/api/v1/join', {'code': '000000000000', 'name': 'x', 'profile': {}})

    def test_auth_rate_limit_shared_across_protected_paths(self):
        for index in range(12):
            path = '/api/v1/nodes' if index % 2 else '/api/v1/nodes/missing'
            self.failure(401, 'GET', path)
        self.failure(429, 'POST', '/api/v1/heartbeat', {'node_id': 'x', 'profile': {}}, 'bad')

    def test_bad_schema_size_and_pin_never_send_join(self):
        code = self.reg.add_pair_code()
        for payload in ({'code': code, 'name': ['bad'], 'profile': {}},
                        {'code': code, 'name': 'x', 'profile': {}, 'unexpected': True},
                        {'code': code, 'name': 'x', 'profile': {'model': {}}},
                        {'protocol_version': 2, 'code': code, 'name': 'x', 'profile': {}},
                        {'code': code, 'name': 'x\nspoof', 'profile': {}}):
            self.failure(400, 'POST', '/api/v1/join', payload)
        self.failure(413, 'POST', '/api/v1/join', {'code': code, 'name': 'x', 'profile': {'x': 'a' * 66000}})
        with self.assertRaises(ClientError):
            request_json(self.origin, '0' * 64, 'POST', '/api/v1/join',
                         {'code': code, 'name': 'x', 'profile': {}})
        # Pin mismatch occurs BEFORE sending request; the code is still available.
        self.assertIsNotNone(self.reg.join(code, 'safe', {}))

    def test_error_responses_do_not_reflect_secrets(self):
        marker = secrets.token_urlsafe(32)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            error = self.failure(400, 'POST', '/api/v1/join',
                                 {'code': marker, 'name': marker, 'profile': {'model': []}})
        self.assertNotIn(marker, output.getvalue())
        self.assertNotIn(marker, str(error))


class ClientIdentityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name) / 'private'
        self.home.mkdir()
        self.reg = Registry(Path(self.tmp.name) / 'db.sqlite3')
        self.reg.initialize('cluster')
        self.code = self.reg.add_pair_code()
        self.patches = [mock.patch.object(cli, 'HOME', self.home),
                        mock.patch.object(identity, 'HOME', self.home),
                        mock.patch.object(cli, 'inspect', return_value={'model': 'Bphone', 'protected': False,
                                                                     'installation_allowed': True}),
                        mock.patch.object(cli.getpass, 'getpass', return_value=self.code)]
        for patch in self.patches:
            patch.start()
            self.addCleanup(patch.stop)
        self.args = argparse.Namespace(controller='https://test:8443', pin='A' * 64, name='phone',
                                       node_id=None, cluster_id=None, sd_test=False, new_code=False)

    def reply(self, origin, pin, method, path, obj=None, token=None):
        if path == '/api/v1/info':
            return {'cluster_id': 'cluster', 'features': ['retry-safe-enrollment-v1']}
        joined = self.reg.join(obj['code'], obj['name'], obj['profile'],
                               obj['enrollment_id'], obj['enrollment_token'], obj.get('node_id'))
        if joined is None:
            raise ClientError('HTTP 403: invalid_or_expired_code', 403, 'invalid_or_expired_code')
        return {'cluster_id': 'cluster', **joined}

    def test_lost_response_restart_reinstall_never_duplicate_or_overwrite_identity(self):
        def lost(*args, **kwargs):
            reply = self.reply(*args, **kwargs)
            if args[3] == '/api/v1/join':
                raise OSError('simulated lost response')
            return reply
        with mock.patch.object(cli, 'request_json', side_effect=lost):
            with self.assertRaises(OSError):
                cli.node_join(self.args)
        pending = (self.home / 'enrollment_pending.json').read_bytes()
        self.assertEqual(len(self.reg.snapshot()['nodes']), 1)
        with mock.patch.object(cli, 'request_json', side_effect=self.reply), contextlib.redirect_stdout(io.StringIO()):
            cli.node_join(self.args)
        node_bytes = (self.home / 'node.json').read_bytes()
        # Restart / reinstall invokes node-join without even requiring network or a code.
        with mock.patch.object(cli, 'request_json', side_effect=AssertionError('unexpected network')), contextlib.redirect_stdout(io.StringIO()):
            cli.node_join(self.args)
        self.assertEqual((self.home / 'node.json').read_bytes(), node_bytes)
        self.assertFalse((self.home / 'enrollment_pending.json').exists())
        self.assertEqual(len(self.reg.snapshot()['nodes']), 1)
        cfg = json.loads(node_bytes)
        self.assertIn(cfg['token'].encode(), pending)
        with self.assertRaises(FileExistsError):
            save_private(self.home / 'node.json', {'token': 'replacement'})
        self.assertEqual((self.home / 'node.json').read_bytes(), node_bytes)

    def test_repair_keeps_id_and_old_identity_backup(self):
        with mock.patch.object(cli, 'request_json', side_effect=self.reply), contextlib.redirect_stdout(io.StringIO()):
            cli.node_join(self.args)
            old = json.loads((self.home / 'node.json').read_text())
            self.reg.revoke(old['node_id'])
            self.code = self.reg.add_pair_code(target_node_id=old['node_id'])
            with mock.patch.object(cli.getpass, 'getpass', return_value=self.code):
                cli.node_repair(self.args)
        new = json.loads((self.home / 'node.json').read_text())
        self.assertEqual(old['node_id'], new['node_id'])
        self.assertNotEqual(old['token'], new['token'])
        self.assertFalse(self.reg.heartbeat(old['node_id'], old['token'], {}))
        self.assertTrue(self.reg.heartbeat(new['node_id'], new['token'], {}))
        self.assertEqual(len(list(self.home.glob('node_before_repair-*.json'))), 1)

    def test_initial_new_code_retains_operation_after_lost_success(self):
        def lost(*args, **kwargs):
            reply = self.reply(*args, **kwargs)
            if args[3] == '/api/v1/join':
                raise OSError('lost response')
            return reply
        with mock.patch.object(cli, 'request_json', side_effect=lost):
            with self.assertRaises(OSError):
                cli.node_join(self.args)
        before = json.loads((self.home / 'enrollment_pending.json').read_text())
        new_code = self.reg.add_pair_code()
        self.args.new_code = True
        with mock.patch.object(cli.getpass, 'getpass', return_value=new_code), mock.patch.object(cli, 'request_json', side_effect=self.reply), contextlib.redirect_stdout(io.StringIO()):
            cli.node_join(self.args)
        saved = json.loads((self.home / 'node.json').read_text())
        self.assertEqual(saved['token'], before['payload']['enrollment_token'])
        self.assertEqual(len(self.reg.snapshot()['nodes']), 1)

    def test_legacy_config_bytes_unchanged_and_future_version_rejected(self):
        cfg = {'node_id': 'legacy', 'cluster_id': 'cluster', 'token': secrets.token_urlsafe(32),
               'controller': 'https://test', 'pin': 'A' * 64}
        save_private(self.home / 'node.json', cfg)
        original = (self.home / 'node.json').read_bytes()
        self.assertEqual(identity.read_private('node.json'), cfg)
        self.assertEqual((self.home / 'node.json').read_bytes(), original)
        identity.replace_private(self.home / 'node.json', {**cfg, 'config_version': 99})
        with self.assertRaises(ValueError):
            identity.read_private('node.json')

    def test_rejected_token_records_repair_required_without_changing_node_identity(self):
        cfg = {'controller': 'https://test', 'pin': 'A' * 64, 'node_id': 'old-node',
               'cluster_id': 'cluster', 'token': secrets.token_urlsafe(32)}
        save_private(self.home / 'node.json', cfg)
        original = (self.home / 'node.json').read_bytes()
        with mock.patch.object(cli, 'request_json', side_effect=ClientError('rejected', 401, 'unauthorized')):
            with self.assertRaises(ClientError):
                cli.agent_once(cfg)
        state = json.loads((self.home / 'agent_state.json').read_text())
        self.assertEqual(state['credential_status'], 'repair-required')
        self.assertEqual((self.home / 'node.json').read_bytes(), original)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            cli.local_status(None)
        self.assertNotIn(cfg['token'], output.getvalue())

    def test_crash_after_node_save_pending_cleanup_is_idempotent(self):
        with mock.patch.object(cli, 'request_json', side_effect=self.reply), contextlib.redirect_stdout(io.StringIO()):
            cli.node_join(self.args)
        cfg = json.loads((self.home / 'node.json').read_text())
        save_private(self.home / 'enrollment_pending.json',
                     {'payload': {'enrollment_token': cfg['token']}, 'expected_cluster_id': cfg['cluster_id']})
        with contextlib.redirect_stdout(io.StringIO()):
            cli.node_join(self.args)
        self.assertFalse((self.home / 'enrollment_pending.json').exists())

    def test_foreground_lock_blocks_duplicate_and_releases(self):
        with foreground_lock(self.home, 'agent'):
            self.assertTrue(running(self.home, 'agent'))
            with self.assertRaises(ValueError):
                with foreground_lock(self.home, 'agent'):
                    self.fail('duplicate process admitted')
        self.assertFalse(running(self.home, 'agent'))

    def test_existing_controller_never_recreates_missing_or_mismatched_registry(self):
        with self.assertRaises(ValueError):
            cli._registry({'cluster_id': 'cluster'})
        self.assertFalse((self.home / 'registry.sqlite3').exists())
        reg = Registry(self.home / 'registry.sqlite3')
        reg.initialize('other-cluster')
        with self.assertRaises(ValueError):
            cli._registry({'cluster_id': 'cluster'})
        self.assertEqual(reg.cluster_id(), 'other-cluster')


class DeviceSafetyTests(unittest.TestCase):
    def test_legacy_untrusted_score_cannot_crash_role_planner(self):
        rows = [
            {'node_id': 'old', 'name': 'old', 'online': True,
             'profile': {'recommended_role': 'controller-candidate', 'readiness_score': {'bad': 1}}},
            {'node_id': 'new', 'name': 'new', 'online': True,
             'profile': {'recommended_role': 'controller-candidate', 'readiness_score': 80}},
        ]
        roles = {item['node_id']: item['suggested_role'] for item in recommend(rows)}
        self.assertEqual(roles['new'], 'preferred-controller-candidate')
        self.assertNotEqual(roles['old'], 'preferred-controller-candidate')

    def test_probe_fsync_failure_cleans_only_created_temp_file(self):
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td) / 'Android/data/com.termux/files'
            folder.mkdir(parents=True)
            original = folder / 'keep.txt'
            original.write_bytes(b'keep')
            with mock.patch.object(probe.os, 'fsync', side_effect=OSError('simulated failure')):
                result = probe.probe_sd_write({'app_dir': str(folder)})
            self.assertEqual(result['status'], 'fail')
            self.assertEqual(list(folder.iterdir()), [original])
            self.assertEqual(original.read_bytes(), b'keep')

    def test_external_alias_is_not_a_second_volume_or_nested_app_folder(self):
        roots = [str(Path('/storage/ABCD-1234')), str(Path('/private/storage/external-1'))]
        app_dir = str(Path(roots[0]) / 'Android' / 'data' / 'com.termux' / 'files')
        with mock.patch.object(probe.glob, 'glob', side_effect=[[roots[0]], [roots[1]]]), mock.patch.object(probe.os.path, 'realpath', side_effect=lambda path: app_dir if path == roots[1] else path), mock.patch.object(probe.os.path, 'isdir', return_value=True), mock.patch.object(probe, '_volume', return_value=None):
            volumes = probe._detect_sd_locations()
        self.assertEqual(len(volumes), 1)
        # os.path.join uses the platform separator; compare the platform-native path.
        expected = str(Path(roots[0]) / 'Android' / 'data' / 'com.termux' / 'files')
        self.assertEqual(volumes[0]['app_dir'], expected)

    def test_unreadable_android_ram_sd_are_unknown_and_install_denied(self):
        with mock.patch.object(probe, '_cmd', return_value=None), mock.patch.object(probe, '_memory_mb', return_value=None), mock.patch.object(probe, '_volume', return_value=None), mock.patch.object(probe, '_detect_sd_locations', return_value=[]):
            profile = probe.inspect(sd_write=True)
        self.assertEqual(profile['model'], 'unknown')
        self.assertIsNone(profile['memory_mb'])
        self.assertIsNone(profile['readiness_score'])
        self.assertIsNone(profile['internal_app_storage'])
        self.assertEqual(profile['sd_status'], 'unknown')
        self.assertFalse(profile['installation_allowed'])
        with mock.patch.object(cli, 'inspect', return_value=profile):
            with self.assertRaises(ValueError):
                cli._must_not_protected('install')

    def test_baseline_does_not_become_runtime_telemetry(self):
        props = {'ro.product.model': 'ZTE V40', 'ro.product.manufacturer': 'ZTE', 'ro.build.version.sdk': '33'}
        with mock.patch.object(probe, '_cmd', side_effect=lambda *args: props.get(args[-1])), mock.patch.object(probe, '_memory_mb', return_value=None), mock.patch.object(probe, '_volume', return_value=None), mock.patch.object(probe, '_detect_sd_locations', return_value=[]):
            profile = probe.inspect()
        self.assertIsNone(profile['memory_mb'])
        self.assertEqual(profile['score_basis'], 'manufacturer-baseline')
        self.assertEqual(profile['profile_version'], 1)
        validation.profile(profile)

    def test_m51_secondary_identity_still_protected_and_never_probed(self):
        props = {'ro.product.manufacturer': 'Samsung', 'ro.product.device': 'm51', 'ro.build.version.sdk': '33'}
        with mock.patch.object(probe, '_cmd', side_effect=lambda *args: props.get(args[-1])), mock.patch.object(probe, '_detect_sd_locations', return_value=[{'app_dir': '/not-used'}]), mock.patch.object(probe, 'probe_sd_write') as write:
            profile = probe.inspect(sd_write=True)
        self.assertTrue(profile['protected'])
        self.assertFalse(profile['installation_allowed'])
        write.assert_not_called()


class LimiterTests(unittest.TestCase):
    def test_global_budget_and_window_reset(self):
        tick = [0]
        limiter = RateLimiter(clock=lambda: tick[0])
        for index in range(60):
            self.assertFalse(limiter.blocked('join', str(index), consume=True))
        self.assertTrue(limiter.blocked('join', 'new-ip', consume=True))
        tick[0] = 61
        self.assertFalse(limiter.blocked('join', 'new-ip', consume=True))


if __name__ == '__main__':
    unittest.main()
