"""Bounded authenticated loopback IPC. No secret flags, redirects or remote HTTP."""
import http.client
import ipaddress
import json
from pathlib import Path

from ..catalog.common import CatalogError, canonical

MAX_FRAME = 16 * 1024**2


class Client:
    def __init__(self, address, token):
        host, port = address.rsplit(':', 1)
        host = host.strip('[]')
        if (not ipaddress.ip_address(host).is_loopback or not port.isdigit() or
                not 1024 <= int(port) <= 65535 or not isinstance(token, str) or not 43 <= len(token) <= 128):
            raise ValueError('invalid loopback IPC configuration')
        self.host, self.port, self._token = host, int(port), token

    @classmethod
    def from_config(cls, path):
        with Path(path).open('rb') as stream:
            raw = stream.read(65537)
        if len(raw) > 65536:
            raise ValueError('consensus configuration limit')
        cfg = json.loads(raw)
        if cfg.get('schema') != 1:
            raise ValueError('unsupported consensus configuration')
        return cls(cfg['ipc_address'], cfg['ipc_token'])

    def request(self, method, path, value=None):
        data = canonical(value) if value is not None else None
        if data is not None and len(data) > MAX_FRAME:
            raise CatalogError('consensus_frame_limit', 413)
        connection = http.client.HTTPConnection(self.host, self.port, timeout=18)
        try:
            connection.request(method, path, body=data, headers={
                'Authorization': 'Bearer ' + self._token, 'Content-Type': 'application/json'})
            response = connection.getresponse()
            raw = response.read(MAX_FRAME + 1)
            if len(raw) > MAX_FRAME:
                raise CatalogError('consensus_frame_limit', 503)
            result = json.loads(raw)
            if response.status != 200:
                # Never reflect untrusted remote errors/payloads into API logs.
                known = {'ipc_unauthorized', 'ipc_busy', 'quorum_read_unavailable', 'commit_unconfirmed',
                         'precondition_conflict', 'request_id_conflict', 'receipt_limit', 'unsupported_operation', 'voter_quarantined'}
                error = result.get('error')
                raise CatalogError(error if error in known else 'consensus_unavailable', response.status)
            return result
        except (OSError, http.client.HTTPException, ValueError, TypeError):
            raise CatalogError('consensus_unavailable', 503) from None
        finally:
            connection.close()

    def state(self, strong=False):
        return self.request('GET', '/v1/state?consistency=' + ('strong' if strong else 'local'))

    def status(self):
        return self.request('GET', '/v1/status')

    def submit(self, command):
        return self.request('POST', '/v1/commands', command)['receipt']
