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
POSIX_FD_SUPPORTED = (os.open in os.supports_dir_fd and os.stat in os.supports_dir_fd
                      and os.stat in os.supports_follow_symlinks and os.unlink in os.supports_dir_fd
                      and os.scandir in os.supports_fd and getattr(os, 'statvfs', None) in os.supports_fd)


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


class _PosixAccess:
    """Pin an approved root directly: ancestors need stat/search, never read-open.

    Absolute lookup is used ONLY for the approved directory. Its descriptor must
    match persisted dev/inode before reading anything below it. Every subsequent
    lookup is no-follow and relative to pinned descriptors. Snapshot/recheck all
    namespace bindings before and after IO; a renamed root/parent/folder/marker
    cannot be silently adopted. This is not a sandbox against the owning OS user.
    """
    def __init__(self, volume):
        self.volume, self.fds, self.folders = volume, [], {}

    @staticmethod
    def identity(info):
        return info.st_dev, info.st_ino

    @staticmethod
    def regular(info):
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise StorageError('unsafe_path', 403)

    @staticmethod
    def marker_identity(info):
        return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns, info.st_nlink)

    def opened(self, path, flags, **kwargs):
        fd = os.open(path, flags, **kwargs)
        self.fds.append(fd)
        return fd

    def __enter__(self):
        try:
            if (not POSIX_FD_SUPPORTED or not getattr(os, 'O_NOFOLLOW', 0) or not getattr(os, 'O_DIRECTORY', 0)
                    or not self.volume.root.is_absolute() or '..' in self.volume.root.parts):
                raise StorageError('safe_volume_access_unavailable', 503)
            root = self.volume.root
            self.paths = {}
            for path in [*reversed(root.parents), root, root / 'staging', root / 'objects']:
                try:
                    info = path.lstat()
                except FileNotFoundError:
                    raise StorageError('volume_unavailable', 503) from None
                if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
                    raise StorageError('unsafe_path', 403)
                self.paths[path] = self.identity(info)
            flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
            self.root = self.opened(root, flags)
            info = os.fstat(self.root)
            if f'{info.st_dev}:{info.st_ino}' != self.volume.record['medium']:
                raise StorageError('volume_identity_changed', 409)
            for folder in ('staging', 'objects'):
                fd = self.opened(folder, flags, dir_fd=self.root)
                if self.identity(os.fstat(fd)) != self.paths[root / folder]:
                    raise StorageError('volume_identity_changed', 409)
                self.folders[folder] = fd
            marker = root / '.asc-volume.json'
            no_links(marker)
            try:
                before = marker.lstat()
            except FileNotFoundError:
                raise StorageError('volume_identity_changed', 409) from None
            self.regular(before)
            if before.st_size > 4096:
                raise StorageError('volume_identity_changed', 409)
            try:
                self.marker = self.opened('.asc-volume.json', os.O_RDONLY | os.O_NOFOLLOW | getattr(os, 'O_NONBLOCK', 0), dir_fd=self.root)
            except FileNotFoundError:
                raise StorageError('volume_identity_changed', 409) from None
            info = os.fstat(self.marker)
            self.regular(info)
            self.marker_info = self.marker_identity(info)
            if self.marker_info != self.marker_identity(before):
                raise StorageError('volume_identity_changed', 409)
            raw = bytearray()
            while len(raw) <= 4096:
                chunk = os.read(self.marker, 4097 - len(raw))
                if not chunk:
                    break
                raw.extend(chunk)
            try:
                data = json.loads(raw.decode('utf-8'))
            except (ValueError, UnicodeError):
                raise StorageError('volume_identity_changed', 409) from None
            expected = {'version': 1, 'volume_id': self.volume.record['volume_id'], 'node_id': self.volume.record['node_id']}
            if len(raw) > 4096 or not isinstance(data, dict) or type(data.get('version')) is not int or data != expected:
                raise StorageError('volume_identity_changed', 409)
            self.validate()
            return self
        except FileNotFoundError:
            self.close()
            raise StorageError('volume_unavailable', 503) from None
        except BaseException:
            self.close()
            raise

    def validate(self):
        for path, expected in self.paths.items():
            try:
                info = path.lstat()
            except FileNotFoundError:
                raise StorageError('volume_identity_changed', 409) from None
            if not stat.S_ISDIR(info.st_mode) or self.identity(info) != expected:
                raise StorageError('volume_identity_changed', 409)
        try:
            info = os.stat('.asc-volume.json', dir_fd=self.root, follow_symlinks=False)
        except FileNotFoundError:
            raise StorageError('volume_identity_changed', 409) from None
        if (not stat.S_ISREG(info.st_mode) or self.marker_identity(info) != self.marker_info
                or self.marker_identity(os.fstat(self.marker)) != self.marker_info):
            raise StorageError('volume_identity_changed', 409)
        for name, fd in self.folders.items():
            try:
                info = os.stat(name, dir_fd=self.root, follow_symlinks=False)
            except FileNotFoundError:
                raise StorageError('volume_identity_changed', 409) from None
            if not stat.S_ISDIR(info.st_mode) or self.identity(info) != self.identity(os.fstat(fd)):
                raise StorageError('volume_identity_changed', 409)

    def close(self):
        for fd in reversed(self.fds):
            os.close(fd)
        self.fds.clear()

    def __exit__(self, kind, *_):
        try:
            if kind is None:
                self.validate()
        finally:
            self.close()


