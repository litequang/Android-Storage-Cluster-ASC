#!/usr/bin/env python3
"""Focused Linux/owned-AVD Native Node data test; ADB control only, SDK NAT bytes.

Requires installed main/test APKs, an enrolled/configured Node, notification
permission and private synthetic Controller fixture. No installs/state resets.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.parse import urlsplit
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from asc.client import request_json
from asc.storage.client import StorageClient


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--adb', required=True)
    parser.add_argument('--adb-port', type=int, default=5038)
    parser.add_argument('--serial', required=True)
    parser.add_argument('--emulator-owner', type=Path, required=True)
    parser.add_argument('--fixture', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if not args.serial.startswith('emulator-') or os.name != 'posix':
        raise ValueError('Linux task-owned emulator only; never physical devices')
    owner = json.loads(args.emulator_owner.read_text())
    proc = Path('/proc') / str(owner['pid'])
    argv = (proc / 'cmdline').read_bytes().split(b'\0')
    expected = owner['args'][owner['args'].index('-avd') + 1]
    if (not expected.startswith('ASC_') or expected.encode() not in argv or
            not Path(os.readlink(proc / 'exe')).name.startswith('qemu-system') or proc.stat().st_uid != os.getuid()):
        raise ValueError('emulator ownership not established')
    fixture = json.loads(args.fixture.read_text())
    url = urlsplit(fixture['origin'])
    if url.scheme != 'https' or url.hostname != '127.0.0.1' or not url.port or url.username:
        raise ValueError('synthetic loopback Controller fixture required')
    args.out.mkdir(mode=0o700, parents=True, exist_ok=False)
    base = [args.adb, '-P', str(args.adb_port), '-s', args.serial]

    def call(arguments, data=None, timeout=30):
        result = subprocess.run(base + arguments, input=data, capture_output=True, timeout=timeout)
        if result.returncode:
            raise RuntimeError('task ADB operation failed; private response suppressed')
        return result.stdout

    if call(['emu', 'avd', 'name']).splitlines()[0].decode() != expected:
        raise ValueError('selected emulator differs from owner receipt')
    info = request_json(fixture['origin'], fixture['pin'], 'GET', '/api/v1/info')
    if info['cluster_id'] != fixture['cluster_id'] or info['mode'] != 'single-writer-development':
        raise ValueError('fixture identity/mode mismatch')
    request = str(uuid.uuid4()); fixture['direct_request_id'] = request
    command = "run-as org.asc.foundation sh -c 'umask 077; cat > files/native-mvp-network-fixture.json'"
    call(['shell', command], json.dumps(fixture).encode())
    mapping = 'tcp:' + str(url.port)
    restore_reverse = mapping.encode() in call(['reverse', '--list']).split()
    if restore_reverse:
        call(['reverse', '--remove', mapping])
    with socket.socket() as selected:
        selected.bind(('127.0.0.1', 0)); port = selected.getsockname()[1]
    nat = False; process = None; log = None; stage = 'nat-setup'
    report = {'request_id': request, 'state': 'ERROR', 'scope': 'SDK NAT, not physical LAN/two replicas',
              'adb_reverse_removed': True, 'adb_control_only': True}
    control = {'request_id': request, 'state': 'ERROR'}
    try:
        if b'OK' not in call(['emu', 'redir', 'add', f'tcp:{port}:9443']):
            raise RuntimeError('SDK NAT setup not confirmed')
        nat = True
        if not any(f'127.0.0.1:{port}' in line for line in subprocess.check_output(['ss', '-ltn'], text=True).splitlines()):
            raise ValueError('NAT endpoint must be loopback-only')
        stage = 'android-startup'
        log = (args.out / 'android.log').open('wb')
        process = subprocess.Popen(base + ['shell', 'am', 'instrument', '-w', '-r', '-e', 'class',
            'org.asc.foundation.NativeNodeDirectTest#actualDirectControllerAndHostToNodeTransferRetainIdentity',
            'org.asc.foundation.test/org.asc.foundation.UpgradeQualificationRunner'],
            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
        start = time.monotonic(); end = start + 180; ready = None
        while time.monotonic() < end and process.poll() is None:
            result = subprocess.run(base + ['exec-out', 'run-as', 'org.asc.foundation', 'cat',
                                           'files/direct-node-ready.json'], capture_output=True, timeout=10)
            try:
                value = json.loads(result.stdout)
                if value.get('request_id') == request:
                    ready = value; break
            except ValueError:
                pass
            time.sleep(.3)
        if ready is None or ready['node_id'] != fixture['node_id']:
            raise ValueError('expected retained Node not ready')
        report['startup_seconds'] = round(time.monotonic() - start, 3)
        stage = 'owner-grant'
        grant = request_json(fixture['origin'], fixture['pin'], 'POST', '/api/v1/admin/storage-grant',
            {'node_id': ready['node_id'], 'volume_id': ready['volume_id'],
             'operations': ['read', 'write', 'verify']}, fixture['owner_token'])['grant']
        client = StorageClient(f'https://127.0.0.1:{port}', ready['pin'], grant, ready['volume_id'])
        data = bytes(range(256)) * 1024; digest = hashlib.sha256(data).hexdigest()
        key = 'direct_' + uuid.uuid4().hex
        stage = 'upload'
        session = client.initiate(key, 'native/' + key + '.bin', len(data), digest)
        client.upload(session['session_id'], io.BytesIO(data), len(data))
        saved = client.commit(session['session_id'])
        stage = 'verify-download'
        if client.json('POST', 'files/' + saved['file_id'] + '/verify', {})['state'] != 'COMMITTED':
            raise ValueError('actual Node verification failed')
        output = io.BytesIO(); client.download(saved['file_id'], output, len(data), digest)
        if output.getvalue() != data:
            raise ValueError('actual downloaded bytes differ')
        control.update(state='PASS', bytes=len(data), sha256=digest, volume_id=ready['volume_id'])
        report.update(control)
    except Exception as exc:
        report.update(stage=stage, error_class=type(exc).__name__)
    finally:
        call(['shell', "run-as org.asc.foundation sh -c 'umask 077; cat > files/direct-node-result.json'"],
             json.dumps(control).encode())
        if process is not None:
            process.wait(timeout=110); log.close()
            if 'OK (1 test)' not in (args.out / 'android.log').read_text():
                report.update(state='ERROR', android='FAIL or incomplete; not inferred from adb exit')
        if nat:
            call(['emu', 'redir', 'del', f'tcp:{port}'])
        if restore_reverse:
            call(['reverse', mapping, mapping])
        (args.out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if report['state'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
