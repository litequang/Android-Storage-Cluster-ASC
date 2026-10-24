"""Phase 2B qualification: fake data, actual isolated Go/Python/TLS processes."""
import base64
import copy
from contextlib import closing
import hashlib
import http.client
import io
import json
import os
from pathlib import Path
from types import SimpleNamespace
import secrets
import shutil
import sqlite3
import ssl
import subprocess
import sys
import tempfile
import time
import threading
import unittest

from asc.catalog.common import CatalogError, canonical, uid, digest
from asc.catalog.client import ClusterClient
from asc.catalog.service import CatalogService
from asc.client import ClientError, request_json, connect_pinned
from asc.consensus.adapter import Adapter, import_seed
from asc.consensus.client import Client
from asc.consensus.projection import export
from asc.failover import state
from asc.failover.cli import upgrade
from asc.failover.discovery import Discovery
from asc.identity import fingerprint_from_pem, require_openssl
from asc.storage.runtime import setup
from asc.storage.client import StorageClient
from asc.store import Registry
from asc.server import Server, Handler
from tests import test_consensus as helpers

ROOT = Path(__file__).resolve().parents[1]


class LostAckProxy(Handler):
    """Test-only pinned fake-volume relay, drops one actual successful commit ACK."""
    def relay(self):
        conn = connect_pinned(self.server.upstream, self.server.pin, timeout=300)
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 <= length <= 1024**2:
                raise ValueError()
            body = self.rfile.read(length) if length else None
            headers = {k: v for k, v in self.headers.items() if k.lower() not in ('host', 'connection')}
            conn.request(self.command, self.path, body, headers)
            response = conn.getresponse(); raw = response.read(2*1024**2+1)
            if len(raw)>2*1024**2:
                raise ValueError()
            self.close_connection = True
            if self.command=='POST' and self.path.endswith('/commit') and response.status==200 and self.server.drop.is_set():
                self.server.drop.clear(); self.server.dropped.set()
                return  # The real immutable commit succeeded; its reply is lost.
            self.send_response(response.status)
            for field in ('Content-Type', 'X-ASC-SHA256'):
                value = response.getheader(field)
                if value is not None:
                    self.send_header(field, value)
            self.send_header('Content-Length', str(len(raw))); self.send_header('Connection', 'close')
            self.end_headers(); self.wfile.write(raw)
        except (OSError, ValueError, http.client.HTTPException):
            self.close_connection = True
        finally:
            conn.close()
    do_GET = do_POST = do_PUT = relay


