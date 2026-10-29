"""Test-only child launcher; never packaged or imported by product runtime.

Inject only filesystem-root read-open denial. Private volume OS IO, TLS, engine,
Controller and authorization remain real. ASC_HOME is selected by the fixture
before Core import, so no module-global override or altered product guard is used.
"""
import errno
import os
from pathlib import Path
import runpy
import sys

original_open = os.open

def android_open(path, flags, mode=0o777, *, dir_fd=None):
    if dir_fd is None and os.fspath(path) == '/':
        raise PermissionError(errno.EACCES, 'synthetic root-open denial')
    return original_open(path, flags, mode, dir_fd=dir_fd)

# This wrapper really delegates dir_fd support; preserve its capability metadata.
# Without this, replacing the function object falsely advertises an unsupported OS.
if original_open in os.supports_dir_fd:
    os.supports_dir_fd = set(os.supports_dir_fd) | {android_open}
os.open = android_open
try:
    os.open('/', os.O_RDONLY | os.O_DIRECTORY)
except PermissionError:
    pass
else:
    raise RuntimeError('synthetic root denial must be armed')

target = Path(sys.argv[1])
arguments = sys.argv[2:]
if target.is_dir():
    sys.path.insert(0, str(target))
    sys.argv = ['asc.demo.cli', *arguments]
    runpy.run_module('asc.demo.cli', run_name='__main__')
else:
    # Existing immutable installed bootstrap still validates release inventory,
    # state binding, compatibility/journal and credentials before starting runtime.
    sys.argv = [str(target), *arguments]
    runpy.run_path(str(target), run_name='__main__')
