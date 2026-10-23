"""Approved local roots, medium identity, bounded probes and no-follow file access."""
from contextlib import contextmanager
import ctypes
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import uuid
import time
import unicodedata
from .errors import StorageError
from ..identity import save_private
from ..probe import _detect_sd_locations

CHUNK = 65536


def logical_path(value):
    if (not isinstance(value, str) or not 1 <= len(value) <= 512 or
            any(unicodedata.category(c).startswith('C') for c in value) or
            any(c in value for c in '\\:%') or value.startswith('/') or
            any(p in ('', '.', '..') or p.endswith((' ', '.')) for p in value.split('/'))):
        raise StorageError('invalid_logical_path', 400)
    return value


def identifier(value):
    try:
        if str(uuid.UUID(value)) != value:
            raise ValueError()
    except (ValueError, TypeError, AttributeError):
        raise StorageError('invalid_id', 400) from None
    return value


def no_links(path):
    for part in [path, *path.parents]:
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise StorageError('unsafe_path', 403)


@contextmanager
def directory_guard(root):
    """On Windows hold directory handles denying delete/rename during each operation."""
    no_links(root)
    handles = []
    if os.name == 'nt':
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.CreateFileW.argtypes = [ctypes.c_wchar_p, ctypes.c_ulong, ctypes.c_ulong,
                                      ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p]
        kernel.CreateFileW.restype = ctypes.c_void_p
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        try:
            for part in [*reversed(root.parents), root, root / 'staging', root / 'objects']:
                handle = kernel.CreateFileW(str(part), 0x80, 3, None, 3, 0x02200000, None)
                if handle == ctypes.c_void_p(-1).value:
                    raise StorageError('volume_unavailable', 503)
                handles.append(handle)
            no_links(root)
            no_links(root / 'staging')
            no_links(root / 'objects')
            yield
        finally:
            for handle in reversed(handles):
                kernel.CloseHandle(handle)
    else:
        yield


