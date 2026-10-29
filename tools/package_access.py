#!/usr/bin/env python3
"""Build or operate an immutable Linux access bundle. Never installs a service."""
import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import runpy
import shutil
import stat
import subprocess
import sys
import tarfile

sys.dont_write_bytecode=True
VERSION='0.1.0-internal'
PREFIX='asc-linux-access/'
MANIFEST='access-release.json'
DOCS=('PHASE5-LINUX-PACKAGE.md','PHASE5-PRIVATE-ACCESS.md','PHASE5-CLOUDFLARE.md',
      'PHASE5-MAINTENANCE.md','SECURITY.md','TROUBLESHOOTING.md','ARCHITECTURE.md','ANDROID-APP-CONTRACT.md')
ASSETS=('index.html','app.js','style.css','manifest.webmanifest','service-worker.js','icon-192.png','icon-512.png')
MODES={'gateway':'asc.access.gateway','edge':'asc.access.cloudflare','maintenance':'asc.access.maintenance'}
MARKERS=('demo.json','controller.json','node.json','manifest.sqlite3','.asc-volume.json',
         'RECOVERY_READ_ONLY.json','failover.json','gateway.json','access-backup.json',
         'backup-complete.json','access-release.json','release.json','install.json','state-binding.json')
MAX_BYTES=16*1024**2


