"""Three isolated Windows-compatible nodes using actual pinned loopback HTTPS."""
import contextlib
import hashlib
import io
import json
import secrets
import socket
import ssl
import tempfile
import threading
import time
from pathlib import Path
import unittest
from unittest import mock
from asc import cli
from asc.client import ClientError, connect_pinned, request_json
from asc.identity import fingerprint_from_pem, make_cert, save_private
from asc.server import Server
from asc.store import Registry, SCHEMA_VERSION
from asc.storage.client import StorageClient
from asc.storage.errors import StorageError
from asc.storage.runtime import StorageRuntime, setup


class ClusterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.admin = secrets.token_urlsafe(32)
        home = self.base / 'controller'; home.mkdir()
        cert, key = home / 'server.crt', home / 'server.key'
        make_cert(cert, key)
        self.pin = fingerprint_from_pem(cert)
        self.reg = Registry(home / 'registry.sqlite3'); self.reg.initialize('test-cluster')
        self.server = Server(('127.0.0.1', 0), self.reg, self.admin)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(cert, key)
        self.server.tls_context = context
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True); self.thread.start()
        self.origin = 'https://127.0.0.1:' + str(self.server.server_address[1])
        self.addCleanup(self.stop_controller)
        self.nodes = []
        for index, name in enumerate(('ZTE V40', 'Bphone A40', 'Sony XZ3')):
            private = self.base / str(index) / 'private'
            private.mkdir(parents=True)
            code = self.controller('POST', '/api/v1/admin/pair', {}, self.admin)['code']
            joined = self.controller('POST', '/api/v1/join',
                                     {'code': code, 'name': name,
                                      'profile': {'profile_version': 1, 'model': name, 'protected': False,
                                                  'memory_mb': None, 'simulation': True}})
            cfg = {**joined, 'controller': self.origin, 'pin': self.pin}
            save_private(private / 'node.json', cfg)
            with socket.socket() as sock:
                sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]
            result = setup(private, cfg, self.base / str(index) / 'data', quota=1024**2, reserve=0, port=port)
            runtime = StorageRuntime(private, cfg).__enter__()
            node = {'name': name, 'private': private, 'cfg': cfg, 'volume': result['volume_id'],
                    'runtime': runtime, 'pin': result['pin'], 'port': port}
            self.nodes.append(node)
            self.addCleanup(lambda n=node: n['runtime'].__exit__(None, None, None))
            with mock.patch.object(cli, 'HOME', private), mock.patch.object(cli, 'inspect',
                    return_value={'profile_version': 1, 'model': name, 'protected': False, 'simulation': True}):
                cli.agent_once(cfg, storage_engine=runtime.engine)
        self.node = self.nodes[0]
        self.client = self.owner(self.node)
        self.data = b'actual HTTPS storage body\x00' * 10000
        self.sha = hashlib.sha256(self.data).hexdigest()

    def stop_controller(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join()

    def controller(self, method, path, obj=None, token=None):
        return request_json(self.origin, self.pin, method, path, obj, token)

    def owner(self, node, operations=None, token=None):
        reply = self.controller('POST', '/api/v1/admin/storage-grant',
                                {'node_id': node['cfg']['node_id'], 'volume_id': node['volume'],
                                 'operations': operations or ['read', 'write', 'list', 'verify']},
                                self.admin)
        return StorageClient('https://127.0.0.1:' + str(node['port']), node['pin'],
                             token or reply['grant'], node['volume'])

    def assert_status(self, status, call):
        with self.assertRaises(ClientError) as caught:
            call()
        self.assertEqual(caught.exception.status, status)

    def upload(self, client=None, key='cluster_request_01', path='docs/demo.bin'):
        client = client or self.client
        row = client.initiate(key, path, len(self.data), self.sha)
        client.upload(row['session_id'], io.BytesIO(self.data), len(self.data))
        return row, client.commit(row['session_id'])

    def test_three_node_upload_download_restart_duplicate_disconnect_and_faults(self):
        snapshot = self.controller('GET', '/api/v1/nodes', token=self.admin)
        self.assertEqual({n['name'] for n in snapshot['nodes']}, {'ZTE V40', 'Bphone A40', 'Sony XZ3'})
        for node in snapshot['nodes']:
            storage = node['profile']['storage']
            self.assertEqual(storage['storage_version'], 1)
            self.assertEqual(storage['recommended_storage_role'], 'Storage')
            self.assertIsNone(node['profile'].get('memory_mb'))
        for node in self.nodes:
            client = self.owner(node)
            row, file = self.upload(client)
            output = io.BytesIO()
            client.download(file['file_id'], output, len(self.data), self.sha)
            self.assertEqual(output.getvalue(), self.data)
            self.assertEqual(client.json('POST', 'files/' + file['file_id'] + '/verify', {})['state'], 'COMMITTED')
            duplicate = client.initiate('cluster_request_01', 'docs/demo.bin', len(self.data), self.sha)
            self.assertEqual(duplicate['session_id'], row['session_id'])
            self.assertEqual(client.commit(row['session_id'])['file_id'], file['file_id'])
            self.assert_status(409, lambda: client.initiate('another_request', 'docs/demo.bin', len(self.data), self.sha))
            node['runtime'].__exit__(None, None, None)
            node['runtime'] = StorageRuntime(node['private'], node['cfg']).__enter__()
            output = io.BytesIO(); client.download(file['file_id'], output, len(self.data), self.sha)
            self.assertEqual(hashlib.sha256(output.getvalue()).hexdigest(), self.sha)
        row = self.client.initiate('disconnect_req', 'partial.bin', len(self.data), self.sha)
        conn = self.client._connection('PUT', 'uploads/' + row['session_id'], len(self.data), 'application/octet-stream')
        conn.send(self.data[:100])
        deadline = time.monotonic() + 5
        while self.client.json('GET', 'uploads/' + row['session_id'])['session']['state'] != 'WRITING':
            if time.monotonic() >= deadline:
                conn.close()
                self.fail('upload worker did not enter WRITING before disconnect')
            time.sleep(0.01)
        conn.close()  # Disconnect an established streaming write, not a pre-handshake TLS request.
        deadline = time.monotonic() + 5
        while True:
            state = self.client.json('GET', 'uploads/' + row['session_id'])['session']['state']
            if state == 'INTERRUPTED' or time.monotonic() >= deadline:
                break
            time.sleep(0.01)
        self.assertEqual(state, 'INTERRUPTED')
        self.client.upload(row['session_id'], io.BytesIO(self.data), len(self.data))
        file = self.client.commit(row['session_id'])
        self.assert_status(507, lambda: self.client.initiate('quota_request', 'too-big', 600000, self.sha))
        root = self.base / '0' / 'data'; offline = root.with_name('offline')
        root.rename(offline)
        try:
            self.assert_status(503, lambda: self.client.json('GET', 'files'))
        finally:
            offline.rename(root)
        with self.node['runtime'].engine.manifest.connect() as db:
            db.execute('UPDATE files SET size=size+1 WHERE file_id=?', (file['file_id'],))
        self.assert_status(409, lambda: self.client.json('GET', 'files/' + file['file_id']))
        self.assertTrue((root / file['relative_path']).exists())

    def test_node_user_separation_scope_pin_expiry_revoke_repair_and_controller_outage(self):
        self.assert_status(403, lambda: self.owner(self.node, token=self.node['cfg']['token']).json('GET', 'files'))
        reader = self.owner(self.node, ['read', 'list'])
        self.assert_status(403, lambda: reader.initiate('read_only_req', 'x', 0, hashlib.sha256(b'').hexdigest()))
        wrong_node = StorageClient('https://127.0.0.1:' + str(self.nodes[1]['port']), self.nodes[1]['pin'],
                                   self.client.grant, self.node['volume'])
        self.assert_status(403, lambda: wrong_node.json('GET', 'files'))
        with self.assertRaises(ClientError):
            StorageClient(self.client.origin, '0' * 64, self.client.grant, self.node['volume']).json('GET', 'files')
        with self.reg.connect() as db:
            db.execute('UPDATE storage_grants SET expires_at=1')
        self.assert_status(403, lambda: self.client.json('GET', 'files'))
        self.client = self.owner(self.node)
        self.controller('POST', '/api/v1/admin/revoke', {'node_id': self.node['cfg']['node_id']}, self.admin)
        self.assert_status(403, lambda: self.client.json('GET', 'files'))
        code = self.controller('POST', '/api/v1/admin/pair', {'node_id': self.node['cfg']['node_id']}, self.admin)['code']
        replacement = self.controller('POST', '/api/v1/join',
                     {'code': code, 'node_id': self.node['cfg']['node_id'], 'name': 'ZTE V40', 'profile': {},
                      'enrollment_id': secrets.token_urlsafe(32), 'enrollment_token': secrets.token_urlsafe(32)})
        self.assertEqual(replacement['node_id'], self.node['cfg']['node_id'])
        self.node['runtime'].server.node_config.update(replacement)
        self.assert_status(403, lambda: self.client.json('GET', 'files'))  # Previous generation grant stays invalid.
        self.client = self.owner(self.node)
        self.assertEqual(self.client.json('GET', 'files')['files'], [])
        with mock.patch('asc.storage.http.request_json', side_effect=OSError('controller unavailable')):
            self.assert_status(503, lambda: self.client.json('GET', 'files'))

    def test_http_framing_traversal_no_anonymous_access_and_uncommitted_hidden(self):
        conn = connect_pinned(self.client.origin, self.client.pin)
        try:
            conn.request('GET', '/storage/v1/files')
            self.assertEqual(conn.getresponse().status, 401)
        finally:
            conn.close()
        self.assert_status(403, lambda: self.owner(self.node, token='a' * 32).json('GET', 'files'))
        self.assert_status(400, lambda: self.client.initiate('traversal_req', '../outside', 0, hashlib.sha256(b'').hexdigest()))
        row = self.client.initiate('pending_request', 'pending.bin', len(self.data), self.sha)
        self.assert_status(404, lambda: self.client.json('GET', 'files/' + row['file_id']))
        self.assert_status(409, lambda: self.client.commit(row['session_id']))
        conn = self.client._connection('PUT', 'uploads/' + row['session_id'], 1, 'application/octet-stream')
        conn.send(b'x')
        self.assertEqual(conn.getresponse().status, 400); conn.close()
        self.assertEqual(self.client.json('GET', 'files')['files'], [])
        with mock.patch('asc.storage.engine.os.fsync', side_effect=OSError(28, 'full')):
            self.assert_status(507, lambda: self.client.upload(row['session_id'], io.BytesIO(self.data), len(self.data)))
        self.assertEqual(self.client.json('GET', 'files')['files'], [])

    def test_cli_owner_upload_download_and_protected_setup_refusal(self):
        source = self.base / 'source.bin'; source.write_bytes(self.data)
        grant = self.base / 'owner-grant.json'
        grant.write_text(json.dumps({'grant': self.client.grant, 'volume_id': self.node['volume']}))
        common = ['--origin', self.client.origin, '--pin', self.client.pin, '--grant-file', str(grant)]
        output = io.StringIO()
        with mock.patch.object(cli, 'inspect', return_value={'protected': False, 'installation_allowed': True, 'simulation': True}), mock.patch('sys.argv', ['asc', 'storage-upload', str(source), 'cli/file.bin',
                                   '--key', 'cli_request_key'] + common), contextlib.redirect_stdout(output):
            cli.main()
        file = json.loads(output.getvalue())
        destination = self.base / 'download.bin'
        with mock.patch.object(cli, 'inspect', return_value={'protected': False, 'installation_allowed': True, 'simulation': True}), mock.patch('sys.argv', ['asc', 'storage-download', file['file_id'], str(destination)] + common), contextlib.redirect_stdout(io.StringIO()):
            cli.main()
        self.assertEqual(destination.read_bytes(), self.data)
        # Exclusive local output never overwrites an existing user's file.
        self.assert_status(404, lambda: self.client.json('GET', 'files/00000000-0000-0000-0000-000000000000'))
        with mock.patch.object(cli, 'HOME', self.node['private']), mock.patch.object(cli, 'inspect',
                return_value={'protected': True, 'installation_allowed': False}), mock.patch('sys.argv', ['asc', 'storage-init']), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                cli.main()
        self.assertEqual(caught.exception.code, 1)


if __name__ == '__main__':
    unittest.main()
