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
        # Never forwards CF_Authorization, assertion, email or other Cloudflare credentials.
        return name+'='+value


class Runtime(gateway.Runtime):
    handler=EdgeHandler
    def __init__(self,root,*,verifier=None):
        super().__init__(root);self.verifier=verifier # Trusted in-process provider; no CLI/config override.
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
    path=private_path(credentials_file) # Path only; NEVER reads or embeds the secret contents.
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
