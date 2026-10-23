"""OS-held foreground locks; no PID-based killing and no boot/service changes."""
from contextlib import contextmanager
import errno
import os


def _lock(fh):
    fh.seek(0)
    if os.name == 'nt':
        import msvcrt
        msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def _unlock(fh):
    fh.seek(0)
    if os.name == 'nt':
        import msvcrt
        msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


@contextmanager
def foreground_lock(home, role):
    path = home / (role + '.lock')
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    with os.fdopen(fd, 'r+b') as fh:
        if path.stat().st_size == 0:
            fh.write(b' ')
            fh.flush()
        try:
            _lock(fh)
        except OSError:
            raise ValueError(f'{role} already running or lifecycle operation in progress; use Ctrl+C in its terminal') from None
        try:
            yield
        finally:
            _unlock(fh)


def running(home, role):
    path = home / (role + '.lock')
    if not path.exists():
        return False
    try:
        fh = path.open('r+b')
    except OSError:
        return None  # Unreadable runtime state is UNKNOWN, never a fabricated running flag.
    with fh:
        try:
            _lock(fh)
        except OSError as exc:
            return True if exc.errno in (errno.EACCES, errno.EAGAIN, errno.EDEADLK) else None
        try:
            _unlock(fh)
        except OSError:
            return None
    return False
