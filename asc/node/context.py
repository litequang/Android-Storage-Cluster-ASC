"""App-owned runtime context, independent of process HOME and CLI dependencies.

The caller is trusted native code, not a browser or network request. Its credential
provider MUST authenticate/encrypt its single atomic record and refuse key loss.
This module never generates a Node/Cluster identity or adopts an existing root.
"""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Protocol
import uuid

from ..catalog.common import canonical
from ..demo.locks import private_lock
from ..storage.volumes import no_links

MAX_RECORD = 65536


class ContextLocked(ValueError):
    def __init__(self):
        super().__init__('native_context_locked')


class CredentialProvider(Protocol):
    """Private in-process interface, never an IPC operation with arbitrary paths.

    CAS compares the complete exact previous plaintext (None means never created).
    Atomic encrypted publication must survive process restart. Loss/corruption is
    an exception, never an empty/default record. Not a Catalog or credential issuer.
    """
    def load(self) -> str | None: ...
    def compare_exchange(self, expected: str | None, replacement: str) -> None: ...


def _uuid(value):
    if not isinstance(value, str) or str(uuid.UUID(value)) != value:
        raise ContextLocked()
    return value


def decode(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ContextLocked()
            result[key] = value
        return result
    try:
        if not isinstance(raw, str) or len(raw.encode('utf-8')) > MAX_RECORD:
            raise ContextLocked()
        return json.loads(raw, object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(ContextLocked()))
    except (ValueError, TypeError, RecursionError):
        raise ContextLocked() from None


def android_device(build):
    """Native Build-provider input; no getprop/subprocess or model override flag.

    Explicit debug AOSP identity is scoped SYNTHETIC, never phone acceptance.
    Protected secondary fields dominate even an otherwise valid emulator/test model.
    Core CLI guards are untouched. Scores/memory never authorize this context.
    """
    keys = {'manufacturer', 'model', 'device', 'product', 'hardware', 'fingerprint', 'sdk', 'debug'}
    if not isinstance(build, dict) or set(build) != keys:
        raise ContextLocked()
    fields = ('manufacturer', 'model', 'device', 'product', 'hardware', 'fingerprint')
    if any(not isinstance(build[k], str) or not 1 <= len(build[k]) <= 512 for k in fields):
        raise ContextLocked()
    values = {k: build[k].lower() for k in fields}
    if (any('m51' in values[k] or 'sm-m515' in values[k] for k in fields[:4]) or
            type(build['sdk']) is not int or not 26 <= build['sdk'] <= 1000 or
            type(build['debug']) is not bool):
        raise ContextLocked()
    synthetic = (build['debug'] and values['hardware'] in ('ranchu', 'goldfish') and
                 'sdk' in values['product'] and
                 any(x in values['fingerprint'] for x in ('generic', 'sdk')))
    vendor, model = values['manufacturer'], values['model']
    known = (('zte' in vendor and (model in ('9045', 'zte9045', 'zte 9045') or 'v40' in model)) or
             (('bphone' in vendor or 'bkav' in vendor) and 'a40' in model) or
             ('sony' in vendor and ('xz3' in model or model in ('h8416', 'h9436', 'h9493'))))
    identity_known = all(values[k] not in ('unknown', 'null') for k in ('manufacturer', 'model'))
    if not (synthetic or known and identity_known):
        raise ContextLocked()
    # Bind hardware identity, not the OS version/fingerprint which can upgrade.
    binding = hashlib.sha256(canonical({k: values[k] for k in fields[:5]})).hexdigest()
    return {'scope': 'LINUX_HOSTED_ANDROID_SYNTHETIC' if synthetic else 'PHONE_NOT_ACCEPTED',
            'binding': binding}


def _directory(path):
    no_links(path)
    info = path.lstat()
    if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077):
        raise ContextLocked()
    return [info.st_dev, info.st_ino]


