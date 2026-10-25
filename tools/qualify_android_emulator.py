#!/usr/bin/env python3
"""Fixed synthetic Android gates. Explicit owned loopback emulator ONLY, never phones."""
import argparse
import contextlib
import hashlib
import json
from pathlib import Path
import re
import secrets
import sqlite3
import ssl
import subprocess
import sys
import threading
import uuid

REPO=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(REPO))
from asc.store import Registry
from asc.identity import make_cert,fingerprint_from_pem
from asc.server import Server


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('runtime','upgrade'))
    parser.add_argument('--adb',type=Path,required=True)
    parser.add_argument('--serial',required=True)
    parser.add_argument('--port',type=int,default=5038)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--baseline',type=Path);parser.add_argument('--baseline-sha256')
    parser.add_argument('--current',type=Path);parser.add_argument('--current-sha256')
    parser.add_argument('--tests',type=Path);parser.add_argument('--foreign',action='store_true')
    parser.add_argument('--host-transport',choices=('nat','adb-reverse-loopback'),default='nat',help='explicit development transport; reverse-loopback NEVER qualifies native LAN')
    parser.add_argument('--resume-unseeded',action='store_true',help='only resume an exact old APK with NO seeded private state after a harness setup failure')
    args=parser.parse_args()
    if not re.fullmatch(r'127\.0\.0\.1:[1-9][0-9]{3,4}',args.serial) or not 1024<=args.port<=65535:
        raise ValueError('explicit owned loopback emulator required')
    out=args.output.absolute()
    if out==REPO or REPO in out.parents or any(p.is_symlink() for p in (out,*out.parents)):
        raise ValueError('private output outside source required')
    out.mkdir(mode=0o700) # Refuse existing/ambiguous output; never overwrite old proof.
    adb=[str(args.adb),'-P',str(args.port),'-s',args.serial]
    def run(command,*,timeout=20,input=None,check=True):
        return subprocess.run(command,timeout=timeout,input=input,capture_output=True,check=check)
    if run(adb+['shell','getprop','ro.kernel.qemu']).stdout.strip()!=b'1':raise ValueError('not an Android emulator')
    if run(adb+['shell','getprop','ro.hardware']).stdout.strip() not in (b'ranchu',b'goldfish'):raise ValueError('unqualified emulator hardware')
    if run(adb+['shell','getprop','sys.boot_completed']).stdout.strip()!=b'1':raise ValueError('actual emulator boot required')
    records=[]
    def instrument(label,component='org.asc.foundation.test/org.asc.foundation.UpgradeQualificationRunner',extra=(),expected='junit'):
        result=run(adb+['shell','am','instrument','-w','-r',*extra,component],timeout=300,check=False)
        raw=result.stdout+result.stderr;(out/(label+'.log')).write_bytes(raw)
        ok=(b'\nOK (' in raw and b'FAILURES' not in raw) if expected=='junit' else b'qualification=PASS' in raw and b'qualification=FAIL' not in raw
        if result.returncode or not ok:raise RuntimeError('Android gate failed: '+label+'; private log retained')
        records.append({'gate':label,'state':'PASS','transport':args.host_transport if args.mode=='runtime' else 'local-apk'});print('PASS',label,flush=True)
        (out/'results.json').write_text(json.dumps(records,indent=2)+'\n')
    if args.mode=='upgrade':
        for path,digest in ((args.baseline,args.baseline_sha256),(args.current,args.current_sha256)):
            if path is None or not re.fullmatch('[a-f0-9]{64}',digest or '') or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
                raise ValueError('trusted exact APK SHA required before installation')
        if args.tests is None:raise ValueError('matching current test APK required')
        installed=run(adb+['shell','pm','path','org.asc.foundation'],check=False).stdout.strip()
        if installed:
            if not args.resume_unseeded:raise ValueError('FRESH AVD required; never downgrade/uninstall/clear existing state')
            if not re.fullmatch(rb'package:/data/app/[A-Za-z0-9_+=/.~\-]+/base\.apk',installed):raise ValueError('ambiguous installed APK')
            path=installed.decode().removeprefix('package:')
            actual=run(adb+['exec-out','cat',path],timeout=120).stdout
            if hashlib.sha256(actual).hexdigest()!=args.baseline_sha256:raise ValueError('installed old APK differs from exact baseline')
            run(adb+['shell',"run-as org.asc.foundation sh -c 'test ! -e files/identity-v1 && test ! -e files/private-probe-v1 && test ! -e files/upgrade-proof.json'"])
        elif args.resume_unseeded:raise ValueError('nothing to resume')
        for apk in ((args.tests,) if installed else (args.baseline,args.tests)):
            result=run(adb+['install','-r',str(apk)],timeout=180)
            if b'Success' not in result.stdout:raise RuntimeError('APK install not confirmed')
        component='org.asc.foundation.test/org.asc.foundation.UpgradeQualificationRunner'
        instrument('seed-exact-old-apk',component,('-e','phase','seed'),'fixed')
        run(adb+['install','-r',str(args.current)],timeout=120)
        instrument('verify-after-same-signer-upgrade',component,('-e','phase','verify'),'fixed')
        run(adb+['shell','am','force-stop','org.asc.foundation'])
        run(adb+['shell','am','start','-W','-n','org.asc.foundation/.MainActivity'],timeout=60)
        instrument('verify-after-actual-process-death',component,('-e','phase','verify'),'fixed')
        denial=run(adb+['install','-r',str(args.baseline)],timeout=120,check=False)
        (out/'downgrade-denial.log').write_bytes(denial.stdout+denial.stderr)
        if b'INSTALL_FAILED_VERSION_DOWNGRADE' not in denial.stdout+denial.stderr:raise RuntimeError('platform downgrade must refuse')
        records.append({'gate':'platform-downgrade-refusal','state':'PASS'})
        instrument('verify-after-refused-downgrade',component,('-e','phase','verify'),'fixed')
        return
    if args.foreign:
        instrument('foreign-uid-signer-permission-denied','org.asc.untrusted.test/androidx.test.runner.AndroidJUnitRunner')
    root=out/'synthetic-controller';root.mkdir(mode=0o700)
    cluster=str(uuid.uuid4());admin=secrets.token_urlsafe(32)
    reg=Registry(root/'registry.sqlite3');reg.initialize(cluster)
    make_cert(root/'server.crt',root/'server.key');pin=fingerprint_from_pem(root/'server.crt').lower()
    ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);ctx.minimum_version=ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain(root/'server.crt',root/'server.key')
    server=thread=None;port=0;reverse_owned=False
    def start():
        nonlocal server,thread,port
        server=Server(('127.0.0.1',port),reg,admin);port=server.server_address[1];server.tls_context=ctx
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    def stop():
        nonlocal server,thread
        if server:server.shutdown();server.server_close();thread.join();server=thread=None
    def config(phase):
        public={'origin':'https://'+('127.0.0.1' if args.host_transport=='adb-reverse-loopback' else '10.0.2.2')+':'+str(port),'pin':pin,'cluster_id':cluster,'phase':phase}
        # PUBLIC synthetic binding only; raw config never interpreted as shell text.
        command="run-as org.asc.foundation sh -c 'umask 077; cat > files/controller-fixture.json'"
        run(adb+['shell',command],input=json.dumps(public).encode())
    try:
        start()
        if args.host_transport=='adb-reverse-loopback':
            run(adb+['reverse','--no-rebind','tcp:'+str(port),'tcp:'+str(port)])
            reverse_owned=True
        config('online')
        # Only this verified AOSP task-owned emulator's built-in virtual WLAN.
        # Enabled != connected. Native precondition must observe a real default route.
        run(adb+['shell','svc','wifi','enable'])
        run(adb+['shell','svc','data','enable'])
        run(adb+['shell','cmd','wifi','connect-network','AndroidWifi','open'])
        instrument('actual-default-network-ready',extra=('-e','class','org.asc.foundation.NetworkReadinessTest'))
        instrument('full-android-online')
        stop();config('offline');instrument('actual-controller-offline',extra=('-e','class','org.asc.foundation.ControllerBindingTest'))
        start()
        config('online');instrument('actual-controller-reconnect',extra=('-e','class','org.asc.foundation.ControllerBindingTest'))
        with contextlib.closing(sqlite3.connect(root/'registry.sqlite3')) as db:
            if db.execute('SELECT COUNT(*) FROM enrollments').fetchone()[0]!=0:raise RuntimeError('native public check must never enroll')
        records.append({'gate':'no-enrollment-or-node-credential-mutation','state':'PASS'})
        (out/'results.json').write_text(json.dumps(records,indent=2)+'\n')
    finally:
        stop()
        if reverse_owned:run(adb+['reverse','--remove','tcp:'+str(port)],check=False)


if __name__=='__main__':main()
