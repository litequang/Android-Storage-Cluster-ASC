"""In-process TLS loader with no plaintext key file or external executable.

Linux/Android sealed anonymous memfd is required. Android uses explicit native
JSSE loading from the opened descriptor; Linux uses CPython SSL. Neither switches
providers after denial or falls back to a plaintext disk key/insecure TLS.
The software TLS key is decrypted only in the owning process; it is NOT claimed
to be a nonexportable AndroidKeyStore signing key.
"""
from contextlib import contextmanager
import hashlib
import os
import ssl
import sys

from .context import ContextLocked


def _anonymous_fd():
    if hasattr(os, 'memfd_create'):
        # A denied syscall never switches providers or falls back to disk.
        return os.memfd_create('asc-native-tls', os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING)
    if sys.platform != 'android' and not hasattr(sys, 'getandroidapilevel'):
        raise ContextLocked()
    # Chaquopy is built against an older Bionic API and omits the Python wrapper.
    # Use ONLY Android's documented public libc symbol (API30+), same app UID and
    # same ordinary kernel/SELinux policy. No raw syscall, permission bypass or
    # unsupported-OS/disk fallback. Missing symbol or errno => fail closed.
    import ctypes
    function = ctypes.CDLL('libc.so', use_errno=True).memfd_create
    function.argtypes = [ctypes.c_char_p, ctypes.c_uint]
    function.restype = ctypes.c_int
    # Official Android UAPI linux/memfd.h: CLOEXEC=1, ALLOW_SEALING=2.
    fd = function(b'asc-native-tls', 0x0001 | 0x0002)
    if fd < 0:
        raise OSError(ctypes.get_errno(), 'anonymous_tls_unavailable')
    return fd


@contextmanager
def _sealed_bytes(raw):
    import fcntl
    required = ('F_ADD_SEALS', 'F_GET_SEALS', 'F_GETFD', 'FD_CLOEXEC',
                'F_SEAL_SEAL', 'F_SEAL_SHRINK', 'F_SEAL_GROW', 'F_SEAL_WRITE')
    if not all(hasattr(fcntl, key) for key in required):
        raise ContextLocked()
    fd = _anonymous_fd()
    try:
        view = memoryview(raw)
        while view:
            count = os.write(fd, view)
            if count <= 0:
                raise ContextLocked()
            view = view[count:]
        seals = fcntl.F_SEAL_SEAL | fcntl.F_SEAL_SHRINK | fcntl.F_SEAL_GROW | fcntl.F_SEAL_WRITE
        fcntl.fcntl(fd, fcntl.F_ADD_SEALS, seals)
        if (fcntl.fcntl(fd, fcntl.F_GET_SEALS) & seals != seals or
                not fcntl.fcntl(fd, fcntl.F_GETFD) & fcntl.FD_CLOEXEC or
                os.fstat(fd).st_nlink != 0 or os.pread(fd, len(raw) + 1, 0) != raw):
            raise ContextLocked()
        yield fd
    finally:
        os.close(fd)


def server_context(identity, tls_provider=None):
    """Validate the exact cert/key/pin before producing a fresh TLS server context."""
    try:
        if (not isinstance(identity, dict) or set(identity) != {'format', 'certificate', 'private_key', 'pin'} or
                type(identity['format']) is not int or identity['format'] != 1 or
                any(not isinstance(identity[k], str) for k in ('certificate', 'private_key', 'pin')) or
                not 1 <= len(identity['certificate']) <= 8192 or not 1 <= len(identity['private_key']) <= 8192 or
                not identity['private_key'].startswith('-----BEGIN PRIVATE KEY-----\n') or
                identity['private_key'].count('-----BEGIN ') != 1 or
                identity['certificate'].count('-----BEGIN CERTIFICATE-----') != 1 or
                hashlib.sha256(ssl.PEM_cert_to_DER_cert(identity['certificate'])).hexdigest() != identity['pin']):
            raise ContextLocked()
        android = sys.platform == 'android' or hasattr(sys, 'getandroidapilevel')
        if android and tls_provider is None:
            raise ContextLocked()  # No automatic proc-path/provider fallback on Android.
        with _sealed_bytes(identity['certificate'].encode('ascii')) as cert, \
                _sealed_bytes(identity['private_key'].encode('ascii')) as key:
            if tls_provider is not None:
                # The public Android TLS provider consumes only readback from
                # already sealed descriptors. No proc reopen or named key file.
                context = tls_provider.load(os.pread(cert, 8193, 0).decode('ascii'),
                                            os.pread(key, 8193, 0).decode('ascii'))
                if context is None:
                    raise ContextLocked()
            else:
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                context.minimum_version = ssl.TLSVersion.TLSv1_2
                context.load_cert_chain('/proc/self/fd/' + str(cert), '/proc/self/fd/' + str(key))
        return context
    except Exception:
        raise ContextLocked() from None
