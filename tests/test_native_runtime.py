"""Real Linux TLS/Controller/Node bytes. Platform fixture != Android proof."""
import hashlib
import io
import json
import os
import socket
import time
import unittest
from unittest.mock import patch
from asc.client import ClientError
from asc.node.context import NodeContext
from asc.node.runtime import NativeRuntime
from asc.node.storage import NativeStorage
from asc.storage.client import StorageClient
from asc.storage.errors import StorageError
import test_native_enrollment as enrollment_fixture
from test_native_context import synthetic_build


class Connection:
    def __init__(self, sock): self.sock = sock
    def read(self, size): return self.sock.recv(size)
    def write(self, data): self.sock.sendall(data)
    def setTimeoutMillis(self, value): self.sock.settimeout(value / 1000)
    def timeoutMillis(self): return int(self.sock.gettimeout() * 1000)
    def peerAddress(self): return self.sock.getpeername()[0]
    def peerPort(self): return self.sock.getpeername()[1]
    def close(self):
        try: self.sock.shutdown(socket.SHUT_RDWR)
        except OSError: pass
        self.sock.close()


class Listener:
    def __init__(self, tls, host, port):
        self.tls = tls; self.connections = []; self.sock = socket.socket()
        self.sock.bind((host, port)); self.sock.listen(32); self.sock.settimeout(.25)
    def accept(self):
        try: sock, _ = self.sock.accept()
        except socket.timeout: return None
        sock.settimeout(12)
        connection = Connection(self.tls.wrap_socket(sock, server_side=True, do_handshake_on_connect=False))
        self.connections.append(connection); return connection
    def port(self): return self.sock.getsockname()[1]
    def close(self):
        self.sock.close()
        for connection in self.connections: connection.close()


class Factory:
    def open(self, tls, host, port): return Listener(tls, host, port)


@unittest.skipUnless(os.name == 'posix', 'native private provider is POSIX-only')
class NativeRuntimeTests(unittest.TestCase):
    setUp = enrollment_fixture.NativeEnrollmentTests.setUp
    join = enrollment_fixture.NativeEnrollmentTests.join

    def setup_storage(self):
        self.join(); self.local = NativeStorage(self.context)
        self.local.configure(2 * 1024**2, 0)
        self.volume = self.context.load()['storage']['volume_id']

    def start_node(self):
        runtime = NativeRuntime(self.context, Factory(), self.profile)
        runtime.start('127.0.0.1', 0); self.addCleanup(runtime.close)
        return runtime

    def client_for(self, runtime, grant=None):
        if grant is None:
            grant = self.reg.storage_grant(self.context.load()['node']['node_id'], self.volume,
                                           ['read', 'write', 'list', 'verify'])['grant']
        return StorageClient('https://127.0.0.1:' + str(runtime.status()['port']), self.pin, grant, self.volume)

    def test_actual_tls_transfer_hash_heartbeat_and_restart_keep_node_volume_and_bytes(self):
        self.setup_storage(); record = self.store.raw; node = self.context.load()['node']
        runtime = self.start_node(); client = self.client_for(runtime)
        body = bytes(range(256)) * 1024; sha = hashlib.sha256(body).hexdigest()
        session = client.initiate('native_mvp_actual', 'native/actual.bin', len(body), sha)
        client.upload(session['session_id'], io.BytesIO(body), len(body)); saved = client.commit(session['session_id'])
        self.assertEqual(client.json('POST', 'files/' + saved['file_id'] + '/verify', {})['state'], 'COMMITTED')
        deadline = time.monotonic() + 5
        while runtime.status()['controller'] != 'ONLINE' and time.monotonic() < deadline: time.sleep(.02)
        self.assertEqual(runtime.status()['controller'], 'ONLINE')
        self.assertTrue(runtime.status()['storage']['volumes'][0]['fsync_tested'])
        self.assertEqual(runtime.server.socket.getsockname()[1], 0)  # No second/plain Python listener.
        runtime.close()
        self.context = NodeContext(self.parent, self.store, self.app, synthetic_build())
        restarted = self.start_node(); output = io.BytesIO()
        self.client_for(restarted).download(saved['file_id'], output, len(body), sha)
        self.assertEqual(output.getvalue(), body); self.assertEqual(record, self.store.raw)
        self.assertEqual(self.context.load()['node'], node)
        self.assertIsNone(restarted.status()['storage_approved'])
        with self.reg.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM catalog_nodes').fetchone()[0], 0)

    def test_missing_existing_metadata_or_marker_never_recreates_identity(self):
        self.setup_storage(); before = self.store.raw
        for path in (self.local.root / 'engine/manifest.sqlite3', self.local.root / 'data/.asc-volume.json'):
            held = path.with_name(path.name + '.held'); path.rename(held)
            try:
                with self.assertRaises((OSError, ValueError, StorageError)):
                    with self.local.open(): self.fail('missing state accepted')
                self.assertFalse(path.exists()); self.assertEqual(before, self.store.raw)
            finally: held.rename(path)
        self.assertEqual(self.context.public_status()['storage'], 'LOCAL_CONFIG_READY')

    def test_interrupted_initial_setup_stays_held_without_second_initialization(self):
        self.join(); local = NativeStorage(self.context)
        with patch('asc.storage.volumes.VolumeManager.register', side_effect=OSError('synthetic interruption')):
            with self.assertRaises(OSError): local.configure(1024**2, 0)
        before = self.store.raw
        self.assertEqual(self.context.public_status()['storage'], 'SETUP_HELD')
        with self.assertRaisesRegex(ValueError, 'storage_setup_held'): local.configure(1024**2, 0)
        self.assertEqual(before, self.store.raw)

    def test_controller_loss_denies_new_storage_writes(self):
        self.setup_storage(); runtime = self.start_node(); client = self.client_for(runtime)
        self.server.shutdown(); self.server.server_close()
        with self.assertRaises(ClientError) as error:
            client.initiate('offline_native_mvp', 'offline.bin', 1, hashlib.sha256(b'x').hexdigest())
        self.assertEqual(error.exception.status, 503)
        self.assertFalse(runtime.status()['writer_authority'])
