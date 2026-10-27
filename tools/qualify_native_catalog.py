#!/usr/bin/env python3
"""Actual Native Node +existing Demo Catalog/Dashboard/Chromium qualification.

Task-owned fresh AVD only, original signer/retained state. Synthetic Linux peer
is a separate process/domain assertion, NOT independent phone hardware. Leaves
private Demo state and Android objects intact. No production runtime bypass.
"""
import argparse
import hashlib
import io
import json
import os
import re
from pathlib import Path
import secrets
import shlex
import signal
import socket
import ssl
import sqlite3
import subprocess
import sys
import tarfile
import time
import traceback
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from asc.client import request_json, connect_pinned, ClientError
from asc.catalog.client import ClusterClient
from asc.demo.package import build
from asc.identity import fingerprint_from_pem
from asc.storage.client import StorageClient


def port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sdk',type=Path,required=True);p.add_argument('--adb-port',type=int,default=5038)
    p.add_argument('--android-api',type=int,choices=(30,35),default=35,
                   help='actual owned SDK image; default API35 contract unchanged')
    p.add_argument('--serial',required=True);p.add_argument('--owner',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--resume',action='store_true')
    p.add_argument('--resume-setup',action='store_true',help='ONLY interrupted pre-identity setup; requires --resume and no app/node state')
    a=p.parse_args();owner=json.loads(a.owner.read_text());proc=Path('/proc')/str(owner['pid'])
    expected_avd=('ASC_NATIVE_CATALOG_API'+str(a.android_api)).encode()
    expected_serial={30:'emulator-5562',35:'emulator-5560'}[a.android_api]
    if a.resume_setup and not a.resume:raise ValueError('setup resume must explicitly retain existing fixture')
    argv=(proc/'cmdline').read_bytes().split(b'\0')
    if (os.name!='posix' or proc.stat().st_uid!=os.getuid() or expected_avd not in argv
            or not Path(os.readlink(proc/'exe')).name.startswith('qemu-system') or a.serial!=expected_serial):
        raise ValueError('requires separate owned Native Catalog AVD; never phones/original AVD')
    adb=[str(a.sdk/'platform-tools/adb'),'-P',str(a.adb_port),'-s',a.serial]
    def call(args,data=None,timeout=40):
        r=subprocess.run(adb+args,input=data,capture_output=True,timeout=timeout)
        if r.returncode:raise RuntimeError('owned ADB failed; private response suppressed')
        return r.stdout
    if call(['emu','avd','name']).splitlines()[0]!=expected_avd:raise ValueError('AVD mismatch')
    for prop,wanted in [('ro.kernel.qemu',b'1'),('sys.boot_completed',b'1'),('ro.build.version.sdk',str(a.android_api).encode())]:
        if call(['shell','getprop',prop]).strip()!=wanted:raise ValueError('actual selected SDK boot required')
    apk=ROOT/'android/app/build/outputs/apk/debug/app-debug.apk'
    signer=subprocess.check_output([str(a.sdk/'build-tools/35.0.0/apksigner'),'verify','--print-certs',str(apk)],text=True)
    if re.search(r'certificate SHA-256 digest: ([a-f0-9]{64})',signer).group(1)!='bba77b68e43ecfe885705442d2224977208bf77a397c216393c26fc151a6bc30':
        raise ValueError('original private signer required')
    installed=call(['shell','pm','path','org.asc.foundation']).decode().strip().removeprefix('package:')
    if not installed.startswith('/data/app/') or not installed.endswith('/base.apk') or '\n' in installed:
        raise ValueError('existing installed task APK required')
    if hashlib.sha256(call(['exec-out','cat',installed])).digest()!=hashlib.sha256(apk.read_bytes()).digest():
        raise ValueError('installed APK differs from qualified local artifact')
    w=a.out.absolute()
    if ROOT==w or ROOT in w.parents or w.exists()!=a.resume:raise ValueError('new private output, or explicit retained resume required')
    if not a.resume:w.mkdir(mode=0o700)
    run=w/'runs'/uuid.uuid4().hex;run.mkdir(parents=True,mode=0o700)
    env=dict(os.environ,HOME=str(w/'home'),PYTHONDONTWRITEBYTECODE='1')
    controller=w/'home/controller';peer=w/'home/peer'
    def private(name,value):
        target=w/name
        with target.open('x') as f:os.chmod(target,0o600);json.dump(value,f)
    if not a.resume:
        (w/'home').mkdir(mode=0o700);(w/'bin').mkdir(mode=0o700)
        for name,body in {'getprop':'''case "$1" in
ro.product.model) echo 'ZTE V40';;
ro.product.manufacturer) echo ZTE;;
ro.build.version.sdk) echo 33;;
esac
''','pkg':'exit 99\n','python3':'exec '+shlex.quote(sys.executable)+' "$@"\n'}.items():
            f=w/'bin'/name;f.write_text('#!/bin/sh\n'+body);f.chmod(0o700)
        build(ROOT,w/'synthetic-source.tar.gz')
        with tarfile.open(w/'synthetic-source.tar.gz') as archive:archive.extractall(w/'source',filter='data')
    env['PATH']=str(w/'bin')+os.pathsep+os.environ['PATH']
    script=w/'source/asc-demo-alpha/scripts/demo-alpha.sh'
    def command(root,*args,secret=None):
        r=subprocess.run(['sh',str(script),'--state',str(root),*args],env=env,cwd=w,
                         input=secret,capture_output=True,text=True,timeout=90)
        if r.returncode:raise RuntimeError('synthetic Demo command refused; private state preserved')
        return json.loads(r.stdout[r.stdout.index('{'):])
    if not a.resume:
        config={'controller_port':port(),'dashboard_port':port(),'peer_port':port()}
        command(controller,'init','--role','controller','--host','127.0.0.1','--port',str(config['controller_port']))
        command(controller,'dashboard-init','--port',str(config['dashboard_port']))
        private('ports.json',config)
    config=json.loads((w/'ports.json').read_text());origin='https://127.0.0.1:'+str(config['controller_port'])
    cfg=json.loads((controller/'controller/controller.json').read_text());pin=fingerprint_from_pem(controller/'controller/server.crt')
    client=ClusterClient(origin,pin,cfg['admin_token'])
    processes=[];logs=[];instrument=None;browser=None;nat=None;report={'state':'ERROR','scope':f'Linux +API{a.android_api} x86_64 synthetic; not phones/physical domains',
       'adb_control_only':True,'native_identity_reset':False}
    def start(root,role):
        log=(w/(role+'-'+uuid.uuid4().hex+'.log')).open('wb');logs.append(log)
        child=subprocess.Popen(['sh',str(script),'--state',str(root),role,*(['--dashboard'] if role=='run-controller' else [])],
                               env=env,cwd=w,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
        processes.append(child);return child
    def stop(child):
        if child.poll() is None:child.send_signal(signal.SIGINT);child.wait(timeout=40)
    def wait(check,seconds=90):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            try:
                value=check()
                if value:return value
            except (OSError,ValueError,ClientError):pass
            time.sleep(.2)
        raise RuntimeError('actual qualification condition not established')
    def put(name,value):
        if name not in ('native-catalog-fixture.json','native-catalog-control.json'):raise ValueError('fixed private fixture only')
        call(['shell',"run-as org.asc.foundation sh -c 'umask 077; cat > files/"+name+".pending && mv files/"+name+".pending files/"+name+"'"],json.dumps(value).encode())
    def read(name):
        if name not in ('native-catalog-ready.json','native-catalog-ack.json'):raise ValueError('fixed public test receipt only')
        raw=subprocess.run(adb+['exec-out','run-as','org.asc.foundation','cat','files/'+name],capture_output=True,timeout=15)
        try:return json.loads(raw.stdout)
        except ValueError:return {}
    def control(action):
        operation=str(uuid.uuid4());put('native-catalog-control.json',{'request_id':request,'operation_id':operation,'action':action})
        return wait(lambda:read('native-catalog-ack.json').get('operation_id')==operation,40)
    def launch(retained):
        method='retainedNodeServesSameCatalogAfterProcessDeath' if retained else 'enrollAndServeActualDashboardReplicas'
        log=(run/('android-retained.log' if retained else 'android-initial.log')).open('wb');logs.append(log)
        child=subprocess.Popen(adb+['shell','am','instrument','-w','-r','-e','class','org.asc.foundation.NativeCatalogTest#'+method,
                     'org.asc.foundation.test/org.asc.foundation.UpgradeQualificationRunner'],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
        return child
    def native_ready():
        value=read('native-catalog-ready.json')
        if value.get('request_id')==request:return value
        if instrument.poll() is not None:raise RuntimeError('actual Native instrumentation exited before READY; preserve app/fixture')
        return False
    def verified_copies(file_id):
        check=client.request('POST','reconcile',{})
        if check.get('busy') is True:return False
        value=client.request('GET','files/'+file_id)
        return value if value['verified_replicas']==2 and value['available_replicas']==2 else False
    try:
        controller_process=start(controller,'run-controller');wait(lambda:request_json(origin,pin,'GET','/api/v1/info'))
        if not a.resume:
            command(peer,'init','--role','node','--host','127.0.0.1')
            pair=command(controller,'pair')
            command(peer,'join','--controller',origin,'--pin',pin,'--name','Synthetic Linux peer',secret=pair['code']+'\n')
            command(peer,'storage-init','--host','127.0.0.1','--port',str(config['peer_port']),'--quota',str(8*1024**2),'--reserve','0')
        peer_process=start(peer,'run-node')
        peer_cfg=json.loads((peer/'node/node.json').read_text());storage=json.loads((peer/'node/storage.json').read_text())
        if a.resume_setup:
            call(['shell',"run-as org.asc.foundation sh -c 'test ! -e files/identity-v1 && test ! -e files/native-runtime-v1 && test ! -e files/native-catalog-proof.json'"])
            with sqlite3.connect((controller/'controller/registry.sqlite3').as_uri()+'?mode=ro',uri=True) as db:
                if [r[0] for r in db.execute("SELECT node_id FROM nodes WHERE node_id!='local-controller'")]!=[peer_cfg['node_id']]:
                    raise ValueError('setup resume cannot discard an existing enrollment')
        with sqlite3.connect((peer/'node/storage/manifest.sqlite3').as_uri()+'?mode=ro',uri=True) as db:
            peer_volume=db.execute('SELECT volume_id FROM volumes').fetchone()[0]
        peer_pin=fingerprint_from_pem(peer/'node/storage.crt')
        command(controller,'approve','--node-id',peer_cfg['node_id'],'--volume-id',peer_volume,'--origin','https://127.0.0.1:'+str(config['peer_port']),
                '--pin',peer_pin,'--domain','synthetic-linux-host')
        request=str(uuid.uuid4())
        if not a.resume:
            pairing=command(controller,'pair');private('native-binding.json',{'origin':'https://10.0.2.2:'+str(config['controller_port']),
                'pin':pin.lower(),'cluster_id':cfg['cluster_id'],'join_request_id':str(uuid.uuid4()),'code':pairing['code']})
        elif a.resume_setup:
            previous=json.loads((w/'native-binding.json').read_text())
            if previous['cluster_id']!=cfg['cluster_id'] or previous['pin']!=pin.lower():raise ValueError('retained Controller binding mismatch')
            (w/'native-binding.json').rename(w/('native-binding-before-setup-resume-'+uuid.uuid4().hex+'.json'))
            pairing=command(controller,'pair');private('native-binding.json',dict(previous,code=pairing['code']))
        fixture=json.loads((w/'native-binding.json').read_text());put('native-catalog-fixture.json',dict(fixture,request_id=request))
        retained_start=a.resume and not a.resume_setup
        instrument=launch(retained_start)
        ready=wait(native_ready,240)
        nat=port()
        if b'OK' not in call(['emu','redir','add',f'tcp:{nat}:9443']):raise RuntimeError('owned standard SDK NAT not confirmed')
        if not any(f'127.0.0.1:{nat}' in line for line in subprocess.check_output(['ss','-ltn'],text=True).splitlines()):raise ValueError('NAT must be loopback-only')
        client.request('POST','nodes/register',{'node_id':ready['node_id'],'volume_ids':[ready['volume_id']],
           'origin':f'https://127.0.0.1:{nat}','pin':ready['pin'],'device_id':'synthetic-android-avd',
           'storage_allowed':True,'metadata_allowed':False})
        wait(lambda:client.request('POST','reconcile',{}))
        browser_out=run/'browser';browser_out.mkdir(mode=0o700)
        data=bytes(range(256))*1024;payload=run/'payload.bin';payload.write_bytes(data);sha=hashlib.sha256(data).hexdigest()
        grant=command(controller,'dashboard-code')
        browser_config={'origin':'https://127.0.0.1:'+str(config['dashboard_port']),'code':grant['code'],'ca':str(controller/'dashboard/ca.crt'),
          'payload':str(payload),'sha':sha,'output':str(browser_out),'logical':'native-browser/'+uuid.uuid4().hex+'/<img src=x onerror=globalThis.dashboardXss=1>.bin',
          'required_native_node_id':ready['node_id'],'existing_file_count':len(client.request('GET','files')['files'])}
        with (run/'browser.stdout').open('wb') as stdout,(run/'browser.stderr').open('wb') as stderr:
            browser=subprocess.Popen(['node',str(ROOT/'tests/browser/demo_dashboard.cjs')],cwd=ROOT,env=env,stdin=subprocess.PIPE,stdout=stdout,stderr=stderr)
            browser.stdin.write(json.dumps(browser_config).encode());browser.stdin.close()
            stopped=False;end=time.monotonic()+210
            while browser.poll() is None and time.monotonic()<end:
                if (browser_out/'stop-node.json').exists() and not stopped:
                    if json.loads((browser_out/'stop-node.json').read_text())['node_id']!=ready['node_id']:raise ValueError('must stop actual Native Node')
                    control('stop');stopped=True;(browser_out/'node-stopped').write_text('actual private Binder closed Native Node')
                time.sleep(.1)
            if browser.poll() is None:raise RuntimeError('actual browser integration deadline')
            if browser.returncode or not stopped:raise RuntimeError('actual browser failed; private sanitized diagnostics retained')
        result=json.loads((run/'browser.stdout').read_text());file_id=result['file_id']
        if hashlib.sha256((browser_out/'downloaded-after-node-offline.bin').read_bytes()).hexdigest()!=sha:raise ValueError('browser bytes mismatch')
        entry=client.request('GET','files/'+file_id)
        if {r['node_id'] for r in entry['replicas']}!={ready['node_id'],peer_cfg['node_id']}:raise ValueError('Native replica absent')
        control('start');wait(lambda:verified_copies(file_id),120)
        plan=client.request('POST','files/'+file_id+'/download',{})
        native=next(r for r in plan['candidates'] if r['node_id']==ready['node_id'])
        direct=StorageClient(native['origin'],native['pin'],native['grant'],native['volume_id'])
        output=io.BytesIO();direct.download(native['local_file_id'],output,len(data),sha)
        if output.getvalue()!=data:raise ValueError('Native restart bytes mismatch')
        stop(controller_process)
        connection=connect_pinned(native['origin'],native['pin']);connection.close() # Node still really listens.
        try:direct.download(native['local_file_id'],io.BytesIO(),len(data),sha)
        except ClientError as denied:
            if denied.status!=503 or denied.code!='authorization_unavailable':raise ValueError('actual online authorization refusal not proven')
        else:raise ValueError('Native accepted stale grant while Controller absent')
        controller_process=start(controller,'run-controller');wait(lambda:request_json(origin,pin,'GET','/api/v1/info'))
        control('finish');instrument.wait(timeout=60)
        initial_log=run/('android-retained.log' if retained_start else 'android-initial.log')
        if 'OK (1 test)' not in initial_log.read_text():raise RuntimeError('initial actual Android test incomplete')
        if retained_start:initial_log.rename(run/'android-resumed.log')
        call(['shell','am','force-stop','org.asc.foundation'])
        request=str(uuid.uuid4());put('native-catalog-fixture.json',dict(fixture,request_id=request));instrument=launch(True)
        retained=wait(native_ready,180)
        if any(retained[k]!=ready[k] for k in ('app_id','node_id','cluster_id','volume_id','pin','context_sha256')):raise ValueError('identity changed after process death')
        wait(lambda:verified_copies(file_id),120);output=io.BytesIO()
        retained_plan=client.request('POST','files/'+file_id+'/download',{})
        retained_native=next(r for r in retained_plan['candidates'] if r['node_id']==ready['node_id'])
        StorageClient(retained_native['origin'],retained_native['pin'],retained_native['grant'],retained_native['volume_id']).download(
            retained_native['local_file_id'],output,len(data),sha)
        if output.getvalue()!=data:raise ValueError('retained Catalog bytes mismatch')
        control('finish');instrument.wait(timeout=60)
        if 'OK (1 test)' not in (run/'android-retained.log').read_text():raise RuntimeError('retained actual Android test incomplete')
        report.update(state='PASS',native_android_tests=2,bytes=len(data),sha256=sha,logical_domains=2,physical_domain_independence=False,
                      actual_browser_login_upload_download=True,native_offline_fallback=True,controller_loss_denied=True,retained_process_identity=True,
                      entry_mode='retained resume' if retained_start else 'fresh initialization',fresh_initialization_junit_completed=not retained_start)
    except Exception as error:
        (run/'host-error-private.log').write_text(traceback.format_exc())
        report.update(state='FAIL',error_class=type(error).__name__,detail=str(error) if isinstance(error,RuntimeError) else 'qualification refused; private state retained')
    finally:
        if instrument is not None and instrument.poll() is None:
            try:control('finish');instrument.wait(timeout=50)
            except Exception:instrument.terminate()
        if browser is not None and browser.poll() is None:browser.terminate();browser.wait(timeout=15)
        if nat is not None:call(['emu','redir','del',f'tcp:{nat}'])
        for child in reversed(processes):stop(child)
        for log in logs:log.close()
        (run/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2));return 0 if report['state']=='PASS' else 1


if __name__=='__main__':sys.exit(main())