def _read_anchor(path):
    no_links(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or
                info.st_uid != os.getuid() or info.st_mode & 0o077 or info.st_size > 4096):
            raise ContextLocked()
        raw = os.read(fd, 4097)
        if (info.st_dev, info.st_ino) != (path.lstat().st_dev, path.lstat().st_ino):
            raise ContextLocked()
        return decode(raw.decode('utf-8'))
    finally:
        os.close(fd)


class NodeContext:
    """One explicit, fixed app-private home with a sealed credential provider.

    `private_parent` comes from trusted canonical Android Context.filesDir before
    first approval. Never resolve an approved/swapped root to make it acceptable.
    Construction/status/restart are read-only. Initialization requires an explicit
    caller action and existing app identity/key; partial state is held for review.
    """
    def __init__(self, private_parent, provider, app_id, build, tls_provider=None):
        self.parent = Path(private_parent)
        self.home = self.parent / 'native-node-v1'
        self.provider = provider
        self.app_id = _uuid(app_id)
        self.device = android_device(build)  # Before any provider/state access.
        self.tls_provider = tls_provider  # Trusted in-process platform loader, never IPC input.
        if not self.parent.is_absolute() or '..' in self.parent.parts:
            raise ContextLocked()
        _directory(self.parent)

    def _check_recovery(self):
        for path in (self.home, *self.home.parents):
            if any((path / name).exists() or (path / name).is_symlink()
                   for name in ('RECOVERY_READ_ONLY.json', 'READY.json')):
                raise ContextLocked()

    def _validate(self, raw):
        record = decode(raw)
        keys = {'format', 'app_id', 'context_id', 'revision', 'binding', 'device_binding',
                'pending', 'node', 'tls', 'storage'}
        if (not isinstance(record, dict) or set(record) != keys or
                type(record['format']) is not int or record['format'] != 1 or
                record['app_id'] != self.app_id or type(record['revision']) is not int or
                not 0 <= record['revision'] < 2**63 or
                record['device_binding'] != self.device['binding']):
            raise ContextLocked()
        _uuid(record['context_id'])
        # Strict components, never arbitrary opaque secrets. A certificate is
        # local TLS identity only, not enrollment/approval/Node or writer authority.
        from .enrollment import validate_components
        validate_components(record)
        from .storage import validate as validate_storage
        validate_storage(record)
        if record['tls'] is not None:
            from .tls import server_context
            server_context(record['tls'], self.tls_provider)
        self._check_recovery()
        expected = {'home': str(self.home), 'parent': _directory(self.parent),
                    'root': _directory(self.home)}
        if canonical(record['binding']) != canonical(expected):
            raise ContextLocked()
        anchor = _read_anchor(self.home / 'context.json')
        if canonical(anchor) != canonical({'format': 1, 'app_id': self.app_id, 'context_id': record['context_id'],
                                          'mode': 'native-storage-node'}):
            raise ContextLocked()
        for name in ('controller.json', 'node.json', 'enrollment_pending.json', 'storage.json',
                     'registry.sqlite3', 'runtime.sqlite3', 'RECOVERY_READ_ONLY.json'):
            if (self.home / name).exists() or (self.home / name).is_symlink():
                raise ContextLocked()  # No legacy HOME/DR adoption or plaintext credentials.
        if expected != {'home': str(self.home), 'parent': _directory(self.parent),
                        'root': _directory(self.home)}:
            raise ContextLocked()
        return record

    def load(self):
        try:
            self._check_recovery()
            raw = self.provider.load()
            if raw is None:
                raise ContextLocked()
            return self._validate(raw)
        except Exception:
            raise ContextLocked() from None

    def initialize(self):
        try:
            self._check_recovery()
            raw = self.provider.load()
            if raw is not None:
                return self.public_status()
            if self.home.exists() or self.home.is_symlink():
                raise ContextLocked()
            # Exclusive descriptor-relative creation under the approved app root;
            # a namespace swap cannot redirect anchor writes into another folder.
            parent_identity = _directory(self.parent)
            parent_fd = os.open(self.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                info = os.fstat(parent_fd)
                if [info.st_dev, info.st_ino] != parent_identity:
                    raise ContextLocked()
                os.mkdir('native-node-v1', mode=0o700, dir_fd=parent_fd)
                root_fd = os.open('native-node-v1', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                  dir_fd=parent_fd)
                try:
                    root_info = os.fstat(root_fd)
                    context_id = str(uuid.uuid4())  # App receipt, NEVER Node/Cluster ID.
                    anchor = canonical({'format': 1, 'app_id': self.app_id,
                              'context_id': context_id, 'mode': 'native-storage-node'})
                    fd = os.open('context.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                                 0o600, dir_fd=root_fd)
                    with os.fdopen(fd, 'wb') as stream:
                        stream.write(anchor); stream.flush(); os.fsync(stream.fileno())
                    os.fsync(root_fd); os.fsync(parent_fd)
                    record = {'format': 1, 'app_id': self.app_id, 'context_id': context_id,
                              'revision': 0, 'binding': {'home': str(self.home),
                              'parent': parent_identity, 'root': [root_info.st_dev, root_info.st_ino]},
                              'device_binding': self.device['binding'],
                              'pending': None, 'node': None, 'tls': None, 'storage': None}
                finally:
                    os.close(root_fd)
            finally:
                os.close(parent_fd)
            self._validate(canonical(record).decode())
            self.provider.compare_exchange(None, canonical(record).decode())
            return self.public_status()
        except Exception:
            raise ContextLocked() from None

    @contextmanager
    def operation(self):
        self.load()  # Validate BEFORE touching even the ownership file.
        with private_lock(self.home, 'native-context'):
            self.load()
            yield self
            self.load()

    def public_status(self):
        record = self.load()
        node, pending = record['node'], record['pending']
        operation = pending['operation'] if pending else node
        return {'context_version': 1, 'state': 'CONTEXT_READY',
                'context_id': record['context_id'], 'application_id': self.app_id,
                'device_scope': self.device['scope'],
                'node_id': node['node_id'] if node else None,
                'cluster_id': node['cluster_id'] if node else None,
                'enrollment': 'ENROLLED_PENDING_APPROVAL' if node else 'PENDING_RECEIPT' if pending else 'NOT_CONFIGURED',
                'join_request_id': pending['request_id'] if pending else None,
                'enrollment_controller': operation['controller'] if operation else None,
                'enrollment_pin': operation['pin'] if operation else None,
                'expected_cluster_id': (operation.get('expected_cluster_id') or operation.get('cluster_id')) if operation else None,
                'controller_confirmation': 'HISTORICAL_JOIN_RECEIPT' if node else 'UNKNOWN',
                'storage_approved': None, 'failure_domain_approved': None,
                'tls': 'IDENTITY_READY' if record['tls'] is not None else 'NOT_CONFIGURED',
                'tls_pin': record['tls']['pin'] if record['tls'] is not None else None,
                'storage': ('LOCAL_CONFIG_READY' if record['storage']['state'] == 'READY' else 'SETUP_HELD')
                           if record['storage'] is not None else 'NOT_CONFIGURED', 'writer_authority': False,
                'runtime_start_supported': record['storage'] is not None and record['storage']['state'] == 'READY'}

    def prepare_tls(self, certificate_provider):
        """Explicit provision once; repeat validates/reuses, never rotates on error.

        certificate_provider is trusted in-process standard-library/third-party
        X.509 generation, not a Binder-supplied implementation or shell command.
        Its raw private material never crosses public IPC or a logging boundary.
        """
        from .tls import server_context
        try:
            with self.operation():
                raw = self.provider.load()
                record = self._validate(raw)
                if record['tls'] is None:
                    identity = decode(certificate_provider.generate())
                    server_context(identity, self.tls_provider)  # Key match before persistence.
                    record['tls'] = identity
                    record['revision'] += 1
                    replacement = canonical(record).decode()
                    self._validate(replacement)
                    self.provider.compare_exchange(raw, replacement)
                return self.public_status()
        except Exception:
            raise ContextLocked() from None

    def tls_context(self):
        from .tls import server_context
        record = self.load()
        if record['tls'] is None:
            raise ContextLocked()
        return server_context(record['tls'], self.tls_provider)
