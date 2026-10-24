"""Bounded process-local owner grants/sessions; never persist browser credentials."""
import hashlib
import hmac
import secrets
import threading
import time

COOKIE = '__Host-ASC-Demo'
SESSION_TTL = 1800
GRANT_TTL = 300


def hashed(value):
    return hashlib.sha256(value.encode('ascii')).hexdigest()


class Sessions:
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.lock = threading.Lock()
        self.grant = None
        self.sessions = {}

    def _prune(self):
        self.sessions = {k: v for k, v in self.sessions.items() if v['expires'] > self.clock()}
        if self.grant and self.grant[1] <= self.clock():
            self.grant = None

    def issue(self):
        with self.lock:
            self._prune()
            code = secrets.token_urlsafe(24)
            self.grant = (hashed(code), self.clock() + GRANT_TTL)
            return code

    def login(self, code):
        if not isinstance(code, str) or not 16 <= len(code) <= 128 or not code.isascii():
            return None
        with self.lock:
            self._prune()
            if not self.grant or not hmac.compare_digest(hashed(code), self.grant[0]):
                return None
            if len(self.sessions) >= 8:
                return None
            self.grant = None  # Exact one-use, serialized redemption; no session fixation.
            cookie = secrets.token_urlsafe(32)
            session = {'csrf': secrets.token_urlsafe(32), 'expires': self.clock() + SESSION_TTL}
            self.sessions[hashed(cookie)] = session
            return cookie, dict(session)

    def authenticate(self, cookie, csrf=None):
        if not isinstance(cookie, str) or not 16 <= len(cookie) <= 128 or not cookie.isascii():
            return None
        with self.lock:
            self._prune()
            identity = hashed(cookie)
            session = self.sessions.get(identity)
            if session is None or csrf is not None and not hmac.compare_digest(str(csrf), session['csrf']):
                return None
            return identity, dict(session)

    def logout(self, cookie):
        if isinstance(cookie, str) and cookie.isascii():
            with self.lock:
                self.sessions.pop(hashed(cookie), None)

    def close(self):
        with self.lock:
            self.grant = None
            self.sessions.clear()
