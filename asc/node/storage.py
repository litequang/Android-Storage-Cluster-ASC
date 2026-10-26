"""Minimal app-owned Node volume; reuse canonical Engine, IDs and probes."""
from contextlib import contextmanager
from ..catalog.common import canonical
from ..storage.engine import StorageEngine
from ..storage.manifest import existing_identity
from .context import ContextLocked, _directory, _uuid


def validate(record):
    item = record['storage']
    if item is None:
        return
    base = {'format', 'state', 'node_id', 'quota', 'reserve'}
    ready = {'root', 'manifest', 'volume_id', 'medium'}
    if (not isinstance(item, dict) or item.get('state') not in ('PREPARING', 'READY') or
            set(item) != base | (ready if item['state'] == 'READY' else set()) or
            type(item['format']) is not int or item['format'] != 1 or record['node'] is None or
            item['node_id'] != record['node']['node_id'] or
            type(item['quota']) is not int or not 1 <= item['quota'] <= 2**40 or
            type(item['reserve']) is not int or not 0 <= item['reserve'] <= 2**40):
        raise ContextLocked()
    if item['state'] == 'READY':
        _uuid(item['volume_id'])
        for key in ('root', 'manifest'):
            if (not isinstance(item[key], list) or len(item[key]) != 2 or
                    any(type(v) is not int or v < 0 for v in item[key])):
                raise ContextLocked()
        if not isinstance(item['medium'], str) or len(item['medium']) > 128:
            raise ContextLocked()


class NativeStorage:
    def __init__(self, context):
        self.context = context
        self.root = context.home / 'node-storage-v1'

    def configure(self, quota, reserve):
        if type(quota) is not int or not 1 <= quota <= 2**40 or type(reserve) is not int or not 0 <= reserve <= 2**40:
            raise ValueError('invalid_storage_quota')
        with self.context.operation():
            raw = self.context.provider.load(); record = self.context._validate(raw)
            if record['node'] is None:
                raise ValueError('enrollment_required')
            if record['storage'] is not None:
                if record['storage']['state'] != 'READY':
                    raise ValueError('storage_setup_held')
                if (record['storage']['quota'], record['storage']['reserve']) != (quota, reserve):
                    raise ValueError('storage_configuration_conflict')
                return self.status()
            if self.root.exists() or self.root.is_symlink():
                raise ValueError('existing_storage_not_adopted')
            # Intent first: interruption holds partial setup, never recreates IDs.
            item = {'format': 1, 'state': 'PREPARING', 'node_id': record['node']['node_id'],
                    'quota': quota, 'reserve': reserve}
            record['storage'] = item; record['revision'] += 1
            pending = canonical(record).decode()
            self.context.provider.compare_exchange(raw, pending)
            self.root.mkdir(mode=0o700)
            with StorageEngine(self.root / 'engine', item['node_id']) as engine:
                volume = engine.volumes.register(self.root / 'data', 'internal', quota, reserve)
                probe = engine.volumes.inspect(probe=True, volume_id=volume['volume_id'])[0]
                if probe['writable'] is not True or probe['fsync_tested'] is not True:
                    raise ValueError('storage_probe_failed')
            item.update(state='READY', root=_directory(self.root),
                        manifest=list(existing_identity(self.root / 'engine/manifest.sqlite3')),
                        volume_id=volume['volume_id'], medium=volume['medium'])
            record['revision'] += 1
            ready = canonical(record).decode(); self.context._validate(ready)
            self.context.provider.compare_exchange(pending, ready)
        return self.status()

    @contextmanager
    def open(self):
        record = self.context.load(); item = record['storage']
        if item is None or item['state'] != 'READY':
            raise ValueError('storage_not_ready')
        if _directory(self.root) != item['root']:
            raise ValueError('storage_root_changed')
        with StorageEngine(self.root / 'engine', item['node_id'], existing_only=True,
                           manifest_identity=item['manifest']) as engine:
            volume = engine.volumes.get(item['volume_id'])
            if (volume.record['node_id'] != item['node_id'] or volume.record['medium'] != item['medium'] or
                    volume.record['root'] != str(self.root / 'data') or
                    (volume.record['quota'], volume.record['reserve']) != (item['quota'], item['reserve'])):
                raise ValueError('storage_identity_changed')
            volume.check()
            yield engine

    def status(self):
        with self.open() as engine:
            return {'state': 'LOCAL_VOLUME_READY', 'node_id': engine.node_id,
                    'storage': engine.capabilities(), 'storage_approved': None,
                    'failure_domain_approved': None, 'writer_authority': False}
