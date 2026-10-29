"""Bounded socket/file facade over an owned native JSSE connection.

Trusted in-process callback, not IPC, TLS verification, HTTP authorization or an
Engine. Native listener must enforce TLS1.2+, private bind, ownership and an
absolute write/read deadline; setSoTimeout alone does not bound Java writes.
"""
import io
import math

CHUNK = 65536


class _Input(io.RawIOBase):
    def __init__(self, sock):
        super().__init__()
        self.sock = sock

    def readable(self):
        return True

    def readinto(self, buffer):
        self._checkClosed()
        if not buffer:
            return 0
        try:
            data = bytes(self.sock.connection.read(min(len(buffer), CHUNK)))
            if len(data) > min(len(buffer), CHUNK):
                raise OSError('native_socket_read_limit')
            buffer[:len(data)] = data
            return len(data)
        except Exception:
            raise OSError('native_socket_read_failed') from None


class NativeSocket:
    """Only operations used by Core's stream HTTP handler, no raw fd adoption.

    A file wrapper does not own the connection; request/server owner closes the
    actual native socket. No /proc, plaintext tunnel, hidden Android FD API or
    filesystem/process access. Unsupported socket operations fail explicitly.
    """
    def __init__(self, connection):
        self.connection = connection
        self.closed = False

    def makefile(self, mode='rb', buffering=-1):
        if self.closed or mode != 'rb' or type(buffering) is not int or not -1 <= buffering <= CHUNK:
            raise ValueError('unsupported_native_socket_file')
        raw = _Input(self)
        return raw if buffering == 0 else io.BufferedReader(raw, CHUNK if buffering == -1 else buffering)

    def sendall(self, data):
        if self.closed:
            raise OSError('native_socket_closed')
        try:
            view = memoryview(data).cast('B')
            for start in range(0, len(view), CHUNK):
                self.connection.write(bytes(view[start:start + CHUNK]))
        except Exception:
            raise OSError('native_socket_write_failed') from None

    def settimeout(self, seconds):
        if (type(seconds) not in (int, float) or not math.isfinite(seconds) or
                not 0 < seconds <= 900):
            raise ValueError('bounded_native_timeout_required')
        try:
            self.connection.setTimeoutMillis(math.ceil(seconds * 1000))
        except Exception:
            raise OSError('native_socket_timeout_failed') from None

    def getpeername(self):
        try:
            return str(self.connection.peerAddress()), int(self.connection.peerPort())
        except Exception:
            raise OSError('native_socket_peer_failed') from None

    def gettimeout(self):
        try:
            return int(self.connection.timeoutMillis()) / 1000
        except Exception:
            raise OSError('native_socket_timeout_failed') from None

    def shutdown(self, _how):
        # Core calls SHUT_WR only after the full handler finishes. Closing the
        # owned TLS connection also unblocks a peer/worker without an unbounded
        # close_notify/shutdownOutput wait. No unrelated socket/PID is affected.
        self.close()

    def close(self):
        if not self.closed:
            self.closed = True
            try:
                self.connection.close()
            except Exception:
                raise OSError('native_socket_close_failed') from None
