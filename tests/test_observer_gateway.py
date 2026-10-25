"""Shared trusted-HTTPS owner facade, actual Core cluster, browser and passive stage."""
import contextlib
import hashlib
import http.client
from http.cookies import SimpleCookie
import io
import json
import os
import re
from pathlib import Path
import socket
import ssl
import subprocess
import time
import unittest
from unittest import mock
from asc.observability import gateway
from asc.bridge import private
from asc.external.recovery import stage
from tests import test_observability as cluster
from tests import test_external as memory


class GatewayFixture(cluster.ObservationClusterFixture):
    @staticmethod
    def port():
        with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]

    def setup_gateway(self):
        self.gateway_root=self.base/'read-only-gateway';self.gateway_port=self.port()
        gateway.init(self.gateway_root,'127.0.0.1',self.gateway_port,self.cluster,self.epoch,self.endpoints,source_roots=self.homes)
        self.origin_browser='https://127.0.0.1:'+str(self.gateway_port)
        self.context=ssl.create_default_context(cafile=str(self.gateway_root/'dashboard/ca.crt'))
        self.cookie='';self.csrf=''

    def browser_request(self,method,path,obj=None,authenticated=True,headers=None):
        connection=http.client.HTTPSConnection('127.0.0.1',self.gateway_port,context=self.context,timeout=40)
        sent={'Origin':self.origin_browser}
        if obj is not None:sent['Content-Type']='application/json'
        if authenticated and self.cookie:sent.update(Cookie=self.cookie,**{'X-ASC-CSRF':self.csrf})
        if headers:sent.update(headers)
        try:
            connection.request(method,path,json.dumps(obj) if obj is not None else None,sent)
            response=connection.getresponse();return response.status,dict(response.getheaders()),response.read()
        finally:connection.close()

    def owner_login(self,runtime):
        status,headers,body=self.browser_request('POST','/api/login',{'code':runtime.api.sessions.issue()},False)
        self.assertEqual(status,200)
        cookies=SimpleCookie(headers['Set-Cookie']);name=runtime.api.cookie_name
        self.cookie=name+'='+cookies[name].value;self.csrf=json.loads(body)['csrf']
        self.assertNotEqual(name,'__Host-ASC-Demo')


class GatewayHTTPTests(GatewayFixture):
    def test_owner_ca_session_mode_and_all_mutations_denied_before_core(self):
        self.make_cluster()
        with mock.patch.dict(os.environ,{'HOME':str(self.base)}):
            self.setup_gateway()
            with gateway.Runtime(self.gateway_root) as runtime:
                self.assertEqual(json.loads(self.browser_request('GET','/api/mode',authenticated=False)[2]),
                                 {'mode':'core-quorum','read_only':True})
                self.assertEqual(self.browser_request('GET','/api/state',authenticated=False)[0],401)
                self.owner_login(runtime)
                session=json.loads(self.browser_request('GET','/api/session')[2]);self.assertTrue(session['read_only'])
                self.assertEqual(session['mode'],'core-quorum');self.assertEqual(session['max_upload_bytes'],0)
                snapshot=json.loads(self.browser_request('GET','/api/state')[2]);self.assertFalse(snapshot['writer_authority'])
                self.assertTrue(snapshot['runtime']['quorum_available'])
                for method,path in [('POST','/api/refresh'),('POST','/api/uploads'),('POST','/api/v1/quick-join/pairings'),
                    ('POST','/api/approve'),('POST','/api/gc'),('POST','/api/promote'),('POST','/api/recovery/activate'),
                    ('GET','/api/files/11111111-1111-4111-8111-111111111111/content')]:
                    self.assertEqual(self.browser_request(method,path,{} if method=='POST' else None)[0],403,(method,path))
                self.assertNotEqual(self.browser_request('POST','/api/logout',{},headers={'Origin':'https://attacker.invalid'})[0],200)
                self.assertNotEqual(self.browser_request('GET','/api/state',headers={'X-ASC-CSRF':'wrong'})[0],200)
                self.assertEqual(self.browser_request('GET','/../gateway.json')[0],400)
                self.assertEqual(self.browser_request('GET','/gateway.json')[0],403)
                self.assertEqual(self.browser_request('POST','/api/logout',{})[0],200)
                self.assertEqual(self.browser_request('GET','/api/state')[0],401)
                untrusted=ssl.create_default_context()
                connection=http.client.HTTPSConnection('127.0.0.1',self.gateway_port,context=untrusted,timeout=5)
                try:
                    with self.assertRaises(ssl.SSLError):connection.request('GET','/')
                finally:connection.close()
            cfg=private.read(self.gateway_root/'gateway.json');cfg['mode']='single-writer-demo'
            private.replace(self.gateway_root/'gateway.json',cfg)
            with self.assertRaises(ValueError):gateway.load(self.gateway_root)
            with self.assertRaises(ValueError):gateway.init(self.base/'public-gateway','0.0.0.0',self.port(),self.cluster,self.epoch,self.endpoints)
            self.assertFalse((self.base/'public-gateway').exists())


