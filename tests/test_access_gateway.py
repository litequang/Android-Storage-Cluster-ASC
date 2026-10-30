"""Actual trusted TLS/private ingress into existing two-node owner Dashboard."""
from contextlib import closing
import hashlib
import http.client
from http.cookies import SimpleCookie
import json
from pathlib import Path
import ssl
import socket
import signal
import subprocess
import sys
import time
import tempfile
import unittest
from asc.access.gateway import initialize, load, Runtime
from asc.client import ClientError
from asc.identity import fingerprint_from_pem
from tests import test_demo_dashboard as dashboard_fixture


class PrivateGatewayTests(unittest.TestCase):
    def setUp(self):
        self.f=dashboard_fixture.DashboardAPITests();self.addCleanup(self.f.doCleanups);self.f.setUp()
        self.temp=tempfile.TemporaryDirectory(prefix='.asc-access-test-',dir=Path.home());self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'gateway'
        self.cfg=dict(format=1,mode='private-gateway',frontend_origin='https://127.0.0.1:'+str(self.f.free_port()),
            upstream_origin=self.f.browser_origin,upstream_pin=fingerprint_from_pem(self.f.controller/'dashboard/server.crt').lower(),
            upstream_mode='single-writer-demo',max_body_bytes=1024**2)
        initialize(self.root,self.cfg);self.runtime=Runtime(self.root);self.runtime.__enter__();self.addCleanup(self.stop_gateway)
        self.origin=self.cfg['frontend_origin'];self.port=int(self.origin.rsplit(':',1)[1])
        self.tls=ssl.create_default_context(cafile=str(self.root/'dashboard/ca.crt'));self.cookie='';self.csrf=''

    def stop_gateway(self):
        if self.runtime is not None:self.runtime.__exit__(None,None,None);self.runtime=None

    def request(self,method,path,obj=None,body=None,headers=None,authenticated=True):
        sent={'Origin':self.origin}
        if obj is not None:body=json.dumps(obj).encode();sent['Content-Type']='application/json'
        if authenticated and self.cookie:sent.update(Cookie=self.cookie,**{'X-ASC-CSRF':self.csrf})
        if headers:sent.update(headers)
        with closing(http.client.HTTPSConnection('127.0.0.1',self.port,context=self.tls,timeout=45)) as c:
            c.request(method,path,body,sent);response=c.getresponse();raw=response.read()
            return response.status,dict(response.getheaders()),raw

    def login(self):
        grant=self.f.command(self.f.controller,'dashboard-code')
        status,headers,raw=self.request('POST','/api/login',{'code':grant['code']},authenticated=False)
        self.assertEqual(status,200,raw);parsed=SimpleCookie(headers['Set-Cookie'])
        self.cookie='__Host-ASC-Demo='+parsed['__Host-ASC-Demo'].value;self.csrf=json.loads(raw)['csrf']
        return grant['code']

    def test_real_login_upload_two_replicas_sha_and_offline_fallback(self):
        self.assertEqual(self.request('GET','/api/state')[0],401)
        code=self.login();self.assertEqual(self.request('POST','/api/login',{'code':code},authenticated=False)[0],401)
        data=self.f.data;sha=hashlib.sha256(data).hexdigest()
        status,_,raw=self.request('POST','/api/uploads',{'logical_path':'remote/actual.bin','size':len(data),
            'sha256':sha,'idempotency_key':'remote_qualify_001'})
        self.assertEqual(status,200,raw);ticket=json.loads(raw)['transfer_id']
        status,_,raw=self.request('PUT','/api/uploads/'+ticket,body=data,headers={'Content-Type':'application/octet-stream'})
        self.assertIn(status,(200,202),raw);file_id=json.loads(raw)['file']['file_id']
        def protected():
            self.request('POST','/api/refresh',{})
            status,_,raw=self.request('GET','/api/files/'+file_id)
            return json.loads(raw) if status==200 and json.loads(raw)['protected'] else False
        entry=self.f.wait_for(protected)
        status,headers,raw=self.request('GET','/api/files/'+file_id+'/content')
        self.assertEqual((status,raw),(200,data));self.assertEqual(headers['X-ASC-SHA256'],sha)
        node=headers['X-ASC-Replica-Node'];self.f.stop(next(n for n in self.f.nodes if n['cfg']['node_id']==node)['process'])
        status,headers,raw=self.request('GET','/api/files/'+file_id+'/content')
        self.assertEqual((status,raw),(200,data));self.assertNotEqual(headers['X-ASC-Replica-Node'],node)

    def test_external_origin_csrf_bearer_and_admin_routes_are_not_forwarded(self):
        self.login()
        status,headers,raw=self.request('GET','/api/capabilities')
        self.assertEqual(status,200);self.assertFalse(json.loads(raw)['node_management'])
        self.assertFalse(json.loads(raw)['account_management'])
        self.assertEqual(headers['X-ASC-Access-Mode'],'file-access-only')
        for headers in ({'Host':'evil.invalid'},{'Origin':'https://evil.invalid'},{'Sec-Fetch-Site':'cross-site'}):
            self.assertEqual(self.request('GET','/api/state',headers=headers)[0],403)
        self.assertEqual(self.request('POST','/api/refresh',{},headers={'X-ASC-CSRF':'wrong'})[0],401)
        self.assertEqual(self.request('POST','/api/refresh',{},authenticated=False,headers={'Cookie':self.cookie})[0],403)
        self.assertEqual(self.request('GET','/api/state',headers={'Authorization':'Bearer synthetic'})[0],400)
        for path in ('/api/v1/nodes','/storage/v1/files','/api/gc','/api/activate','/api/v1/quick-join/pairings',
                     '/api/manage/v1/nodes/local-controller/preview','/api/manage/v1/confirm/anything'):
            self.assertEqual(self.request('POST',path,{})[0],403)
        self.assertEqual(self.request('GET','/api/accounts')[0],403)
        self.assertEqual(self.request('POST','/api/accounts',{})[0],403)
        self.assertEqual(self.request('POST','/api/accounts/primary/change',{})[0],403)
        self.assertEqual(self.request('GET','/api/state',authenticated=False,headers={'Forwarded':'for=127.0.0.1','X-Forwarded-User':'owner'})[0],401)

    def test_wrong_pin_mode_and_existing_identity_cannot_be_silently_replaced(self):
        with closing(http.client.HTTPSConnection('127.0.0.1',self.port,context=ssl.create_default_context(),timeout=4)) as c:
            with self.assertRaises(ssl.SSLError):c.connect()
        before=(self.root/'dashboard/server.crt').read_bytes();self.stop_gateway()
        self.assertEqual(initialize(self.root,self.cfg)['url'],self.origin)
        for field,value in [('upstream_pin','b'*64),('upstream_mode','core-quorum')]:
            cfg=dict(self.cfg);cfg[field]=value;other=Path(self.temp.name)/field
            initialize(other,cfg)
            with self.assertRaises(ClientError if field=='upstream_pin' else ValueError):
                with Runtime(other):pass
        changed=dict(self.cfg);changed['upstream_pin']='b'*64
        with self.assertRaises(ValueError):initialize(self.root,changed)
        self.assertEqual((self.root/'dashboard/server.crt').read_bytes(),before)
        with closing(http.client.HTTPSConnection('127.0.0.1',int(self.f.browser_origin.rsplit(':',1)[1]),context=ssl.create_default_context(),timeout=4)) as c:
            with self.assertRaises(ssl.SSLError):c.connect()

    def test_framing_and_size_fail_before_forwarding_body(self):
        self.login()
        self.assertEqual(self.request('POST','/api/uploads',body=b'',headers={'Content-Length':'8193'})[0],413)
        self.assertEqual(self.request('POST','/api/uploads',body=b'{}',headers={'Transfer-Encoding':'chunked'})[0],400)
        with closing(http.client.HTTPSConnection('127.0.0.1',self.port,context=self.tls,timeout=10)) as c:
            c.putrequest('POST','/api/login');c.putheader('Origin',self.origin)
            c.putheader('Content-Length','2');c.putheader('Content-Length','2');c.endheaders()
            response=c.getresponse();self.assertEqual(response.status,400);response.read()

    def test_gateway_restart_keeps_backend_session_but_backend_restart_revokes_it(self):
        self.login();cert=(self.root/'dashboard/server.crt').read_bytes();self.stop_gateway()
        self.runtime=Runtime(self.root);self.runtime.__enter__()
        self.assertEqual(self.request('GET','/api/state')[0],200)
        self.assertEqual((self.root/'dashboard/server.crt').read_bytes(),cert)
        self.f.stop(self.f.controller_process)
        self.assertEqual(self.request('GET','/api/state')[0],503)
        self.f.controller_process=self.f.start(self.f.controller,'run-controller')
        self.assertEqual(self.request('GET','/api/state')[0],401)
        self.login();self.assertEqual(self.request('GET','/api/state')[0],200)

    def test_cli_private_init_info_and_foreground_stop(self):
        root=Path(self.temp.name)/'cli';source=Path(__file__).resolve().parents[1]
        cfg=dict(self.cfg,frontend_origin='https://127.0.0.1:'+str(self.f.free_port()))
        path=Path(self.temp.name)/'profile.json';path.write_text(json.dumps(cfg));path.chmod(0o600)
        cli=[sys.executable,'-m','asc.access.gateway','--root',str(root)]
        for args in (['init','--profile',str(path)],['info']):
            result=subprocess.run(cli+args,cwd=source,capture_output=True,timeout=15)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertFalse(json.loads(result.stdout)['writer_authority'])
        child=subprocess.Popen(cli+['serve'],cwd=source,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        def cleanup():
            if child.poll() is None:child.send_signal(signal.SIGINT)
            child.communicate(timeout=15)
        self.addCleanup(cleanup)
        context=ssl.create_default_context(cafile=str(root/'dashboard/ca.crt'));deadline=time.monotonic()+15;connected=False
        while time.monotonic()<deadline:
            self.assertIsNone(child.poll(),'CLI refused foreground runtime')
            try:
                with closing(http.client.HTTPSConnection('127.0.0.1',int(cfg['frontend_origin'].rsplit(':',1)[1]),context=context,timeout=1)) as c:
                    c.request('GET','/api/mode',headers={'Origin':cfg['frontend_origin']})
                    response=c.getresponse();self.assertEqual(response.status,200)
                    self.assertEqual(json.loads(response.read())['mode'],'single-writer-demo');connected=True
                break
            except OSError:time.sleep(.1)
        self.assertTrue(connected)
        child.send_signal(signal.SIGINT);out,err=child.communicate(timeout=15)
        self.assertEqual(child.returncode,0,err);self.assertTrue(json.loads(out)['listener_started'])
