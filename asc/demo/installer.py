"""Read-only Android preflight; immutable, separately located Demo source install."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from ..identity import ensure_private_home, save_private
from ..probe import inspect
from ..storage.volumes import no_links
from ..runtime import foreground_lock
from .package import verify


def private_path(value, code_prefix=False):
    if '..' in Path(value).parts:
        raise ValueError('private paths must not contain parent traversal')
    path = Path(value).expanduser().absolute()
    no_links(path)
    home = Path.home().resolve()
    source = Path(__file__).resolve().parents[2]
    if (home not in path.parents or path == source or source in path.parents
            or (path in source.parents and not code_prefix) or path == home):
        raise ValueError('choose a dedicated private HOME directory outside source')
    return path


def preflight():
    profile = inspect(sd_write=False)
    missing = [x for x in ('pkg', 'openssl') if shutil.which(x) is None]
    if sys.version_info < (3, 10):
        missing.append('python>=3.10')
    # Dependency readiness only; never execute pkg or install/upgrade packages.
    if 'openssl' not in missing:
        try:
            result = subprocess.run(['openssl', 'version'], capture_output=True, timeout=5)
            if result.returncode:
                missing.append('working-openssl')
        except (OSError, subprocess.TimeoutExpired):
            missing.append('working-openssl')
    allowed = profile['installation_allowed'] and not missing
    return {'format': 1, 'allowed': allowed, 'device_allowed': profile['installation_allowed'],
            'protected': profile['protected'], 'identity': profile['device_identity_status'],
            'sdk': profile['sdk'], 'missing_dependencies': missing,
            'internal_space': profile['internal_app_storage'],
            'sd_candidates': profile['sd_candidates'], 'write_tested': False,
            'runtime_qualification': 'Android NOT TESTED; no runtime readiness claim',
            'manual_dependency_hint': 'Review Termux source; manually install python/openssl if missing. No package changes performed.'}


def guard():
    result = preflight()
    if not result['allowed']:
        raise ValueError('device/dependency preflight denied; run preflight for details; no override')
    return result


LAUNCHER = '''#!/data/data/com.termux/files/usr/bin/sh
# Also runnable as `sh <prefix>/bin/asc-demo ...` in Linux synthetic tests.
set -eu
DEMO_INSTALL_PREFIX=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
export PYTHONDONTWRITEBYTECODE=1
exec python3 -I -B "$DEMO_INSTALL_PREFIX/launch.py" "$DEMO_INSTALL_PREFIX" "$@"
'''
BOOTSTRAP = '''import hashlib, json, os, pathlib, sys
prefix = pathlib.Path(sys.argv.pop(1))
pointer = json.loads((prefix / 'install.json').read_text())
rid = pointer['release_id']
if pointer.get('format') != 1 or len(rid) != 64 or any(c not in '0123456789abcdef' for c in rid):
    raise SystemExit('invalid installed release pointer')
release = prefix / 'releases' / rid
if release.is_symlink():
    raise SystemExit('unsafe release path')
manifest = json.loads((release / 'release.json').read_text())
body = {k: v for k, v in manifest.items() if k != 'release_id'}
encoded = json.dumps(body, sort_keys=True, separators=(',', ':')).encode('utf-8')
if hashlib.sha256(encoded).hexdigest() != rid or manifest['release_id'] != rid:
    raise SystemExit('release manifest checksum mismatch')
actual = set()
for path in release.rglob('*'):
    if path.is_symlink() or (not path.is_file() and not path.is_dir()):
        raise SystemExit('unsafe release entry')
    if path.is_file():
        name = path.relative_to(release).as_posix()
        actual.add(name)
        if name != 'release.json' and hashlib.sha256(path.read_bytes()).hexdigest() != manifest['files'].get(name):
            raise SystemExit('release file checksum mismatch')
if actual != set(manifest['files']) | {'release.json'}:
    raise SystemExit('release inventory mismatch')
sys.path.insert(0, str(release))
os.environ['ASC_DEMO_PREFIX'] = str(prefix)
from asc.demo.cli import main
sys.exit(main())
'''


def install(source, prefix, dry_run=False):
    guard()  # Before ANY filesystem mutation, including prefix/lock creation.
    source = Path(source)
    release = verify(source)
    prefix = private_path(prefix, code_prefix=True)
    if prefix.exists() and not (prefix / 'install.json').exists():
        raise ValueError('existing unmarked installation; preserve for explicit recovery')
    if dry_run:
        return {'dry_run': True, 'release_id': release['release_id'], 'state_changed': False}
    if not prefix.exists():
        ensure_private_home(prefix)
        # Durable marker first: a partial source install is retryable, never identity adoption.
        save_private(prefix / 'install.json', {'format': 1, 'release_id': release['release_id']})
    with foreground_lock(prefix, 'install'):
        pointer = json.loads((prefix / 'install.json').read_text())
        if pointer != {'format': 1, 'release_id': release['release_id']}:
            raise ValueError('different active release; explicit stopped upgrade required')
        releases = prefix / 'releases'
        releases.mkdir(mode=0o700, exist_ok=True)
        target = releases / release['release_id']
        no_links(target)
        if target.exists():
            if verify(target) != release:
                raise ValueError('installed release differs; preserve source for review')
        else:
            with tempfile.TemporaryDirectory(prefix='.stage-', dir=releases) as temporary:
                staging = Path(temporary) / 'release'
                shutil.copytree(source, staging, symlinks=True)
                verify(staging)
                os.rename(staging, target)
        # Never overwrite launcher modifications or existing source.
        (prefix / 'bin').mkdir(mode=0o700, exist_ok=True)
        for path, body in ((prefix / 'bin' / 'asc-demo', LAUNCHER), (prefix / 'launch.py', BOOTSTRAP)):
            no_links(path)
            if path.exists():
                if path.read_text() != body:
                    raise ValueError('existing launcher differs; explicit recovery required')
            else:
                fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o700)
                with os.fdopen(fd, 'w') as stream:
                    stream.write(body)
    return {'installed': True, 'release_id': release['release_id'],
            'capabilities': release['capabilities'], 'private_state_changed': False}
