#!/usr/bin/env python3
"""Positive UI/private Binder/Core join on a NEW owned emulator only.

Never targets the retained upgrade AVD or phones, and never removes app state.
Explicit setup retry may reuse the same unprovisioned sandbox before enrollment.
Uses explicit dev ADB loopback, not direct LAN. Leaves all proof/state intact.
"""
import argparse
import contextlib
import hashlib
import http.server
import json
import os
from pathlib import Path
import re
import secrets
import ssl
import subprocess
import sys
import threading
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tests')]
from asc.identity import make_cert, fingerprint_from_pem
from asc.server import Server
from asc.store import Registry
from test_quick_join import JoinProxy


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sdk', type=Path, required=True)
    p.add_argument('--adb-port', type=int, required=True)
    p.add_argument('--serial', required=True)
    p.add_argument('--avd', required=True)
    p.add_argument('--owner-receipt', type=Path, required=True)
    p.add_argument('--expected-signer', required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--resume-setup', action='store_true', help='reuse ONLY failed pre-enrollment fixture; never re-seed existing identity')
    a = p.parse_args()
    if a.avd == 'ASC_UPGRADE_API35' or not a.avd.startswith('ASC_JOIN_'):
        raise ValueError('requires a separate NEW join-qualification AVD')
    owner = json.loads(a.owner_receipt.read_text());proc = Path('/proc') / str(int(owner['pid']))
    command = (proc / 'cmdline').read_bytes().split(b'\0')
    if (proc.stat().st_uid != os.getuid() or b'-avd' not in command or
            command[command.index(b'-avd') + 1].decode() != a.avd or str(a.sdk.absolute()) not in command[0].decode()):
        raise ValueError('live owned emulator receipt mismatch')
    adb = [str(a.sdk / 'platform-tools/adb'), '-P', str(a.adb_port), '-s', a.serial]
    def call(parts, timeout=120, data=None):
        r = subprocess.run(adb + parts, capture_output=True, input=data, timeout=timeout)
        if r.returncode:
            if a.output.is_dir():
                failure = {'operation': parts[:2], 'exit': r.returncode,
                           'stdout': r.stdout.decode(errors='replace'),
                           'stderr': r.stderr.decode(errors='replace')}
                (a.output / ('adb-failure-' + uuid.uuid4().hex + '.json')).write_text(json.dumps(failure))
            raise RuntimeError('ADB operation failed; preserve private diagnostic output/state')
        return r.stdout.decode()
    for prop, expected in {'ro.kernel.qemu': '1', 'ro.hardware': 'ranchu',
                           'ro.boot.qemu.avd_name': a.avd, 'sys.boot_completed': '1'}.items():
        if call(['shell', 'getprop', prop]).strip() != expected:
            raise ValueError('owned guest identity/boot mismatch')
    installed = 'package:org.asc.foundation' in call(['shell', 'cmd', 'package', 'list', 'packages', 'org.asc.foundation'])
    if installed and not a.resume_setup:
        raise ValueError('fresh-sandbox prerequisite failed; NEVER uninstall/clear existing state')
    out = a.output.absolute()
    if out == ROOT or ROOT in out.parents or (out.exists() != a.resume_setup):
        raise ValueError('requires NEW private output outside checkout')
    if not a.resume_setup:
        out.mkdir(mode=0o700)
    elif (not out.is_dir() or out.is_symlink() or out.stat().st_uid != os.getuid() or
          out.stat().st_mode & 0o077 or not installed or any(out.glob('ui-join-*.log'))):
        raise ValueError('setup recovery requires installed fixture and NO prior UI phase/evidence')
    if not re.fullmatch('[a-f0-9]{64}', a.expected_signer):
        raise ValueError('original signer SHA required')
    apk = ROOT / 'android/app/build/outputs/apk/debug/app-debug.apk'
    packages = (apk, ROOT / 'android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk')
    for path in packages:
        cert = subprocess.check_output([str(a.sdk / 'build-tools/35.0.0/apksigner'), 'verify', '--print-certs', str(path)], text=True)
        if re.search(r'certificate SHA-256 digest: ([a-f0-9]{64})', cert).group(1) != a.expected_signer:
            raise ValueError('original signer mismatch')
    for path in packages:
        if 'Success' not in call(['install', '-r', str(path)], timeout=240):
            raise RuntimeError('fresh isolated install failed')
    registry = Registry(out / 'registry.sqlite3')
    if a.resume_setup:
        config = json.loads((out / 'private-fixture.json').read_text())
        cluster = registry.cluster_id()
        pin = fingerprint_from_pem(out / 'fixture.crt').lower()
        if config['cluster_id'] != cluster or config['pin'] != pin:
            raise ValueError('retained synthetic Controller binding mismatch')
        with registry.connect() as db:
            counts = [db.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0] for table in ('nodes', 'catalog_nodes')]
            row = db.execute('SELECT expires_at FROM join_codes WHERE code_hash=?',
                             (hashlib.sha256(config['code'].encode()).hexdigest(),)).fetchone()
            if counts != [0, 0] or row is None or row['expires_at'] <= time.time():
                raise ValueError('not an untouched pre-enrollment fixture; preserve state for reviewed resume')
        proxy_port = int(config['origin'].removeprefix('https://127.0.0.1:'))
    else:
        cluster = str(uuid.uuid4());registry.initialize(cluster)
        make_cert(out / 'fixture.crt', out / 'fixture.key');pin = fingerprint_from_pem(out / 'fixture.crt').lower()
        proxy_port = 0
    tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);tls.minimum_version = ssl.TLSVersion.TLSv1_2
    tls.load_cert_chain(out / 'fixture.crt', out / 'fixture.key')
    with contextlib.ExitStack() as resources:
        def start(server):
            thread = threading.Thread(target=server.serve_forever, daemon=True);thread.start()
            resources.callback(lambda: (server.shutdown(), server.server_close(), thread.join()))
            return server
        controller = start(Server(('127.0.0.1', 0), registry, secrets.token_urlsafe(32)));controller.tls_context = tls
        proxy = http.server.ThreadingHTTPServer(('127.0.0.1', proxy_port), JoinProxy)
        proxy.origin = 'https://127.0.0.1:' + str(controller.server_address[1]);proxy.pin = pin
        proxy.drop, proxy.dropped, proxy.override, proxy.join_calls = True, False, None, 0
        proxy.socket = tls.wrap_socket(proxy.socket, server_side=True);start(proxy)
        port = proxy.server_address[1];mapping = 'tcp:' + str(port)
        if mapping in call(['reverse', '--list']):
            raise ValueError('refuse replacing existing reverse mapping')
        call(['reverse', mapping, mapping]);resources.callback(lambda: call(['reverse', '--remove', mapping]))
        if not a.resume_setup:
            config = {'origin': 'https://127.0.0.1:' + str(port), 'pin': pin, 'cluster_id': cluster,
                      'code': registry.add_pair_code(ttl=1800)}
            (out / 'private-fixture.json').write_text(json.dumps(config))
        # First Activity creates the platform filesDir; it NEVER provisions app/Node.
        # Seed still requires actual vault NOT_PROVISIONED before explicit UI consent.
        call(['shell', 'am', 'start', '-W', '-n', 'org.asc.foundation/.MainActivity'])
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            ready = subprocess.run(adb + ['shell', 'run-as', 'org.asc.foundation', 'test', '-d', 'files'],
                                   capture_output=True, timeout=15)
            if ready.returncode == 0:
                break
            time.sleep(0.2)
        else:
            raise RuntimeError('actual app filesDir not ready; no manual directory/identity creation')
        call(['shell', "run-as org.asc.foundation sh -c 'umask 077; cat > files/native-ui-join-fixture.json'"], data=json.dumps(config).encode())
        uid = call(['shell', 'cmd', 'package', 'list', 'packages', '-U', 'org.asc.foundation'])
        runner = 'org.asc.foundation.test/org.asc.foundation.UpgradeQualificationRunner'
        for phase in ('ui-join-seed', 'ui-join-resume', 'ui-join-verify'):
            if phase != 'ui-join-seed':
                call(['shell', 'am', 'force-stop', 'org.asc.foundation'])
                call(['shell', 'am', 'start', '-W', '-n', 'org.asc.foundation/.MainActivity'])
            result = call(['shell', 'am', 'instrument', '-w', '-r', '-e', 'phase', phase, runner], timeout=600)
            (out / (phase + '.log')).write_text(result)
            if 'qualification=PASS' not in result or 'qualification=FAIL' in result:
                raise RuntimeError('actual UI/Binder phase failed: ' + phase + '; preserve private proof/state')
            print('PASS actual native UI/private Binder/Core', phase, flush=True)
        if not proxy.dropped or proxy.join_calls != 2:
            raise RuntimeError('must drop actual successful TLS201 ACK and retry SAME enrollment once')
        with registry.connect() as db:
            if db.execute('SELECT COUNT(*) FROM nodes').fetchone()[0] != 1 or db.execute('SELECT COUNT(*) FROM catalog_nodes').fetchone()[0] != 0:
                raise RuntimeError('duplicate Node or automatic approval')
        if call(['shell', 'cmd', 'package', 'list', 'packages', '-U', 'org.asc.foundation']) != uid:
            raise RuntimeError('UID changed')
        report = {'checkpoint': '4.2g.2c', 'fixed_ui_process_phases': 3,
                  'actual_successful_ack_losses': 1, 'server_join_posts': 2,
                  'accepted_nodes': 1, 'approved_storage_nodes': 0,
                  'apk_sha256': hashlib.sha256(apk.read_bytes()).hexdigest(),
                  'signer_sha256': a.expected_signer,
                  'scope': 'fresh separate owned API35 x86_64 AVD; actual native UI/Binder/Core; explicit ADB loopback ONLY',
                  'direct_lan': 'NOT PASSED', 'phone_runtime': 'NOT TESTED', 'storage_agent_fgs': 'NOT IMPLEMENTED',
                  'in_place_upgrade': 'NOT CLAIMED for fresh sandbox; original retained AVD proof is separate',
                  'full_phase_accepted': False}
        (out / 'public-report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
