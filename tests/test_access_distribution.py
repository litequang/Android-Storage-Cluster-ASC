"""Actual installed wrapper lifecycle and canonical access tests from bundle code."""
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from tools import package_access as package
from tests import test_access_gateway as fixtures
from tests.test_access_package import PIP,WHEELS


class InstalledAccessDistributionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='.asc-installed-access-',dir=Path.home());self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name);self.repo=Path(__file__).resolve().parents[1]
        self.artifacts=Path('/workspace/work/phase5-distribution');self.artifacts.mkdir(mode=0o700,exist_ok=True)
    def install(self,label,version,edge=False):
        archive=self.base/(label+'.tar.gz');report=package.build(self.repo,archive,version)
        code=self.base/(label+'-code');package.unpack(archive,code,report['sha256'])
        env=self.base/(label+'-env');package.prepare_env(code,env,edge,PIP if edge else None,WHEELS if edge else None)
        return code,env/'bin/python'
    def stop(self,child):
        if child.poll() is None:child.send_signal(signal.SIGINT)
        child.wait(timeout=25)
        self.assertEqual(child.returncode,0,'owned packaged gateway failed foreground stop')
    def start(self,code,python,f):
        log=(self.base/('gateway-'+str(time.monotonic_ns())+'.log')).open('w+')
        self.addCleanup(log.close)
        child=subprocess.Popen([str(python),'-I','-B',str(code/'access.py'),'gateway','--root',str(f.root),'serve'],
            cwd=self.base,stdout=log,stderr=log)
        self.addCleanup(self.stop,child)
        def ready():
            self.assertIsNone(child.poll(),'packaged gateway refused startup; private fixture log retained until cleanup')
            return f.request('GET','/api/mode',authenticated=False)[0]==200
        f.f.wait_for(ready);return child
    @staticmethod
    def inventory(root):return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
    def upload(self,f,path,key):
        data=f.f.data;sha=hashlib.sha256(data).hexdigest()
        status,_,raw=f.request('POST','/api/uploads',dict(logical_path=path,size=len(data),sha256=sha,idempotency_key=key))
        self.assertEqual(status,200,raw);transfer=json.loads(raw)['transfer_id']
        status,_,raw=f.request('PUT','/api/uploads/'+transfer,body=data,headers={'Content-Type':'application/octet-stream'})
        self.assertIn(status,(200,202),raw);file_id=json.loads(raw)['file']['file_id']
        def protected():
            f.request('POST','/api/refresh',{});status,_,raw=f.request('GET','/api/files/'+file_id)
            return status==200 and json.loads(raw)['protected']
        f.f.wait_for(protected);return file_id,sha

    def test_installed_https_upload_code_upgrade_profile_backup_and_old_code_rollback(self):
        f=fixtures.PrivateGatewayTests();self.addCleanup(f.doCleanups);f.setUp();f.stop_gateway()
        identity=self.inventory(f.root)
        code1,python1=self.install('first','0.1.0-internal');child=self.start(code1,python1,f)
        f.login();file1,sha=self.upload(f,'distribution/before.bin','distribution_before_001')
        self.stop(child)
        backup=self.base/'private-profile-backup';shutil.copytree(f.root,backup)
        self.assertEqual(self.inventory(backup),identity)
        for p in backup.rglob('*'):
            if p.is_file():self.assertEqual(p.stat().st_mode&0o777,0o600)
        # Separate immutable CODE/env version; no profile/Node state copy/adoption.
        code2,python2=self.install('second','0.1.1-internal');child=self.start(code2,python2,f)
        self.assertEqual(f.request('GET','/api/state')[0],200,'backend session must survive access-code switch')
        file2,_=self.upload(f,'distribution/after.bin','distribution_after_001')
        self.assertEqual(self.inventory(f.root),identity);self.stop(child)
        # No old backup restored: old code directly serves BOTH newer/current files.
        child=self.start(code1,python1,f)
        for file_id in (file1,file2):
            status,headers,raw=f.request('GET','/api/files/'+file_id+'/content')
            self.assertEqual((status,raw),(200,f.f.data));self.assertEqual(headers['X-ASC-SHA256'],sha)
        node=headers['X-ASC-Replica-Node'];f.f.stop(next(n for n in f.f.nodes if n['cfg']['node_id']==node)['process'])
        status,headers,raw=f.request('GET','/api/files/'+file2+'/content')
        self.assertEqual((status,raw),(200,f.f.data));self.assertNotEqual(headers['X-ASC-Replica-Node'],node)
        self.assertEqual(self.inventory(f.root),identity)
        self.assertEqual(self.inventory(backup),identity);self.stop(child)

    def test_original_42_access_gates_with_installed_canonical_modules_and_real_edge_env(self):
        code,python=self.install('all-access','0.1.0-internal',True)
        # Keep prior private QA images/results, not any app/AVD/private Node data.
        preserved=self.artifacts/('previous-browser-'+str(time.monotonic_ns()));preserved.mkdir(mode=0o700)
        for name in ('phase5-private-browser','phase5-edge-browser'):
            old=Path('/workspace/work')/name
            if old.is_dir():shutil.copytree(old,preserved/name)
        modules=['tests.test_access_policy','tests.test_access_gateway','tests.test_access_jwt',
            'tests.test_access_cloudflare','tests.test_access_browser','tests.test_access_observer',
            'tests.test_access_edge_qualification','tests.test_access_maintenance']
        driver='''import sys,pathlib,unittest
code,repo=sys.argv[1:3];sys.path[:0]=[code,repo]
import asc,asc.access.gateway,asc.access.cloudflare,asc.access.maintenance
for module in (asc,asc.access.gateway,asc.access.cloudflare,asc.access.maintenance):
 assert pathlib.Path(module.__file__).resolve().is_relative_to(pathlib.Path(code))
suite=unittest.defaultTestLoader.loadTestsFromNames(sys.argv[3:]);assert suite.countTestCases()==42
result=unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() and result.testsRun==42 and not result.skipped else 1)
'''
        env=dict(os.environ,PYTHONPATH=str(code),PYTHONDONTWRITEBYTECODE='1',GOMAXPROCS='2',
            ASC_GO=os.environ.get('ASC_GO','/workspace/asc-cloud/go1.27.3/go/bin/go'))
        log=self.artifacts/('installed-42-'+str(time.monotonic_ns())+'.log')
        with log.open('x') as output:
            result=subprocess.run([str(python),'-I','-B','-c',driver,str(code),str(self.repo),*modules],
                cwd=self.base,env=env,stdout=output,stderr=subprocess.STDOUT,timeout=420)
        self.assertEqual(result.returncode,0,'installed canonical access regression failed; inspect private installed-42 log')
        (self.artifacts/'latest-installed-log.txt').write_text(str(log)+'\n')
