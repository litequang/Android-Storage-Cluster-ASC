"""Cloudflare Access RS256 verification, never an ASC owner/session authority."""
import json
import re
import ssl
import threading
import time
import urllib.request
from ..server import _unique_object

KEY_TTL = 300
REFRESH_INTERVAL = 30
MAX_TOKEN = 8192
MAX_KEYS_BYTES = 65536


class AccessDenied(ValueError):
    def __init__(self):super().__init__('edge_access_denied')


class KeysUnavailable(ValueError):
    def __init__(self):super().__init__('edge_keys_unavailable')


def access_issuer(team):
    if type(team) is not str or not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?',team):
        raise ValueError('invalid explicit Access team')
    return 'https://'+team+'.cloudflareaccess.com'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):raise OSError('JWKS redirect refused')


def fetch_keys(url):
    # URL derives ONLY from configured team, never from an unverified token.
    opener=urllib.request.build_opener(NoRedirect(),urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    with opener.open(urllib.request.Request(url,headers={'Accept':'application/json'}),timeout=8) as response:
        if response.geturl()!=url or response.headers.get_content_type()!='application/json':raise KeysUnavailable()
        raw=response.read(MAX_KEYS_BYTES+1)
    if len(raw)>MAX_KEYS_BYTES:raise KeysUnavailable()
    return json.loads(raw,object_pairs_hook=_unique_object)


class AccessVerifier:
    def __init__(self,team,audience,*,fetcher=fetch_keys,clock=time.monotonic):
        self.issuer=access_issuer(team)
        if type(audience) is not str or not re.fullmatch('[0-9a-f]{64}',audience):raise ValueError('invalid Access audience')
        try:
            import jwt
            from cryptography.hazmat.primitives.asymmetric import rsa
        except ImportError:raise KeysUnavailable() from None
        self.jwt=jwt;self.rsa=rsa;self.audience=audience;self.fetcher=fetcher;self.clock=clock
        self.url=self.issuer+'/cdn-cgi/access/certs';self.lock=threading.Lock()
        self.keys={};self.expires=0;self.last_attempt=float('-inf')

    def _refresh(self):
        now=self.clock()
        if now-self.last_attempt<REFRESH_INTERVAL:raise KeysUnavailable()
        self.last_attempt=now
        try:
            body=self.fetcher(self.url)
            if type(body) is not dict or type(body.get('keys')) is not list or not 1<=len(body['keys'])<=8:
                raise ValueError()
            keys={}
            for item in body['keys']:
                if (type(item) is not dict or item.get('kty')!='RSA' or item.get('alg','RS256')!='RS256'
                        or item.get('use','sig')!='sig' or type(item.get('kid')) is not str
                        or not re.fullmatch('[A-Za-z0-9_-]{1,128}',item['kid']) or item['kid'] in keys
                        or any(k in item for k in ('d','p','q','dp','dq','qi','oth'))):raise ValueError()
                key=self.jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(item))
                if not isinstance(key,self.rsa.RSAPublicKey) or not 2048<=key.key_size<=4096:raise ValueError()
                keys[item['kid']]=key
        except (OSError,ValueError,TypeError,KeyError,self.jwt.PyJWTError):raise KeysUnavailable() from None
        self.keys=keys;self.expires=self.clock()+KEY_TTL

    def refresh(self):
        with self.lock:self._refresh()

    def verify(self,token):
        if type(token) is not str or not 1<=len(token)<=MAX_TOKEN or not token.isascii():raise AccessDenied()
        try:
            header=self.jwt.get_unverified_header(token)
            if (set(header)-{'alg','kid','typ'} or header.get('alg')!='RS256' or header.get('typ','JWT')!='JWT'
                    or type(header.get('kid')) is not str or not re.fullmatch('[A-Za-z0-9_-]{1,128}',header['kid'])):
                raise AccessDenied()
            with self.lock:
                if self.clock()>=self.expires:self._refresh()
                elif header['kid'] not in self.keys and self.clock()-self.last_attempt>=REFRESH_INTERVAL:self._refresh()
                key=self.keys.get(header['kid'])
            if key is None:raise AccessDenied()
            claims=self.jwt.decode(token,key,algorithms=['RS256'],audience=self.audience,issuer=self.issuer,
                leeway=0,options={'require':['iss','aud','exp','iat','sub'],'verify_nbf':True})
            if (type(claims['exp']) is not int or type(claims['iat']) is not int
                    or 'nbf' in claims and type(claims['nbf']) is not int
                    or not 0<claims['exp']-claims['iat']<=86400
                    or type(claims['sub']) is not str or not 1<=len(claims['sub'])<=256
                    or claims.get('type')!='app'):
                raise AccessDenied()
        except (self.jwt.PyJWTError,ValueError,TypeError,KeyError) as error:
            if isinstance(error,KeysUnavailable):raise
            raise AccessDenied() from None
        # Claims grant NO ASC session, owner role, Node approval or writer authority.
