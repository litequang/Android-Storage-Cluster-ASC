#!/usr/bin/env python3
"""Check native debug APK inventory and canonical Core build inputs (not a binary SAST)."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import zipfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('apk', type=Path)
    parser.add_argument('--sdk', type=Path, required=True)
    parser.add_argument('--version-code', type=int, default=2)
    parser.add_argument('--version-name', default='0.2.0-foundation')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    canonical = root / 'asc'
    generated = root / 'android/app/build/generated/asc-python/asc'
    expected = {str(p.relative_to(canonical)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in canonical.rglob('*.py')}
    actual = {str(p.relative_to(generated)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in generated.rglob('*.py')}
    if actual != expected:
        raise ValueError('generated Core inputs differ from canonical checkout')
    findings = []
    test_names = tuple(p.stem.encode() for folder in ('androidTest', 'test')
                       for p in (root / 'android/app/src' / folder).rglob('*.kt'))
    def inspect(name, data):
        if re.search(r'(^|/)(node\.json|controller\.json|storage\.json|[^/]*\.(sqlite3|key|keystore|jks|p12))$', name):
            findings.append(name + ': private-state path')
        if re.search(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----\s+[A-Za-z0-9+/=\r\n]{64,}', data):
            findings.append(name + ': private-key payload')
        if re.search(rb'(gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|AKIA[A-Z0-9]{16})', data):
            findings.append(name + ': credential pattern')
        if name.endswith('.dex') and any(n in data for n in test_names + (b'ForeignCallerTest',)):
            findings.append(name + ': test-only class')
    with zipfile.ZipFile(args.apk) as apk:
        names = apk.namelist()
        for name in names:
            data = apk.read(name)
            inspect(name, data)
            if name.endswith('.imy'):
                with zipfile.ZipFile(io.BytesIO(data)) as inner:
                    for entry in inner.namelist():
                        inspect(name + '/' + entry, inner.read(entry))
        with zipfile.ZipFile(io.BytesIO(apk.read('assets/chaquopy/app.imy'))) as app:
            modules = {n[:-1] for n in app.namelist() if n.startswith('asc/') and n.endswith('.pyc')}
            if modules != {'asc/' + p for p in expected}:
                findings.append('canonical packaged module inventory mismatch')
        abis = sorted({n.split('/')[1] for n in names if n.startswith('lib/')})
        if abis != ['arm64-v8a', 'x86_64']:
            findings.append('unexpected ABI inventory')
    if findings:
        raise ValueError('; '.join(findings))
    build_tools = args.sdk / 'build-tools/35.0.0'
    signer = subprocess.check_output([str(build_tools/'apksigner'), 'verify', '--print-certs', str(args.apk)], text=True)
    digest = re.search(r'certificate SHA-256 digest: ([a-f0-9]{64})', signer).group(1)
    badging = subprocess.check_output([str(build_tools/'aapt2'), 'dump', 'badging', str(args.apk)], text=True)
    for required in (f"name='org.asc.foundation' versionCode='{args.version_code}' versionName='{args.version_name}'", "minSdkVersion:'26'", "targetSdkVersion:'35'", 'application-debuggable'):
        if required not in badging:
            raise ValueError('unexpected APK metadata')
    permissions = re.findall(r"uses-permission: name='([^']+)'", badging)
    if set(permissions) != {'org.asc.foundation.permission.LOCAL_ENGINE', 'android.permission.INTERNET', 'android.permission.ACCESS_NETWORK_STATE'}:
        raise ValueError('unexpected permissions')
    print(json.dumps({'sha256': hashlib.sha256(args.apk.read_bytes()).hexdigest(),
        'bytes': args.apk.stat().st_size, 'application_id': 'org.asc.foundation',
        'version_code': args.version_code, 'version_name': args.version_name, 'min_sdk': 26, 'target_sdk': 35,
        'debug_signer_certificate_sha256': digest, 'abis': abis, 'permissions': permissions,
        'canonical_core_modules': len(expected), 'inventory_findings': findings,
        'scope': 'internal debug FOUNDATION; no native Node, migration or phone acceptance'}, indent=2))


if __name__ == '__main__':
    main()