class LocalVolume:
    """Filesystem adapter seam; SAF must implement equivalent semantics, not raw paths."""
    def __init__(self, record):
        self.record = dict(record)
        self.root = Path(record['root'])

    def check(self):
        if os.name != 'nt':
            with _PosixAccess(self):
                return
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
        if not isinstance(relative, str):
            raise StorageError('unsafe_path', 403)
        parts = PurePosixPath(relative).parts
        if (len(parts) != 2 or '/'.join(parts) != relative or parts[0] not in ('staging', 'objects') or
                not parts[1] or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-.' for c in parts[1]) or
                parts[1] in ('.', '..')):
            raise StorageError('unsafe_path', 403)
        return parts

    @contextmanager
    def open(self, relative, create=False):
        folder, name = self._parts(relative)
        if os.name != 'nt':
            with _PosixAccess(self) as access:
                flags = (os.O_WRONLY | os.O_CREAT | os.O_EXCL) if create else os.O_RDONLY
                fd = os.open(name, flags | os.O_NOFOLLOW | getattr(os, 'O_NONBLOCK', 0), 0o600, dir_fd=access.folders[folder])
                try:
                    info = os.fstat(fd)
                    access.regular(info)
                    current = os.stat(name, dir_fd=access.folders[folder], follow_symlinks=False)
                    if access.identity(current) != access.identity(info):
                        raise StorageError('unsafe_path', 403)
                    access.validate()
                    with os.fdopen(fd, 'wb' if create else 'rb', closefd=False) as stream:
                        yield stream
                finally:
                    os.close(fd)
            return
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
            try:
                info = os.fstat(fd)
                if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or
                        getattr(info, 'st_file_attributes', 0) & 0x400):
                    raise StorageError('unsafe_path', 403)
                with os.fdopen(fd, 'wb' if create else 'rb', closefd=False) as stream:
                    yield stream
            finally:
                os.close(fd)

    def remove_staging(self, relative, *, expected_identity=None):
        folder, name = self._parts(relative)
        if folder != 'staging':
            raise StorageError('deletion_forbidden', 403)
        if os.name != 'nt':
            with _PosixAccess(self) as access:
                parent = access.folders['staging']
                try:
                    info = os.stat(name, dir_fd=parent, follow_symlinks=False)
                except FileNotFoundError:
                    return
                access.regular(info)
                if expected_identity is not None and access.identity(info) != expected_identity:
                    raise StorageError('unsafe_path', 403)
                access.validate()
                current = os.stat(name, dir_fd=parent, follow_symlinks=False)
                if access.identity(current) != access.identity(info) or current.st_nlink != 1:
                    raise StorageError('unsafe_path', 403)
                os.unlink(name, dir_fd=parent)
                os.fsync(parent)
            return
        self.check()
        with directory_guard(self.root):
            self.check()
            target = self.root / folder / name
            no_links(target)
            if expected_identity is not None and target.exists():
                info = target.lstat()
                _PosixAccess.regular(info)
                if _PosixAccess.identity(info) != expected_identity:
                    raise StorageError('unsafe_path', 403)
            target.unlink(missing_ok=True)

    @staticmethod
    def _folder(folder):
        if folder not in ('staging', 'objects'):
            raise StorageError('unsafe_path', 403)
        return folder

    def sync_directory(self, folder):
        self._folder(folder)
        if os.name != 'nt':
            with _PosixAccess(self) as access:
                os.fsync(access.folders[folder])
            return True
        self.check()
        return None  # No portable directory-fsync promise on Windows/exFAT.

    @contextmanager
    def entries(self, folder):
        self._folder(folder)
        if os.name != 'nt':
            with _PosixAccess(self) as access:
                with os.scandir(access.folders[folder]) as entries:
                    yield entries
            return
        self.check()
        with directory_guard(self.root), os.scandir(self.root / folder) as entries:
            yield entries

    def disk_usage(self):
        if os.name != 'nt':
            with _PosixAccess(self) as access:
                return shutil.disk_usage(access.root)  # statvfs(fd), no /proc dependency.
        self.check()
        with directory_guard(self.root):
            return shutil.disk_usage(self.root)

    def allocated_files(self):
        """Charge retained/orphan bodies as well as manifest reservations; bounded audit."""
        self.check()
        result, count = {}, 0
        with directory_guard(self.root):
            self.check()
            for folder in ('staging', 'objects'):
                with self.entries(folder) as entries:
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

    def inspect(self, probe=False, volume_id=None):
        result = []
        for record in self.records():
            if volume_id is not None and record['volume_id']!=volume_id:
                continue
            item = {key: record[key] for key in ('volume_id', 'node_id', 'kind', 'quota', 'reserve')}
            item.update(total_bytes=None, free_bytes=None, readable=None, writable=None,
                        fsync_tested=None, state='unknown', checked_at=int(time.time()), last_error=None)
            try:
                volume = LocalVolume(record)
                volume.check()
                item['readable'] = True  # The approved identity marker was actually read.
                space = volume.disk_usage()
                item.update(total_bytes=space.total, free_bytes=space.free, state='online')
                if probe:
                    relative = 'staging/' + str(uuid.uuid4()) + '.probe'
                    data = b'asc-bounded-storage-probe-v1'
                    created = None
                    try:
                        with volume.open(relative, create=True) as stream:
                            created = _PosixAccess.identity(os.fstat(stream.fileno()))
                            stream.write(data); stream.flush(); os.fsync(stream.fileno())
                        with volume.open(relative) as stream:
                            actual = stream.read(len(data) + 1)
                        if hashlib.sha256(actual).digest() != hashlib.sha256(data).digest():
                            raise StorageError('probe_checksum_failed', 503)
                        volume.sync_directory('staging')
                    finally:
                        if created is not None:
                            volume.remove_staging(relative, expected_identity=created)
                    item.update(readable=True, writable=True, fsync_tested=True)
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
