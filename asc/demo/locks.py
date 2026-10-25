"""Demo coordination files: validate and open without links before any write."""
from contextlib import contextmanager
import os
from pathlib import Path
import stat
from ..runtime import _lock, _unlock
from ..storage.volumes import no_links


def validate_lock(path):
    no_links(path)
    try:
        info = path.lstat()
    except FileNotFoundError:
        return
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > 1:
        raise ValueError('unexpected coordination file; preserve it for review')


@contextmanager
def private_lock(home, role):
    path = Path(home) / (role + '.lock')
    validate_lock(path)
    fd = os.open(path, os.O_RDWR | os.O_CREAT | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    with os.fdopen(fd, 'r+b') as stream:
        opened = os.fstat(stream.fileno())
        validate_lock(path)
        current = path.lstat()
        if ((opened.st_dev, opened.st_ino) != (current.st_dev, current.st_ino)
                or not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1 or opened.st_size > 1):
            raise ValueError('coordination file identity changed')
        if opened.st_size and stream.read(2) != b' ':
            raise ValueError('unexpected coordination contents; preserve for review')
        if not opened.st_size:
            stream.write(b' ')
            stream.flush()
        try:
            _lock(stream)  # Reuse the existing Core OS primitive; no new PID authority.
        except OSError:
            raise ValueError('runtime/lifecycle operation already running; stop its foreground normally') from None
        try:
            yield
        finally:
            _unlock(stream)
