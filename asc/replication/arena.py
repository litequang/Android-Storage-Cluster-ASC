"""In-process fixture capabilities. No CLI/config/environment enable switch exists."""
import os
from pathlib import Path
import platform
import sys
import tempfile
import weakref

from ..catalog.common import CatalogError

_issued=weakref.WeakSet()
_seal=object()


def supported_test_host():
    if (sys.platform=='android' or os.environ.get('ANDROID_ROOT') or
            os.environ.get('PREFIX','').startswith('/data/data/') or
            platform.machine().lower() not in ('x86_64','amd64','x64') or
            platform.system() not in ('Linux','Windows')):
        raise CatalogError('physical_gc_real_device_locked',403)


def temporary_identity(path):
    supported_test_host()
    raw=Path(path).absolute();root=Path(tempfile.gettempdir()).resolve()
    if raw.is_symlink():raise CatalogError('unsafe_gc_test_arena',403)
    resolved=raw.resolve(strict=True)
    if resolved==root or not resolved.is_relative_to(root):raise CatalogError('unsafe_gc_test_arena',403)
    for parent in (raw,*raw.parents):
        if parent==root:break
        if parent.is_symlink() or (parent/'.git').exists():raise CatalogError('unsafe_gc_test_arena',403)
    info=resolved.stat()
    if not resolved.is_dir():raise CatalogError('unsafe_gc_test_arena',403)
    return resolved,(info.st_dev,info.st_ino)


class ControllerTestContext:
    def __init__(self,seal,home):
        if seal is not _seal:raise CatalogError('physical_gc_locked',403)
        self.home,self.identity=temporary_identity(home)
        _issued.add(self)

    def validate(self):
        if self not in _issued or temporary_identity(self.home)!=(self.home,self.identity):
            raise CatalogError('physical_gc_locked',403)


def fixture_controller_context(home):
    """Only synthetic test harnesses call this; normal runtime never constructs it."""
    return ControllerTestContext(_seal,home)


def require_controller(service):
    capability=getattr(service,'gc_test_context',None)
    if type(capability) is not ControllerTestContext:raise CatalogError('physical_gc_locked',403)
    capability.validate()
    return capability
