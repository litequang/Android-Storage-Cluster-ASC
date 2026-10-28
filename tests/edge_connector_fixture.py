"""TEST-ONLY loopback HTTPS connector; NOT public DNS/cloudflared/IdP proof."""
from contextlib import closing
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import http.client
import ipaddress
import ssl
import threading
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def dns_identity(root):
    root.mkdir(mode=0o700);now=datetime.now(timezone.utc)
    ca=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'ASC synthetic connector CA')])
    cert=(x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(ca.public_key())
        .serial_number(x509.random_serial_number()).not_valid_before(now-timedelta(minutes=1))
        .not_valid_after(now+timedelta(days=1)).add_extension(x509.BasicConstraints(ca=True,path_length=0),critical=True)
        .add_extension(x509.KeyUsage(False,False,False,False,False,True,True,False,False),critical=True).sign(ca,hashes.SHA256()))
    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    leaf=(x509.CertificateBuilder().subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'asc.example.com')]))
        .issuer_name(name).public_key(key.public_key()).serial_number(x509.random_serial_number())
        .not_valid_before(now-timedelta(minutes=1)).not_valid_after(now+timedelta(days=1))
        .add_extension(x509.BasicConstraints(ca=False,path_length=None),critical=True)
        .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]),critical=False)
        .add_extension(x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.SERVER_AUTH]),critical=False)
        .sign(ca,hashes.SHA256()))
    for filename,raw in [('ca.crt',cert.public_bytes(serialization.Encoding.PEM)),
                         ('server.crt',leaf.public_bytes(serialization.Encoding.PEM)),
                         ('server.key',key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))]:
        path=root/filename
        with path.open('xb') as output:output.write(raw)
        path.chmod(0o600)
    # Ephemeral CA signing key remains in memory; nothing is reused outside fixture.


class SyntheticConnector:
    def __init__(self,fixture):
        self.fixture=fixture;self.received=0
        self.context=ssl.create_default_context(cafile=str(fixture.root/'dashboard/ca.crt'))
        outer=self
        class Front(BaseHTTPRequestHandler):
            protocol_version='HTTP/1.1'
            def log_message(self,*args):pass
            def handle_request(inner):
                inner.close_connection=True
                if (inner.headers.get_all('Host',[])!=[outer.frontend.removeprefix('https://')]
                        or inner.headers.get('Origin',outer.frontend)!=outer.frontend):inner.send_error(403);return
                length=int(inner.headers.get('Content-Length','0'))
                if not 0<=length<=1024**2:inner.send_error(413);return
                headers={key:value for key,value in inner.headers.items() if key.lower() in
                    ('cookie','x-asc-csrf','content-type','origin','sec-fetch-site')}
                headers.update({'Host':'asc.example.com','Cf-Access-Jwt-Assertion':fixture.token,'Connection':'close'})
                if 'Origin' in inner.headers:headers['Origin']='https://asc.example.com'
                body=inner.rfile.read(length) if length else None
                with closing(http.client.HTTPSConnection('127.0.0.1',fixture.port,context=outer.context,timeout=45)) as c:
                    c.request(inner.command,inner.path,body,headers);response=c.getresponse();outer.received+=1
                    inner.send_response(response.status)
                    for key,value in response.getheaders():
                        if key.lower() not in ('server','date','connection'):inner.send_header(key,value)
                    inner.send_header('Connection','close');inner.end_headers()
                    while block:=response.read1(65536):inner.wfile.write(block)
            do_GET=do_POST=do_PUT=handle_request
        self.root=fixture.base/'connector';self.root.mkdir(mode=0o700);dns_identity(self.root/'dashboard')
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Front)
        self.frontend='https://127.0.0.1:'+str(self.server.server_port)
        tls=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);tls.minimum_version=ssl.TLSVersion.TLSv1_2
        tls.load_cert_chain(self.root/'dashboard/server.crt',self.root/'dashboard/server.key')
        self.server.socket=tls.wrap_socket(self.server.socket,server_side=True)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
    def stop(self):self.server.shutdown();self.server.server_close();self.thread.join()
