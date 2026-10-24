"""Real Go subprocesses + pinned TLS Python Catalog; all state is temporary."""
import base64
import copy
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import sqlite3
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock
from types import SimpleNamespace

from asc.catalog.common import CatalogError, canonical, digest, now, uid
from asc.catalog.state import Catalog, insert
from asc.catalog.queue import JobQueue
from asc.client import ClientError, request_json
from asc.consensus.adapter import Adapter, import_seed
from asc.consensus.client import Client
from asc.consensus.projection import export, prepare, validate
from asc.identity import fingerprint_from_pem, require_openssl
from asc.server import Server
from asc.store import Registry
from asc import cli


ROOT = Path(__file__).resolve().parents[1]


def go_executable():
    candidate = os.environ.get('ASC_GO') or shutil.which('go')
    if not candidate and os.name == 'nt':
        candidate = str(Path(os.environ['LOCALAPPDATA']) / 'ASC-DevTools/go1.27.3/go/bin/go.exe')
    if not candidate or not Path(candidate).is_file():
        raise RuntimeError('Go toolchain required for consensus tests; set ASC_GO; no test skipped')
    return candidate


def unused_address():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return '127.0.0.1:' + str(sock.getsockname()[1])


class SimulatedCrash(BaseException):
    pass


class ConsensusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='asc-consensus-tests-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.base = Path(cls.temp.name)
        cls.binary = cls.base / ('asc-raft.exe' if os.name == 'nt' else 'asc-raft')
        subprocess.run([go_executable(), 'build', '-trimpath', '-o', str(cls.binary), './cmd/asc-raft'],
                       cwd=ROOT / 'consensus', check=True, capture_output=True, timeout=120)

    def assert_code(self, code, action):
        with self.assertRaises(CatalogError) as caught:
            action()
        self.assertEqual(caught.exception.code, code)

    def make_cluster(self):
        cluster = uid(); homes = []
        self.processes = [None] * 3
        self.addCleanup(self.stop_all)
        self.configs, self.clients, self.registries, self.adapters = [], [], [], []
        for i in range(3):
            home = self.base / ('voter-' + str(i)); home.mkdir(); homes.append(home)
            cert, key = home / 'peer.crt', home / 'peer.key'
            subprocess.run([require_openssl(), 'req', '-x509', '-newkey', 'ec', '-pkeyopt', 'ec_paramgen_curve:P-256',
                            '-sha256', '-nodes', '-days', '1', '-keyout', str(key), '-out', str(cert),
                            '-subj', '/CN=ASC-SIMULATED-' + str(i), '-addext', 'subjectAltName=IP:127.0.0.1',
                            '-addext', 'extendedKeyUsage=serverAuth,clientAuth', '-addext', 'basicConstraints=critical,CA:TRUE'],
                           check=True, capture_output=True, timeout=20)
            reg = Registry(home / 'registry.sqlite3'); reg.initialize(cluster); self.registries.append(reg)
        # Reuse an actual v0.6 Global Catalog file and its pending private job.
        reg = self.registries[0]
        self.original_node = reg.join(reg.add_pair_code(), 'simulated-storage', {'protected': False})
        volume = uid(); caps = {'volumes': [{'volume_id': volume, 'state': 'online', 'writable': True,
                 'readable': True, 'free_bytes': 1024**2, 'quota': 1024**2, 'used_bytes': 0, 'reserve': 0}], 'max_upload_bytes': 1024**2}
        with reg.connect() as db:
            insert(db, 'catalog_nodes', {'node_id': self.original_node['node_id'], 'origin': 'https://127.0.0.1:9443',
                'pin': 'a'*64, 'device_id': 'fixture-domain', 'metadata_allowed': 1, 'storage_allowed': 1,
                'approved_generation': 1, 'volume_ids': json.dumps([volume]), 'capabilities': json.dumps(caps), 'checked_at': now()})
        file = Catalog(reg).mutate('CREATE', {'idempotency_key': 'original-upload', 'logical_path': 'existing/file.txt',
            'size': 4, 'sha256': hashlib.sha256(b'test').hexdigest(), 'policy': 'single', 'version': 1})
        self.file_id = file['file']['file_id']
        with reg.connect() as db:
            job_id = db.execute('SELECT job_id FROM catalog_jobs').fetchone()[0]
        queue = JobQueue(Catalog(reg)); queue.ack_upload(job_id, uid(), uid())
        self.assertEqual(queue.claim(job_id)['state'], 'RUNNING')
        self.old_grant = reg.storage_grant(self.original_node['node_id'], volume, ['write'])
        self.assertIsNotNone(reg.storage_authorize(self.original_node['node_id'], self.original_node['token'],
            self.old_grant['grant'], volume, 'write'))
        with reg.connect() as db:
            self.seed = canonical(validate(export(db)))
            self.original_jobs = [dict(r) for r in db.execute('SELECT * FROM catalog_jobs')]
        for reg in self.registries[1:]:
            import_seed(reg, self.seed)
        doc = json.loads(self.seed)
        peers = [{'id': str(i), 'address': unused_address(), 'certificate': (home/'peer.crt').read_text()}
                 for i, home in enumerate(homes)]
        for i, home in enumerate(homes):
            seed = home / 'seed.json'; seed.write_bytes(self.seed)
            cfg = {'schema': 1, 'cluster_id': cluster, 'epoch': doc['epoch'], 'node_id': str(i), 'peers': peers,
                   'state_dir': str(home/'raft-state'), 'seed_file': str(seed), 'seed_sha256': hashlib.sha256(self.seed).hexdigest(),
                   'cert_file': str(home/'peer.crt'), 'key_file': str(home/'peer.key'),
                   'ipc_address': unused_address(), 'ipc_token': secrets.token_urlsafe(40)}
            path = home / 'consensus.json'; path.write_bytes(canonical(cfg)); self.configs.append(path)
            self.clients.append(Client.from_config(path))
            subprocess.run([str(self.binary), 'init', '--config', str(path)], check=True, capture_output=True, timeout=20)
        for i in range(3):
            self.start(i)
        leader = self.leader()
        for reg, client in zip(self.registries, self.clients):
            self.adapters.append(Adapter(reg, client).activate())
        return leader

    def start(self, i):
        flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        self.processes[i] = subprocess.Popen([str(self.binary), 'run', '--config', str(self.configs[i])],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags)
        end = time.monotonic() + 15
        while time.monotonic() < end:
            if self.processes[i].poll() is not None:
                self.fail('Go sidecar startup refused; inspect isolated fixture consistency')
            try:
                self.clients[i].status(); return
            except CatalogError:
                time.sleep(0.05)
        self.fail('Go sidecar startup timeout')

    def stop(self, i, crash=False):
        proc = self.processes[i]
        if proc is None:
            return
        if proc.poll() is None:
            if crash:
                proc.kill()
            else:
                try:
                    self.clients[i].request('POST', '/v1/shutdown', {})
                except CatalogError:
                    proc.terminate()
        proc.wait(timeout=20); self.processes[i] = None

    def stop_all(self):
        for i in range(3):
            self.stop(i)

    def leader(self, among=(0, 1, 2)):
        end = time.monotonic() + 50
        while time.monotonic() < end:
            for i in among:
                if self.processes[i] is None:
                    continue
                try:
                    if self.clients[i].status()['role'] == 'Leader':
                        self.clients[i].state(strong=True); return i
                except CatalogError:
                    pass
            time.sleep(0.1)
        self.fail('no quorum-confirmed sidecar leader')

    def wait_revision(self, i, revision):
        end = time.monotonic() + 20
        while time.monotonic() < end:
            result = self.adapters[i].sync()
            if result['revision'] == revision:
                return result
            time.sleep(0.05)
        self.fail('follower did not reach exact committed revision')

    def test_metadata_consensus_crashes_replay_bypass_and_quorum(self):
        leader = self.make_cluster()
        policy = {'file_id': self.file_id, 'policy': 'replicated_2'}
        with self.subTest('election_and_existing_catalog_import'):
            self.assertEqual(self.adapters[leader].sync(strong=True)['revision'], 1)
            self.assertNotIn(self.original_node['token'].encode(), self.seed)
            self.assertNotIn(b'token_hash', self.seed)
            self.assertIsNone(self.registries[0].storage_authorize(self.original_node['node_id'],
                self.original_node['token'], self.old_grant['grant'], self.old_grant['volume_id'], 'write'))
        with self.subTest('committed_metadata_replicates_and_follower_is_stale'):
            committed = self.adapters[leader].submit('POLICY', policy, 'request-policy-001')
            self.assertEqual(committed['revision'], 2)
            for i in range(3):
                result = self.wait_revision(i, 2)
                self.assertTrue(result['stale']); self.assertEqual(result['document'], committed['document'])
        with self.subTest('all_internal_catalog_registry_jobs_and_grants_writers_fenced'):
            reg = self.registries[0]
            self.assert_code('consensus_required', lambda: Catalog(reg).mutate('POLICY', policy))
            for command in ('CREATE', 'COMPLETE', 'REPLICA_STATE', 'REVERIFY'):
                self.assert_code('consensus_required', lambda command=command: Catalog(reg).mutate(command, {}))
            with reg.connect() as db:
                tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
            for table in tables:
                with self.assertRaises(sqlite3.Error), reg.connect() as db:
                    db.execute(f'DELETE FROM {table}')
            with self.assertRaises(sqlite3.Error), closing(sqlite3.connect(reg.path)) as db:
                db.execute("UPDATE catalog_files SET policy='single'")
            with self.assertRaises(sqlite3.Error):
                reg.add_pair_code()
            self.assert_code('distributed_fencing_required', lambda: JobQueue(Catalog(reg)).claim())
            reg.initialize(reg.cluster_id())  # Safe no-write reopen of an attached registry.
            with reg.connect() as db:
                self.assertEqual([dict(r) for r in db.execute('SELECT * FROM catalog_jobs')], self.original_jobs)
        with self.subTest('duplicate_request_exactly_once_and_conflicting_replay_denied'):
            replay = self.adapters[leader].submit('POLICY', policy, 'request-policy-001')
            self.assertEqual(replay['revision'], 2); self.assertEqual(replay['receipt'], committed['receipt'])
            self.assertEqual(self.adapters[leader].submit('POLICY', policy, 'request-policy-noop')['revision'], 2)
            self.assert_code('request_id_conflict', lambda: self.adapters[leader].submit(
                'POLICY', {**policy, 'policy': 'single'}, 'request-policy-001'))
        with self.subTest('python_crash_before_and_during_apply'):
            for point, expected_revision in [('raft_committed_before_sync', 3), ('inside_python_apply_transaction', 4),
                                               ('python_applied_before_ack', 5)]:
                adapter = self.adapters[leader]
                def fault(actual, point=point):
                    if actual == point:
                        raise SimulatedCrash()
                adapter.fault_hook = fault
                crash_policy = {**policy, 'policy': 'single' if expected_revision % 2 else 'replicated_3'}
                with self.assertRaises(SimulatedCrash):
                    adapter.submit('POLICY', crash_policy, 'crash-' + point)
                # Reconstruct Python state/client as a restarted Controller.
                adapter = Adapter(self.registries[leader], self.clients[leader]).activate()
                self.adapters[leader] = adapter
                result = adapter.submit('POLICY', crash_policy, 'crash-' + point)
                self.assertEqual(result['revision'], expected_revision)
        with self.subTest('leader_stop_re_election_old_leader_follower_and_replay'):
            old = leader; self.stop(old, crash=True)
            leader = self.leader(tuple(i for i in range(3) if i != old))
            self.assertEqual(self.adapters[leader].submit('POLICY', policy, 'request-policy-001')['revision'], 5)
            self.start(old); self.wait_revision(old, 5)
            self.assertEqual(self.clients[old].status()['role'], 'Follower')
        with self.subTest('committed_unapplied_snapshot_and_full_sidecar_restart'):
            view = self.adapters[leader].sync(strong=True); state = view['state']
            doc = prepare(view['document'], 'POLICY', policy, 'snapshot-unapplied', uid(), now())
            self.clients[leader].submit({'schema': 1, 'cluster_id': state['cluster_id'], 'epoch': state['epoch'],
                'request_id': 'snapshot-unapplied', 'intent_sha256': digest({'operation': 'POLICY', 'data': policy}),
                'expected_sha256': state['document_sha256'], 'document': base64.b64encode(canonical(doc)).decode()})
            self.clients[leader].request('POST', '/v1/snapshot', {})
            with self.registries[leader].connect() as db:
                self.assertEqual(export(db)['revision'], 5)  # Python has not applied committed rev 6.
            for i in range(3):
                self.stop(i, crash=True)
            for i in range(3):
                self.start(i)
            leader = self.leader()
            for i in range(3):
                self.wait_revision(i, 6)
        with self.subTest('quorum_loss_rejects_write_and_strong_read_but_keeps_stale_revision'):
            stopped = [i for i in range(3) if i != leader]
            for i in stopped:
                self.stop(i)
            self.assert_code('quorum_read_unavailable', lambda: self.adapters[leader].submit('POLICY', policy, 'minority-rejected'))
            stale = self.adapters[leader].sync(); self.assertTrue(stale['stale']); self.assertEqual(stale['revision'], 6)
            for i in stopped:
                self.start(i)
            leader = self.leader()
            self.assertEqual(self.adapters[leader].submit('POLICY', {**policy, 'policy':'replicated_3'}, 'after-quorum-recovery')['revision'], 7)
        with self.subTest('IPC_authentication_and_static_membership_api'):
            config = json.loads(self.configs[leader].read_bytes())
            bad = Client(config['ipc_address'], secrets.token_urlsafe(40))
            self.assert_code('ipc_unauthorized', bad.status)
            self.assert_code('unsupported_operation', lambda: self.clients[leader].request('POST', '/v1/membership', {}))
        with self.subTest('real_catalog_TLS_API_bypass_and_follower_stale_strong_reads'):
            follower = (leader + 1) % 3
            self.wait_revision(follower, 7)
            admin = secrets.token_urlsafe(40)
            service = SimpleNamespace(distributed=True, adapter=self.adapters[follower])
            server = Server(('127.0.0.1', 0), self.registries[follower], admin, catalog=service)
            config = json.loads(self.configs[follower].read_bytes())
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); context.load_cert_chain(config['cert_file'], config['key_file'])
            server.tls_context = context
            thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
            origin = 'https://127.0.0.1:' + str(server.server_address[1]); pin = fingerprint_from_pem(config['cert_file'])
            try:
                response = request_json(origin, pin, 'GET', '/catalog/v1/files', token=admin)
                self.assertEqual(response['revision'], 7); self.assertTrue(response['stale'])
                self.assertIsNone(response['files'][0]['available_replicas'])
                for path, data in [('/catalog/v1/uploads', {}), ('/catalog/v1/jobs/run', {}), ('/api/v1/admin/pair', {})]:
                    with self.assertRaises(ClientError):
                        request_json(origin, pin, 'POST', path, data, token=admin)
                with self.assertRaises(ClientError):
                    request_json(origin, pin, 'GET', '/catalog/v1/files?consistency=strong', token=admin)
                info = request_json(origin, pin, 'GET', '/api/v1/info')
                self.assertTrue(info['raft_enabled']); self.assertFalse(info['automatic_failover'])
            finally:
                server.shutdown(); server.server_close(); thread.join(timeout=5)
        with self.subTest('actual_python_controller_write_crash_restart_and_no_legacy_fallback'):
            home = self.configs[leader].parent
            shutil.copyfile(home/'peer.crt', home/'server.crt'); shutil.copyfile(home/'peer.key', home/'server.key')
            admin = secrets.token_urlsafe(40); api_address = unused_address()
            config = json.loads(self.configs[leader].read_bytes())
            (home/'controller.json').write_bytes(canonical({'cluster_id': config['cluster_id'],
                'admin_token': admin, 'listen_port': int(api_address.rsplit(':', 1)[1])}))
            env = dict(os.environ, ASC_HOME=str(home)); pin = fingerprint_from_pem(home/'server.crt')
            origin = 'https://' + api_address
            command = [sys.executable, '-B', '-m', 'asc.cli']
            if os.name != 'nt':
                # Synthetic metadata Controller only; no product platform bypass.
                script = ("from unittest.mock import patch; from types import SimpleNamespace; "
                          "import asc.cli as c; "
                          "p=patch.object(c,'os',SimpleNamespace(name='nt')); p.start(); "
                          "q=patch.object(c,'inspect',return_value={'protected':False,"
                          "'installation_allowed':True,'simulation':True}); q.start(); c.main()")
                command = [sys.executable, '-B', '-c', script]
            def launch_controller():
                proc = subprocess.Popen(command + ['controller-run',
                    '--consensus-config', str(self.configs[leader])], cwd=ROOT, env=env,
                    stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                end = time.monotonic()+20
                while time.monotonic()<end:
                    if proc.poll() is not None:
                        stdout, stderr = proc.communicate(timeout=2)
                        self.fail('Python metadata Controller startup failed: '+(stdout+stderr).decode(errors='replace')[-1500:])
                    try:
                        request_json(origin, pin, 'GET', '/api/v1/info'); return proc
                    except (ClientError, OSError):
                        time.sleep(0.05)
                proc.kill(); proc.wait(); self.fail('Python Controller startup timeout')
            proc = launch_controller()
            try:
                declaration = {'request_id':'api-declare-001', 'logical_path':'new/tiếng-Việt-<tag>.txt',
                    'version':1, 'size':0, 'sha256':hashlib.sha256(b'').hexdigest(), 'policy':'single'}
                response = request_json(origin, pin, 'POST', '/catalog/v1/metadata/declare', declaration, token=admin)
                self.assertEqual(response['revision'], 8)
                files = request_json(origin, pin, 'GET', '/catalog/v1/files?consistency=strong', token=admin)
                file_id = next(f['file']['file_id'] for f in files['files'] if f['file']['logical_path']==declaration['logical_path'])
                response = request_json(origin, pin, 'POST', '/catalog/v1/files/'+file_id+'/policy',
                    {'request_id':'api-policy-002', 'policy':'replicated_3'}, token=admin)
                self.assertEqual(response['revision'], 9)
            finally:
                proc.kill(); proc.communicate(timeout=10)
            proc = launch_controller()
            try:
                files = request_json(origin, pin, 'GET', '/catalog/v1/files?consistency=strong', token=admin)
                self.assertEqual(files['revision'], 9); self.assertFalse(files['stale'])
            finally:
                proc.kill(); proc.communicate(timeout=10)
            fallback = subprocess.run(command + ['controller-run'], cwd=ROOT,
                env=env, capture_output=True, timeout=15)
            self.assertNotEqual(fallback.returncode, 0)
            self.assertIn(b'consensus configuration required', fallback.stderr)
            with self.registries[0].connect() as db:
                self.assertEqual([dict(r) for r in db.execute('SELECT * FROM catalog_jobs')], self.original_jobs)
        with self.subTest('membership_binding_missing_state_and_no_automatic_bootstrap'):
            self.stop_all()
            config = json.loads(self.configs[0].read_bytes())
            changed = copy.deepcopy(config); changed['peers'][1]['id'] = 'spoofed-member'
            bad_path = self.configs[0].parent/'changed-membership.json'; bad_path.write_bytes(canonical(changed))
            result = subprocess.run([str(self.binary), 'run', '--config', str(bad_path)], capture_output=True, timeout=15)
            self.assertEqual(result.returncode, 1)
            state_dir = Path(config['state_dir']); moved = state_dir.with_name('lost-state-fixture')
            state_dir.rename(moved)
            for mode in ('run', 'init'):
                result = subprocess.run([str(self.binary), mode, '--config', str(self.configs[0])], capture_output=True, timeout=15)
                self.assertEqual(result.returncode, 1)
                self.assertFalse(state_dir.exists(), 'lost voter state was recreated')

    def test_projection_validation_and_stable_preparation(self):
        with tempfile.TemporaryDirectory() as root:
            reg = Registry(Path(root)/'registry.sqlite3'); reg.initialize(uid())
            with reg.connect() as db:
                seed = export(db)
            data = {'logical_path': 'docs/tiếng-Việt-<tag>.txt', 'version': 1, 'size': 0,
                    'sha256': hashlib.sha256(b'').hexdigest(), 'policy': 'single'}
            file_id = uid()
            one = prepare(seed, 'DECLARE', data, 'request-declare-1', file_id, 123)
            two = prepare(seed, 'DECLARE', data, 'request-declare-1', file_id, 123)
            self.assertEqual(canonical(one), canonical(two))
            altered = copy.deepcopy(one); altered['events'][0]['digest'] = '0'*64
            self.assert_code('invalid_consensus_history', lambda: validate(altered))
            altered = copy.deepcopy(one); altered['files'][0]['policy'] = 'replicated_3'
            self.assert_code('consensus_materialization_conflict', lambda: validate(altered))
            self.assert_code('distributed_fencing_required', lambda: prepare(one, 'COMPLETE', {}, 'request-rejected', uid(), 124))
            self.assert_code('consensus_import_refused', lambda: import_seed(reg, canonical({**one, 'cluster_id': uid()})))

    def test_metadata_windows_development_never_overrides_android_or_protected_guard(self):
        args = SimpleNamespace(consensus_config='private-placeholder')
        for os_name, profile in [('nt', {'protected': True, 'installation_allowed': False}),
                                 ('posix', {'protected': False, 'installation_allowed': False})]:
            with mock.patch.object(cli.os, 'name', os_name), mock.patch.object(cli, 'inspect', return_value=profile):
                with self.assertRaises(ValueError):
                    cli.controller_run(args)
