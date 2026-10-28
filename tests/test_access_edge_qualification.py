"""Edge synthetic browser and real Core/passive E2E. Never live Cloudflare."""
import json
from pathlib import Path
import shutil
import ssl
import time
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from asc.access import cloudflare as edge
from asc.access.access_jwt import AccessVerifier
from asc.identity import fingerprint_from_pem
from tests import test_access_browser as browser
from tests import test_access_cloudflare as demo
from tests import test_access_observer as observers
from tests.edge_connector_fixture import SyntheticConnector


class EdgeBrowserTests(browser.PrivateGatewayBrowserTests):
    def setUp(self):
        for name in ('node','chromium','certutil'):
            self.assertIsNotNone(shutil.which(name),'real browser required; no TLS bypass/skip')
        self.f=demo.EdgeOriginTests();self.addCleanup(self.f.doCleanups);self.f.setUp()
        connector=SyntheticConnector(self.f);self.addCleanup(connector.stop)
        self.connector=connector;self.f.origin=connector.frontend
        # Local synthetic front translates only its own verified Host/Origin to
        # the reserved edge hostname; no real public-host browser/DNS/provider proof.
        # Runtime already owns the original loopback identity, which is unchanged.
        self.f.root=connector.root;self.f.artifact_directory='/workspace/work/phase5-edge-browser'

    def test_actual_chromium_owner_files_pwa_sha_fallback_and_network_loss(self):
        super().test_actual_chromium_owner_files_pwa_sha_fallback_and_network_loss()
        self.assertGreater(self.connector.received,20)


class EdgeObserverMixin:
    def ingress_runtime(self):return edge.Runtime(self.root,verifier=self.verifier)
    def configure(self,backend_root,backend_origin,mode):
        self.port=observers.fixtures.GatewayFixture.port();self.origin='https://asc.example.com'
        self.root=backend_root.parent/'access'
        cfg=dict(format=2,mode='cloudflare-edge',frontend_origin=self.origin,
            listen_origin='https://127.0.0.1:'+str(self.port),upstream_origin=backend_origin,
            upstream_pin=fingerprint_from_pem(backend_root/'dashboard/server.crt').lower(),
            upstream_mode=mode,max_body_bytes=1024**2,access_team='asc-synthetic',access_audience='a'*64)
        edge.initialize(self.root,cfg)
        key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        jwk=dict(json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key())),kid='observer-key')
        def public_keys(url):
            self.assertEqual(url,'https://asc-synthetic.cloudflareaccess.com/cdn-cgi/access/certs')
            return {'keys':[jwk]} # Synthetic key transport only; real signature verification.
        self.verifier=AccessVerifier('asc-synthetic','a'*64,fetcher=public_keys)
        now=int(time.time());self.token=jwt.encode(dict(iss=self.verifier.issuer,aud=['a'*64],sub='synthetic-observer',
            type='app',iat=now-1,exp=now+300),key,algorithm='RS256',headers={'kid':'observer-key'})
        self.tls=ssl.create_default_context(cafile=str(self.root/'dashboard/ca.crt'));self.cookie='';self.csrf=''
    def request(self,method,path,obj=None,body=None,headers=None,authenticated=True):
        sent={'Host':'asc.example.com','Cf-Access-Jwt-Assertion':self.token}
        if headers:sent.update(headers)
        return observers.browser.PrivateGatewayTests.request(self,method,path,obj,body,sent,authenticated)


class EdgeCoreIngressTests(EdgeObserverMixin,observers.CorePrivateIngressTests):
    pass # Inherits every original actual quorum partition/heal and mutation assertion.


class EdgeRecoveryIngressTests(EdgeObserverMixin,observers.RecoveryPrivateIngressTests):
    pass # Inherits exact staged-byte preservation, credentials absent and no writer.
