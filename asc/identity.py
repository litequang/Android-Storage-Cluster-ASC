"""Local private configuration, X.509 self-signed LAN certificate, fingerprint pinning."""
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import ssl
import subprocess
import tempfile

HOME = Path(os.environ.get('ASC_HOME', str(Path.home() / '.asc')))


class DependencyError(ValueError):
    """An external development/runtime dependency is unavailable; never skip TLS."""


def require_openssl():
    executable = shutil.which('openssl')
    if executable is None:
        raise DependencyError(
            'OpenSSL CLI not found on PATH. Certificate generation and TLS tests require it. '
            'On Windows, install OpenSSL and add the bin directory containing openssl.exe '
            'to PATH in this terminal; verify with Get-Command openssl and openssl version. '
            'Python ssl does not install the OpenSSL executable. See README-VI section 8.')
    return executable


def ensure_private_home(home=HOME):
    home = Path(home).resolve()
    source = Path(__file__).resolve().parent.parent
    shared = (Path('/storage'), Path('/sdcard'), Path('/mnt/media_rw'))
    if home == source or source in home.parents or any(home == root or root in home.parents for root in shared):
        raise ValueError('ASC_HOME must be private HOME outside source and shared storage')
    home.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(home, 0o700)
    return home


def replace_private(path, obj):
    """Atomic update for snapshots/status or EXPLICIT re-pair, never implicit identity replacement."""
    path = Path(path)
    fd, staging = tempfile.mkstemp(prefix='.asc-tmp-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as fh:
            json.dump(obj, fh, ensure_ascii=False, indent=2)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(staging, path)
    finally:
        if os.path.exists(staging):
            os.unlink(staging)


def save_private(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    data = json.dumps(obj, ensure_ascii=False, indent=2).encode('utf-8')
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, 'wb', closefd=False) as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fd)
    finally:
        os.close(fd)


def read_private(name):
    with open(HOME / name, 'r', encoding='utf-8') as f:
        obj = json.load(f)
    if not isinstance(obj, dict):
        raise ValueError('invalid private configuration')
    version = obj.get('config_version', 1)
    if type(version) is not int or version != 1:
        raise ValueError('unsupported private configuration version; use matching release')
    return obj


def make_cert(cert, key):
    executable = require_openssl()
    try:
        subprocess.run([executable, 'req', '-x509', '-newkey', 'rsa:2048', '-sha256',
                        '-nodes', '-days', '365', '-keyout', str(key), '-out', str(cert),
                        '-subj', '/CN=ASC-LAN-Controller'], check=True, capture_output=True, text=True)
    except FileNotFoundError:
        # Also handle removal after PATH lookup / a missing Windows loader dependency.
        raise DependencyError('OpenSSL was found but could not start. Check its installation/DLLs '
                              'and PATH, then rerun TLS tests; no insecure fallback is allowed.') from None
    except subprocess.CalledProcessError:
        raise DependencyError('OpenSSL certificate generation failed. Check dependency and private '
                              'directory permissions; preserve any partial TLS files for review.') from None
    os.chmod(key, 0o600)
    os.chmod(cert, 0o600)


def fingerprint_from_pem(pem_path):
    pem = Path(pem_path).read_text(encoding='utf-8')
    der = ssl.PEM_cert_to_DER_cert(pem)
    return hashlib.sha256(der).hexdigest().upper()


def new_admin_token():
    return secrets.token_urlsafe(40)
