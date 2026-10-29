"""Linux facade contract only; fake stream is NOT JSSE/Android TLS evidence."""
import unittest
from asc.node.socket import NativeSocket, CHUNK


class MemoryConnection:
    def __init__(self, incoming=b''):
        self.incoming = incoming; self.written = bytearray(); self.closed = 0; self.writes = []
    def read(self, limit):
        data, self.incoming = self.incoming[:limit], self.incoming[limit:]
        return data
    def write(self, data): self.writes.append(len(data)); self.written.extend(data)
    def setTimeoutMillis(self, millis): self.timeout = millis
    def peerAddress(self): return '127.0.0.1'
    def peerPort(self): return 8443
    def close(self): self.closed += 1


class NativeSocketTests(unittest.TestCase):
    def test_binary_readline_read1_and_partial_readinto_preserve_all_bytes(self):
        data = bytes(range(256)) * 400
        bridge = MemoryConnection(b'header\n' + data); sock = NativeSocket(bridge)
        with sock.makefile('rb') as stream:
            self.assertEqual(stream.readline(), b'header\n')
            first = stream.read1(400)
            rest = bytearray(len(data) - len(first)); self.assertEqual(stream.readinto(rest), len(rest))
            self.assertEqual(first + rest, data); self.assertEqual(stream.read(1), b'')
        self.assertEqual(bridge.closed, 0)  # File wrapper does not steal socket ownership.
        sock.sendall(b'reply'); self.assertEqual(bridge.written, b'reply')
        sock.close(); sock.close(); self.assertEqual(bridge.closed, 1)

    def test_sendall_chunks_without_text_conversion_and_exact_peer(self):
        bridge = MemoryConnection(); sock = NativeSocket(bridge); body = bytes(range(256)) * 777
        sock.sendall(memoryview(body)); self.assertEqual(bridge.written, body)
        self.assertTrue(all(0 < n <= CHUNK for n in bridge.writes))
        self.assertEqual(sock.getpeername(), ('127.0.0.1', 8443))
        sock.settimeout(0.25); self.assertEqual(bridge.timeout, 250)
        sock.shutdown(1); self.assertEqual(bridge.closed, 1)
        with self.assertRaises(OSError): sock.sendall(b'closed')

    def test_unbounded_timeout_paths_and_non_readonly_file_modes_refuse(self):
        sock = NativeSocket(MemoryConnection())
        for timeout in (None, 0, -1, float('inf'), float('nan'), 901, True, '12'):
            with self.assertRaises(ValueError): sock.settimeout(timeout)
        for mode in ('w', 'wb', 'r', '/private/key', 'r+b'):
            with self.assertRaises(ValueError): sock.makefile(mode)
        for size in (-2, CHUNK + 1, None, True):
            with self.assertRaises(ValueError): sock.makefile(buffering=size)

    def test_native_failure_and_oversized_callback_do_not_reflect_secret_or_write_buffer(self):
        class Bad(MemoryConnection):
            def read(self, limit): raise RuntimeError('private synthetic credential detail')
            def write(self, data): raise RuntimeError('private synthetic credential detail')
        sock = NativeSocket(Bad())
        for action in (lambda: sock.makefile().read(1), lambda: sock.sendall(b'data')):
            with self.assertRaises(OSError) as result: action()
            self.assertNotIn('credential', str(result.exception))
        class TooLarge(MemoryConnection):
            def read(self, limit): return b'x' * (limit + 1)
        buffer = bytearray(b'untouched'); stream = NativeSocket(TooLarge()).makefile(buffering=0)
        with self.assertRaises(OSError): stream.readinto(buffer)
        self.assertEqual(buffer, b'untouched')
