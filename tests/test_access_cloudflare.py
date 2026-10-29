"""Actual local TLS/JWKS/owner/file I/O, synthetic issuer, never a live tunnel."""
from contextlib import closing
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import http.client
import json
from pathlib import Path
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import uuid
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from asc.access import cloudflare as edge
from asc.access.access_jwt import AccessVerifier, KEY_TTL
from asc.access.gateway import load as load_private
from asc.client import ClientError, request_json
from asc.demo.dashboard.tls import generate_identity
from asc.identity import fingerprint_from_pem
from tests import test_demo_dashboard as fixtures
from tests import test_access_gateway as private_fixture


class EdgeOriginTests(unittest.TestCase):
    stop_gateway=private_fixture.PrivateGatewayTests.stop_gateway
    login=private_fixture.PrivateGatewayTests.login

    def setUp(self):
        self.f=fixtures.DashboardAPITests();self.addCleanup(self.f.doCleanups);self.f.setUp()
        self.temp=tempfile.TemporaryDirectory(prefix='.asc-edge-test-',dir=Path.home());self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name);self.root=self.base/'edge'
        self.port=self.f.free_port();self.origin='https://asc.example.com'
        self.cfg=dict(format=2,mode='cloudflare-edge',frontend_origin=self.origin,
            listen_origin='https://127.0.0.1:'+str(self.port),upstream_origin=self.f.browser_origin,
            upstream_pin=fingerprint_from_pem(self.f.controller/'dashboard/server.crt').lower(),
            upstream_mode='single-writer-demo',max_body_bytes=1024**2,
            access_team='asc-synthetic',access_audience='a'*64)
        edge.initialize(self.root,self.cfg)
        self.key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        body=json.dumps({'keys':[dict(json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(self.key.public_key())),
            kid='local-key',alg='RS256',use='sig')]}).encode()
        keyroot=self.base/'keys';keyroot.mkdir(mode=0o700);generate_identity(keyroot,'127.0.0.1','Synthetic JWKS')
        class Keys(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(inner):
                reply=body
                if inner.path=='/api/mode':reply=b'{"mode":"single-writer-demo","read_only":false}'
                if inner.path=='/api/state':
                    inner.server.observed_headers=dict(inner.headers);reply=b'{"observed":true}'
                inner.send_response(200 if inner.path in ('/cdn-cgi/access/certs','/api/mode','/api/state') else 404)
                inner.send_header('Content-Type','application/json');inner.send_header('Content-Length',str(len(reply)))
                inner.end_headers();inner.wfile.write(reply)
        server=ThreadingHTTPServer(('127.0.0.1',0),Keys)
        context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.minimum_version=ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(keyroot/'server.crt',keyroot/'server.key')
        server.socket=context.wrap_socket(server.socket,server_side=True)
        self.keys_server=server;self.keys_thread=threading.Thread(target=server.serve_forever,daemon=True)
        self.keys_thread.start();self.addCleanup(self.stop_keys)
        key_origin='https://127.0.0.1:'+str(server.server_port);pin=fingerprint_from_pem(keyroot/'server.crt').lower()
        self.key_origin=key_origin;self.key_pin=pin
        def fetch(url):
            self.assertEqual(url,'https://asc-synthetic.cloudflareaccess.com/cdn-cgi/access/certs')
            # Real pinned HTTPS; trusted fixture changes only transport location, not JWT checks.
            return request_json(key_origin,pin,'GET','/cdn-cgi/access/certs',timeout=2)
        self.clock=[100.];self.verifier=AccessVerifier('asc-synthetic','a'*64,fetcher=fetch,clock=lambda:self.clock[0])
        self.runtime=edge.Runtime(self.root,verifier=self.verifier);self.runtime.__enter__();self.addCleanup(self.stop_gateway)
        self.tls=ssl.create_default_context(cafile=str(self.root/'dashboard/ca.crt'));self.cookie='';self.csrf=''
        self.token=self.signed()

    def stop_keys(self):
        if self.keys_server is not None:
            self.keys_server.shutdown();self.keys_server.server_close();self.keys_thread.join();self.keys_server=None

    def signed(self,**changes):
        now=int(time.time());claims=dict(iss=self.verifier.issuer,aud=['a'*64],sub='synthetic-owner',type='app',iat=now-1,exp=now+300)
        claims.update(changes)
        return jwt.encode(claims,self.key,algorithm='RS256',headers={'kid':'local-key'})

    def request(self,method,path,obj=None,body=None,headers=None,authenticated=True,access=True):
        sent={'Host':'asc.example.com','Origin':self.origin}
        if access:sent['Cf-Access-Jwt-Assertion']=self.token
        if obj is not None:body=json.dumps(obj).encode();sent['Content-Type']='application/json'
        if authenticated and self.cookie:sent.update(Cookie=self.cookie,**{'X-ASC-CSRF':self.csrf})
        if headers:sent.update(headers)
        with closing(http.client.HTTPSConnection('127.0.0.1',self.port,context=self.tls,timeout=45)) as connection:
            connection.request(method,path,body,sent);response=connection.getresponse()
            return response.status,dict(response.getheaders()),response.read()

    def test_access_is_additional_to_owner_and_never_consumes_code_without_jwt(self):
        self.assertEqual(self.request('GET','/api/state')[0],401)
        grant=self.f.command(self.f.controller,'dashboard-code')
        self.assertEqual(self.request('POST','/api/login',{'code':grant['code']},access=False)[0],403)
        status,headers,raw=self.request('POST','/api/login',{'code':grant['code']})
        self.assertEqual(status,200,raw);parsed=SimpleCookie(headers['Set-Cookie'])
        self.cookie='__Host-ASC-Demo='+parsed['__Host-ASC-Demo'].value;self.csrf=json.loads(raw)['csrf']
        self.assertEqual(self.request('GET','/api/state')[0],200)
        for token in ('invalid',self.signed(aud=['b'*64]),self.signed(iss='https://other.cloudflareaccess.com'),self.signed(exp=int(time.time())-1)):
            self.assertEqual(self.request('GET','/api/state',headers={'Cf-Access-Jwt-Assertion':token})[0],403)
        self.assertEqual(self.request('GET','/api/state',access=False,headers={'Cookie':'CF_Authorization='+self.token,
            'Cf-Access-Authenticated-User-Email':'owner@example.com'})[0],403)
        self.assertEqual(self.request('POST','/api/refresh',{},headers={'X-ASC-CSRF':'incorrect'})[0],401)
        for headers in ({'Host':'evil.invalid'},{'Origin':'https://evil.invalid'},{'Sec-Fetch-Site':'cross-site'}):
            self.assertEqual(self.request('GET','/api/state',headers=headers)[0],403)
        with closing(http.client.HTTPSConnection('127.0.0.1',self.port,context=self.tls,timeout=4)) as c:
            c.putrequest('GET','/api/state',skip_host=True);c.putheader('Host','asc.example.com')
            c.putheader('Cf-Access-Jwt-Assertion',self.token);c.putheader('Cf-Access-Jwt-Assertion',self.token);c.endheaders()
            response=c.getresponse();self.assertEqual(response.status,403);response.read()

    def test_actual_two_node_bytes_sha_and_fallback(self):
        self.login();data=self.f.data;sha=hashlib.sha256(data).hexdigest()
        status,_,raw=self.request('POST','/api/uploads',{'logical_path':'edge/actual.bin','size':len(data),
            'sha256':sha,'idempotency_key':'edge_actual_001'})
        self.assertEqual(status,200,raw);transfer=json.loads(raw)['transfer_id']
        status,_,raw=self.request('PUT','/api/uploads/'+transfer,body=data,headers={'Content-Type':'application/octet-stream'})
        self.assertIn(status,(200,202),raw);file_id=json.loads(raw)['file']['file_id']
        def protected():
            self.request('POST','/api/refresh',{});status,_,raw=self.request('GET','/api/files/'+file_id)
            return status==200 and json.loads(raw)['protected']
        self.f.wait_for(protected)
        status,headers,raw=self.request('GET','/api/files/'+file_id+'/content')
        self.assertEqual((status,raw),(200,data));self.assertEqual(headers['X-ASC-SHA256'],sha)
        node=headers['X-ASC-Replica-Node'];self.f.stop(next(n for n in self.f.nodes if n['cfg']['node_id']==node)['process'])
        status,headers,raw=self.request('GET','/api/files/'+file_id+'/content')
        self.assertEqual((status,raw),(200,data));self.assertNotEqual(headers['X-ASC-Replica-Node'],node)

    def test_real_key_endpoint_loss_and_expired_cache_fail_closed(self):
        self.login();self.assertEqual(self.request('GET','/api/state')[0],200)
        self.stop_keys();self.clock[0]+=KEY_TTL+1
        status,_,raw=self.request('GET','/api/state');self.assertEqual(status,503,raw)
        self.assertEqual(json.loads(raw),{'protocol_version':1,'error':'edge_keys_unavailable'})

    def test_identity_pin_mode_cookie_filter_and_connector_contract(self):
        self.login()
        self.assertEqual(self.request('GET','/api/state',headers={'Cookie':self.cookie+'; CF_Authorization=not_forwarded'})[0],200)
        self.assertEqual(self.request('GET','/api/state',headers={'Cookie':self.cookie+'; '+self.cookie})[0],400)
        for path in ('/api/v1/nodes','/storage/v1/files','/api/gc','/api/activate'):
            self.assertEqual(self.request('POST',path,{})[0],403)
        before=(self.root/'dashboard/server.crt').read_bytes();self.stop_gateway()
        self.assertEqual(edge.initialize(self.root,self.cfg)['url'],self.origin)
        changed=dict(self.cfg,upstream_pin='b'*64)
        with self.assertRaises(ValueError):edge.initialize(self.root,changed)
        with self.assertRaises(ValueError):load_private(self.root)
        for field,value in [('upstream_pin','b'*64),('upstream_mode','core-quorum')]:
            cfg=dict(self.cfg);cfg[field]=value;root=self.base/field;edge.initialize(root,cfg)
            with self.assertRaises(ClientError if field=='upstream_pin' else ValueError):
                with edge.Runtime(root,verifier=self.verifier):pass
        self.assertEqual((self.root/'dashboard/server.crt').read_bytes(),before)
        credential=self.base/'never-read-credentials.json'
        config=edge.connector(self.root,edge.load(self.root),str(uuid.uuid4()),credential)
        self.assertFalse(credential.exists());self.assertEqual(config['ingress'][-1],{'service':'http_status:404'})
        origin=config['ingress'][0]['originRequest'];self.assertFalse(origin['noTLSVerify'])
        self.assertTrue(origin['access']['required']);self.assertEqual(origin['access']['audTag'],['a'*64])
        self.assertEqual(origin['httpHostHeader'],'asc.example.com');self.assertEqual(origin['originServerName'],'127.0.0.1')
        self.runtime=edge.Runtime(self.root,verifier=self.verifier);self.runtime.__enter__()
        with closing(http.client.HTTPSConnection('127.0.0.1',self.port,context=ssl.create_default_context(),timeout=4)) as c:
            with self.assertRaises(ssl.SSLError):c.connect()
        self.assertEqual(self.request('GET','/api/state')[0],200)

    def test_assertion_and_cloudflare_cookies_never_reach_real_tls_upstream(self):
        self.login();owner=self.cookie;self.stop_gateway()
        # A real TLS recording transport, not an authorization or Catalog substitute.
        self.root=self.base/'recording-edge';cfg=dict(self.cfg,upstream_origin=self.key_origin,upstream_pin=self.key_pin)
        edge.initialize(self.root,cfg);self.tls=ssl.create_default_context(cafile=str(self.root/'dashboard/ca.crt'))
        self.runtime=edge.Runtime(self.root,verifier=self.verifier);self.runtime.__enter__()
        status,_,_=self.request('GET','/api/state',headers={'Cookie':owner+'; CF_Authorization='+self.token+'; other=ignored',
            'Cf-Access-Authenticated-User-Email':'owner@example.com','Forwarded':'for=127.0.0.1'})
        self.assertEqual(status,200);observed=self.keys_server.observed_headers
        self.assertEqual(observed['Cookie'],owner)
        names={name.lower() for name in observed}
        self.assertFalse(any(name.startswith('cf-') or name=='forwarded' for name in names))
        self.assertEqual(observed['Host'],self.key_origin.removeprefix('https://'))
        self.assertEqual(observed['Origin'],self.key_origin)

    def test_cli_render_never_reads_credentials_or_overwrites_output(self):
        root=self.base/'cli';profile=self.base/'profile.json';profile.write_text(json.dumps(self.cfg));profile.chmod(0o600)
        cli=[sys.executable,'-m','asc.access.cloudflare','--root',str(root)]
        for args in (['init','--profile',str(profile)],['info']):
            result=subprocess.run(cli+args,capture_output=True,timeout=15)
            self.assertEqual(result.returncode,0,result.stderr);self.assertFalse(json.loads(result.stdout)['writer_authority'])
        target=self.base/'connector.json';missing=self.base/'missing-credentials.json'
        args=['render-connector','--tunnel-id',str(uuid.uuid4()),'--credentials-file',str(missing),'--output',str(target)]
        result=subprocess.run(cli+args,capture_output=True,timeout=15);self.assertEqual(result.returncode,0,result.stderr)
        self.assertFalse(json.loads(result.stdout)['credentials_read']);self.assertFalse(missing.exists())
        before=target.read_bytes();result=subprocess.run(cli+args,capture_output=True,timeout=15)
        self.assertNotEqual(result.returncode,0);self.assertEqual(target.read_bytes(),before)