class RuntimeStateTests(unittest.TestCase):
    def test_runtime_preserves_exact_metadata_snapshot_and_delta_envelopes(self):
        from unittest import mock
        from asc.catalog.metadata import MetadataSource, MetadataReplica
        from asc.failover.service import RuntimeHandler
        reg = state.MemoryRegistry(uid())
        self.addCleanup(reg.db.close)
        source = MetadataSource(reg)
        handler = object.__new__(RuntimeHandler)
        runtime = SimpleNamespace(local=SimpleNamespace(term=3),
            view=mock.Mock(side_effect=AssertionError('must not relabel versioned metadata payload')))
        handler.server = SimpleNamespace(catalog=SimpleNamespace(runtime=runtime))
        handler.command = 'GET'
        with tempfile.TemporaryDirectory(prefix='asc-metadata-envelope-') as root:
            replica = MetadataReplica(Path(root)/'cache.sqlite3', source.snapshot()['cluster_id'])
            for route, value, install in [('snapshot', source.snapshot(), replica.install),
                                          ('changes', source.changes(0), replica.apply)]:
                with self.subTest(route=route):
                    handler.path = '/catalog/v1/metadata/'+route+'?node_id='+uid()
                    original = copy.deepcopy(value)
                    with mock.patch.object(Handler, '_json', side_effect=lambda status, body: body):
                        reply = handler._json(200, value)
                    self.assertEqual(reply, original)
                    self.assertEqual(install(reply)['revision'], 0)
            runtime.view.assert_not_called()
            # HTTP parsing can reject a request before BaseHTTPRequestHandler
            # has initialized path. Its safe error response must still work.
            del handler.path
            with mock.patch.object(Handler, '_json', side_effect=lambda status, body: body):
                self.assertEqual(handler._json(400, {'error': 'bad_request'}), {'error': 'bad_request'})

    def test_attachment_proves_primary_or_fresh_follower_and_preserves_conflicting_authority(self):
        with tempfile.TemporaryDirectory() as root:
            cluster = uid()
            primary = Registry(Path(root)/'primary.sqlite3'); primary.initialize(cluster)
            joined = primary.join(primary.add_pair_code(), 'primary fake identity', {'protected': False},
                                  secrets.token_urlsafe(40), secrets.token_urlsafe(40))
            with primary.connect() as db:
                seed = canonical(export(db))
            fake = SimpleNamespace(state=lambda: {'state': {'schema': 1, 'cluster_id': cluster,
                'epoch': json.loads(seed)['epoch'], 'index': 0, 'term': 0, 'receipts': {},
                'document_sha256': hashlib.sha256(seed).hexdigest(), 'document': base64.b64encode(seed).decode()}})
            Adapter(primary, fake).activate()
            with primary.connect() as db:
                initial = state.takeover(state.export(db, 0, {'node_id': 'voter-a', 'term': 2}), 'voter-a', 2)
            sha = hashlib.sha256(seed).hexdigest()
            receipt = {'term': 2, 'document_sha256': digest(initial),
                       'intent_sha256': digest({'upgrade': 2, 'expected_sha256': sha})}
            view = {'state': {'receipts': {'runtime-upgrade-'+sha: receipt}}}
            self.assertEqual(state.verify_attachment(primary, view, ['voter-a', 'voter-b', 'voter-c']), 'primary-source')
            for name, conflict in [('fresh', False), ('conflicting', True)]:
                reg = Registry(Path(root)/(name+'.sqlite3')); reg.initialize(cluster); import_seed(reg, seed)
                private_identity = None
                if conflict:
                    private_identity = reg.join(reg.add_pair_code(), 'independent identity', {},
                                                secrets.token_urlsafe(40), secrets.token_urlsafe(40))
                Adapter(reg, fake).activate()
                if conflict:
                    with self.assertRaises(CatalogError) as rejected:
                        state.verify_attachment(reg, view, ['voter-a', 'voter-b', 'voter-c'])
                    self.assertEqual(rejected.exception.code, 'unmerged_controller_authority')
                    self.assertTrue(reg.authenticate_node(private_identity['node_id'], private_identity['token']))
                else:
                    self.assertEqual(state.verify_attachment(reg, view, ['voter-a', 'voter-b', 'voter-c']), 'fresh-metadata-follower')
            from unittest import mock
            with mock.patch('asc.catalog.schema.uid', side_effect=AssertionError('randomness during validation')):
                state.validate(initial)

    def test_discovery_never_adopts_an_advertised_endpoint_or_another_identity(self):
        from unittest import mock
        endpoints = [{'node_id': 'a', 'origin': 'https://127.0.0.1:8443', 'pin': 'a'*64}]
        router = Discovery(uid(), endpoints, secrets.token_urlsafe(40), attempts=1)
        reply = {'cluster_id': router.cluster_id, 'node_id': 'spoofed-b', 'write_ready': True,
                 'leader_endpoint': 'https://192.0.2.1:9000', 'pin': 'f'*64}
        with mock.patch('asc.failover.discovery.request_json', return_value=reply) as request:
            with self.assertRaises(ClientError):
                router.request('POST', '/api/v1/heartbeat', {})
            self.assertEqual(request.call_count, 1)
            self.assertEqual(request.call_args.args[:2], ('https://127.0.0.1:8443', 'A'*64))
        with self.assertRaises(ValueError):
            Discovery(uid(), [{**endpoints[0], 'token': secrets.token_urlsafe(40)}], secrets.token_urlsafe(40))
        with mock.patch('asc.failover.discovery.request_json', side_effect=[ClientError('unauthorized',401),
                {'cluster_id':router.cluster_id,'node_id':'a','leader_hint':True,'routing_hint_only':True},
                ClientError('credential rejected',401,'credential_rejected_repair_required')]) as request:
            with self.assertRaises(ClientError) as rejected:
                router.request('POST','/api/v1/heartbeat',{})
            self.assertEqual(rejected.exception.status,401)
            self.assertEqual(request.call_count,3)
            self.assertIsNone(router.cached)

    def test_authority_projection_preserves_hashes_and_rejects_private_columns(self):
        reg = state.MemoryRegistry(uid())
        try:
            token = secrets.token_urlsafe(40)
            joined = reg.join(reg.add_pair_code(), 'fake ZTE', {'protected': False}, secrets.token_urlsafe(40), token)
            doc = state.export(reg.db, 1, {'node_id': 'voter-a', 'term': 1})
            self.assertEqual(state.validate(doc), doc)
            self.assertNotIn(token.encode(), canonical(doc))
            with self.subTest('private_columns_denied'):
                bad = copy.deepcopy(doc); bad['tables']['nodes'][0]['private_key'] = 'forbidden'
                with self.assertRaises(CatalogError):
                    state.validate(bad)
            with self.subTest('revoked_token_cannot_return_on_takeover'):
                reg.revoke(joined['node_id'])
                revoked = state.export(reg.db, 2, doc['authority'])
                taken = state.takeover(revoked, 'voter-b', 2)
                recovered = state.prepare_registry(taken)
                try:
                    self.assertFalse(recovered.authenticate_node(joined['node_id'], token))
                    self.assertEqual(taken['catalog'], revoked['catalog'])
                finally:
                    recovered.db.close()
        finally:
            reg.db.close()


