"""Bounded private operator documents, separate from IPC frame limits and Catalog."""
import json
import os
import stat
import secrets
from contextlib import contextmanager
from ...bridge import private
from ...catalog.common import canonical
from ...server import _unique_object
from ...storage.volumes import no_links

LIMIT = 2 * 1024**2


@contextmanager
def directory(path):
    parent=private.directory(path.parent)
    fd=os.open(parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    def check():
        private.directory(parent)
        expected,current=os.fstat(fd),parent.lstat()
        if (expected.st_dev,expected.st_ino)!=(current.st_dev,current.st_ino):
            raise ValueError('operator directory changed')
    try:
        check();yield fd,check;check()
    finally:os.close(fd)


def read(path):
    with directory(path) as (parent,check):
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,dir_fd=parent)
        try:
            info = os.fstat(fd)
            if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid()
                    or info.st_mode & 0o077 or not 1 <= info.st_size <= LIMIT):
                raise ValueError('unsafe operator document')
            with os.fdopen(os.dup(fd), 'rb') as stream:raw = stream.read(LIMIT+1)
            current = os.stat(path.name,dir_fd=parent,follow_symlinks=False);check()
            if ((info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns) !=
                    (current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns) or len(raw) != info.st_size):
                raise ValueError('operator document changed')
            value = json.loads(raw.decode('utf-8'), object_pairs_hook=_unique_object,
                parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
            if type(value) is not dict:raise ValueError('invalid operator document')
            return value
        finally:os.close(fd)


def write(path, value):
    private.directory(path.parent); no_links(path)
    raw = canonical(value)
    if len(raw) > LIMIT:
        raise ValueError('operator document limit')
    try:
        path.lstat()
    except FileNotFoundError:
        pass
    else:
        read(path)  # Never overwrite corrupt/unsafe existing state.
    with directory(path) as (parent,check):
        temporary='.history-'+secrets.token_hex(16)
        fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=parent)
        try:
            with os.fdopen(fd, 'wb') as stream:
                stream.write(raw); stream.flush(); os.fsync(stream.fileno())
            check();no_links(path)
            os.replace(temporary,path.name,src_dir_fd=parent,dst_dir_fd=parent);os.fsync(parent);check()
        finally:
            try:os.unlink(temporary,dir_fd=parent)  # Only exclusively-created temp in held approved directory.
            except FileNotFoundError:pass
