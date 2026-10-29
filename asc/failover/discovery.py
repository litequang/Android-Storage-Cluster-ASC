"""Pinned bootstrap allowlist, bounded discovery/retry and expiring routing cache."""
import threading
import time

from ..catalog.common import origin
from ..client import ClientError, request_json


class Discovery:
    def __init__(self, cluster_id, endpoints, token=None, ttl=2, attempts=3):
        if (not isinstance(endpoints, list) or not 1 <= len(endpoints) <= 3 or
                type(ttl) is not int or not 1 <= ttl <= 30 or
                type(attempts) is not int or not 1 <= attempts <= 5):
            raise ValueError('invalid bounded bootstrap configuration')
        self.cluster_id, self.ttl, self.attempts = cluster_id, ttl, attempts
        self.endpoints = []
        for endpoint in endpoints:
            if set(endpoint) - {'node_id', 'origin', 'pin', 'token'} or not {'node_id', 'origin', 'pin'} <= set(endpoint):
                raise ValueError('invalid pinned endpoint')
            if token is not None and 'token' in endpoint:
                raise ValueError('do not mix node credential with per-endpoint owner credentials')
            address, pin = origin(endpoint['origin'], endpoint['pin'])
            self.endpoints.append({**endpoint, 'origin': address, 'pin': pin, 'token': endpoint.get('token', token)})
        if (len({e['node_id'] for e in self.endpoints}) != len(endpoints) or
                len({e['origin'] for e in self.endpoints}) != len(endpoints)):
            raise ValueError('duplicate pinned endpoint')
        self.cached, self.expires = None, 0
        self.lock = threading.RLock()

    def _call(self, endpoint, method, path, obj=None):
        # Catalog requests include measured placement and multi-pass physical
        # verification. Preserve the existing bounded owner operation budget.
        timeout = 300 if method == 'POST' and path.startswith('/catalog/v1/') else 20
        return request_json(endpoint['origin'], endpoint['pin'], method, path, obj, endpoint['token'], timeout=timeout)

    def leader(self):
        with self.lock:
            if self.cached is not None and time.monotonic() < self.expires:
                return self.cached
            # A reply may only identify itself, never add endpoints/pins. Hints
            # don't bypass the configured allowlist or prove write authority.
            for endpoint in self.endpoints:
                try:
                    reply = self._call(endpoint, 'GET', '/cluster/v1/leader')
                    if (reply.get('cluster_id') == self.cluster_id and reply.get('node_id') == endpoint['node_id'] and
                            reply.get('write_ready') is True):
                        self.cached, self.expires = endpoint, time.monotonic()+self.ttl
                        return endpoint
                except ClientError as exc:
                    if exc.status in (401, 403):
                        # A revoked/rotated Agent still needs to route its
                        # heartbeat to the current quorum-gated API to receive
                        # the authoritative repair-required rejection. This
                        # pinned self hint never grants permission/readiness.
                        try:
                            hint = self._call(endpoint, 'GET', '/api/v1/info')
                            if (hint.get('cluster_id') == self.cluster_id and hint.get('node_id') == endpoint['node_id'] and
                                    hint.get('routing_hint_only') is True and hint.get('leader_hint') is True):
                                return endpoint  # No cache: only the actual API can authorize.
                        except (ClientError, OSError, ValueError):
                            pass
                    continue
                except (OSError, ValueError):
                    continue
            raise ClientError('no write-ready pinned Controller', 503, 'controller_not_ready')

    def request(self, method, path, obj=None):
        last = None
        for attempt in range(self.attempts):
            try:
                endpoint = self.leader()
                return self._call(endpoint, method, path, obj)
            except (OSError, ClientError) as exc:
                if isinstance(exc, ClientError) and exc.status is not None and exc.status not in (409, 429, 502, 503, 504):
                    raise
                # A semantic 409 is not a routing failure. Preserve it verbatim.
                if isinstance(exc, ClientError) and exc.status == 409 and exc.code not in ('stale_authority', 'controller_not_ready'):
                    raise
                last = exc
                with self.lock:
                    self.cached, self.expires = None, 0
                if attempt+1 < self.attempts:
                    time.sleep(min(2, 0.25 * 2**attempt))
        raise last

    def local(self, path):
        for endpoint in self.endpoints:
            try:
                reply = self._call(endpoint, 'GET', path)
                if reply.get('cluster_id') == self.cluster_id and reply.get('stale') is True:
                    return reply
            except (ClientError, OSError, ValueError):
                continue
        raise ClientError('no verified local catalog', 503)
