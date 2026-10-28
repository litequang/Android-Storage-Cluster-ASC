"""Private ingress to actual Core quorum observer and passive recovery staging."""
from http.cookies import SimpleCookie
import json
from pathlib import Path
import ssl
import tempfile
import time
import unittest
from asc.access import gateway as access
from asc.observability import gateway as observer
from asc.external.recovery import stage
from asc.identity import fingerprint_from_pem
from tests import test_observer_gateway as fixtures
from tests import test_access_gateway as browser
from tests import test_external as recovery_fixture


class IngressMixin:
    request=browser.PrivateGatewayTests.request
    def ingress_runtime(self):return access.Runtime(self.root)
    def configure(self,backend_root,backend_origin,mode):
        self.port=fixtures.GatewayFixture.port();self.origin='https://127.0.0.1:'+str(self.port)
        self.root=backend_root.parent/'access'
        cfg=dict(format=1,mode='private-gateway',frontend_origin=self.origin,upstream_origin=backend_origin,
            upstream_pin=fingerprint_from_pem(backend_root/'dashboard/server.crt').lower(),upstream_mode=mode,max_body_bytes=1024**2)
        access.initialize(self.root,cfg)
        self.tls=ssl.create_default_context(cafile=str(self.root/'dashboard/ca.crt'));self.cookie='';self.csrf=''
    def owner_login(self,backend):
        status,headers,raw=self.request('POST','/api/login',{'code':backend.api.sessions.issue()},authenticated=False)
        self.assertEqual(status,200,raw);cookies=SimpleCookie(headers['Set-Cookie']);name=next(iter(cookies))
        self.assertTrue(name.startswith('__Host-ASC-Observer-'));self.cookie=name+'='+cookies[name].value;self.csrf=json.loads(raw)['csrf']
    def assert_mutations_refused(self):
        for path in ('/api/uploads','/api/refresh','/api/approve','/api/promote','/api/gc','/api/recovery/activate','/api/v1/quick-join/pairings'):
            self.assertEqual(self.request('POST',path,{})[0],403,path)


class CorePrivateIngressTests(IngressMixin,fixtures.GatewayFixture):
    def test_real_quorum_partition_and_heal_never_gains_writer(self):
        self.make_cluster()
        with tempfile.TemporaryDirectory(prefix='.asc-core-access-',dir=Path.home()) as tmp:
            root=Path(tmp)/'observer';port=self.port();upstream='https://127.0.0.1:'+str(port)
            observer.init(root,'127.0.0.1',port,self.cluster,self.epoch,self.endpoints,source_roots=self.homes)
            with observer.Runtime(root) as backend:
                self.configure(root,upstream,'core-quorum')
                with self.ingress_runtime():
                    self.owner_login(backend)
                    status,_,raw=self.request('GET','/api/state');self.assertEqual(status,200,raw)
                    state=json.loads(raw);self.assertTrue(state['runtime']['quorum_available']);self.assertFalse(state['writer_authority'])
                    self.assert_mutations_refused()
                    self.split([{0},{1},{2}])
                    deadline=time.monotonic()+30;unavailable=None
                    while time.monotonic()<deadline:
                        status,_,raw=self.request('GET','/api/state');self.assertEqual(status,200,raw);unavailable=json.loads(raw)
                        if unavailable['runtime']['quorum_available'] is False:break
                        time.sleep(.2)
                    self.assertFalse(unavailable['runtime']['quorum_available']);self.assertFalse(unavailable['writer_authority'])
                    self.assertIn(unavailable['runtime']['state'],('QUORUM UNAVAILABLE','UNKNOWN'))
                    self.assert_mutations_refused()
                    self.split([set(range(3))]);self.wait_ready()
                    status,_,raw=self.request('GET','/api/state');self.assertEqual(status,200,raw)
                    state=json.loads(raw);self.assertTrue(state['runtime']['quorum_available']);self.assertFalse(state['writer_authority'])


class RecoveryPrivateIngressTests(IngressMixin,unittest.TestCase):
    setUp=recovery_fixture.ExternalBackupTests.setUp
    def test_actual_passive_stage_bytes_retained_no_recovery_writer(self):
        backup=self.engine.create(self.source,self.roots);target=self.base/'stage';target.mkdir(mode=0o700)
        stage(self.store,backup['backup_id'],backup['manifest_sha256'],target,self.roots,self.source.doc['cluster_id'],100)
        before={p.relative_to(target):p.read_bytes() for p in target.rglob('*') if p.is_file()}
        with tempfile.TemporaryDirectory(prefix='.asc-recovery-access-',dir=Path.home()) as tmp:
            root=Path(tmp)/'observer';port=fixtures.GatewayFixture.port();upstream='https://127.0.0.1:'+str(port)
            observer.init(root,'127.0.0.1',port,self.source.doc['cluster_id'],self.source.doc['epoch'],
                recovery={'root':str(target),'anchor':backup['manifest_sha256']},source_roots=self.roots,minimum_index=100)
            with observer.Runtime(root) as backend:
                self.configure(root,upstream,'recovery-read-only')
                with self.ingress_runtime():
                    self.owner_login(backend);status,_,raw=self.request('GET','/api/state');self.assertEqual(status,200,raw)
                    state=json.loads(raw);self.assertEqual(state['runtime']['state'],'RECOVERY READ-ONLY')
                    self.assertFalse(state['writer_authority']);self.assertFalse(state['backup']['recovery']['credentials_restored'])
                    self.assert_mutations_refused()
        self.assertEqual(before,{p.relative_to(target):p.read_bytes() for p in target.rglob('*') if p.is_file()})
        self.assertFalse((target/'registry.sqlite3').exists());self.assertFalse((target/'controller.json').exists())