def encoded(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def unique(pairs):
    value={}
    for key,item in pairs:
        if key in value:raise ValueError('duplicate field')
        value[key]=item
    return value
def decode(raw):return json.loads(raw,object_pairs_hook=unique)


def no_links(path):
    for item in (path,*path.parents):
        if item.is_symlink():raise ValueError('link refused')


def read_file(path,limit=MAX_BYTES):
    no_links(path)
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as stream:
        before=os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_nlink!=1 or before.st_size>limit:raise ValueError('unsafe file')
        raw=stream.read(limit+1);after=os.fstat(stream.fileno());current=path.stat()
        if (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns) or (current.st_dev,current.st_ino)!=(before.st_dev,before.st_ino):raise ValueError('file changed')
    if len(raw)>limit:raise ValueError('oversize file')
    return raw


def host_guard(legacy_demo=False):
    if (sys.platform!='linux' or sys.version_info<(3,11) or platform.machine() not in ('x86_64','AMD64')
            or hasattr(sys,'getandroidapilevel') or (not legacy_demo and shutil.which('getprop')) or os.environ.get('ANDROID_ROOT')
            or 'com.termux' in os.environ.get('PREFIX','')):raise ValueError('platform not qualified')


def new_destination(value):
    path=Path(value).expanduser().absolute();no_links(path)
    if '..' in path.parts or Path.home().resolve() not in path.parents or path.exists():raise ValueError('new private HOME path required')
    for ancestor in path.parents:
        if any((ancestor/name).exists() or (ancestor/name).is_symlink() for name in MARKERS):raise ValueError('destination overlaps state or code')
    parent=path.parent.stat()
    if not stat.S_ISDIR(parent.st_mode) or parent.st_uid!=os.getuid() or parent.st_mode&0o077:raise ValueError('private parent required')
    return path


def write_new(path,raw):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as target:target.write(raw);target.flush();os.fsync(target.fileno())


def allowed(name):
    p=PurePosixPath(name)
    return (str(p)==name and not p.is_absolute() and '..' not in p.parts and '\\' not in name
        and (name in ('access.py','README.md','requirements-cloudflare.txt') or name in {'docs/'+n for n in DOCS}
             or name.startswith('asc/') and name.endswith('.py')
             or name in {'asc/demo/dashboard/web/'+n for n in ASSETS}))


def validate_manifest(value):
    if (type(value) is not dict or set(value)!={'format','kind','version','profile_formats','maintenance_format','files','release_id'}
        or type(value['format']) is not int or value['format']!=1 or value['kind']!='asc-linux-access'
        or type(value['version']) is not str or not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+-internal',value['version'])
        or encoded(value['profile_formats'])!=b'[1,2]' or type(value['maintenance_format']) is not int or value['maintenance_format']!=1
        or type(value['files']) is not dict or not 10<=len(value['files'])<=256):raise ValueError('unsupported bundle')
    required={'access.py','README.md','requirements-cloudflare.txt',*('docs/'+n for n in DOCS),
        'asc/access/gateway.py','asc/access/cloudflare.py','asc/access/maintenance.py'}
    if not required<=set(value['files']):raise ValueError('incomplete bundle')
    for name,sha in value['files'].items():
        if not allowed(name) or type(sha) is not str or not re.fullmatch('[0-9a-f]{64}',sha):raise ValueError('unsafe manifest entry')
    if value['release_id']!=digest(encoded({k:v for k,v in value.items() if k!='release_id'})):raise ValueError('manifest mismatch')
    return value


def verify(root):
    root=Path(root);no_links(root)
    info=root.stat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid!=os.getuid() or info.st_mode&0o022:raise ValueError('unsafe code directory')
    value=validate_manifest(decode(read_file(root/MANIFEST,1024**2)))
    actual=set()
    for path in root.rglob('*'):
        no_links(path)
        if path.is_dir():continue
        name=path.relative_to(root).as_posix();actual.add(name)
        if name!=MANIFEST and (name not in value['files'] or digest(read_file(path))!=value['files'][name]):raise ValueError('bundle contents changed')
    if actual!=set(value['files'])|{MANIFEST}:raise ValueError('bundle inventory differs')
    return value


def build(source,output,version=VERSION):
    source=Path(source).absolute();output=Path(output);checksum=output.with_name(output.name+'.sha256')
    no_links(output)
    if any(any((parent/name).exists() or (parent/name).is_symlink() for name in MARKERS)
           for parent in output.absolute().parents):raise ValueError('build output overlaps state or code')
    if output.exists() or checksum.exists():raise ValueError('new output required')
    names=[p.relative_to(source).as_posix() for p in (source/'asc').rglob('*.py')]
    names+=['asc/demo/dashboard/web/'+n for n in ASSETS]+['requirements-cloudflare.txt']+['docs/'+n for n in DOCS]
    files={n:read_file(source/n) for n in names}
    files['access.py']=read_file(source/'tools/package_access.py')
    files['README.md']=files['docs/PHASE5-LINUX-PACKAGE.md']
    body=dict(format=1,kind='asc-linux-access',version=version,profile_formats=[1,2],maintenance_format=1,
              files={n:digest(raw) for n,raw in sorted(files.items())})
    manifest=dict(body,release_id=digest(encoded(body)));validate_manifest(manifest)
    files[MANIFEST]=encoded(manifest)+b'\n'
    with output.open('xb') as raw,gzip.GzipFile(fileobj=raw,mode='wb',mtime=0,filename='') as zipped:
        with tarfile.open(fileobj=zipped,mode='w') as archive:
            for name,data in sorted(files.items()):
                entry=tarfile.TarInfo(PREFIX+name);entry.size=len(data);entry.mode=0o600;entry.mtime=0
                archive.addfile(entry,io.BytesIO(data))
    sha=digest(read_file(output));write_new(checksum,(sha+'  '+output.name+'\n').encode())
    return dict(version=version,release_id=manifest['release_id'],sha256=sha,files=len(files),scope='Linux internal test bundle')


def unpack(archive,destination,expected):
    host_guard();destination=new_destination(destination)
    raw=read_file(Path(archive));
    if type(expected) is not str or not re.fullmatch('[0-9a-f]{64}',expected) or digest(raw)!=expected:raise ValueError('archive checksum mismatch')
    entries={};total=0
    with gzip.GzipFile(fileobj=io.BytesIO(raw),mode='rb') as compressed:tar_raw=compressed.read(MAX_BYTES+1)
    if len(tar_raw)>MAX_BYTES:raise ValueError('expanded archive too large')
    with tarfile.open(fileobj=io.BytesIO(tar_raw),mode='r:') as saved:
        for entry in saved:
            if not entry.isfile() or entry.sparse is not None or not entry.name.startswith(PREFIX):raise ValueError('archive type refused')
            name=entry.name[len(PREFIX):];total+=entry.size
            if name in entries or len(entries)>=257 or total>MAX_BYTES or entry.size<0 or entry.mode!=0o600 or (name!=MANIFEST and not allowed(name)):raise ValueError('archive entry refused')
            entries[name]=saved.extractfile(entry).read()
    manifest=validate_manifest(decode(entries.get(MANIFEST,b'')))
    if set(entries)!=set(manifest['files'])|{MANIFEST} or any(digest(entries[n])!=sha for n,sha in manifest['files'].items()):raise ValueError('archive manifest mismatch')
    destination.mkdir(mode=0o700)
    for name,data in sorted(entries.items(),key=lambda x:x[0]==MANIFEST):
        target=destination/name;target.parent.mkdir(mode=0o700,parents=True,exist_ok=True);write_new(target,data)
    verify(destination)
    for folder in sorted([p for p in destination.rglob('*') if p.is_dir()]+[destination,destination.parent],key=lambda p:len(p.parts),reverse=True):
        fd=os.open(folder,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        try:os.fsync(fd)
        finally:os.close(fd)
    return dict(unpacked=True,release_id=manifest['release_id'],identity_created=False,runtime_started=False)


def prepare_env(root,destination,with_edge=False,pip_python=None,wheelhouse=None):
    host_guard();release=verify(root);destination=new_destination(destination)
    subprocess.run([sys.executable,'-I','-B','-m','venv','--without-pip',str(destination)],check=True,capture_output=True,timeout=60)
    python=destination/'bin/python'
    if with_edge:
        command=[str(pip_python or sys.executable),'-m','pip','--python',str(python),'install','--require-hashes',
                 '--no-compile','-r',str(Path(root)/'requirements-cloudflare.txt')]
        if wheelhouse:command+=['--no-index','--find-links',str(wheelhouse)]
        subprocess.run(command,check=True,capture_output=True,timeout=180)
        subprocess.run([str(pip_python or sys.executable),'-m','pip','--python',str(python),'check'],check=True,capture_output=True,timeout=30)
    receipt=dict(format=1,release_id=release['release_id'],edge_dependencies=bool(with_edge),python=list(sys.version_info[:3]))
    write_new(destination/'access-env.json',encoded(receipt)+b'\n')
    return dict(prepared=True,release_id=release['release_id'],edge_dependencies=bool(with_edge),runtime_started=False)


def runtime(root,mode,arguments):
    # Canonical maintenance retains its existing protected/unknown-device Demo
    # guard (including Linux synthetic profiles); gateway/edge retain theirs.
    # Never remove Android/Termux refusal or invent a device-profile override.
    host_guard(legacy_demo=mode=='maintenance');release=verify(root)
    if sys.prefix==sys.base_prefix:raise ValueError('prepared private environment required')
    receipt_path=Path(sys.prefix)/'access-env.json';receipt=decode(read_file(receipt_path,8192))
    if receipt_path.stat().st_uid!=os.getuid() or receipt_path.stat().st_mode&0o077:raise ValueError('unsafe environment receipt')
    if (set(receipt)!={'format','release_id','edge_dependencies','python'} or type(receipt['format']) is not int or receipt['format']!=1
            or receipt['release_id']!=release['release_id'] or type(receipt['edge_dependencies']) is not bool
            or receipt['python']!=list(sys.version_info[:3]) or mode=='edge' and not receipt['edge_dependencies']):raise ValueError('environment/release mismatch')
    if mode=='edge':
        from importlib.metadata import version
        pins=dict(re.findall(r'^([A-Za-z][A-Za-z0-9_-]*)==([^\s]+)',read_file(root/'requirements-cloudflare.txt').decode(),re.M))
        if set(pins)!={'PyJWT','cryptography','cffi','pycparser'} or any(version(name)!=pin for name,pin in pins.items()):raise ValueError('edge dependency mismatch')
    sys.path.insert(0,str(root));sys.argv=[MODES[mode],*arguments]
    runpy.run_module(MODES[mode],run_name='__main__')


def main(argv=None):
    args=list(sys.argv[1:] if argv is None else argv);root=Path(__file__).absolute().parent
    try:
        if args and args[0] in MODES:return runtime(root,args[0],args[1:])
        parser=argparse.ArgumentParser(description=__doc__);commands=parser.add_subparsers(dest='command',required=True)
        p=commands.add_parser('build');p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--version',default=VERSION)
        commands.add_parser('verify')
        p=commands.add_parser('unpack');p.add_argument('--archive',type=Path,required=True);p.add_argument('--destination',type=Path,required=True);p.add_argument('--sha256',required=True)
        p=commands.add_parser('prepare-env');p.add_argument('--destination',type=Path,required=True);p.add_argument('--with-edge',action='store_true');p.add_argument('--pip-python',type=Path);p.add_argument('--wheelhouse',type=Path)
        a=parser.parse_args(args)
        if a.command=='build':reply=build(a.source,a.output,a.version)
        elif a.command=='verify':
            release=verify(root);reply=dict(verified=True,release_id=release['release_id'],version=release['version'])
        elif a.command=='unpack':reply=unpack(a.archive,a.destination,a.sha256)
        else:reply=prepare_env(root,a.destination,a.with_edge,a.pip_python,a.wheelhouse)
        print(json.dumps(reply,sort_keys=True));return 0
    except (ValueError,OSError,KeyError,TypeError,ImportError,subprocess.SubprocessError,tarfile.TarError):
        print('{"error":"access_bundle_refused","runtime_started":false}');return 1


if __name__=='__main__':raise SystemExit(main())
