"""Private owner-only no-link control files. Not a general filesystem API."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sqlite3
import stat
from ..catalog.common import canonical
from ..demo.installer import private_path
from ..storage.volumes import no_links
from .contract import Refused, decode


def directory(path):
    path = private_path(path)
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise Refused('unsafe_control_directory')
    return path


def read(path, limit=8192):
    no_links(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1 or info.st_mode & 0o077 or info.st_size > limit:
            raise Refused('unsafe_control_file')
        raw = os.read(fd, limit + 1)
        current = path.lstat()
        if (info.st_dev, info.st_ino) != (current.st_dev, current.st_ino):
            raise Refused('control_identity_changed')
        return decode(raw)
    finally:
        os.close(fd)


def create(path, value):
    raw = canonical(value)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as out:
        out.write(raw); out.flush(); os.fsync(out.fileno())
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try: os.fsync(fd)
    finally: os.close(fd)


@contextmanager
def journal(root):
    path = root / 'requests.sqlite3'
    no_links(path)
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise Refused('unsafe_control_file')
    db = sqlite3.connect(path, timeout=3)
    try:
        db.execute('PRAGMA synchronous=FULL')
        if db.execute('PRAGMA user_version').fetchone()[0] != 1 or db.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
            raise Refused('journal_incompatible')
        with db: yield db
    finally: db.close()


def initialize_journal(root):
    path = root / 'requests.sqlite3'
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600); os.close(fd)
    db = sqlite3.connect(path)
    try:
        with db:
            db.execute('PRAGMA synchronous=FULL')
            db.execute('CREATE TABLE requests(request_id TEXT PRIMARY KEY,app_id TEXT NOT NULL,intent TEXT NOT NULL,code_sha256 TEXT,state TEXT NOT NULL,result TEXT)')
            db.execute('PRAGMA user_version=1')
    finally: db.close()


def replace(path, value):
    """Replace an already validated owned receipt, never arbitrary state."""
    import tempfile
    if path.exists() or path.is_symlink():read(path)
    fd, name = tempfile.mkstemp(prefix='.receipt-', dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as out:
            out.write(canonical(value));out.flush();os.fsync(out.fileno())
        no_links(path);os.replace(name,path)
        directory_fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        try:os.fsync(directory_fd)
        finally:os.close(directory_fd)
    finally:
        if os.path.exists(name):os.unlink(name)  # Only temporary receipt exclusively made here.
