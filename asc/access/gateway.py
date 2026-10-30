"""Linux synthetic private HTTPS browser gateway. No shell or cluster authority."""
import argparse
import http.client
import json
import signal
import ssl
import threading
import time
from pathlib import Path
from urllib.parse import urlsplit
from ..bridge import private
from ..client import ClientError, connect_pinned, request_json
from ..demo.dashboard.http import Rejected
from ..catalog.common import CatalogError
from ..demo.dashboard.tls import FILES, generate_identity, openssl
from ..demo.locks import private_lock
from ..demo.installer import private_path
from ..external.cli import host_guard
from ..identity import fingerprint_from_pem
from ..observability.gateway import reject_engine_ancestry
from ..server import Handler, Server
from ..storage.volumes import no_links
from .policy import Profile, private_origin, MAX_BODY


def initialize(root, value):
    host_guard();root=private_path(root);reject_engine_ancestry(root);profile=Profile.parse(value)
    if root.exists():
        existing=load(root)
        if existing!=profile:raise ValueError('existing gateway profile and TLS identity retained')
        return info(root,profile)
    root.mkdir(mode=0o700);(root/'dashboard').mkdir(mode=0o700)
    generate_identity(root/'dashboard',private_origin(profile.frontend_origin)[0],'ASC Private Access')
    private.create(root/'gateway.json',value)
    return info(root,load(root))


def load(root):
    host_guard();root=private.directory(root);reject_engine_ancestry(root)
    profile=Profile.parse(private.read(root/'gateway.json'))
    validate_tls(root,private_origin(profile.frontend_origin)[0])
    return profile


def validate_tls(root,host):
    private.directory(root/'dashboard')
    for name in FILES:
        path=root/'dashboard'/name;no_links(path);st=path.stat()
        if not path.is_file() or st.st_nlink!=1 or st.st_uid!=root.stat().st_uid or st.st_mode&0o077 or st.st_size>65536:
            raise ValueError('unsafe gateway TLS identity')
    openssl('verify','-CAfile',root/'dashboard/ca.crt','-purpose','sslserver',
            '-verify_ip',host,root/'dashboard/server.crt')


def info(root,profile):
    return dict(profile.public(),public_ca=str(root/'dashboard/ca.crt'),
                ca_sha256=fingerprint_from_pem(root/'dashboard/ca.crt'),
                trust_required='Independently verify and trust only public CA. Never bypass TLS errors.',
                platform='Linux source/synthetic only; Android/Termux/phones NOT QUALIFIED')


class GatewayHandler(Handler):
    server_version='ASC-Private-Access'

    def authorize_ingress(self):
        pass # Private format1 keeps existing owner authorization in backend.

    def session_cookie(self):
        return self.headers.get('Cookie')

    def _dispatch(self):
        started=False;upstream=None;self.close_connection=True
        try:
            profile=self.server.profile
            if len(self.headers)>32 or sum(len(k)+len(v) for k,v in self.headers.items())>16384:
                raise Rejected(431,'headers_too_large')
            if not profile.permits(self.command,self.path):raise Rejected(403,'route_denied')
            origins=self.headers.get_all('Origin',[])
            if (self.headers.get_all('Host',[])!=[urlsplit(profile.frontend_origin).netloc]
                    or len(origins)>1 or origins and origins!=[profile.frontend_origin]
                    or self.command!='GET' and origins!=[profile.frontend_origin]
                    or self.headers.get('Sec-Fetch-Site','same-origin') not in ('same-origin','none')):
                raise Rejected(403,'origin_rejected')
            if any(self.headers.get_all(k,[]) for k in ('Authorization','Proxy-Authorization','Transfer-Encoding','Expect','Upgrade')):
                raise Rejected(400,'unsupported_framing_or_credential')
            lengths=self.headers.get_all('Content-Length',[])
            if self.command=='GET' and not lengths:length=0
            elif len(lengths)==1 and lengths[0].isascii() and lengths[0].isdigit() and str(int(lengths[0]))==lengths[0]:length=int(lengths[0])
            else:raise Rejected(400,'bad_framing')
            if self.command=='GET' and length:raise Rejected(400,'bad_framing')
            maximum=profile.max_body_bytes if self.command=='PUT' else 8192
            if length>maximum:raise Rejected(413,'body_too_large')
            for name,limit in [('Cookie',4096),('X-ASC-CSRF',128),('Content-Type',128)]:
                values=self.headers.get_all(name,[])
                if len(values)>1 or values and len(values[0])>limit:raise Rejected(400,'bad_headers')
            # Bounded aggregate ingress rate; existing backend owner limits still apply.
            if self._rate('gateway',consume=True):return
            self.authorize_ingress()
            upstream=connect_pinned(profile.upstream_origin,profile.upstream_pin,timeout=12)
            upstream.putrequest(self.command,self.path,skip_host=True,skip_accept_encoding=True)
            upstream.putheader('Host',urlsplit(profile.upstream_origin).netloc)
            upstream.putheader('Origin',profile.upstream_origin) # Only after external-origin validation.
            upstream.putheader('Connection','close')
            if self.command!='GET':upstream.putheader('Content-Length',str(length))
            cookie=self.session_cookie()
            if cookie is not None:upstream.putheader('Cookie',cookie)
            for name in ('X-ASC-CSRF','Content-Type'):
                if self.headers.get(name) is not None:upstream.putheader(name,self.headers[name])
            # No Authorization/Forwarded/CF identity header is ever forwarded.
            upstream.endheaders();deadline=time.monotonic()+120;remaining=length
            while remaining:
                if time.monotonic()>deadline:raise Rejected(408,'request_timeout')
                block=self.rfile.read1(min(65536,remaining))
                if not block:raise Rejected(400,'incomplete_body')
                upstream.send(block);remaining-=len(block)
            upstream.sock.settimeout(min(60,max(1,deadline-time.monotonic())))
            response=upstream.getresponse();sizes=response.headers.get_all('Content-Length',[])
            if (response.status not in (200,201,202,204,400,401,403,404,408,409,413,422,429,500,502,503,507)
                    or len(response.headers)>32
                    or any('\r' in v or '\n' in v for _,v in response.getheaders())
                    or response.headers.get('Transfer-Encoding') or len(sizes)!=1 or not sizes[0].isascii()
                    or not sizes[0].isdigit() or int(sizes[0])>max(profile.max_body_bytes,2*1024**2)):
                raise Rejected(502,'upstream_framing_rejected')
            replacement=None
            if self.path=='/api/capabilities' and response.status==200:
                if int(sizes[0])>8192:raise Rejected(502,'upstream_framing_rejected')
                raw=response.read(8193)
                if len(raw)!=int(sizes[0]):raise Rejected(502,'upstream_framing_rejected')
                capabilities=json.loads(raw)
                if (type(capabilities) is not dict or type(capabilities.get('dashboard_api_version')) is not int
                        or capabilities['dashboard_api_version']!=1 or capabilities.get('mode')!=profile.upstream_mode):
                    raise Rejected(502,'upstream_framing_rejected')
                capabilities.update(node_management=False,account_management=False,access_mode='file-access-only')
                replacement=json.dumps(capabilities,separators=(',',':'),allow_nan=False).encode()
            self.send_response(response.status)
            allowed={'content-type','content-length','cache-control','set-cookie','content-disposition',
                'x-asc-sha256','x-asc-replica-node','content-security-policy','x-content-type-options',
                'referrer-policy','x-frame-options','cross-origin-resource-policy','permissions-policy','retry-after'}
            for name,value in response.getheaders():
                if name.lower() in allowed and not (replacement is not None and name.lower()=='content-length'):self.send_header(name,value)
            if replacement is not None:self.send_header('Content-Length',str(len(replacement)))
            self.send_header('X-ASC-Access-Mode','file-access-only')
            self.send_header('Connection','close');self.end_headers();started=True
            if replacement is not None:
                self.wfile.write(replacement);return
            remaining=int(sizes[0])
            while remaining:
                if time.monotonic()>deadline:raise OSError('bounded response deadline')
                block=response.read1(min(65536,remaining))
                if not block:raise OSError('incomplete upstream response')
                self.wfile.write(block);remaining-=len(block)
        except Rejected as error:
            if not started:self._json(error.status,{'error':error.code})
        except (OSError,ClientError,ValueError,http.client.HTTPException):
            if not started:self._json(503,{'error':'upstream_unavailable'})
        finally:
            if upstream is not None:upstream.close()

    do_GET=do_POST=do_PUT=_dispatch


