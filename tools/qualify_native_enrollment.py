#!/usr/bin/env python3
"""Explicit owned-emulator Core enrollment gates, not direct LAN or phone proof.

Build first; preserves installed signer/UID/app data. Private actual TLS Registry,
fixture codes and logs are generated ONLY in the specified outside-repo directory.
Never use against a physical device. No uninstall, clear, wipe or signing repair.
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
import socket
import ssl
import subprocess
import sys
import threading
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tests')]
from asc.identity import make_cert, fingerprint_from_pem
from asc.server import Server
from asc.store import Registry
from test_quick_join import JoinProxy


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk', type=Path, required=True)
    parser.add_argument('--adb-port', type=int, required=True)
    parser.add_argument('--serial', required=True)
    parser.add_argument('--avd', required=True)
    parser.add_argument('--owner-receipt', type=Path, required=True)
    parser.add_argument('--expected-signer', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.absolute()
    if ROOT == out or ROOT in out.parents or out.exists():
        raise ValueError('output must be a NEW private directory outside checkout')
    if not re.fullmatch('[a-f0-9]{64}', args.expected_signer):
        raise ValueError('expected original signer required')
    adb = [str(args.sdk / 'platform-tools/adb'), '-P', str(args.adb_port), '-s', args.serial]
    owner = json.loads(args.owner_receipt.read_text())
    proc = Path('/proc') / str(int(owner['pid']))
    command = (proc / 'cmdline').read_bytes().split(b'\0')
    if (proc.stat().st_uid != os.getuid() or b'-avd' not in command or
            command[command.index(b'-avd') + 1].decode() != args.avd or
            str(args.sdk.absolute()) not in command[0].decode()):
        raise ValueError('live task-owned emulator process does not match receipt')
    def call(parts, timeout=120, data=None):
        result = subprocess.run(adb + parts, input=data, capture_output=True, timeout=timeout)
        result.check_returncode()
        return result.stdout.decode()
    if (call(['shell', 'getprop', 'ro.kernel.qemu']).strip() != '1' or
            call(['shell', 'getprop', 'ro.hardware']).strip() not in ('ranchu', 'goldfish') or
            call(['shell', 'getprop', 'sys.boot_completed']).strip() != '1' or
            call(['shell', 'getprop', 'ro.boot.qemu.avd_name']).strip() != args.avd):
        raise ValueError('owned booted emulator identity mismatch')
    out.mkdir(mode=0o700)
    def signer(path):
        text = subprocess.check_output([str(args.sdk / 'build-tools/35.0.0/apksigner'),
                                       'verify', '--print-certs', str(path)], text=True)
        return re.search(r'certificate SHA-256 digest: ([a-f0-9]{64})', text).group(1)
    uid = call(['shell', 'cmd', 'package', 'list', 'packages', '-U', 'org.asc.foundation'])
    if not re.search(r'package:org.asc.foundation uid:\d+', uid):
        raise ValueError('retained app missing; no automatic fresh-install upgrade claim')
    installed = call(['shell', 'pm', 'path', 'org.asc.foundation']).strip()
    if not re.fullmatch(r'package:/data/app/[^\n]+/base.apk', installed):
        raise ValueError('unexpected retained APK path')
    call(['pull', installed.removeprefix('package:'), str(out / 'prior-installed.apk')])
    apk = ROOT / 'android/app/build/outputs/apk/debug/app-debug.apk'
    test_apk = ROOT / 'android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk'
    for path in (out / 'prior-installed.apk', apk, test_apk):
        if signer(path) != args.expected_signer:
            raise ValueError('original signer mismatch; no install/clear/uninstall attempted')
    for path in (apk, test_apk):
        if 'Success' not in call(['install', '-r', str(path)], timeout=240):
            raise RuntimeError('normal retained-state upgrade failed')
    if call(['shell', 'cmd', 'package', 'list', 'packages', '-U', 'org.asc.foundation']) != uid:
        raise ValueError('retained app/test UID changed')
    registry = Registry(out / 'registry.sqlite3'); cluster = str(uuid.uuid4()); registry.initialize(cluster)
    make_cert(out / 'fixture.crt', out / 'fixture.key')
    pin = fingerprint_from_pem(out / 'fixture.crt').lower()
    tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); tls.minimum_version = ssl.TLSVersion.TLSv1_2
    tls.load_cert_chain(out / 'fixture.crt', out / 'fixture.key')
    with contextlib.ExitStack() as resources:
        def start(server):
            thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
            resources.callback(lambda: (server.shutdown(), server.server_close(), thread.join()))
            return server
        controller = start(Server(('127.0.0.1', 0), registry, secrets.token_urlsafe(32)))
        controller.tls_context = tls
        origin = 'https://127.0.0.1:' + str(controller.server_address[1])
        def proxy(drop=False, override=None):
            server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), JoinProxy)
            server.origin, server.pin = origin, pin
            server.drop, server.dropped, server.override, server.join_calls = drop, False, override, 0
            server.socket = tls.wrap_socket(server.socket, server_side=True)
            return start(server)
        dropped, seed, quorum = proxy(True), proxy(True), proxy(override={'mode': 'core-quorum', 'raft_enabled': True})
        offline = socket.socket(); offline.bind(('127.0.0.1', 0)); resources.callback(offline.close)
        # Explicit development tunnel, no fallback/proxy changes or LAN claim.
        existing = call(['reverse', '--list'])
        for port in [controller.server_address[1], dropped.server_address[1], seed.server_address[1], quorum.server_address[1], offline.getsockname()[1]]:
            mapping = 'tcp:' + str(port)
            if mapping in existing:
                raise ValueError('refuse replacing an existing reverse mapping')
            call(['reverse', mapping, mapping])
            resources.callback(lambda name=mapping: call(['reverse', '--remove', name]))
        config = {'origin': origin, 'pin': pin, 'cluster_id': cluster,
                  'drop_origin': 'https://127.0.0.1:' + str(dropped.server_address[1]),
                  'seed_origin': 'https://127.0.0.1:' + str(seed.server_address[1]),
                  'quorum_origin': 'https://127.0.0.1:' + str(quorum.server_address[1]),
                  'offline_origin': 'https://127.0.0.1:' + str(offline.getsockname()[1])}
        for name in ('expired_code', 'fresh_code', 'drop_code', 'replacement_code', 'negative_code', 'seed_code'):
            config[name] = registry.add_pair_code(ttl=900)
            if name == 'expired_code':
                with registry.connect() as db:
                    db.execute('UPDATE join_codes SET expires_at=0')
        fixture = 'files/native-join-fixture.json'
        call(['shell', 'run-as org.asc.foundation test ! -e ' + fixture])
        call(['shell', "run-as org.asc.foundation sh -c 'umask 077; cat > " + fixture + "'"], data=json.dumps(config).encode())
        # Keep synthetic private receipt for fault diagnosis, never print fixture secrets.
        (out / 'private-fixture.json').write_text(json.dumps(config))
        runner = 'org.asc.foundation.test/org.asc.foundation.UpgradeQualificationRunner'
        classes = ','.join('org.asc.foundation.' + name for name in (
            'NativeEnrollmentTest', 'BinderEnrollmentTest', 'NativeTLSTest', 'NativeContextTest',
            'EmbeddedEngineTest', 'VaultStorageTest', 'BinderTest', 'NativeUiTest'))
        result = call(['shell', 'am', 'instrument', '-w', '-r', '-e', 'class', classes, runner], timeout=900)
        (out / 'android-targeted.log').write_text(result)
        if 'OK (28 tests)' not in result or 'FAILURES' in result:
            raise RuntimeError('actual Android targeted gates failed; inspect private log')
        print('Actual Android28 targeted PASS', flush=True)
        def phase(name):
            result = call(['shell', 'am', 'instrument', '-w', '-r', '-e', 'phase', name, runner], timeout=240)
            (out / (name + '.log')).write_text(result)
            if 'qualification=PASS' not in result or 'qualification=FAIL' in result:
                raise RuntimeError('fixed phase failed: ' + name)
            print('PASS actual Android fixed phase', name, flush=True)
        for name in ('join-pending-seed', 'join-pending-resume', 'join-receipt-verify'):
            if name != 'join-pending-seed':
                call(['shell', 'am', 'force-stop', 'org.asc.foundation'])
                call(['shell', 'am', 'start', '-W', '-n', 'org.asc.foundation/.MainActivity'])
            phase(name)
        phase('tls-verify'); phase('verify-v3')
        result = call(['shell', 'am', 'instrument', '-w', '-r', 'org.asc.untrusted.test/androidx.test.runner.AndroidJUnitRunner'])
        (out / 'foreign-caller.log').write_text(result)
        if not re.search(r'OK \(1 tests?\)', result):
            raise RuntimeError('actual foreign-caller gate failed')
        if not (dropped.dropped and seed.dropped and dropped.join_calls == seed.join_calls == 2):
            raise RuntimeError('must lose real successful TLS201 ACKs and retry exactly')
        with registry.connect() as db:
            if db.execute('SELECT COUNT(*) FROM nodes').fetchone()[0] != 4 or db.execute('SELECT COUNT(*) FROM catalog_nodes').fetchone()[0] != 0:
                raise RuntimeError('unexpected enrollment/automatic approval')
        if call(['shell', 'cmd', 'package', 'list', 'packages', '-U', 'org.asc.foundation']) != uid:
            raise RuntimeError('UID changed')
        report = {'android_tests': 28, 'foreign_caller_tests': 1, 'fixed_phases': 5,
                  'scope': 'API35 x86_64 owned emulator, explicit ADB loopback; NOT LAN/phone/Node Agent',
                  'signer_sha256': args.expected_signer, 'apk_sha256': hashlib.sha256(apk.read_bytes()).hexdigest(),
                  'committed_nodes': 4, 'approved_storage_nodes': 0, 'successful_ack_losses': 2}
        (out / 'public-report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
