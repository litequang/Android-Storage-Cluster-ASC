> Resume2026-10-28: executor recovered; dirty gateway/cloudflare source preserved,
> docs-only commits fast-forwarded safely. See latest PHASE5-PROGRESS for actual
> new test results. Historical untested draft below is not the current status.

# Phase5.2b executor interruption — RECOVERY DRAFT, NOT QUALIFIED

2026-10-28: the Cloud executor became unavailable. Last successful production-source
checkpoint is 783dd7d9a737fcdd58011c054a98fcc85e525618 on feature/phase5-remote-access.
It was normally pushed and fetch/advertised HEAD verified BEFORE runtime work.
Fresh tests.test_access_jwt + tests.test_access_policy:16PASS0skip/fail0.066s.
Optional workspace env pip-check passed; no full/Cloudflare/provider/phone PASS.

The shared gateway refactor and new cloudflare.py below were acknowledged by
apply_patch, but NOT tested, committed or reread after executor failure.
Creating/running tests/test_access_cloudflare.py then failed at CreateProcess:
"exec-server transport disconnected". No successful test command or test results.
Do not assume that test file exists, that any 5.2b server started, or that workspace
is lost. Cloud environment_status still reported connected while actual exec
transport was unavailable: only the real command establishes execution readiness.

## Safe resume, BEFORE editing or running services
1. Inspect original workspace/branch/status/staged/unstaged/untracked; preserve ALL
   dirty source, old private signer, SDK/Node states and identities. No reset/clean/
   force checkout/uninstall/clear/data clone or old DB restoration.
2. Fetch current feature head. New remote commits after783 may be DOCS-ONLY handoff.
   Integrate them without overwriting dirty runtime files; inspect conflicts rather
   than blindly replace files from this draft. Original Core/Demo/Phase4 refs stay.
3. Compare asc/access/gateway.py and any asc/access/cloudflare.py with this candidate.
   This is a TOOL-CALL reconstruction, not a byte-verified workspace backup. Recover
   only missing work after review. The new integration file creation was not
   acknowledged; construct it from the scenarios below if absent.
4. Existing optional env: /workspace/asc-access-dev/edge-env/bin/python (3.13.5).
   PyJWT2.15.1/cryptography50.0.2/cffi2.1.1/pycparser3.12, verified official wheels in
   /workspace/asc-access-dev/wheels and private dependency-receipt.json. Requirements
   source: requirements-cloudflare.txt. Initial ensurepip unavailable; private
   --without-pip env +existing pip --python/local --require-hashes worked. No apt,
   global install, proxy/CA change, get-pip, system update or crypto fallback.
5. Run fresh16foundation tests, then actual edge/private/Dashboard/browser/Core
   targeted regression. Shared gateway changes INVALIDATE automatic reuse of the
   old private gateway integration evidence until corresponding tests rerun.
6. No live Cloudflare account/Access app/JWT/tunnel or provider credentials configured.
   No actual cloudflared binary downloaded/qualified in this interruption. Source/
   synthetic only; do not deploy. Phone gates DEFERRED BY OWNER, not PASS.

## Acknowledged shared gateway refactor
In asc/access/gateway.py:
- Extract existing TLS-directory/file/CA/IP verification from load into
  validate_tls(root, host); load still parses private Profile1 then invokes it.
- GatewayHandler.authorize_ingress() defaults no-op for existing private profile;
  session_cookie() defaults original Cookie header. Call authorize_ingress AFTER
  existing rate/framing/origin checks and BEFORE any upstream connection. Forward
  only session_cookie() as Cookie, then existing X-ASC-CSRF/Content-Type.
- Runtime.handler=GatewayHandler, load_profile()->load(root),
  bind_address()->private_origin(profile.frontend_origin), prepare_server(server)
  default no-op. __enter__ invokes those trusted in-process hooks, including server
  preparation before serving. Existing TLS, pin/mode checks, limits/locks unchanged.
No public bind, private-profile widening, new owner session or arbitrary command.

## Candidate new asc/access/cloudflare.py (UNTESTED, compare before recovery)

