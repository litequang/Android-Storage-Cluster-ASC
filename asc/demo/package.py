"""Deterministic source-only package and strict installed-tree verification."""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile
from . import VERSION, CAPABILITIES, STATE_FORMATS
from .dashboard.assets import ASSETS


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode('utf-8')


def safe_name(name):
    p = PurePosixPath(name)
    return (isinstance(name, str) and not p.is_absolute() and str(p) == name
            and all(x not in ('.', '..', '') for x in p.parts) and '\\' not in name)


def verify(root):
    root = Path(root)
    if not root.is_dir() or any(p.is_symlink() for p in (root, *root.parents)):
        raise ValueError('unsafe release root')
    manifest_path = root / 'release.json'
    if manifest_path.is_symlink() or manifest_path.stat().st_size > 1024 * 1024:
        raise ValueError('invalid release manifest')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if (not isinstance(manifest, dict) or type(manifest.get('format')) is not int or manifest.get('format') != 1 or not isinstance(manifest.get('files'), dict)
            or not manifest['files'] or not isinstance(manifest.get('capabilities'), list)
            or any(not isinstance(x, str) for x in manifest['capabilities'])
            or not isinstance(manifest.get('state_formats'), dict)):
        raise ValueError('unsupported release manifest')
    body = {k: v for k, v in manifest.items() if k != 'release_id'}
    if manifest.get('release_id') != digest(encoded(body)):
        raise ValueError('release manifest checksum mismatch')
    expected = set(manifest['files']) | {'release.json'}
    actual = set()
    for path in root.rglob('*'):
        if path.is_symlink():
            raise ValueError('release contains a symbolic link')
        if path.is_file():
            name = path.relative_to(root).as_posix()
            actual.add(name)
            if name != 'release.json':
                if name not in manifest['files'] or digest(path.read_bytes()) != manifest['files'][name]:
                    raise ValueError('release file checksum mismatch')
        elif not path.is_dir():
            raise ValueError('release contains a special file')
    if actual != expected or any(not safe_name(n) for n in manifest['files']):
        raise ValueError('release inventory mismatch')
    return manifest


def build(source, output):
    source, output = Path(source), Path(output)
    # Public source allowlist only. Private state, binaries and build outputs never enter.
    names = [p.relative_to(source).as_posix() for p in (source / 'asc').rglob('*.py')]
    names += ['asc/demo/dashboard/web/' + name for name, _ in ASSETS.values()]
    names += ['scripts/demo-alpha.sh', 'docs/DEMO-QUICKSTART.md', 'docs/DEMO-ANDROID-PILOT.md', 'docs/DEMO-ZTE-0.4.1.md', 'docs/PHASE4-QUICK-JOIN.md', 'docs/PHASE4-1-OPERATIONS.md', 'docs/LOCAL-ENGINE-BRIDGE.md', 'docs/LOCAL-ENGINE-THREAT-MODEL.md', 'docs/CORE-QUORUM-DASHBOARD.md', 'docs/ANDROID-APP-CONTRACT.md']
    files = {}
    for name in sorted(names):
        p = source / name
        if not safe_name(name) or p.is_symlink():
            raise ValueError('unsafe package source')
        files[name] = p.read_bytes()
    files['README.md'] = ('# ASC source candidate ' + VERSION + '\n\nNot a public Android release. Read docs/PHASE4-1-OPERATIONS.md first for candidate scope,\ntrust, upgrade and rollback. The following historical Demo guide is reference only;\nits released archive examples do not install this candidate.\n\n').encode() + (source / 'docs/DEMO-QUICKSTART.md').read_bytes()
    body = {'format': 1, 'version': VERSION, 'capabilities': CAPABILITIES,
            'state_formats': STATE_FORMATS,
            'files': {name: digest(data) for name, data in files.items()}}
    manifest = dict(body, release_id=digest(encoded(body)))
    files['release.json'] = encoded(manifest) + b'\n'
    # gzip has a deterministic timestamp through GzipFile, rather than tarfile w:gz.
    import gzip
    with output.open('xb') as raw, gzip.GzipFile(fileobj=raw, mode='wb', mtime=0, filename='') as gz:
        with tarfile.open(fileobj=gz, mode='w') as archive:
            for name, data in sorted(files.items()):
                entry = tarfile.TarInfo('asc-demo-alpha/' + name)
                entry.size, entry.mtime = len(data), 0
                entry.mode = 0o700 if name.endswith('.sh') else 0o600
                archive.addfile(entry, io.BytesIO(data))
    checksum = digest(output.read_bytes())
    output.with_name(output.name + '.sha256').write_text(checksum + '  ' + output.name + '\n')
    return {'version': VERSION, 'release_id': manifest['release_id'], 'sha256': checksum,
            'files': len(files), 'capabilities': CAPABILITIES}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(json.dumps(build(Path(__file__).resolve().parents[2], args.output), indent=2))


if __name__ == '__main__':
    main()
