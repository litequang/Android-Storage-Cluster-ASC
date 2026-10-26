"""Native owner-session client of the EXISTING read-only gateway.

No Node credentials, source bootstrap, Catalog, disk state, or writer operations.
Session credentials live only in this object's RAM; process death requires login.
"""
import copy
from http.cookies import SimpleCookie, CookieError
import json
import re
import threading
import time

from ..catalog.common import identifier, origin
from ..client import connect_pinned, ClientError
from .core import unavailable, downgrade


class ObserverRefused(Exception):
    """Only fixed local error labels may reach native UI."""


class NativeObserver:
    def __init__(self, endpoint, pin, cluster_id, epoch, mode, minimum_index=0):
        self.origin, self.pin = origin(endpoint, pin)
        identifier(cluster_id); identifier(epoch)
        if mode not in ('core-quorum', 'recovery-read-only'):
            raise ValueError('explicit observer mode required')
        if type(minimum_index) is not int or minimum_index < 0:
            raise ValueError('invalid checkpoint floor')
        self.cluster, self.epoch, self.mode = cluster_id, epoch, mode
        self.floor = minimum_index
        self.lock = threading.RLock()
        self.cookie = self.csrf = None

    def _request(self, action, code=None):
        # There is deliberately no caller-supplied HTTP method/path/body/token API.
        method, path = {'mode': ('GET', '/api/mode'), 'login': ('POST', '/api/login'),
                        'state': ('GET', '/api/state'), 'logout': ('POST', '/api/logout')}[action]
        connection = connect_pinned(self.origin, self.pin, timeout=90)
        try:
            headers = {'Origin': self.origin, 'Accept': 'application/json'}
            if action in ('state', 'logout'):
                if not self.cookie or not self.csrf:
                    raise ObserverRefused('observer_login_required')
                headers.update(Cookie=self.cookie, **{'X-ASC-CSRF': self.csrf})
            body = None
            if method == 'POST':
                body = json.dumps({'code': code} if action == 'login' else {}).encode('utf-8')
                headers['Content-Type'] = 'application/json'
            connection.request(method, path, body=body, headers=headers)
            response = connection.getresponse()
            raw = response.read(2 * 1024**2 + 1)
            if response.status in (401, 403):
                raise ObserverRefused('observer_login_required')
            if response.status != 200 or len(raw) > 2 * 1024**2:
                raise ObserverRefused('observer_unavailable')
            value = json.loads(raw.decode('utf-8'))
            if type(value) is not dict:
                raise ObserverRefused('observer_response_rejected')
            return value, response.getheaders()
        finally:
            connection.close()

    def _mode(self):
        mode, _ = self._request('mode')
        if mode != {'mode': self.mode, 'read_only': True}:
            raise ObserverRefused('observer_mode_mismatch')

    def login(self, code):
        if not isinstance(code, str) or not re.fullmatch(r'[A-Za-z0-9_-]{16,128}', code):
            raise ObserverRefused('observer_code_required')
        with self.lock:
            # An explicit new login revokes this local object's prior authority.
            self.cookie = self.csrf = None
            try:
                self._mode()  # Pin and explicit read-only mode BEFORE grant submission.
                value, headers = self._request('login', code)
                cookies = [v for k, v in headers if k.lower() == 'set-cookie']
                if value.get('authenticated') is not True or len(cookies) != 1:
                    raise ObserverRefused('observer_response_rejected')
                parsed = SimpleCookie(); parsed.load(cookies[0])
                if len(parsed) != 1:
                    raise ObserverRefused('observer_response_rejected')
                name, cookie = next(iter(parsed.items()))
                if (not re.fullmatch(r'__Host-ASC-Observer-[a-f0-9]{32}', name)
                        or not re.fullmatch(r'[A-Za-z0-9_-]{16,128}', cookie.value)
                        or not cookie['secure'] or not cookie['httponly']
                        or cookie['path'] != '/' or cookie['samesite'].lower() != 'strict'
                        or cookie['domain']
                        or not isinstance(value.get('csrf'), str)
                        or not re.fullmatch(r'[A-Za-z0-9_-]{16,128}', value['csrf'])):
                    raise ObserverRefused('observer_response_rejected')
                self.cookie, self.csrf = name + '=' + cookie.value, value['csrf']
                return self._state()
            except (ObserverRefused, ClientError, OSError, ValueError, TypeError, KeyError, CookieError):
                self.cookie = self.csrf = None
                raise ObserverRefused('observer_login_unconfirmed') from None

    def _state(self):
        value, _ = self._request('state')
        runtime = value.get('runtime', {})
        cluster = value.get('cluster', {})
        if type(runtime) is not dict or type(cluster) is not dict:
            raise ObserverRefused('observer_response_rejected')
        state = runtime.get('state')
        if (type(value.get('observer_version')) is not int or value['observer_version'] != 1
                or value.get('read_only') is not True or value.get('writer_authority') is not False
                or cluster.get('mode') != self.mode or cluster.get('cluster_id') != self.cluster
                or state not in ('ONLINE', 'OFFLINE', 'DEGRADED', 'UNKNOWN', 'QUORUM UNAVAILABLE', 'RECOVERY READ-ONLY')
                or runtime.get('epoch') != self.epoch and not (state == 'UNKNOWN' and runtime.get('epoch') is None)):
            raise ObserverRefused('observer_binding_mismatch')
        checkpoint = runtime.get('checkpoint')
        if checkpoint is not None:
            if (type(checkpoint) is not dict or type(checkpoint.get('index')) is not int
                    or checkpoint['index'] < self.floor):
                raise ObserverRefused('observer_checkpoint_rejected')
            self.floor = checkpoint['index']
        elif state != 'UNKNOWN':
            raise ObserverRefused('observer_checkpoint_rejected')
        for name in ('nodes', 'files', 'jobs'):
            if type(value.get(name)) is not list:
                raise ObserverRefused('observer_response_rejected')
        # Only the canonical gateway's public projection enters native IPC.
        allowed = set(unavailable())
        result = {k: copy.deepcopy(v) for k, v in value.items() if k in allowed}
        if self.mode == 'core-quorum':
            if state == 'RECOVERY READ-ONLY':
                raise ObserverRefused('observer_mode_mismatch')
            if runtime.get('strong_read_confirmed') is not True or runtime.get('quorum_available') is not True:
                result = downgrade(result, state if state in ('UNKNOWN', 'OFFLINE', 'QUORUM UNAVAILABLE') else 'UNKNOWN')
                if state == 'QUORUM UNAVAILABLE' and runtime.get('quorum_available') is False:
                    result['runtime']['quorum_available'] = False
        elif state != 'UNKNOWN':
            recovery = value.get('backup', {}).get('recovery', {})
            if (state != 'RECOVERY READ-ONLY' or recovery.get('state') != 'VERIFIED_RECOVERY_STAGING'
                    or recovery.get('writer_authority') is not False or recovery.get('credentials_restored') is not False):
                raise ObserverRefused('observer_recovery_unverified')
        result.update(read_only=True, writer_authority=False)
        result['native_observer'] = {'state': 'AUTHENTICATED', 'checked_at': int(time.time()),
                                     'session_persistence': 'RAM_ONLY'}
        return result

    def state(self):
        with self.lock:
            try:
                self._mode()
                return self._state()
            except ObserverRefused as exc:
                if str(exc) == 'observer_login_required':
                    self.cookie = self.csrf = None
                return self.unavailable(str(exc))
            except (ClientError, OSError, ValueError, TypeError, KeyError):
                return self.unavailable('observer_unavailable')

    def unavailable(self, reason='observer_login_required'):
        # Never display stale node health/protection as current on network failure.
        result = unavailable(cluster_id=self.cluster, epoch=self.epoch)
        result['cluster']['mode'] = self.mode
        result['native_observer'] = {'state': 'UNKNOWN', 'error': reason,
                                     'checked_at': int(time.time()), 'session_persistence': 'RAM_ONLY'}
        return result

    def close(self):
        with self.lock:
            try:
                if self.cookie:
                    self._request('logout')
            except (ObserverRefused, ClientError, OSError, ValueError, TypeError, KeyError):
                pass
            finally:
                self.cookie = self.csrf = None