~~~python
"""Explicit loopback-only Cloudflare origin. Never starts a tunnel or creates DNS."""
import argparse
from http.cookies import SimpleCookie, CookieError
import json
from pathlib import Path
import re
import signal
import threading
import uuid
from urllib.parse import urlsplit
from ..bridge import private
from ..catalog.common import CatalogError
from ..client import ClientError
from ..demo.dashboard.http import Rejected
from ..demo.dashboard.tls import generate_identity
from ..demo.installer import private_path
from ..external.cli import host_guard
from ..observability.gateway import reject_engine_ancestry
from . import gateway
from .access_jwt import AccessVerifier, AccessDenied, KeysUnavailable
from .edge_policy import EdgeProfile
from .policy import private_origin


def initialize(root,value):
    host_guard();root=private_path(root);reject_engine_ancestry(root);profile=EdgeProfile.parse(value)
    if root.exists():
        if load(root)!=profile:raise ValueError('existing edge identity/profile retained')
        return info(root,profile)
    root.mkdir(mode=0o700);(root/'dashboard').mkdir(mode=0o700)
    generate_identity(root/'dashboard','127.0.0.1','ASC Edge Loopback')
    private.create(root/'gateway.json',value)
    return info(root,load(root))


def load(root):
    host_guard();root=private.directory(root);reject_engine_ancestry(root)
    profile=EdgeProfile.parse(private.read(root/'gateway.json'));gateway.validate_tls(root,'127.0.0.1')
    return profile


def info(root,profile):
    value=gateway.info(root,profile)
    value['trust_required']='Connector must verify this PUBLIC CA and loopback IP SAN; no noTLSVerify.'
    return value


class EdgeHandler(gateway.GatewayHandler):
    server_version='ASC-Edge-Origin'
    def authorize_ingress(self):
        tokens=self.headers.get_all('Cf-Access-Jwt-Assertion',[])
        if len(tokens)!=1:raise Rejected(403,'edge_access_denied')
        try:self.server.access_verifier.verify(tokens[0])
        except AccessDenied:raise Rejected(403,'edge_access_denied') from None
        except KeysUnavailable:raise Rejected(503,'edge_keys_unavailable') from None

    def session_cookie(self):
        raw=self.headers.get('Cookie','')
        names=re.findall(r'(?:^|;)\s*([^=;\s]+)\s*=',raw)
        if len(names)!=len(set(names)):raise Rejected(400,'ambiguous_cookie')
        parsed=SimpleCookie()
        try:parsed.load(raw)
        except CookieError:raise Rejected(400,'bad_owner_cookie') from None
        if self.server.profile.upstream_mode=='single-writer-demo':
            selected=[k for k in parsed if k=='__Host-ASC-Demo']
        else:selected=[k for k in parsed if re.fullmatch('__Host-ASC-Observer-[0-9a-f]{32}',k)]
        if len(selected)>1:raise Rejected(400,'ambiguous_cookie')
        if not selected:return None
        name=selected[0];value=parsed[name].value
        if not re.fullmatch('[A-Za-z0-9_-]{16,128}',value):raise Rejected(400,'bad_owner_cookie')
        return name+'='+value


class Runtime(gateway.Runtime):
    handler=EdgeHandler
    def __init__(self,root,*,verifier=None):
        super().__init__(root);self.verifier=verifier
    def load_profile(self):
        profile=load(self.root)
        if self.verifier is None:self.verifier=AccessVerifier(profile.access_team,profile.access_audience)
        if (type(self.verifier) is not AccessVerifier or self.verifier.audience!=profile.access_audience
                or self.verifier.issuer!='https://'+profile.access_team+'.cloudflareaccess.com'):
            raise ValueError('explicit edge verifier binding mismatch')
        if self.verifier.clock()>=self.verifier.expires:self.verifier.refresh()
        return profile
    def bind_address(self):return private_origin(self.profile.listen_origin)
    def prepare_server(self,server):server.access_verifier=self.verifier


def connector(root,profile,tunnel_id,credentials_file):
    if str(uuid.UUID(tunnel_id))!=tunnel_id:raise ValueError('canonical explicit tunnel ID required')
    path=private_path(credentials_file)
    return {'tunnel':tunnel_id,'credentials-file':str(path),'ingress':[
        {'hostname':urlsplit(profile.frontend_origin).hostname,'service':profile.listen_origin,'originRequest':{
            'httpHostHeader':urlsplit(profile.frontend_origin).netloc,'originServerName':'127.0.0.1',
            'matchSNItoHost':False,'caPool':str(Path(root)/'dashboard/ca.crt'),'noTLSVerify':False,
            'http2Origin':False,'disableChunkedEncoding':True,'connectTimeout':'10s','tlsTimeout':'10s',
            'access':{'required':True,'teamName':profile.access_team,'audTag':[profile.access_audience]}}},
        {'service':'http_status:404'}]}