class LocalVolume:
    """Filesystem adapter seam; SAF must implement equivalent semantics, not raw paths."""
    def __init__(self, record):
        self.record = dict(record)
        self.root = Path(record['root'])

    def check(self):
        if not self.root.is_dir():
            raise StorageError('volume_unavailable', 503)
        no_links(self.root)
        try:
            marker = self.root / '.asc-volume.json'
            no_links(marker)
            if marker.stat().st_size > 4096:
                raise StorageError('volume_identity_changed', 409)
            data = json.loads(marker.read_text(encoding='utf-8'))
            info = self.root.stat()
            medium = f'{info.st_dev}:{info.st_ino}'
            if (data != {'version': 1, 'volume_id': self.record['volume_id'],
                         'node_id': self.record['node_id']} or medium != self.record['medium']):
                raise StorageError('volume_identity_changed', 409)
            for folder in ('staging', 'objects'):
                no_links(self.root / folder)
                if not (self.root / folder).is_dir():
                    raise StorageError('volume_unavailable', 503)
        except (OSError, ValueError):
            raise StorageError('volume_identity_changed', 409) from None

    def _parts(self, relative):
        parts = PurePosixPath(relative).parts
        if (len(parts) != 2 or parts[0] not in ('staging', 'objects') or
                not parts[1] or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-.' for c in parts[1]) or
                parts[1] in ('.', '..')):
            raise StorageError('unsafe_path', 403)
        return parts

    @contextmanager
    def open(self, relative, create=False):
        folder, name = self._parts(relative)
        self.check()
        with directory_guard(self.root):
            self.check()
            target = self.root / folder / name
            no_links(target)
            flags = (os.O_WRONLY | os.O_CREAT | os.O_EXCL) if create else os.O_RDONLY
            if os.name == 'nt':
                import msvcrt
                kernel = ctypes.WinDLL('kernel32', use_last_error=True)
                kernel.CreateFileW.argtypes = [ctypes.c_wchar_p, ctypes.c_ulong, ctypes.c_ulong,
                                              ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p]
                kernel.CreateFileW.restype = ctypes.c_void_p
                kernel.CloseHandle.argtypes = [ctypes.c_void_p]
                handle = kernel.CreateFileW(str(target), 0xC0000000 if create else 0x80000000,
                                            1, None, 1 if create else 3, 0x00200000, None)
                if handle == ctypes.c_void_p(-1).value:
                    error = ctypes.get_last_error()
                    if error in (80, 183):
                        raise FileExistsError()
                    if error in (2, 3):
                        raise FileNotFoundError()
                    if error == 112:
                        raise OSError(28, 'no space')
                    if error == 5:
                        raise PermissionError(13, 'storage permission denied')
                    raise StorageError('file_unavailable', 503)
                fd = msvcrt.open_osfhandle(handle, flags & ~(os.O_CREAT | os.O_EXCL) | os.O_BINARY)
            else:
                # Walk every component by descriptor; no symlink parent traversal.
                parent = os.open(self.root.anchor, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    for part in self.root.parts[1:]:
                        child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
                        os.close(parent)
                        parent = child
                    info = os.fstat(parent)
                    if f'{info.st_dev}:{info.st_ino}' != self.record['medium']:
                        raise StorageError('volume_identity_changed', 409)
                    child = os.open(folder, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
                    os.close(parent)
                    parent = child
                    fd = os.open(name, flags | os.O_NOFOLLOW, 0o600, dir_fd=parent)
                finally:
                    os.close(parent)
            try:
                info = os.fstat(fd)
                if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or
                        getattr(info, 'st_file_attributes', 0) & 0x400):
                    raise StorageError('unsafe_path', 403)
                with os.fdopen(fd, 'wb' if create else 'rb', closefd=False) as stream:
                    yield stream
            finally:
                os.close(fd)

    def remove_staging(self, relative):
        folder, name = self._parts(relative)
        if folder != 'staging':
            raise StorageError('deletion_forbidden', 403)
        self.check()
        with directory_guard(self.root):
            self.check()
            target = self.root / folder / name
            no_links(target)
            if os.name == 'nt':
                target.unlink(missing_ok=True)
            else:
                # Same no-follow walk as open, including the approved root ancestors.
                parent = os.open(self.root.anchor, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    for part in self.root.parts[1:]:
                        child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
                        os.close(parent)
                        parent = child
                    info = os.fstat(parent)
                    if f'{info.st_dev}:{info.st_ino}' != self.record['medium']:
                        raise StorageError('volume_identity_changed', 409)
                    child = os.open(folder, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
                    os.close(parent)
                    parent = child
                    try:
                        os.unlink(name, dir_fd=parent)
                    except FileNotFoundError:
                        pass
                finally:
                    os.close(parent)

    def sync_directory(self, folder):
        self.check()
        if os.name == 'nt':
            return None  # No portable directory-fsync promise on Windows/exFAT.
        with directory_guard(self.root):
            no_links(self.root / folder)
            fd = os.open(self.root / folder, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
        return True

    def allocated_files(self):
        """Charge retained/orphan bodies as well as manifest reservations; bounded audit."""
        self.check()
        result, count = {}, 0
        with directory_guard(self.root):
            self.check()
            for folder in ('staging', 'objects'):
                with os.scandir(self.root / folder) as entries:
                    for entry in entries:
                        count += 1
                        if count > 20256:
                            raise StorageError('volume_inventory_limit', 409)
                        with self.open(folder + '/' + entry.name) as stream:
                            result[folder + '/' + entry.name] = os.fstat(stream.fileno()).st_size
        return result


class VolumeManager:
    def __init__(self, manifest, node_id):
        self.manifest, self.node_id = manifest, node_id

    def register(self, root, kind='directory', quota=64 * 1024**2, reserve=64 * 1024**2):
        if kind not in ('directory', 'internal', 'termux_sd'):
            raise StorageError('adapter_not_implemented', 400)
        if type(quota) is not int or type(reserve) is not int or quota < 1 or reserve < 0:
            raise StorageError('invalid_quota', 400)
        if '..' in Path(root).parts:
            raise StorageError('unsafe_storage_root', 400)
        root = Path(root).absolute()
        no_links(root)
        private = self.manifest.path.parent.resolve()
        source = Path(__file__).resolve().parents[2]
        if root == private or root in private.parents or root == source or source in root.parents:
            raise StorageError('unsafe_storage_root', 400)
        if kind == 'termux_sd' and not any(Path(v['app_dir']) in root.parents and v['app_dir_exists'] for v in _detect_sd_locations()):
            raise StorageError('unapproved_sd_root', 403)
        with self.manifest.connect() as db:
            prior = db.execute('SELECT * FROM volumes WHERE root=?', (str(root),)).fetchone()
        if prior:
            LocalVolume(prior).check()
            if (prior['kind'], prior['quota'], prior['reserve']) != (kind, quota, reserve):
                raise StorageError('volume_configuration_conflict', 409)
            return dict(prior)
        if len(self.records()) >= 8:
            raise StorageError('volume_limit', 409)
        # Existing non-empty user folders are never adopted or inventoried.
        if root.exists() and any(root.iterdir()):
            raise StorageError('storage_root_not_empty', 409)
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        no_links(root)
        volume_id = str(uuid.uuid4())
        save_private(root / '.asc-volume.json',
                     {'version': 1, 'volume_id': volume_id, 'node_id': self.node_id})
        for folder in ('staging', 'objects'):
            (root / folder).mkdir(mode=0o700)
        info = root.stat()
        medium = f'{info.st_dev}:{info.st_ino}'
        with self.manifest.connect() as db:
            db.execute('INSERT INTO volumes VALUES (?,?,?,?,?,?,?)',
                       (volume_id, self.node_id, kind, str(root), medium, quota, reserve))
        return self.get(volume_id).record

    def get(self, volume_id):
        identifier(volume_id)
        with self.manifest.connect() as db:
            row = db.execute('SELECT * FROM volumes WHERE volume_id=?', (volume_id,)).fetchone()
        if row is None:
            raise StorageError('volume_not_found', 404)
        return LocalVolume(row)

    def records(self):
        with self.manifest.connect() as db:
            return [dict(row) for row in db.execute('SELECT * FROM volumes ORDER BY volume_id')]

    def discover(self, private_home):
        """Read-only candidates; only private internal storage can be auto-approved by opt-in setup."""
        return [{'kind': 'internal', 'root': str(Path(private_home) / 'data')}]+[
            {'kind': 'termux_sd', 'root': str(Path(v['app_dir']) / 'asc-storage')} for v in _detect_sd_locations()
            if v['app_dir_exists']]

    def inspect(self, probe=False):
        result = []
        for record in self.records():
            item = {key: record[key] for key in ('volume_id', 'node_id', 'kind', 'quota', 'reserve')}
            item.update(total_bytes=None, free_bytes=None, readable=None, writable=None,
                        fsync_tested=None, state='unknown', checked_at=int(time.time()), last_error=None)
            try:
                volume = LocalVolume(record)
                volume.check()
                item['readable'] = True  # The approved identity marker was actually read.
                space = shutil.disk_usage(volume.root)
                item.update(total_bytes=space.total, free_bytes=space.free, state='online')
                if probe:
                    relative = 'staging/' + str(uuid.uuid4()) + '.probe'
                    data = b'asc-bounded-storage-probe-v1'
                    try:
                        with volume.open(relative, create=True) as stream:
                            stream.write(data); stream.flush(); os.fsync(stream.fileno())
                        with volume.open(relative) as stream:
                            actual = stream.read(len(data) + 1)
                        if hashlib.sha256(actual).digest() != hashlib.sha256(data).digest():
                            raise StorageError('probe_checksum_failed', 503)
                        item.update(readable=True, writable=True, fsync_tested=True)
                    finally:
                        volume.remove_staging(relative)
            except StorageError as exc:
                item.update(state='unavailable', last_error=exc.code)
            except OSError as exc:
                if exc.errno in (13, 30):
                    item.update(writable=False, state='online' if item['readable'] else 'unknown',
                                last_error='write_denied')
                else:
                    item.update(state='unknown', last_error='volume_io_error')
            result.append(item)
        return result