class GatewayBrowserTests(GatewayFixture):
    def test_actual_trusted_shared_browser_three_nodes_policy3_quorum_loss_and_heal(self):
        self.make_cluster();data=b'Core shared browser bytes\0'*1200
        logical='core/<img src=x onerror=globalThis.coreXss=1>.bin'
        uploaded=self.owner.upload(io.BytesIO(data),logical,'core_browser_actual','replicated_3')
        if uploaded['job_state']!='COMPLETED':self.wait_job(uploaded['job_id'])
        self.wait_copies(uploaded['file']['file']['file_id'],3)
        with mock.patch.dict(os.environ,{'HOME':str(self.base)}):
            self.setup_gateway()
            with gateway.Runtime(self.gateway_root) as runtime:
                output=self.base/'core-browser';output.mkdir(mode=0o700)
                config={'origin':self.origin_browser,'code':runtime.api.sessions.issue(),
                        'ca':str(self.gateway_root/'dashboard/ca.crt'),'output':str(output),'logical':logical}
                script=Path(__file__).parent/'browser/core_observer.cjs'
                process=subprocess.Popen(['node',str(script)],cwd=script.parents[2],stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                process.stdin.write(json.dumps(config));process.stdin.close()
                self.addCleanup(lambda:process.kill() if process.poll() is None else None)
                partitioned=healed=False;deadline=time.monotonic()+120
                while process.poll() is None and time.monotonic()<deadline:
                    if (output/'partition').exists() and not partitioned:
                        self.split([{0},{1},{2}]);(output/'partitioned').write_text('actual three-island transport partition');partitioned=True
                    if (output/'heal').exists() and not healed:
                        self.split([set(range(3))]);self.wait_ready();(output/'healed').write_text('actual quorum read restored');healed=True
                    time.sleep(.1)
                if process.poll() is None:process.kill()
                process.wait(timeout=10);stdout=process.stdout.read();stderr=process.stderr.read()
                process.stdout.close();process.stderr.close()
                safe=re.findall(r'Synthetic Core observer browser failed at [a-z-]+: [A-Za-z]+; credentials suppressed\.',stderr)
                self.assertEqual(process.returncode,0,safe[-1] if safe else 'Core browser gate failed; private output suppressed')
                self.assertTrue(json.loads(stdout)['passed']);self.assertTrue(partitioned);self.assertTrue(healed)


class RecoveryGatewayTests(unittest.TestCase):
    setUp=memory.ExternalBackupTests.setUp
    port=staticmethod(GatewayFixture.port)
    browser_request=GatewayFixture.browser_request
    owner_login=GatewayFixture.owner_login

    def test_verified_recovery_gateway_shared_read_only_mode_no_runtime_creation(self):
        backup=self.engine.create(self.source,self.roots);root=self.base/'passive-stage';root.mkdir(mode=0o700)
        stage(self.store,backup['backup_id'],backup['manifest_sha256'],root,self.roots,self.source.doc['cluster_id'],100)
        before={p.relative_to(root):p.read_bytes() for p in root.rglob('*') if p.is_file()}
        self.gateway_root=self.base/'passive-gateway';self.gateway_port=self.port();self.origin_browser='https://127.0.0.1:'+str(self.gateway_port)
        with mock.patch.dict(os.environ,{'HOME':str(self.base)}):
            gateway.init(self.gateway_root,'127.0.0.1',self.gateway_port,self.source.doc['cluster_id'],self.source.doc['epoch'],
                recovery={'root':str(root),'anchor':backup['manifest_sha256']},source_roots=self.roots,minimum_index=100)
            self.context=ssl.create_default_context(cafile=str(self.gateway_root/'dashboard/ca.crt'));self.cookie='';self.csrf=''
            with gateway.Runtime(self.gateway_root) as runtime:
                self.owner_login(runtime)
                self.assertEqual(json.loads(self.browser_request('GET','/api/mode',authenticated=False)[2])['mode'],'recovery-read-only')
                state=json.loads(self.browser_request('GET','/api/state')[2])
                self.assertEqual(state['runtime']['state'],'RECOVERY READ-ONLY');self.assertFalse(state['writer_authority'])
                self.assertFalse(state['backup']['recovery']['credentials_restored'])
                self.assertEqual(self.browser_request('POST','/api/recovery/activate',{})[0],403)
            self.assertEqual(before,{p.relative_to(root):p.read_bytes() for p in root.rglob('*') if p.is_file()})
            self.assertFalse((root/'registry.sqlite3').exists());self.assertFalse((root/'controller.json').exists())
