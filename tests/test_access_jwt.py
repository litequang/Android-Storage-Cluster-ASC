"""Real ephemeral RSA signatures; synthetic issuer/key transport, not Cloudflare live."""
import copy
import json
import time
import unittest
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from asc.access.access_jwt import AccessVerifier,AccessDenied,KeysUnavailable,KEY_TTL
from asc.access.edge_policy import EdgeProfile
from tests import test_access_policy as private


class AccessJWTTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        cls.other=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    def setUp(self):
        self.clock=[100.];self.count=0
        self.jwk=dict(json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(self.key.public_key())),kid='key-a',alg='RS256',use='sig')
        self.body={'keys':[self.jwk]};self.unavailable=False
        def fetch(url):
            self.assertEqual(url,'https://asc-synthetic.cloudflareaccess.com/cdn-cgi/access/certs');self.count+=1
            if self.unavailable:raise OSError('synthetic provider offline')
            return self.body
        self.verifier=AccessVerifier('asc-synthetic','a'*64,fetcher=fetch,clock=lambda:self.clock[0])
    def token(self,changes=None,headers=None,key=None):
        now=int(time.time());claims=dict(iss=self.verifier.issuer,aud=['a'*64],sub='synthetic-user',type='app',iat=now-1,exp=now+300)
        if changes:claims.update(changes)
        return jwt.encode(claims,key or self.key,algorithm='RS256',headers=dict(kid='key-a',**(headers or {})))
    def test_real_signature_and_fresh_bounded_public_key_cache(self):
        self.verifier.verify(self.token());self.verifier.verify(self.token());self.assertEqual(self.count,1)
        self.assertEqual(set(self.verifier.keys),{'key-a'})
    def test_wrong_signature_issuer_audience_and_expiry_refuse(self):
        for changes in ({'iss':'https://other.cloudflareaccess.com'},{'aud':['b'*64]},
                        {'exp':int(time.time())-1},{'iat':int(time.time())+3600},{'sub':''},{'type':'service'},
                        {'iat':True},{'exp':int(time.time())+90000},{'nbf':int(time.time())+3600}):
            with self.subTest(changes=changes),self.assertRaises(AccessDenied):self.verifier.verify(self.token(changes))
        with self.assertRaises(AccessDenied):self.verifier.verify(self.token(key=self.other))
    def test_no_unsigned_symmetric_algorithm_or_untrusted_key_url(self):
        for token in ('invalid','x'*8193,jwt.encode({'sub':'x'},'',algorithm='none',headers={'kid':'key-a'}),
                      jwt.encode({'sub':'x'},'synthetic-hmac-test-material-32bytes',algorithm='HS256',headers={'kid':'key-a'}),
                      self.token(headers={'jku':'https://attacker.invalid/keys'}),self.token(headers={'crit':['x']})):
            with self.subTest(kind=token[:8]),self.assertRaises(AccessDenied):self.verifier.verify(token)
        self.assertEqual(self.count,0)
    def test_missing_required_claims_refuse(self):
        claims=jwt.decode(self.token(),options={'verify_signature':False}) # Test construction only, NOT production validation.
        for field in ('iss','aud','exp','iat','sub'):
            bad=dict(claims);bad.pop(field)
            with self.subTest(field=field),self.assertRaises(AccessDenied):
                self.verifier.verify(jwt.encode(bad,self.key,algorithm='RS256',headers={'kid':'key-a'}))
    def test_expired_key_cache_network_loss_never_uses_stale_keys(self):
        self.verifier.verify(self.token());self.clock[0]+=KEY_TTL+1;self.unavailable=True
        with self.assertRaises(KeysUnavailable):self.verifier.verify(self.token())
        self.assertEqual(self.count,2)
        with self.assertRaises(KeysUnavailable):self.verifier.verify(self.token())
        self.assertEqual(self.count,2) # Flood cannot bypass bounded refresh interval.
    def test_rotation_and_unknown_kid_refresh_are_bounded(self):
        self.verifier.verify(self.token());rotated=dict(self.jwk,kid='key-b');self.body={'keys':[rotated]}
        signed=jwt.encode(dict(iss=self.verifier.issuer,aud=['a'*64],sub='u',type='app',iat=int(time.time())-1,exp=int(time.time())+60),self.key,algorithm='RS256',headers={'kid':'key-b'})
        with self.assertRaises(AccessDenied):self.verifier.verify(signed)
        self.assertEqual(self.count,1);self.clock[0]+=31;self.verifier.verify(signed);self.assertEqual(self.count,2)
    def test_ambiguous_weak_or_private_jwk_sets_refuse(self):
        for body in ({'keys':[]},{'keys':[self.jwk]*2},{'keys':[dict(self.jwk,kty='EC')]},
                     {'keys':[dict(self.jwk,d='not-public')]},{'keys':[dict(self.jwk,use='enc')]},{'keys':[self.jwk]*9}):
            self.body=copy.deepcopy(body);self.clock[0]+=31
            with self.subTest(body=body),self.assertRaises(KeysUnavailable):self.verifier.refresh()


class EdgeProfileTests(unittest.TestCase):
    def value(self):
        value=private.profile();value.update(format=2,mode='cloudflare-edge',frontend_origin='https://asc.example.com',
            listen_origin='https://127.0.0.1:8446',access_team='asc-synthetic',access_audience='a'*64);return value
    def test_edge_profile_is_separate_and_loopback_only(self):
        value=self.value();p=EdgeProfile.parse(value);self.assertFalse(p.public()['writer_authority'])
        with self.assertRaises(ValueError):private.Profile.parse(value)
        for key,bad in [('listen_origin','https://0.0.0.0:8446'),('listen_origin','https://192.168.1.2:8446'),
                        ('frontend_origin','http://asc.example.com'),('frontend_origin','https://asc.example.com:443'),
                        ('frontend_origin','https://127.0.0.1'),('access_team','evil/path'),('access_audience','')]:
            raw=dict(value);raw[key]=bad
            with self.subTest(key=key,bad=bad),self.assertRaises(ValueError):EdgeProfile.parse(raw)
    def test_no_public_mode_fallback_or_cloud_token_as_owner(self):
        value=self.value();value['upstream_mode']='recovery-read-only';p=EdgeProfile.parse(value)
        self.assertFalse(p.permits('POST','/api/uploads'));self.assertFalse(p.public()['live_cloudflare_accepted'])
        self.assertEqual(p.public()['remote_reachability'],'UNKNOWN')
