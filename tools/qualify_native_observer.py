#!/usr/bin/env python3
"""Focused actual Core/gateway/owned-emulator observer UI qualification.

Requires installed main/test APKs and retained provisioned/enrolled task app.
Does not install, initialize, clear, or migrate native state. ADB is test control
only; gateway HTTPS uses the explicitly approved private host network address.
"""
import argparse
import io
import ipaddress
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest
from unittest import mock
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from asc.identity import fingerprint_from_pem
from asc.observability import gateway
from tests.test_observer_gateway import GatewayFixture


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--adb', required=True)
    parser.add_argument('--adb-port', type=int, default=5038)
    parser.add_argument('--serial', required=True)
    parser.add_argument('--emulator-owner', type=Path, required=True)
    parser.add_argument('--host', required=True, help='explicit task host private IPv4; never wildcard/public')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    host = ipaddress.IPv4Address(args.host)
    if not (host in ipaddress.IPv4Network('10.0.0.0/8') or host in ipaddress.IPv4Network('172.16.0.0/12')
            or host in ipaddress.IPv4Network('192.168.0.0/16')):
        raise ValueError('explicit private task host only')
    if os.name != 'posix' or not args.serial.startswith('emulator-'):
        raise ValueError('task-owned Linux emulator only')
    owner = json.loads(args.emulator_owner.read_text()); proc = Path('/proc') / str(owner['pid'])
    argv = (proc/'cmdline').read_bytes().split(b'\0')
    expected = owner['args'][owner['args'].index('-avd') + 1]
    if (not expected.startswith('ASC_') or expected.encode() not in argv or proc.stat().st_uid != os.getuid()
            or not Path(os.readlink(proc/'exe')).name.startswith('qemu-system')):
        raise ValueError('owned AVD not verified')
    args.out.mkdir(parents=True, mode=0o700, exist_ok=False)
    adb = [args.adb, '-P', str(args.adb_port), '-s', args.serial]

    def call(arguments, data=None, timeout=30):
        result = subprocess.run(adb+arguments, input=data, capture_output=True, timeout=timeout)
        if result.returncode:
            raise RuntimeError('owned ADB operation failed; private output suppressed')
        return result.stdout

    if (call(['emu', 'avd', 'name']).splitlines()[0].decode() != expected
            or call(['shell', 'getprop', 'ro.kernel.qemu']).strip() != b'1'
            or call(['shell', 'getprop', 'ro.build.version.sdk']).strip() != b'35'):
        raise ValueError('selected target not verified emulator')

    def write(name, obj):
        # Fixed task-private fixture filenames only; no secret in argv/environment.
        if name not in ('native-observer-fixture.json', 'native-observer-ack.json'):
            raise ValueError('fixed fixture file required')
        call(['shell', "run-as org.asc.foundation sh -c 'umask 077; cat > files/"+name+
              ".pending && mv files/"+name+".pending files/"+name+"'"], json.dumps(obj).encode())

    report = {'state': 'ERROR', 'scope': 'API35 synthetic Core gateway over direct private host network; not physical phones',
              'adb_control_only': True, 'new_native_identity': False}

    class Qualification(GatewayFixture):
        def runTest(self):
            self.make_cluster()
            data = b'Native authenticated observer actual Core file\0' * 512
            logical = 'observer/android-real.bin'
            upload = self.owner.upload(io.BytesIO(data), logical, 'native_observer_actual', 'replicated_3')
            if upload['job_state'] != 'COMPLETED': self.wait_job(upload['job_id'])
            self.wait_copies(upload['file']['file']['file_id'], 3)
            self.gateway_root = self.base/'native-app-gateway'; port = self.port()
            with mock.patch.dict(os.environ, {'HOME': str(self.base)}):
                gateway.init(self.gateway_root, args.host, port, self.cluster, self.epoch, self.endpoints, source_roots=self.homes)
                with gateway.Runtime(self.gateway_root) as runtime:
                    request_id = str(uuid.uuid4())
                    write('native-observer-fixture.json', {'request_id': request_id,
                        'endpoint': f'https://{args.host}:{port}', 'pin': fingerprint_from_pem(self.gateway_root/'dashboard/server.crt'),
                        'cluster_id': self.cluster, 'epoch': self.epoch, 'logical_path': logical, 'code': runtime.api.sessions.issue()})
                    phases = []; started = time.monotonic()
                    with (args.out/'android.log').open('wb') as output:
                        process = subprocess.Popen(adb+['shell', 'am', 'instrument', '-w', '-r', '-e', 'class',
                            'org.asc.foundation.NativeObserverTest#actualPinnedOwnerUiQuorumLossReconnectAndRetainedNode',
                            'org.asc.foundation.test/org.asc.foundation.UpgradeQualificationRunner'], stdin=subprocess.DEVNULL,
                            stdout=output, stderr=subprocess.STDOUT)
                        try:
                            deadline = time.monotonic()+360
                            while process.poll() is None and time.monotonic()<deadline:
                                raw = subprocess.run(adb+['exec-out','run-as','org.asc.foundation','cat','files/native-observer-request.json'],
                                                     capture_output=True, timeout=15).stdout
                                try: control = json.loads(raw)
                                except ValueError: control = {}
                                phase = control.get('phase')
                                if control.get('request_id') == request_id and phase not in phases:
                                    if phase == 'partition': self.split([{0}, {1}, {2}])
                                    elif phase == 'heal': self.split([set(range(3))]); self.wait_ready()
                                    else: raise ValueError('unsupported qualification fault')
                                    phases.append(phase); report['phases']=list(phases)
                                    write('native-observer-ack.json', {'request_id': request_id, 'phase': phase})
                                time.sleep(.25)
                            self.assertIsNotNone(process.poll(), 'Android observer did not complete within actual fault budget')
                        finally:
                            if process.poll() is None: process.terminate(); process.wait(timeout=15)
                    text = (args.out/'android.log').read_text()
                    self.assertIn('OK (1 test)', text, 'actual Android test failed/incomplete; see private android.log')
                    self.assertEqual(phases, ['partition','heal'])
                    report.update(state='PASS', android_tests=1, phases=phases,
                                  elapsed_seconds=round(time.monotonic()-started,3), replicas_observed=3)

    with (args.out/'host.log').open('w') as log:
        result = unittest.TextTestRunner(stream=log, verbosity=2).run(unittest.TestSuite([Qualification()]))
    if not result.wasSuccessful(): report.update(state='FAIL', detail='actual qualification failed; private host/android logs retained')
    (args.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return 0 if result.wasSuccessful() and report['state']=='PASS' else 1


if __name__ == '__main__': sys.exit(main())
