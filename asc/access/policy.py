"""Version1 private browser ingress contract, independent from cluster authority."""
from dataclasses import dataclass
import ipaddress
import re
from urllib.parse import urlsplit
from ..demo.dashboard.assets import ASSETS
from ..demo.state import lan_origin

MODES = ('single-writer-demo', 'core-quorum', 'recovery-read-only')
MAX_BODY = 32 * 1024**2
UUID = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'


def private_origin(value):
    if not isinstance(value, str):
        raise ValueError('explicit private numeric HTTPS origin required')
    url = urlsplit(value)
    try:
        host = str(ipaddress.IPv4Address(url.hostname))
        port = url.port
        networks = ('127.0.0.0/8', '10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16', '100.64.0.0/10')
        if (url.scheme != 'https' or url.username or url.password or type(port) is not int
                or not 1024 <= port <= 65535 or value != f'https://{host}:{port}'
                or not any(ipaddress.IPv4Address(host) in ipaddress.IPv4Network(n) for n in networks)):
            raise ValueError()
    except (ValueError, TypeError):
        raise ValueError('explicit private numeric HTTPS origin required') from None
    return host, port


@dataclass(frozen=True)
class Profile:
    frontend_origin: str
    upstream_origin: str
    upstream_pin: str
    upstream_mode: str
    max_body_bytes: int

    @classmethod
    def parse(cls, value):
        fields = {'format', 'mode', 'frontend_origin', 'upstream_origin', 'upstream_pin', 'upstream_mode', 'max_body_bytes'}
        if (type(value) is not dict or set(value) != fields or type(value['format']) is not int
                or value['format'] != 1 or value['mode'] != 'private-gateway'):
            raise ValueError('unsupported private access profile')
        private_origin(value['frontend_origin'])
        private_origin(value['upstream_origin'])
        lan_origin(value['upstream_origin'])  # Existing Dashboard supports RFC1918/loopback only.
        if (value['frontend_origin'] == value['upstream_origin']
                or type(value['upstream_pin']) is not str or not re.fullmatch('[0-9a-f]{64}', value['upstream_pin'])
                or value['upstream_mode'] not in MODES or type(value['max_body_bytes']) is not int
                or not 1 <= value['max_body_bytes'] <= MAX_BODY):
            raise ValueError('invalid private access binding')
        return cls(**{name: value[name] for name in fields - {'format', 'mode'}})

    def permits(self, method, path):
        if (type(path) is not str or not path.isascii() or any(c in path for c in ('%', '?', '#', '\\'))
                or '//' in path or any(p in ('.', '..') for p in path.split('/'))):
            return False
        if method == 'GET' and path in (*ASSETS, '/favicon.ico', '/api/mode', '/api/session', '/api/state'):
            return True
        if method == 'POST' and path in ('/api/login', '/api/logout'):
            return True
        if method == 'GET' and re.fullmatch(r'/api/files/' + UUID, path):
            return True
        if self.upstream_mode != 'single-writer-demo':
            return False
        return bool(method == 'POST' and path in ('/api/refresh', '/api/uploads')
                    or method == 'GET' and re.fullmatch(r'/api/files/' + UUID + r'/content', path)
                    or method in ('GET', 'PUT') and re.fullmatch(r'/api/uploads/' + UUID, path)
                    or method == 'GET' and re.fullmatch(r'/api/nodes/(?:local-controller|' + UUID + ')', path))

    def public(self):
        return {'format': 1, 'mode': 'private-gateway', 'url': self.frontend_origin,
                'upstream_mode': self.upstream_mode, 'writer_authority': False,
                'vpn_membership': 'UNKNOWN', 'remote_reachability': 'UNKNOWN',
                'production_accepted': False}
