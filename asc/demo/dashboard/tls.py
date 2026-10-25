"""Explicit separate browser CA/IP-SAN identity; never replace Core or node TLS."""
import os
from pathlib import Path
import stat
import subprocess
import tempfile
from ...identity import ensure_private_home, fingerprint_from_pem, require_openssl, save_private
from ...storage.volumes import no_links
from ..installer import guard, private_path
from ..state import read_json

MAX_UPLOAD = 32 * 1024**2
FILES = ('ca.crt', 'ca.key', 'server.crt', 'server.key')


def openssl(*args):
    try:
        subprocess.run([require_openssl(), *map(str, args)], check=True, capture_output=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        raise ValueError('Dashboard TLS operation failed; preserve partial private files') from None


def load_config(root, marker):
    home = Path(root) / 'dashboard'
    no_links(home)
    cfg = read_json(home / 'dashboard.json')
    if (set(cfg) != {'format', 'host', 'port', 'max_upload_bytes'} or type(cfg['format']) is not int or cfg['format'] != 1
            or marker['role'] != 'controller' or cfg['host'] != marker['host']
            or type(cfg['port']) is not int or not 1024 <= cfg['port'] <= 65535 or cfg['port'] == marker['port']
            or type(cfg['max_upload_bytes']) is not int or not 1 <= cfg['max_upload_bytes'] <= MAX_UPLOAD):
        raise ValueError('unsupported browser TLS configuration')
    for name in FILES:
        path = home / name
        no_links(path)
        info = path.stat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > 65536:
            raise ValueError('unexpected browser identity file')
        if name.endswith('.key') and os.name == 'posix' and info.st_mode & 0o077:
            raise ValueError('browser private key permissions require owner review')
    openssl('verify', '-CAfile', home / 'ca.crt', '-purpose', 'sslserver', '-verify_ip', cfg['host'], home / 'server.crt')
    # Loading the chain also detects a mismatched private leaf key before listener startup.
    import ssl
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(home / 'server.crt', home / 'server.key')
    storage = Path(root) / 'node/storage.json'
    if storage.exists() and read_json(storage)['port'] == cfg['port']:
        raise ValueError('Dashboard/storage port conflict')
    return cfg


def setup(root, port=8444, max_upload=MAX_UPLOAD):
    guard()
    from ..upgrade import stopped
    from ..state import inspect_state
    root = private_path(root)
    with stopped(root):
        marker = inspect_state(root)
        if (marker['role'] != 'controller' or type(port) is not int or not 1024 <= port <= 65535
                or port == marker['port'] or type(max_upload) is not int or not 1 <= max_upload <= MAX_UPLOAD):
            raise ValueError('invalid explicit Dashboard setup')
        storage = root / 'node/storage.json'
        if storage.exists() and read_json(storage)['port'] == port:
            raise ValueError('Dashboard/storage port conflict')
        home = root / 'dashboard'
        if home.exists():
            cfg = load_config(root, marker)
            if (cfg['port'], cfg['max_upload_bytes']) != (port, max_upload):
                raise ValueError('existing browser identity/configuration retained')
            return public_info(root, cfg)
        ensure_private_home(home)
        ca_key, ca_cert = home / 'ca.key', home / 'ca.crt'
        key, cert = home / 'server.key', home / 'server.crt'
        # New private directory only; interrupted/partial state is never overwritten on retry.
        with tempfile.TemporaryDirectory(prefix='.csr-', dir=home) as directory:
            directory = Path(directory)
            extensions = directory / 'leaf.ext'
            extensions.write_text('basicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth\nsubjectAltName=IP:' + marker['host'] + '\n')
            openssl('req', '-x509', '-newkey', 'rsa:2048', '-sha256', '-nodes', '-days', '730',
                    '-subj', '/CN=ASC Demo Browser CA', '-keyout', ca_key, '-out', ca_cert,
                    '-addext', 'basicConstraints=critical,CA:TRUE,pathlen:0',
                    '-addext', 'keyUsage=critical,keyCertSign,cRLSign')
            openssl('req', '-new', '-newkey', 'rsa:2048', '-sha256', '-nodes', '-subj', '/CN=ASC Demo Dashboard',
                    '-keyout', key, '-out', directory / 'leaf.csr')
            openssl('x509', '-req', '-in', directory / 'leaf.csr', '-CA', ca_cert, '-CAkey', ca_key,
                    '-set_serial', '0x' + os.urandom(16).hex(), '-days', '365', '-sha256',
                    '-extfile', extensions, '-out', cert)
        for name in FILES:
            os.chmod(home / name, 0o600)
        (home / 'spool').mkdir(mode=0o700)
        cfg = {'format': 1, 'host': marker['host'], 'port': port, 'max_upload_bytes': max_upload}
        save_private(home / 'dashboard.json', cfg)
        load_config(root, marker)
        return public_info(root, cfg)


def public_info(root, cfg):
    return {'url': f"https://{cfg['host']}:{cfg['port']}", 'max_upload_bytes': cfg['max_upload_bytes'],
            'ca_sha256': fingerprint_from_pem(Path(root) / 'dashboard/ca.crt'),
            'trust_required': 'Verify CA SHA-256 out of band and explicitly trust ONLY the public CA on the browser device.'}


def export_ca(root, output):
    from ..state import inspect_state
    guard()
    marker = inspect_state(root)
    cfg = load_config(root, marker)
    output = private_path(output)
    no_links(output)
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write((Path(root) / 'dashboard/ca.crt').read_bytes())
        stream.flush()
        os.fsync(stream.fileno())
    return dict(public_info(root, cfg), exported_public_ca=True)
