"""Opt-in local storage runtime, retaining the Phase 1.1 node identity."""
import json
import ipaddress
from pathlib import Path
import ssl
import threading
from .engine import StorageEngine
from .http import StorageServer
from ..identity import make_cert, save_private, fingerprint_from_pem


def validate_host(host):
    ip = ipaddress.ip_address(host)
    if not (ip.is_private or ip.is_loopback) or ip.is_unspecified or ip.is_multicast:
        raise ValueError('bind an explicit loopback/private LAN address')
    return host


def load_config(home):
    cfg = json.loads((Path(home) / 'storage.json').read_text(encoding='utf-8'))
    if (not isinstance(cfg, dict) or type(cfg.get('config_version')) is not int or cfg.get('config_version') != 1 or not isinstance(cfg.get('host'), str) or
            type(cfg.get('port')) is not int or not 1024 <= cfg['port'] <= 65535):
        raise ValueError('unsupported storage configuration')
    validate_host(cfg['host'])
    return cfg


def setup(home, node, root, kind='directory', quota=64 * 1024**2, reserve=64 * 1024**2,
          port=9443, host='127.0.0.1', max_upload=64 * 1024**2, rate=8 * 1024**2):
    home = Path(home)
    validate_host(host)
    if (home / 'storage.json').exists():
        raise ValueError('storage already configured; inspect existing state instead of replacing it')
    if not 1024 <= port <= 65535 or not host:
        raise ValueError('invalid storage bind')
    cert, key = home / 'storage.crt', home / 'storage.key'
    if cert.exists() or key.exists():
        raise ValueError('existing storage TLS files; preserve and recover explicitly')
    with StorageEngine(home / 'storage', node['node_id'], max_upload, rate) as engine:
        volume = engine.volumes.register(root, kind, quota, reserve)
        make_cert(cert, key)
        save_private(home / 'storage.json', {'config_version': 1, 'host': host, 'port': port,
                     'node_id': node['node_id'], 'max_upload': max_upload, 'rate': rate})
        return {'volume_id': volume['volume_id'], 'pin': fingerprint_from_pem(cert),
                'capabilities': engine.capabilities()}


class StorageRuntime:
    def __init__(self, home, node):
        self.home, self.node = Path(home), node

    def __enter__(self):
        cfg = load_config(self.home)
        if cfg['node_id'] != self.node['node_id']:
            raise ValueError('storage node identity mismatch')
        self.engine = StorageEngine(self.home / 'storage', self.node['node_id'], cfg['max_upload'], cfg['rate'])
        try:
            self.server = StorageServer((cfg['host'], cfg['port']), self.engine, self.node)
            self.server.daemon_threads = False
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.minimum_version = ssl.TLSVersion.TLSv1_2
            context.load_cert_chain(str(self.home / 'storage.crt'), str(self.home / 'storage.key'))
            self.server.tls_context = context
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            return self
        except BaseException:
            if hasattr(self, 'server'):
                self.server.server_close()
            self.engine.close()
            raise

    def __exit__(self, *_):
        self.server.shutdown(); self.server.server_close(); self.thread.join()
        self.engine.close()
