"""Optional private owner/viewer accounts; standard PBKDF2, no default password."""
import hashlib
import hmac
import re
import secrets
import threading
import time
import uuid

from ...bridge import private
from ...storage.errors import StorageError

ITERATIONS = 600_000
ROLES = ('owner', 'viewer')


class AccountError(Exception):
    def __init__(self, status, code):
        self.status, self.code = status, code


def username(value):
    if type(value) is not str or not re.fullmatch('[a-z][a-z0-9_.-]{2,47}', value):
        raise ValueError('invalid account name')
    return value


def password_bytes(value):
    if type(value) is not str or not 12 <= len(value) <= 128:
        raise ValueError('password must contain 12 to 128 characters')
    raw = value.encode('utf-8')
    if len(raw) > 512:
        raise ValueError('password too long')
    return raw


def public(name, row):
    return dict(username=name, **{k: row[k] for k in ('account_id', 'role', 'generation', 'created_at', 'updated_at')})


class Accounts:
    def __init__(self, root, cluster_id):
        if str(uuid.UUID(cluster_id)) != cluster_id:
            raise ValueError('invalid account cluster binding')
        self.cluster_id = cluster_id
        self.directory = private.directory(root/'dashboard')
        self.path = self.directory/'accounts.json'
        self.lock = threading.Lock()
        self._read()  # Corrupt existing credentials never become an empty store.

    def _read(self):
        try:
            private.directory(self.directory)
            try:
                self.path.lstat()
            except FileNotFoundError:
                return dict(format=1, cluster_id=self.cluster_id, kdf='pbkdf2-hmac-sha256', iterations=ITERATIONS, revision=0, accounts={})
            value = private.read(self.path)
            if (set(value) != {'format', 'cluster_id', 'kdf', 'iterations', 'revision', 'accounts'}
                    or type(value['format']) is not int or value['format'] != 1
                    or value['cluster_id'] != self.cluster_id
                    or value['kdf'] != 'pbkdf2-hmac-sha256' or type(value['iterations']) is not int
                    or value['iterations'] != ITERATIONS or type(value['revision']) is not int
                    or not 1 <= value['revision'] <= 1000000 or type(value['accounts']) is not dict
                    or not 1 <= len(value['accounts']) <= 8):
                raise ValueError()
            ids = set()
            for name, row in value['accounts'].items():
                username(name)
                if (type(row) is not dict or set(row) != {'account_id', 'role', 'generation', 'salt', 'password_hash', 'created_at', 'updated_at'}
                        or row['role'] not in ROLES or type(row['generation']) is not int or not 1 <= row['generation'] <= 1000000
                        or type(row['salt']) is not str or not re.fullmatch('[0-9a-f]{32}', row['salt'])
                        or type(row['password_hash']) is not str or not re.fullmatch('[0-9a-f]{64}', row['password_hash'])
                        or type(row['created_at']) is not int or type(row['updated_at']) is not int
                        or not 0 <= row['created_at'] <= row['updated_at']):
                    raise ValueError()
                if str(uuid.UUID(row['account_id'])) != row['account_id'] or row['account_id'] in ids:
                    raise ValueError()
                ids.add(row['account_id'])
            if not any(row['role'] == 'owner' for row in value['accounts'].values()):
                raise ValueError()
            return value
        except (ValueError, TypeError, KeyError, OSError, StorageError):
            raise AccountError(503, 'account_state_unavailable') from None

    def _write(self, value):
        if value['revision'] >= 1000000:
            raise AccountError(409, 'account_limit')
        value['revision'] += 1
        private.directory(self.directory)
        private.replace(self.path, value)  # Existing no-link owner-only atomic fsync helper.

    def list(self):
        with self.lock:
            value = self._read()
            return {'account_api_version': 1, 'accounts': [public(k, v) for k, v in sorted(value['accounts'].items())],
                    'password_enabled': bool(value['accounts']), 'roles': list(ROLES),
                    'viewer_scope': 'read all cluster files; no upload/management; no per-file sharing ACL'}

    def authenticate(self, name, password):
        try:
            username(name); raw = password_bytes(password)
        except (ValueError, UnicodeError):
            return None
        with self.lock:
            row = self._read()['accounts'].get(name)
            salt = bytes.fromhex(row['salt']) if row else bytes(16)
            actual = hashlib.pbkdf2_hmac('sha256', raw, salt, ITERATIONS).hex()
            matched = hmac.compare_digest(actual, row['password_hash'] if row else '0'*64)
            return public(name, row) if row and matched else None

    def valid(self, session):
        with self.lock:
            return any(row['account_id'] == session.get('account_id') and row['generation'] == session.get('account_generation')
                       and row['role'] == session.get('role') for row in self._read()['accounts'].values())

    def create(self, obj):
        if type(obj) is not dict or set(obj) != {'username', 'password', 'role'}:
            raise ValueError('invalid account request')
        name = username(obj['username']); raw = password_bytes(obj['password'])
        if obj['role'] not in ROLES:
            raise ValueError('invalid account role')
        with self.lock:
            value = self._read()
            if name in value['accounts']:
                raise AccountError(409, 'account_exists')
            if len(value['accounts']) >= 8:
                raise AccountError(409, 'account_limit')
            if not value['accounts'] and obj['role'] != 'owner':
                raise AccountError(409, 'last_owner_required')
            salt = secrets.token_bytes(16); stamp = int(time.time())
            row = dict(account_id=str(uuid.uuid4()), role=obj['role'], generation=1, salt=salt.hex(),
                       password_hash=hashlib.pbkdf2_hmac('sha256', raw, salt, ITERATIONS).hex(), created_at=stamp, updated_at=stamp)
            value['accounts'][name] = row; self._write(value)
            return public(name, row)

    def change(self, name, obj):
        username(name)
        if type(obj) is not dict or set(obj) != {'expected_generation', 'role', 'password', 'delete'}:
            raise ValueError('invalid account update')
        if (type(obj['expected_generation']) is not int or obj['expected_generation'] < 1
                or obj['role'] not in ROLES or type(obj['delete']) is not bool or type(obj['password']) is not str):
            raise ValueError('invalid account update')
        if obj['delete'] and obj['password']:
            raise ValueError('delete does not change password')
        raw = password_bytes(obj['password']) if obj['password'] else None
        with self.lock:
            value = self._read(); row = value['accounts'].get(name)
            if row is None or row['generation'] != obj['expected_generation']:
                raise AccountError(409, 'account_state_changed')
            if row['generation'] >= 1000000:
                raise AccountError(409, 'account_limit')
            if (row['role'] == 'owner' and (obj['delete'] or obj['role'] != 'owner')
                    and sum(v['role'] == 'owner' for v in value['accounts'].values()) <= 1):
                raise AccountError(409, 'last_owner_required')
            old_id = row['account_id']
            if obj['delete']:
                del value['accounts'][name]
            else:
                row['role'] = obj['role']; row['generation'] += 1; row['updated_at'] = max(row['updated_at'], int(time.time()))
                if raw is not None:
                    salt = secrets.token_bytes(16); row['salt'] = salt.hex()
                    row['password_hash'] = hashlib.pbkdf2_hmac('sha256', raw, salt, ITERATIONS).hex()
            self._write(value)
            return {'account_id': old_id, 'username': name, 'deleted': obj['delete']}