class FailoverTests(unittest.TestCase):
    start = helpers.ConsensusTests.start
    stop = helpers.ConsensusTests.stop
    stop_all = helpers.ConsensusTests.stop_all
    leader = helpers.ConsensusTests.leader

    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='asc-failover-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.base = Path(cls.temp.name)
        cls.binary = cls.base / ('asc-raft.exe' if os.name == 'nt' else 'asc-raft')
        subprocess.run([helpers.go_executable(), 'build', '-trimpath', '-o', str(cls.binary), './cmd/asc-raft'],
                       cwd=ROOT/'consensus', check=True, capture_output=True, timeout=120)
        cls.fixture_binary = cls.base / ('raft-fixture.exe' if os.name == 'nt' else 'raft-fixture')
        subprocess.run([helpers.go_executable(), 'test', '-c', '-o', str(cls.fixture_binary), '.'],
                       cwd=ROOT/'consensus', check=True, capture_output=True, timeout=120)

    def start(self, i):
        control = self.homes[i]/'test-control.json'
        if not control.exists():
            control.write_bytes(canonical({'address': helpers.unused_address(), 'token': secrets.token_urlsafe(40)}))
        env = dict(os.environ, ASC_TEST_RUNTIME_CONFIG=str(self.configs[i]), ASC_TEST_CONTROL_CONFIG=str(control))
        self.processes[i] = subprocess.Popen([str(self.fixture_binary)], env=env,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        deadline = time.monotonic()+20
        while time.monotonic()<deadline:
            if self.processes[i].poll() is not None:
                self.fail('test-only sidecar fixture refused startup')
            try:
                self.clients[i].status(); return
            except CatalogError:
                time.sleep(0.05)
        self.fail('test-only sidecar startup timeout')

    def partition(self, isolated, blocked=True):
        self.split([{isolated}, set(range(3))-{isolated}] if blocked else [set(range(3))])

    def split(self, groups):
        for i, home in enumerate(self.homes):
            cfg = json.loads((home/'test-control.json').read_bytes())
            group = next(g for g in groups if i in g)
            ids = [n['node_id'] for j, n in enumerate(self.nodes) if j not in group]
            conn = http.client.HTTPConnection(cfg['address'], timeout=3)
            try:
                conn.request('POST', '/fault', canonical({'blocked': ids, 'delay_ms': 0}),
                             {'Authorization': 'Bearer '+cfg['token'], 'Content-Type': 'application/json'})
                reply = conn.getresponse(); reply.read(); self.assertEqual(reply.status, 200)
            finally:
                conn.close()

    def make_cluster(self):
        cluster = uid()
        self.processes, self.python = [None]*3, [None]*3
        self.configs, self.clients, self.homes, self.registries = [], [], [], []
        self.nodes, self.endpoints = [], []
        self.addCleanup(self.close_cluster)
        self.addCleanup(self.failure_diagnostics)
        for i, name in enumerate(('ZTE V40', 'Bphone A40', 'Sony XZ3')):
            home = self.base / str(i); home.mkdir(); self.homes.append(home)
            cert, key = home/'peer.crt', home/'peer.key'
            subprocess.run([require_openssl(), 'req', '-x509', '-newkey', 'ec', '-pkeyopt', 'ec_paramgen_curve:P-256',
                '-sha256', '-nodes', '-days', '1', '-keyout', str(key), '-out', str(cert), '-subj', '/CN=ASC-SIMULATED-'+str(i),
                '-addext', 'subjectAltName=IP:127.0.0.1', '-addext', 'extendedKeyUsage=serverAuth,clientAuth',
                '-addext', 'basicConstraints=critical,CA:TRUE'], check=True, capture_output=True, timeout=20)
            shutil.copyfile(cert, home/'server.crt'); shutil.copyfile(key, home/'server.key')
            reg = Registry(home/'registry.sqlite3'); reg.initialize(cluster); self.registries.append(reg)
        primary = self.registries[0]
        legacy = CatalogService(primary)
        for i, home in enumerate(self.homes):
            token = secrets.token_urlsafe(40)
            node = primary.join(primary.add_pair_code(), ('ZTE V40', 'Bphone A40', 'Sony XZ3')[i],
                {'protected': False, 'simulation': True}, secrets.token_urlsafe(40), token)
            self.nodes.append(node)
            endpoint = {'node_id': node['node_id'], 'origin': 'https://'+helpers.unused_address(),
                        'pin': fingerprint_from_pem(home/'server.crt'), 'token': secrets.token_urlsafe(40)}
            self.endpoints.append(endpoint)
            (home/'controller.json').write_bytes(canonical({'cluster_id': cluster, 'admin_token': endpoint['token']}))
            volume = setup(home, node, self.base/('volume-'+str(i)), quota=8*1024**2, reserve=0,
                           port=int(helpers.unused_address().rsplit(':', 1)[1]))
            storage = json.loads((home/'storage.json').read_bytes())
            legacy.register(node['node_id'], 'https://127.0.0.1:'+str(storage['port']), volume['pin'],
                            'simulated-device-'+str(i), [volume['volume_id']])
        with primary.connect() as db:
            seed = canonical(export(db))
        for reg in self.registries[1:]:
            import_seed(reg, seed)
        doc = json.loads(seed)
        peers = [{'id': n['node_id'], 'address': helpers.unused_address(),
                  'certificate': (h/'peer.crt').read_text()} for n, h in zip(self.nodes, self.homes)]
        for i, home in enumerate(self.homes):
            (home/'seed.json').write_bytes(seed)
            cfg = {'schema': 1, 'cluster_id': cluster, 'epoch': doc['epoch'], 'node_id': self.nodes[i]['node_id'],
                'peers': peers, 'state_dir': str(home/'raft-state'), 'seed_file': str(home/'seed.json'),
                'seed_sha256': hashlib.sha256(seed).hexdigest(), 'cert_file': str(home/'peer.crt'),
                'key_file': str(home/'peer.key'), 'ipc_address': helpers.unused_address(), 'ipc_token': secrets.token_urlsafe(40)}
            path = home/'consensus.json'; path.write_bytes(canonical(cfg)); self.configs.append(path)
            self.clients.append(Client.from_config(path))
            subprocess.run([str(self.binary), 'init', '--config', str(path)], check=True, capture_output=True, timeout=20)
        for i in range(3):
            self.start(i)
        leader = self.leader()
        for reg, client in zip(self.registries, self.clients):
            Adapter(reg, client).activate()
        # Authoritative private registry is on voter 0. Upgrade requires a local
        # leader sidecar: use an explicit exact shared-state seed transaction
        # prepared from that stopped primary, without copying private keys.
        upgrade(primary.path, self.configs[leader], hashlib.sha256(seed).hexdigest())
        public = [{k: v for k, v in e.items() if k != 'token'} for e in self.endpoints]
        for i, home in enumerate(self.homes):
            node = {**self.nodes[i], 'cluster_id': cluster, 'cluster_epoch': doc['epoch'], 'controllers': public,
                    'controller': self.endpoints[0]['origin'], 'pin': self.endpoints[0]['pin']}
            (home/'node.json').write_bytes(canonical(node))
            port = int(self.endpoints[i]['origin'].rsplit(':', 1)[1])
            (home/'failover.json').write_bytes(canonical({'schema': 1, 'home': str(home),
                'consensus_config': str(self.configs[i]), 'host': '127.0.0.1', 'port': port}))
        for i in range(3):
            self.launch_python(i)
        self.cluster, self.epoch = cluster, doc['epoch']
        self.owner = ClusterClient(cluster_id=cluster, controllers=self.endpoints)
        return self.wait_ready()

    def launch_python(self, i):
        proc = subprocess.Popen([sys.executable, '-B', '-m', 'asc.failover.cli', 'run', '--config', str(self.homes[i]/'failover.json')],
            cwd=ROOT, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        self.python[i] = proc
        deadline = time.monotonic()+30
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                out, err = proc.communicate(timeout=2)
                self.fail('isolated runtime startup failed: '+(out+err).decode(errors='replace')[-2000:])
            try:
                e = self.endpoints[i]
                request_json(e['origin'], e['pin'], 'GET', '/api/v1/info', timeout=2)
                return
            except (ClientError, OSError):
                time.sleep(0.1)
        self.fail('Python Controller did not start')

    def kill_python(self, i):
        proc = self.python[i]
        if proc is not None:
            if proc.poll() is None:
                proc.kill()
            proc.communicate(timeout=15)
            self.python[i] = None

    def close_cluster(self):
        for i in range(3):
            self.kill_python(i)
        self.stop_all()

    def failure_diagnostics(self):
        if self._outcome.result.wasSuccessful():
            return
        for i, home in enumerate(self.homes):
            try:
                status = self.clients[i].status()
                print('\nIsolated Go diagnostics', i, status['role'], status['term'],
                      'quarantined', status['quarantined'], flush=True)
                view = self.clients[i].state()['state']
                print('Isolated Go receipts', i, len(view['receipts']), flush=True)
            except (CatalogError, OSError, ValueError, KeyError):
                print('\nIsolated Go diagnostics unavailable', i, flush=True)
            if not (home/'runtime.sqlite3').exists():
                continue
            try:
                doc = self.cached(i)['document']
                print('\nIsolated fixture diagnostics', i,
                    'jobs', [(j['kind'], j['state'], j['last_error']) for j in doc['tables']['catalog_jobs']],
                    'replicas', [r['state'] for r in doc['catalog']['replicas']],
                    'nodes', [(n['state'], int(time.time())-n['last_seen']) for n in doc['tables']['nodes']],
                    'probes', [(n['last_error'], int(time.time())-n['checked_at'] if n['checked_at'] else None)
                               for n in doc['tables']['catalog_nodes']], flush=True)
            except (OSError, sqlite3.Error, ValueError, KeyError):
                print('Isolated fixture diagnostics unavailable', i, flush=True)

    def wait_ready(self, exclude=()):
        deadline = time.monotonic()+70
        while time.monotonic() < deadline:
            ready = []
            for i, e in enumerate(self.endpoints):
                if i in exclude or self.python[i] is None:
                    continue
                try:
                    reply = request_json(e['origin'], e['pin'], 'GET', '/cluster/v1/leader', token=e['token'], timeout=20)
                    if reply['write_ready']:
                        ready.append(i)
                except (OSError, ClientError):
                    pass
            if ready:
                self.assertEqual(len(ready), 1)
                return ready[0]
            time.sleep(0.2)
        self.fail('no single write-ready Controller')

    def cached(self, i):
        with closing(sqlite3.connect(self.homes[i]/'runtime.sqlite3', timeout=15)) as db:
            return json.loads(db.execute('SELECT data FROM projection').fetchone()[0])

    def wait_job(self, job_id, timeout=150):
        deadline = time.monotonic()+timeout
        while time.monotonic()<deadline:
            job = self.owner.request('GET', 'jobs/'+job_id)['job']
            if job['state'] == 'COMPLETED':
                return job
            self.assertNotEqual(job['state'], 'FAILED', job['last_error'])
            time.sleep(0.25)
        self.fail('persistent job did not complete within its qualified recovery budget')

    def checkpoint(self, leader, file_id):
        deadline = time.monotonic()+150
        while time.monotonic()<deadline:
            doc = self.cached(leader)['document']
            for job in doc['tables']['catalog_jobs']:
                if job['file_id'] == file_id and job['kind'] == 'COPY' and job['state'] == 'RUNNING' and job['target_session_id']:
                    return dict(job)
            time.sleep(0.03)
        self.fail('copy never reached durable RUNNING/session checkpoint before injection')

    def direct(self, i, method, path, obj=None, token=None):
        e = self.endpoints[i]
        return request_json(e['origin'], e['pin'], method, path, obj, token or e['token'], timeout=300 if method=='POST' else 20)

    def mark(self, number, label):
        print(f'\nPhase 2B {number:02d} PASS: {label}', flush=True)

    def physical_job_state(self, job, data):
        """Check this job across every volume; unrelated background copies may grow."""
        result = []
        for i, home in enumerate(self.homes):
            with closing(sqlite3.connect(home/'storage'/'manifest.sqlite3', timeout=15)) as db:
                db.row_factory = sqlite3.Row
                uploads = db.execute('SELECT session_id,file_id,principal,idempotency_key,logical_path,volume_id,state '
                    'FROM uploads WHERE principal=? OR idempotency_key=? OR logical_path=? ORDER BY session_id',
                    ('job:'+job['job_id'], job['idempotency_key'], job['logical_path'])).fetchall()
                files = db.execute('SELECT file_id,logical_path,volume_id,relative_path,size,sha256,state '
                    'FROM files WHERE logical_path=? OR file_id IN '
                    '(SELECT file_id FROM uploads WHERE principal=? OR idempotency_key=?) ORDER BY file_id',
                    (job['logical_path'], 'job:'+job['job_id'], job['idempotency_key'])).fetchall()
            self.assertEqual({r['file_id'] for r in uploads}, {r['file_id'] for r in files})
            for upload in uploads:
                self.assertEqual(upload['principal'], 'job:'+job['job_id'])
                self.assertEqual(upload['idempotency_key'], job['idempotency_key'])
                self.assertEqual(upload['logical_path'], job['logical_path'])
                self.assertEqual(upload['state'], 'COMMITTED')
            for file in files:
                self.assertEqual(file['state'], 'COMMITTED')
                self.assertEqual(file['size'], len(data))
                self.assertEqual(file['sha256'], hashlib.sha256(data).hexdigest())
                self.assertEqual((self.base/('volume-'+str(i))/file['relative_path']).read_bytes(), data)
            result.append((tuple(tuple(r) for r in uploads), tuple(tuple(r) for r in files)))
        self.assertEqual(sum(len(uploads) for uploads, _ in result), 1, 'job must retain exactly one physical session/object')
        return result

    def sync_metadata(self, index, file_id):
        from asc.catalog.metadata import MetadataReplica, synchronize
        home = self.homes[index]
        node = json.loads((home/'node.json').read_bytes())
        status = synchronize(home, node)
        self.assertTrue(status['read_only'])
        self.assertTrue(status['stale'])
        self.assertEqual(status['cluster_id'], self.cluster)
        self.assertEqual(status['epoch'], self.epoch)
        cache = MetadataReplica(home/'catalog-metadata.sqlite3', self.cluster, read_only=True)
        self.assertEqual(cache.file(file_id)['entry']['file']['file_id'], file_id)
        self.assertEqual(cache.status()['revision'], status['revision'])

    def upload_job(self, file_id):
        jobs = self.owner.request('GET', 'jobs')['jobs']
        uploads = [j for j in jobs if j['file_id']==file_id and j['kind']=='UPLOAD']
        self.assertEqual(len(uploads), 1, 'retry must retain exactly one UPLOAD job')
        return self.owner.request('GET', 'jobs/'+uploads[0]['job_id'])['job']

    def lose_actual_commit_ack(self, leader, data):
        obj = {'idempotency_key': 'lost-actual-commit-ack', 'logical_path': 'phase2b/lost-ack.bin',
               'size': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'policy': 'single', 'version': 1}
        plan = self.owner.request('POST', 'uploads', obj)
        target = plan['target']
        index = next(i for i, node in enumerate(self.nodes) if node['node_id']==target['node_id'])
        original = next(n for n in self.cached(leader)['document']['tables']['catalog_nodes'] if n['node_id']==target['node_id'])
        proxy = Server(('127.0.0.1', 0), None, '', LostAckProxy)
        proxy.upstream, proxy.pin = original['origin'], original['pin']
        proxy.drop, proxy.dropped = threading.Event(), threading.Event(); proxy.drop.set()
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(self.homes[index]/'storage.crt', self.homes[index]/'storage.key')
        proxy.tls_context = context
        thread = threading.Thread(target=proxy.serve_forever, daemon=True); thread.start()
        self.addCleanup(lambda: (proxy.shutdown(), proxy.server_close(), thread.join(timeout=5)))
        proxy_origin = 'https://127.0.0.1:'+str(proxy.server_address[1])
        registration = {'node_id': original['node_id'], 'device_id': original['device_id'], 'origin': proxy_origin,
                        'pin': original['pin'], 'volume_ids': json.loads(original['volume_ids'])}
        self.owner.request('POST', 'nodes/register', registration)
        client = StorageClient(proxy_origin, target['pin'], target['grant'], target['volume_id'], timeout=300)
        session = client.initiate(plan['idempotency_key'], plan['local_logical_path'], len(data), obj['sha256'])
        client.upload(session['session_id'], io.BytesIO(data), len(data))
        with self.assertRaises((OSError, http.client.HTTPException, ClientError)):
            client.commit(session['session_id'])
        self.assertTrue(proxy.dropped.is_set())
        file_id = plan['file']['file']['file_id']
        job = self.upload_job(file_id)
        before = self.physical_job_state(job, data)
        result = self.owner.upload(io.BytesIO(data), obj['logical_path'], obj['idempotency_key'], 'single')
        if result['job_state']!='COMPLETED':
            self.wait_job(result['job_id'])
        completed = self.upload_job(file_id)
        self.assertEqual(completed['job_id'], plan['job_id'])
        self.assertEqual(completed['target_session_id'], session['session_id'])
        self.assertEqual(completed['target_local_file_id'], session['file_id'])
        self.assertEqual(self.physical_job_state(completed, data), before)
        self.assertEqual(result['file']['file']['file_id'], file_id)
        self.owner.request('POST', 'nodes/register', {**registration, 'origin': original['origin']})

    def test_real_process_upload_and_controller_takeover(self):
        leader = self.make_cluster()
        self.mark(1, 'one automatically elected, quorum-confirmed write-ready Controller')
        data = b'fake Phase 2B bytes\0'*128
        result = self.owner.upload(io.BytesIO(data), 'phase2b/one.bin', 'phase2b-upload-001', 'replicated_2')
        file_id = result['file']['file']['file_id']
        deadline = time.monotonic()+180
        while time.monotonic() < deadline:
            report = self.owner.request('GET', 'files/'+file_id+'?consistency=strong')
            if report['verified_replicas'] >= 2:
                break
            time.sleep(0.5)
        self.assertGreaterEqual(report['verified_replicas'], 2)
        for index in range(3):
            self.sync_metadata(index, file_id)
        self.mark(2, 'actual upload, independent manifests/objects and verified replication')
        old = leader
        self.kill_python(old)
        # Kill Python only: its armed sidecar must withdraw automatically.
        leader = self.wait_ready(exclude=(old,))
        self.assertNotEqual(old, leader)
        self.mark(3, 'Leader failure automatically activates another Controller')
        result = self.owner.upload(io.BytesIO(data), 'phase2b/two.bin', 'phase2b-upload-002', 'single')
        if result['job_state'] != 'COMPLETED':
            self.wait_job(result['job_id'])
        self.mark(4, 'same client automatically rediscovers pinned new Leader')
        self.mark(5, 'new upload completes after takeover')
        self.sync_metadata(leader, result['file']['file']['file_id'])
        output = io.BytesIO(); self.owner.download(file_id, output)
        self.assertEqual(output.getvalue(), data)
        # Restart old cohost from complete durable state. Its old sidecar has
        # withdrawn; it may only follow the surviving quorum.
        self.stop(old)
        self.start(old); self.launch_python(old)
        leader = self.wait_ready()
        self.assertNotEqual(old, leader)
        self.assertEqual(self.clients[old].status()['role'], 'Follower')
        with self.assertRaises(ClientError) as rejected:
            self.direct(old, 'POST', '/catalog/v1/files/'+file_id+'/policy', {'policy': 'single'})
        self.assertEqual(rejected.exception.status, 503)
        self.mark(8, 'returned old Leader is a follower and rejects direct writes')

        # Kill Go after durable checkpoint, with Python and Storage alive.
        third = self.owner.upload(io.BytesIO(data*8), 'phase2b/recovery.bin', 'phase2b-upload-003', 'single')
        if third['job_state'] != 'COMPLETED':
            self.wait_job(third['job_id'])
        recover_file = third['file']['file']['file_id']
        self.owner.request('POST', 'files/'+recover_file+'/policy', {'policy': 'replicated_2'})
        checkpoint = self.checkpoint(leader, recover_file)
        self.stop(leader, crash=True)
        next_leader = self.wait_ready(exclude=(leader,))
        self.assertNotEqual(leader, next_leader)
        self.start(leader)
        leader = next_leader
        completed = self.wait_job(checkpoint['job_id'])
        self.assertEqual(completed['target_session_id'], checkpoint['target_session_id'])
        self.assertEqual(completed['target_local_file_id'], checkpoint['target_local_file_id'])
        self.mark(6, 'persistent copy resumes same job/session/object after Leader loss')
        self.mark(15, 'actual Go process killed mid-job; Python cannot continue old authority')
        upload_job = self.upload_job(recover_file)
        before = self.physical_job_state(upload_job, data*8)
        copied = self.physical_job_state(completed, data*8)
        replay = self.owner.upload(io.BytesIO(data*8), 'phase2b/recovery.bin', 'phase2b-upload-003', 'single')
        self.assertEqual(replay['file']['file']['file_id'], recover_file)
        self.assertEqual(self.upload_job(recover_file)['job_id'], upload_job['job_id'])
        self.assertEqual(before, self.physical_job_state(upload_job, data*8))
        self.assertEqual(copied, self.physical_job_state(completed, data*8))
        self.lose_actual_commit_ack(leader, data)
        self.mark(7, 'actual successful commit ACK dropped over TLS; safe replay creates no duplicate object')

        fourth = self.owner.upload(io.BytesIO(data*8), 'phase2b/python-recovery.bin', 'phase2b-upload-004', 'single')
        if fourth['job_state'] != 'COMPLETED':
            self.wait_job(fourth['job_id'])
        fourth_id = fourth['file']['file']['file_id']
        self.owner.request('POST', 'files/'+fourth_id+'/policy', {'policy': 'replicated_2'})
        python_checkpoint = self.checkpoint(leader, fourth_id)
        self.kill_python(leader)
        next_leader = self.wait_ready(exclude=(leader,))
        self.stop(leader); self.start(leader); self.launch_python(leader)
        leader = next_leader
        completed = self.wait_job(python_checkpoint['job_id'])
        self.assertEqual(completed['target_session_id'], python_checkpoint['target_session_id'])
        self.assertEqual(completed['target_local_file_id'], python_checkpoint['target_local_file_id'])
        self.mark(16, 'Python killed mid-copy; watchdog withdrawal and new Controller recover stable checkpoints')

        # Bidirectional 1/2 partition is injected into test-only Go transport;
        # this endpoint does not exist in the production sidecar binary.
        old_view = self.clients[leader].state(strong=True)['state']
        self.partition(leader)
        minority = leader
        leader = self.wait_ready(exclude=(minority,))
        with self.assertRaises(ClientError) as rejected:
            self.direct(minority, 'POST', '/catalog/v1/files/'+file_id+'/policy', {'policy': 'single'})
        self.assertEqual(rejected.exception.status, 503)
        self.owner.request('POST', 'files/'+file_id+'/policy', {'policy': 'replicated_3'})
        self.mark(9, '1/2 partition leaves only majority Controller write-authorized')
        delayed = {'schema': 1, 'cluster_id': self.cluster, 'epoch': self.epoch,
            'request_id': 'delayed-old-runtime', 'intent_sha256': digest({'test': 'delayed-old'}),
            'authority_term': json.loads(base64.b64decode(old_view['document']))['authority']['term'],
            'expected_sha256': old_view['document_sha256'], 'document': old_view['document']}
        with self.assertRaises(CatalogError):
            self.clients[minority].submit(delayed)
        self.partition(minority, False)
        view = self.clients[leader].state(strong=True)['state']
        forged = json.loads(base64.b64decode(view['document']))
        forged['authority']['term'] = 1000000; forged['revision'] += 1
        with self.assertRaises(CatalogError) as rejected:
            self.clients[leader].submit({**delayed, 'request_id': 'forged-high-runtime',
                'authority_term': 1000000, 'expected_sha256': view['document_sha256'],
                'document': base64.b64encode(canonical(forged)).decode()})
        self.assertEqual(rejected.exception.code, 'stale_authority')
        self.mark(17, 'delayed old request and self-asserted high term cannot change authority')

        self.split([{0}, {1}, {2}])
        for i in range(3):
            with self.assertRaises(ClientError) as rejected:
                self.direct(i, 'POST', '/catalog/v1/files/'+file_id+'/policy', {'policy': 'single'})
            self.assertEqual(rejected.exception.status, 503)
        self.mark(10, 'all three isolated Controllers reject mutations without quorum')
        for i in range(3):
            stale = self.direct(i, 'GET', '/catalog/v1/files')
            self.assertTrue(stale['stale']); self.assertTrue(stale['read_only'])
            cached = self.cached(i)
            self.assertEqual(stale['revision'], cached['document']['catalog']['revision'])
            self.assertEqual(stale['applied_index'], cached['state']['index'])
            self.assertIsNone(stale['available_replicas'])
        self.mark(11, 'offline stale reads report exact verified local revisions/checkpoints')
        self.split([set(range(3))]); leader = self.wait_ready()

        # Current identity and revoked hashes are authoritative across takeover.
        victim = (leader+1)%3
        node = self.nodes[victim]
        self.owner.discovery.request('POST', '/api/v1/admin/revoke', {'node_id': node['node_id']})
        self.stop(leader, crash=True)
        next_leader = self.wait_ready(exclude=(leader,)); self.start(leader); leader = next_leader
        with self.assertRaises(ClientError) as rejected:
            self.owner.discovery.request('POST', '/api/v1/heartbeat',
                {'node_id': node['node_id'], 'profile': {} })
        # The owner token cannot impersonate node heartbeat either.
        self.assertIn(rejected.exception.status, (401, 403))
        with self.assertRaises(ClientError) as rejected:
            self.direct(leader, 'POST', '/api/v1/heartbeat', {'node_id': node['node_id'], 'profile': {}}, node['token'])
        self.assertEqual(rejected.exception.status, 401)
        with self.assertRaises(ClientError):
            self.owner.request('POST', 'nodes/register', {'node_id': node['node_id'], 'device_id': 'revoked',
                'metadata_allowed': True, 'storage_allowed': False})
        self.mark(12, 'revoked Agent remains rejected and cannot receive new storage authority after failover')
        pair = self.owner.discovery.request('POST', '/api/v1/admin/pair', {'node_id': node['node_id']})
        replacement_token = secrets.token_urlsafe(40)
        enrollment = {'code': pair['code'], 'name': 'repaired fake node', 'profile': {'protected': False},
            'enrollment_id': secrets.token_urlsafe(40), 'enrollment_token': replacement_token, 'node_id': node['node_id']}
        replacement = self.owner.discovery.request('POST', '/api/v1/join', enrollment)
        replay = self.owner.discovery.request('POST', '/api/v1/join', enrollment)
        self.assertEqual(replacement['node_id'], node['node_id'])
        for field in ('node_id', 'token', 'token_version'):
            self.assertEqual(replay[field], replacement[field])
        topology = self.owner.discovery.request('GET', '/api/v1/nodes')
        self.assertEqual(len(topology['nodes']), 3)
        self.mark(13, 'retry-safe re-pair rotates generation while retaining identity and operation routing')
        cfg_path = self.homes[victim]/'node.json'; cfg = json.loads(cfg_path.read_bytes())
        cfg.update(token=replacement_token, token_version=replacement['token_version'])
        cfg_path.write_bytes(canonical(cfg))
        self.kill_python(victim)
        # Controlled cohost restart after private-token repair. This node may
        # itself be Leader; do not race discovery against watchdog withdrawal.
        # Python-only fault recovery is qualified independently in cases 3/16.
        self.stop(victim); self.start(victim)
        self.launch_python(victim)
        leader = self.wait_ready()
        approval = next(n for n in self.cached(leader)['document']['tables']['catalog_nodes'] if n['node_id']==node['node_id'])
        self.owner.request('POST', 'nodes/register', {'node_id': node['node_id'], 'device_id': approval['device_id'],
            'origin': approval['origin'], 'pin': approval['pin'], 'volume_ids': json.loads(approval['volume_ids'])})

        before = self.clients[leader].state(strong=True)['state']
        self.clients[leader].request('POST', '/v1/snapshot', {})
        for i in range(3):
            self.stop(i, crash=True)
        for i in range(3):
            self.start(i)
        leader = self.wait_ready()
        after = self.clients[leader].state(strong=True)['state']
        before_doc = json.loads(base64.b64decode(before['document']))
        after_doc = json.loads(base64.b64decode(after['document']))
        self.assertEqual(before_doc['catalog'], after_doc['catalog'])
        self.assertEqual(before_doc['tables']['enrollments'], after_doc['tables']['enrollments'])
        self.sync_metadata(victim, recover_file)
        self.mark(14, 'snapshot and all-sidecar restart preserve committed Catalog history and identities')
        for raw_secret in [n['token'] for n in self.nodes]+[replacement_token]+[e['token'] for e in self.endpoints]:
            self.assertNotIn(raw_secret.encode(), canonical(after_doc))
        with self.assertRaises(ClientError) as rejected:
            self.direct(leader, 'POST', '/api/v1/heartbeat', {'node_id': node['node_id'], 'profile': {}}, node['token'])
        self.assertEqual(rejected.exception.status, 401)
        self.mark(19, 'snapshot/failover never restores old bearer; log projection contains hashes only')

        # Corrupt one fake copy only. The other copy must remain readable and
        # the suspect physical body must be retained, never overwritten/GC'd.
        report = self.owner.request('GET', 'files/'+recover_file+'?consistency=strong')
        replica = report['replicas'][0]
        index = next(i for i, n in enumerate(self.nodes) if n['node_id']==replica['node_id'])
        object_path = self.base/('volume-'+str(index))/'objects'/(replica['local_file_id']+'.blob')
        original = object_path.read_bytes(); corrupt = b'X'+original[1:]; object_path.write_bytes(corrupt)
        deadline = time.monotonic()+150
        while time.monotonic()<deadline:
            self.owner.request('POST', 'reconcile', {})
            report = self.owner.request('GET', 'files/'+recover_file+'?consistency=strong')
            state_by_id = {r['replica_id']: r['state'] for r in report['replicas']}
            if state_by_id.get(replica['replica_id']) == 'CORRUPT':
                break
            time.sleep(0.5)
        self.assertEqual(state_by_id[replica['replica_id']], 'CORRUPT')
        self.assertEqual(object_path.read_bytes(), corrupt)
        self.assertTrue(any(r['state']=='VERIFIED' for r in report['replicas']))
        self.mark(18, 'physical mismatch is reconciled without deleting suspect/last copies')
        from unittest import mock
        from asc.failover import cli as runtime_cli
        with mock.patch.object(runtime_cli, 'inspect', return_value={'protected': True}):
            with self.assertRaises(ValueError):
                runtime_cli.run('never-read-protected-config')
        protected_pair = self.owner.discovery.request('POST', '/api/v1/admin/pair', {})
        protected = self.owner.discovery.request('POST', '/api/v1/join', {'code': protected_pair['code'],
            'name': 'M51 protected simulation', 'profile': {'protected': True},
            'enrollment_id': secrets.token_urlsafe(40), 'enrollment_token': secrets.token_urlsafe(40)})
        with self.assertRaises(ClientError) as rejected:
            self.owner.request('POST', 'nodes/register', {'node_id': protected['node_id'], 'device_id': 'protected',
                'storage_allowed': False, 'metadata_allowed': True})
        self.assertEqual(rejected.exception.status, 403)
        configured_voters = {p['id'] for p in json.loads(self.configs[leader].read_bytes())['peers']}
        self.assertNotIn(protected['node_id'], configured_voters)
        self.mark(20, 'protected simulation cannot start Controller or become approved work target')
