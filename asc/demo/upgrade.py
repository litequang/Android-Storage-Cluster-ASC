"""Stopped, exact-format source upgrades; verified private backup, no schema restore."""
from contextlib import contextmanager, ExitStack
import hashlib
import re
import sqlite3
import os
from pathlib import Path
import shutil
import stat
import tempfile
from ..identity import ensure_private_home, replace_private, save_private
from ..runtime import running
from .locks import private_lock as foreground_lock
from ..storage.volumes import LocalVolume, no_links
from ..storage.errors import StorageError
from .installer import private_path, guard
from .package import digest, encoded, verify
from .state import FORMATS, inspect_state, read_db, read_json

REQUIRED = {'installer', 'lan-single-writer', 'upgrade-safe'}


def durable_json(path, value):
    no_links(path)
    replace_private(path, value)
    if os.name == 'posix':
        fd = os.open(path.parent, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def binding(prefix, root, create=False):
    prefix, root = private_path(prefix, code_prefix=True), private_path(root)
    marker = inspect_state(root)
    path = prefix / 'state-binding.json'
    expected = {'format': 1, 'state': str(root), 'installation_id': marker['installation_id']}
    if not path.exists():
        if not create:
            raise ValueError('installed prefix has no state binding; initialize via installed launcher')
        with foreground_lock(prefix, 'install'):
            if not path.exists():
                save_private(path, expected)
    if read_json(path) != expected:
        raise ValueError('code prefix already belongs to another Demo state')
    return expected


def read_journal(prefix):
    journal = read_json(Path(prefix) / 'upgrade-journal.json')
    fields = {'format', 'status', 'action', 'installation_id', 'old_release', 'new_release', 'backup', 'backup_sha256'}
    if (set(journal) != fields or type(journal['format']) is not int or journal['format'] != 1
            or journal['status'] not in ('PREPARED', 'COMPLETED', 'RECOVERED_OLD_CODE')
            or journal['action'] not in ('upgrade', 'rollback')
            or any(not isinstance(journal[k], str) or not re.fullmatch(r'[a-f0-9]{64}', journal[k])
                   for k in ('old_release', 'new_release', 'backup_sha256'))):
        raise ValueError('unsupported activation journal')
    private_path(journal['backup'])
    return journal


def startup_check(prefix, root):
    binding(prefix, root)
    journal = Path(prefix) / 'upgrade-journal.json'
    if journal.exists() and read_journal(prefix)['status'] == 'PREPARED':
        raise ValueError('interrupted activation; explicit recover-upgrade required before runtime')


@contextmanager
def stopped(root):
    root = private_path(root)
    with foreground_lock(root, 'demo-operation'), ExitStack() as stack:
        inspect_state(root)
        for home, roles in ((root / 'controller', ('controller', 'catalog-worker')),
                            (root / 'node', ('agent',)), (root / 'node/storage', ('storage-engine',))):
            if home.is_dir():
                for role in roles:
                    stack.enter_context(foreground_lock(home, role))
        yield


def sources(root):
    root = private_path(root)
    result = {'state': root}
    manifest = root / 'node/storage/manifest.sqlite3'
    if manifest.exists():
        rows = read_db(manifest, 1, lambda db: [dict(zip([d[0] for d in cur.description], r))
                       for cur in [db.execute('SELECT * FROM volumes ORDER BY volume_id')] for r in cur])
        for row in rows:
            LocalVolume(row).check()  # Require actual approved original medium, not space estimates.
            volume = Path(row['root'])
            if volume != root and root not in volume.parents:
                if any(volume == p or volume in p.parents or p in volume.parents for p in result.values()):
                    raise ValueError('overlapping backup sources')
                result['volume-' + row['volume_id']] = volume
    return result


def inventory(roots):
    result = {}
    for label, root in roots.items():
        no_links(root)
        if not root.is_dir():
            raise ValueError('backup source missing')
        result[label] = {'directory': True}
        for path in sorted(root.rglob('*')):
            no_links(path)
            info = path.lstat()
            if stat.S_ISDIR(info.st_mode):
                result[label + '/' + path.relative_to(root).as_posix()] = {'directory': True}
                continue
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise ValueError('backup refuses links or special files')
            # OS-held lock files are coordination, not recoverable private data.
            if label == 'state' and path.relative_to(root).as_posix() in {
                    'demo-operation.lock', 'controller/controller.lock', 'controller/catalog-worker.lock',
                    'node/agent.lock', 'node/storage/storage-engine.lock'}:
                continue
            sha = hashlib.sha256()
            fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
            with os.fdopen(fd, 'rb') as stream:
                opened = os.fstat(stream.fileno())
                if (opened.st_dev, opened.st_ino, opened.st_size) != (info.st_dev, info.st_ino, info.st_size):
                    raise ValueError('backup source changed')
                while chunk := stream.read(65536):
                    sha.update(chunk)
                after = os.fstat(stream.fileno())
            if (after.st_size, after.st_mtime_ns, after.st_ctime_ns) != (info.st_size, info.st_mtime_ns, info.st_ctime_ns):
                raise ValueError('backup source changed')
            result[label + '/' + path.relative_to(root).as_posix()] = {'sha256': sha.hexdigest(), 'size': info.st_size}
    return result


def backup_locked(root, destination, prefix):
    root, destination, prefix = private_path(root), private_path(destination), private_path(prefix, code_prefix=True)
    binding(prefix, root)
    roots = sources(root)
    for source in [*roots.values(), prefix]:
        if destination == source or source in destination.parents or destination in source.parents:
            raise ValueError('backup must be separate from code/state/volumes')
    if destination.exists():
        raise ValueError('backup destination must be new; never overwrite')
    before = inventory(roots)
    total = sum(v.get('size', 0) for v in before.values())
    parent = destination.parent
    if not parent.is_dir() or shutil.disk_usage(parent).free < total + max(16 * 1024**2, total // 10):
        raise ValueError('backup parent missing or insufficient measured capacity')
    ensure_private_home(destination)
    for name, entry in before.items():
        target = destination / name
        if entry.get('directory') is True:
            target.mkdir(mode=0o700, parents=True, exist_ok=True)
            continue
        label, relative = name.split('/', 1)
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        source = roots[label] / relative
        no_links(source)
        fd = os.open(source, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
        with os.fdopen(fd, 'rb') as stream, target.open('xb') as output:
            os.chmod(target, 0o600)
            shutil.copyfileobj(stream, output, 65536)
            output.flush()
            os.fsync(output.fileno())
    if inventory(roots) != before:
        raise ValueError('backup source changed; incomplete backup retained for review')
    copied = inventory({label: destination / label for label in roots})
    if copied != before:
        raise ValueError('backup readback checksum mismatch')
    pointer = read_json(prefix / 'install.json')
    marker = inspect_state(root)
    body = {'format': 1, 'installation_id': marker['installation_id'], 'state_formats': FORMATS,
            'release_id': pointer['release_id'], 'entries': before,
            'sources': {label: str(path) for label, path in roots.items()}}
    report = dict(body, backup_sha256=digest(encoded(body)))
    if os.name == 'posix':
        for directory in sorted([p for p in destination.rglob('*') if p.is_dir()] + [destination], key=lambda p: len(p.parts), reverse=True):
            fd = os.open(directory, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
    durable_json(destination / 'backup-complete.json', report)
    if os.name == 'posix':
        fd = os.open(destination.parent, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    return {'backup_sha256': report['backup_sha256'], 'files': sum('size' in v for v in before.values()), 'bytes': total}


def verify_backup(destination, root=None):
    destination = private_path(destination)
    report = read_json(destination / 'backup-complete.json')
    body = {k: v for k, v in report.items() if k != 'backup_sha256'}
    if (type(report.get('format')) is not int or report.get('format') != 1 or report.get('state_formats') != FORMATS
            or any(type(v) is not int for v in report['state_formats'].values())
            or digest(encoded(body)) != report.get('backup_sha256')):
        raise ValueError('invalid backup manifest')
    if not isinstance(report.get('sources'), dict) or 'state' not in report['sources']:
        raise ValueError('invalid backup sources')
    for label in report['sources']:
        if label != 'state' and not re.fullmatch(r'volume-[a-f0-9-]{36}', label):
            raise ValueError('invalid backup labels')
    if {p.name for p in destination.iterdir()} != set(report['sources']) | {'backup-complete.json'}:
        raise ValueError('backup inventory differs')
    roots = {label: destination / label for label in report['sources']}
    if inventory(roots) != report['entries']:
        raise ValueError('backup contents changed')
    if root is not None:
        if inspect_state(root)['installation_id'] != report['installation_id']:
            raise ValueError('backup belongs to another installation')
        if {k: str(v) for k, v in sources(root).items()} != report['sources'] or inventory(sources(root)) != report['entries']:
            raise ValueError('state changed since backup; preserve it and make a fresh stopped backup')
    return report


def compatibility(release, root):
    inspect_state(root)
    if (release.get('state_formats') != FORMATS or any(type(x) is not int for x in release['state_formats'].values())
            or not REQUIRED.issubset(release.get('capabilities', []))):
        raise ValueError('release incompatible; no implicit schema migration or downgrade')
    return {'compatible': True, 'schema_migration': False}


def release_path(prefix, release_id):
    if not isinstance(release_id, str) or not re.fullmatch(r'[a-f0-9]{64}', release_id):
        raise ValueError('invalid release identity')
    target = Path(prefix) / 'releases' / release_id
    no_links(target)
    return target


def stage(source, prefix):
    guard()
    prefix = private_path(prefix, code_prefix=True)
    source = Path(source).absolute()
    release = verify(source)
    with foreground_lock(prefix, 'install'):
        read_json(prefix / 'install.json')
        target = prefix / 'releases' / release['release_id']
        no_links(target)
        if target.exists():
            verify(target)
        else:
            with tempfile.TemporaryDirectory(prefix='.stage-', dir=prefix / 'releases') as temp:
                staging = Path(temp) / 'release'
                shutil.copytree(source, staging, symlinks=True)
                verify(staging)
                os.rename(staging, target)
    return {'staged': True, 'release_id': release['release_id'], 'activated': False}


def activate(root, prefix, release_id, backup_destination, action='upgrade'):
    guard()
    root, backup_destination = private_path(root), private_path(backup_destination)
    prefix = private_path(prefix, code_prefix=True)
    release_path(prefix, release_id)
    with stopped(root), foreground_lock(prefix, 'install'):
        startup_check(prefix, root)
        old = read_json(prefix / 'install.json')
        verify(release_path(prefix, old['release_id']))
        release = verify(release_path(prefix, release_id))
        compatibility(release, root)
        backup = backup_locked(root, backup_destination, prefix)
        verify_backup(backup_destination, root)
        journal = {'format': 1, 'status': 'PREPARED', 'action': action,
                   'installation_id': inspect_state(root)['installation_id'],
                   'old_release': old['release_id'], 'new_release': release_id,
                   'backup': str(backup_destination), 'backup_sha256': backup['backup_sha256']}
        durable_json(prefix / 'upgrade-journal.json', journal)
        durable_json(prefix / 'install.json', {'format': 1, 'release_id': release_id})
        durable_json(prefix / 'upgrade-journal.json', dict(journal, status='COMPLETED'))
        return {'activated': True, 'action': action, 'release_id': release_id,
                'previous_release_id': old['release_id'], 'backup_sha256': backup['backup_sha256'],
                'identity_preserved': True, 'schema_migration': False}


def recover(root, prefix):
    guard()
    prefix = private_path(prefix, code_prefix=True)
    with stopped(root), foreground_lock(prefix, 'install'):
        binding(prefix, root)
        journal = read_journal(prefix)
        if journal['status'] != 'PREPARED' or journal['installation_id'] != inspect_state(root)['installation_id']:
            raise ValueError('no matching interrupted upgrade')
        backup = verify_backup(journal['backup'], root)
        if backup['backup_sha256'] != journal['backup_sha256']:
            raise ValueError('journal backup differs')
        current = read_json(prefix / 'install.json')['release_id']
        if current not in (journal['old_release'], journal['new_release']):
            raise ValueError('unexpected active release; preserve for review')
        old = verify(release_path(prefix, journal['old_release']))
        compatibility(old, root)
        durable_json(prefix / 'install.json', {'format': 1, 'release_id': journal['old_release']})
        durable_json(prefix / 'upgrade-journal.json', dict(journal, status='RECOVERED_OLD_CODE'))
        return {'recovered': True, 'release_id': journal['old_release'], 'state_restored': False}


def diagnose(root):
    """Only fixed status fields/counts; never raw configs, profiles, filenames or exceptions."""
    from . import VERSION
    report = {'format': 1, 'version': VERSION, 'qualification': 'Linux synthetic only; Android NOT TESTED'}
    try:
        marker = inspect_state(root)
        root = Path(root)
        report.update(state='compatible', role=marker['role'], mode=marker['mode'])
        report['running'] = {name: running(root / home, role) for name, home, role in
                             (('controller', 'controller', 'controller'), ('node', 'node', 'agent'))}
        registry = root / 'controller/registry.sqlite3'
        if registry.exists():
            report['counts'] = read_db(registry, 4, lambda db: {name: db.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0]
                                      for name, table in (('nodes', 'nodes'), ('files', 'catalog_files'), ('jobs', 'catalog_jobs'))})
        manifest = root / 'node/storage/manifest.sqlite3'
        if manifest.exists():
            records = read_db(manifest, 1, lambda db: [dict(zip([d[0] for d in cur.description], r))
                              for cur in [db.execute('SELECT * FROM volumes')] for r in cur])
            report['volumes'] = []
            for row in records:
                try:
                    LocalVolume(row).check()
                    space = shutil.disk_usage(row['root'])
                    report['volumes'].append({'status': 'accessible', 'free_bytes': space.free, 'quota': row['quota']})
                except (OSError, ValueError, StorageError):
                    report['volumes'].append({'status': 'unavailable', 'free_bytes': None})
    except (OSError, ValueError, KeyError, TypeError, StorageError, sqlite3.Error):
        report['state'] = 'incompatible_or_unavailable'
    return report