def main():
    parser=gateway.Parser(description=__doc__);parser.add_argument('--root',type=Path,required=True)
    commands=parser.add_subparsers(dest='command',required=True)
    setup=commands.add_parser('init');setup.add_argument('--profile',type=Path,required=True)
    commands.add_parser('info');commands.add_parser('serve')
    render=commands.add_parser('render-connector');render.add_argument('--tunnel-id',required=True)
    render.add_argument('--credentials-file',type=Path,required=True);render.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:
        if args.command=='init':reply=initialize(args.root,private.read(args.profile))
        else:
            root=private.directory(args.root);profile=load(root)
            if args.command=='info':reply=info(root,profile)
            elif args.command=='render-connector':
                target=private_path(args.output);private.directory(target.parent)
                private.create(target,connector(root,profile,args.tunnel_id,args.credentials_file))
                reply={'connector_template_written':True,'cloudflared_started':False,'credentials_read':False,
                       'live_cloudflare_accepted':False,'output':str(target)}
            else:
                stop=threading.Event()
                for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,lambda *_:stop.set())
                with Runtime(root) as runtime:
                    print(json.dumps(dict(info(root,runtime.profile),listener_started=True)),flush=True);stop.wait()
                return 0
        print(json.dumps(reply));return 0
    except (ValueError,OSError,ClientError,CatalogError):
        print('{"error":"edge_origin_refused","state":"UNKNOWN"}');return 1


if __name__=='__main__':raise SystemExit(main())
~~~

## Required integration tests (NOT RUN)
Build tests/test_access_cloudflare.py against existing DashboardAPITests fixture,
fresh private temporary roots under real development HOME. No global HOME, real
phones/M51/Termux, resets or source guards altered.

- Actual local HTTPS JWKS server: ephemeral RSA2048 key, public JWK, fixed certs
  path, pinned TLS, bounded JSON. AccessVerifier uses a trusted in-process fetcher
  asserting the exact configured issuer URL and obtaining that local HTTPS JSON.
  Real PyJWT signature/claim checks ALWAYS execute. Clearly label synthetic issuer,
  not live Cloudflare. Never replace verify() with true/skip the signatures.
- Actual loopback TLS edge origin with profile public Host asc.example.com and
  matching Origin; client validates origin public CA/IP SAN independently.
- Valid signed Access JWT WITHOUT ASC owner session returns401. Missing/invalid/
  expired/wrong-audience/wrong-issuer/duplicate assertion remains403 EVEN with a
  valid owner cookie. A CF_Authorization cookie/email header never replaces JWT.
- Missing JWT login request must not consume the existing backend one-use owner
  code; subsequent correctly signed login can still redeem it. CSRF mandatory.
- Actual two-node upload/download SHA/two logical replicas, stop one OWNED node,
  fallback; no two-phone/hardware claim.
- Stop actual JWKS server, expire public-key cache, existing owner request gets503,
  never uses stale expired key or invents session/writer success.
- Cookie filtering keeps only backend __Host owner cookie; CF assertions/cookies/
  identity are absent upstream. Connector rendering never reads actual credentials,
  uses trusted CA/IP SAN/noTLSVerifyfalse/per-rule Access and final404.
- Wrong pin/mode, private profile1 backwards compatibility, Core/recovery mutation
  refusals, CLI init/info/serve/render/stop, partial-root identity preservation.
- Rerun private/API/CLI/browser/Core targeted suite after shared refactor. Then
  obtain officially checksum-verified cloudflared ONLY in workspace development,
  run version/offline ingress config validation without starting a live tunnel.
  Nothing in this handoff proves actual binary/config/provider acceptance.

Keep current tested source783 unchanged as baseline; publish qualified5.2b only
AFTER targeted PASS/docs/CODEMAP/secrets/normal push+remote verification. No provider/
Cloudflare/remote/production ACCEPTED or new APK/archive from this draft. Hardware
is DEFERRED BY OWNER, not a failure/skip or requirement to stop source development.