class Runtime:
    handler=GatewayHandler
    def __init__(self,root):self.root=Path(root)
    def load_profile(self):return load(self.root)
    def bind_address(self):return private_origin(self.profile.frontend_origin)
    def prepare_server(self,server):pass
    def __enter__(self):
        self.profile=self.load_profile()
        mode=request_json(self.profile.upstream_origin,self.profile.upstream_pin,'GET','/api/mode')
        if mode!={'mode':self.profile.upstream_mode,'read_only':self.profile.upstream_mode!='single-writer-demo'}:
            raise ValueError('pinned upstream mode mismatch; no automatic fallback')
        self.owner=private_lock(self.root,'access-gateway');self.owner.__enter__()
        try:
            self.server=Server(self.bind_address(),None,'',handler=self.handler)
            self.server.limiter.limits['gateway']=(120,240)
            self.server.profile=self.profile;self.server.slots=threading.BoundedSemaphore(8);self.server.daemon_threads=False
            self.prepare_server(self.server)
            context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.minimum_version=ssl.TLSVersion.TLSv1_2
            context.load_cert_chain(self.root/'dashboard/server.crt',self.root/'dashboard/server.key')
            self.server.tls_context=context
            self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start();return self
        except BaseException:
            if hasattr(self,'server'):self.server.server_close()
            self.owner.__exit__(None,None,None);raise
    def __exit__(self,*args):
        try:self.server.shutdown();self.server.server_close();self.thread.join()
        finally:self.owner.__exit__(*args)


class Parser(argparse.ArgumentParser):
    def error(self,message):self.exit(2,'Invalid private gateway command; use --help.\n')


def main():
    parser=Parser(description=__doc__);parser.add_argument('--root',type=Path,required=True)
    commands=parser.add_subparsers(dest='command',required=True)
    setup=commands.add_parser('init');setup.add_argument('--profile',type=Path,required=True)
    commands.add_parser('info');commands.add_parser('serve');args=parser.parse_args()
    try:
        if args.command=='init':reply=initialize(args.root,private.read(args.profile))
        elif args.command=='info':reply=info(args.root,load(args.root))
        else:
            stop=threading.Event()
            for name in (signal.SIGINT,signal.SIGTERM):signal.signal(name,lambda *_:stop.set())
            with Runtime(args.root) as runtime:
                print(json.dumps(dict(info(args.root,runtime.profile),listener_started=True)),flush=True)
                stop.wait()
            return 0
        print(json.dumps(reply));return 0
    except (ValueError,OSError,ClientError,CatalogError):
        print('{"error":"private_gateway_refused","state":"UNKNOWN"}');return 1


if __name__=='__main__':raise SystemExit(main())
