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
    try:resolved=raw.resolve(strict=True)
    except OSError:raise CatalogError('unsafe_gc_test_arena',403) from None
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


class NodeTestVolume:
    def __init__(self,seal,engine,volume,binding):
        if seal is not _seal:raise CatalogError('physical_gc_locked',403)
        self.home,self.home_identity=temporary_identity(engine.home)
        self.root,self.root_identity=temporary_identity(volume.root)
        self.record=dict(volume.record);self.binding=dict(binding)
        _issued.add(self)

    def validate(self,engine):
        if type(self) is not NodeTestVolume or self not in _issued:raise CatalogError('physical_gc_locked',403)
        if platform.system()!='Linux' or os.name!='posix':raise CatalogError('physical_gc_platform_locked',403)
        if temporary_identity(self.home)!=(self.home,self.home_identity) or temporary_identity(self.root)!=(self.root,self.root_identity):
            raise CatalogError('unsafe_gc_test_arena',403)
        volume=engine.volumes.get(self.record['volume_id']);volume.check()
        for folder in ('objects','staging'):
            info=(volume.root/folder).stat()
            if [info.st_dev,info.st_ino]!=self.binding[folder+'_identity']:
                raise CatalogError('unsafe_gc_test_arena',403)
        if volume.record!=self.record or engine.node_id!=self.binding['node_id']:
            raise CatalogError('unsafe_gc_test_arena',403)
        return volume


def fixture_node_capability(engine,volume_id):
    """Mint only before first data; restart needs the exact retained arena binding."""
    import json
    import uuid
    from ..identity import save_private
    from ..storage.volumes import no_links
    if platform.system()!='Linux' or os.name!='posix':raise CatalogError('physical_gc_platform_locked',403)
    temporary_identity(engine.home)
    volume=engine.volumes.get(volume_id);volume.check();temporary_identity(volume.root)
    if volume.record['kind']!='directory':raise CatalogError('physical_gc_locked',403)
    path=engine.home/('gc-test-volume-'+volume_id+'.json');no_links(path)
    base={'schema':1,'node_id':engine.node_id,'volume_id':volume_id,
          'root':str(volume.root),'medium':volume.record['medium'],
          **{folder+'_identity':[(volume.root/folder).stat().st_dev,(volume.root/folder).stat().st_ino] for folder in ('objects','staging')}}
    if path.exists():
        if path.stat().st_size>4096:raise CatalogError('unsafe_gc_test_arena',403)
        binding=json.loads(path.read_text())
        if set(binding)!={*base,'arena_id'} or any(binding[k]!=v for k,v in base.items()):raise CatalogError('unsafe_gc_test_arena',403)
        from ..catalog.common import identifier
        identifier(binding['arena_id'])
    else:
        with engine.manifest.connect() as db:
            if (db.execute('SELECT COUNT(*) FROM files WHERE volume_id=?',(volume_id,)).fetchone()[0] or
                    db.execute('SELECT COUNT(*) FROM uploads WHERE volume_id=?',(volume_id,)).fetchone()[0] or
                    any((volume.root/'objects').iterdir()) or any((volume.root/'staging').iterdir())):
                raise CatalogError('gc_existing_volume_not_adopted',403)
        binding={**base,'arena_id':str(uuid.uuid4())};save_private(path,binding)
    return NodeTestVolume(_seal,engine,volume,binding)
