"""Private POSIX local adapter: pinned descriptors, no-follow, one store owner.

Local filesystems with dir_fd, flock, hardlinks and directory fsync only. A mounted
NAS/USB needs qualification; this is not an object-store or hostile-OS sandbox.
"""
from contextlib import contextmanager
import os
from pathlib import Path
import re
import stat
from .format import fail, decode


def identity(s):
    return s.st_dev, s.st_ino


def component(name):
    if not isinstance(name, str) or name in ('.','..') or not re.fullmatch(r'[A-Za-z0-9_.-]{1,100}', name):
        fail('unsafe_external_path', 400)
    return name


def private(s, directory=False, links=1):
    if (not (stat.S_ISDIR(s.st_mode) if directory else stat.S_ISREG(s.st_mode)) or
            s.st_uid != os.getuid() or s.st_mode & 0o077 or
            not directory and s.st_nlink != links):
        fail('unsafe_external_path', 403)


class Tree:
    """All callers are under the top-level Store ownership lock."""
    def __init__(self, path, parent=None, name=None, create=False):
        if os.name != 'posix' or not getattr(os, 'O_NOFOLLOW', 0) or not getattr(os, 'O_DIRECTORY', 0):
            fail('external_filesystem_unsupported', 503)
        self.path = Path(path)
        self.parent, self.name = parent, name
        if parent:
            parent.check(); component(name)
            if create:
                os.mkdir(name, 0o700, dir_fd=parent.fd); os.fsync(parent.fd)
            self.fd = os.open(name, os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW, dir_fd=parent.fd)
        else:
            if not self.path.is_absolute() or '..' in self.path.parts:
                fail('unsafe_external_path', 400)
            self.ancestors = [(p, identity(p.lstat())) for p in reversed([self.path, *self.path.parents])]
            if any(stat.S_ISLNK(p.lstat().st_mode) or (p/'.git').exists() for p,_ in self.ancestors):
                fail('unsafe_external_path', 403)
            self.fd = os.open(self.path, os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        self.bound = identity(os.fstat(self.fd))
        try:
            private(os.fstat(self.fd), True); self.check()
        except BaseException:
            os.close(self.fd); raise

    def close(self):
        os.close(self.fd)

    def __enter__(self): return self
    def __exit__(self, *exc): self.close()

    def check(self):
        if self.parent:
            self.parent.check()
            observed = os.stat(self.name, dir_fd=self.parent.fd, follow_symlinks=False)
        else:
            for p,bound in self.ancestors:
                current = p.lstat()
                if not stat.S_ISDIR(current.st_mode) or identity(current) != bound:
                    fail('external_directory_changed', 409)
            observed = self.path.lstat()
        private(observed, True)
        if identity(observed) != self.bound or identity(os.fstat(self.fd)) != self.bound:
            fail('external_directory_changed', 409)

    def sub(self, name, create=False):
        return Tree(self.path/name, self, name, create)

    def names(self):
        self.check()
        names=[]
        with os.scandir(self.fd) as entries:
            for entry in entries:
                if len(names)>=4096:fail('external_entry_limit',429)
                names.append(entry.name)
        self.check(); return sorted(names)

    def exists(self, name):
        self.check(); component(name)
        try: os.stat(name, dir_fd=self.fd, follow_symlinks=False); return True
        except FileNotFoundError: return False

    @contextmanager
    def file(self, name, flags=os.O_RDONLY, links=1):
        self.check(); component(name)
        fd = os.open(name, flags|os.O_NOFOLLOW|os.O_NONBLOCK, 0o600, dir_fd=self.fd)
        try:
            before = os.fstat(fd); private(before, links=links)
            if identity(os.stat(name, dir_fd=self.fd, follow_symlinks=False)) != identity(before):
                fail('external_file_changed', 409)
            with os.fdopen(fd, 'r+b' if flags & (os.O_WRONLY|os.O_RDWR) else 'rb', closefd=False) as stream:
                yield stream
            self.check()
            after = os.stat(name, dir_fd=self.fd, follow_symlinks=False)
            private(after, links=links)
            if identity(after) != identity(before): fail('external_file_changed', 409)
        finally:
            os.close(fd)

    def read(self, name, limit):
        with self.file(name) as f:
            before=os.fstat(f.fileno()); raw=f.read(limit+1); after=os.fstat(f.fileno())
            if (before.st_size,before.st_mtime_ns,before.st_ctime_ns) != (after.st_size,after.st_mtime_ns,after.st_ctime_ns):
                fail('external_file_changed', 409)
            if len(raw)>limit: fail('external_metadata_limit', 413)
            return raw

    def write_new(self, name, raw):
        with self.file(name, os.O_RDWR|os.O_CREAT|os.O_EXCL) as f:
            f.write(raw); f.flush(); os.fsync(f.fileno())
        self.check(); os.fsync(self.fd)

    def unlink_partial(self, name, expected):
        self.check(); current=os.stat(name,dir_fd=self.fd,follow_symlinks=False)
        private(current)
        if identity(current)!=expected: fail('external_file_changed',409)
        os.unlink(name,dir_fd=self.fd); os.fsync(self.fd); self.check()

    def publish(self, part, final):
        """No-replace hardlink then exact temporary unlink; crash replay below."""
        self.check()
        with self.file(part) as f: bound=identity(os.fstat(f.fileno()))
        os.link(part, final, src_dir_fd=self.fd, dst_dir_fd=self.fd, follow_symlinks=False)
        os.fsync(self.fd)
        self.finish_link(part, final, bound)

    def finish_link(self, part, final, bound=None):
        self.check()
        a=os.stat(part,dir_fd=self.fd,follow_symlinks=False)
        b=os.stat(final,dir_fd=self.fd,follow_symlinks=False)
        private(a,links=2);private(b,links=2)
        if identity(a)!=identity(b) or bound is not None and identity(a)!=bound:
            fail('external_file_changed',409)
        os.unlink(part,dir_fd=self.fd);os.fsync(self.fd);self.check()


def separate(destination, source_roots):
    dest=Path(destination)
    if not source_roots: fail('external_source_roots_required',400)
    for root in source_roots:
        root=Path(root)
        if not root.is_absolute() or not root.exists() or root.resolve()!=root:
            fail('unsafe_external_source_root',400)
        if dest==root or root in dest.parents or dest in root.parents:
            fail('external_destination_overlaps_source',403)


class LocalStore:
    def __init__(self, path): self.path=Path(path)

    @classmethod
    def initialize(cls, path, source_roots):
        separate(path, source_roots)
        with Tree(path) as root:
            if root.names(): fail('external_destination_not_empty',409)
            from ..catalog.common import canonical, uid
            root.write_new('store.json',canonical({'format':1,'store_id':uid(),'kind':'asc-private-external-store'}))
            for name in ('working','completed'):
                with root.sub(name,True): pass
        return cls(path)

    @contextmanager
    def open(self, source_roots=None):
        if source_roots is not None: separate(self.path,source_roots)
        with Tree(self.path) as root:
            marker=decode(root.read('store.json',4096),4096)
            from ..catalog.common import identifier
            if set(marker)!={'format','store_id','kind'} or type(marker['format']) is not int or marker['format']!=1 or marker['kind']!='asc-private-external-store':
                fail('external_store_invalid',409)
            identifier(marker['store_id'])
            try: root.write_new('owner.lock',b'')
            except FileExistsError: pass
            with root.file('owner.lock',os.O_RDWR) as lock:
                import fcntl
                try: fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError: fail('external_store_busy',429)
                try: yield root
                finally: fcntl.flock(lock.fileno(),fcntl.LOCK_UN)
