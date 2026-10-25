"""Explicit read-only Core gateway; shared Dashboard security/TLS/assets, no engine."""
import argparse
import json
import os
from pathlib import Path
import signal
import ssl
import threading
import uuid
from ..bridge import private
from ..catalog.common import identifier
from ..demo.installer import private_path
from ..demo.state import lan_host,read_json
from ..demo.locks import private_lock
from ..demo.dashboard.auth import Sessions
from ..demo.dashboard.http import DashboardHandler
from ..demo.dashboard.tls import generate_identity,openssl,FILES
from ..external.cli import host_guard
from ..external.local import separate
from ..identity import fingerprint_from_pem
from ..server import Server
from ..storage.volumes import no_links
from ..storage.errors import StorageError
from .client import Observer,RecoveryObserver


def reject_engine_ancestry(root):
    for parent in (root,*root.parents):
        if any((parent/name).exists() or (parent/name).is_symlink() for name in
               ('demo.json','controller.json','node.json','manifest.sqlite3','.asc-volume.json','RECOVERY_READ_ONLY.json','failover.json')):
            raise ValueError('gateway must stay outside engine/volume/recovery roots')


def init(root,host,port,cluster,epoch,controllers=None,recovery=None,source_roots=(),minimum_index=0):
    host_guard();root=private_path(root);lan_host(host);identifier(cluster);identifier(epoch)
    if type(port) is not int or not 1024<=port<=65535:raise ValueError('invalid explicit gateway port')
    reject_engine_ancestry(root);separate(root,source_roots)
    if recovery is None:Observer(cluster,epoch,controllers,minimum_index)
    else:
        if type(recovery) is not dict or set(recovery)!={'root','anchor'}:raise ValueError('invalid passive recovery source')
        separate(root,[Path(recovery['root']),*source_roots]);RecoveryObserver(recovery['root'],recovery['anchor'],cluster,minimum_index)
    root.mkdir(mode=0o700);private.directory(root)
    (root/'dashboard').mkdir(mode=0o700)
    generate_identity(root/'dashboard',host,'ASC Core Read-only')
    cfg={'format':1,'gateway_id':str(uuid.uuid4()),'mode':'core-quorum' if recovery is None else 'recovery-read-only',
         'host':host,'port':port,'cluster_id':cluster,'epoch':epoch,'minimum_index':minimum_index,
         'controllers':controllers if recovery is None else None,'recovery':recovery,'source_roots':[str(p) for p in source_roots]}
    private.create(root/'gateway.json',cfg)
    return public_info(root,cfg)


def load(root):
    host_guard();root=private.directory(root);reject_engine_ancestry(root);cfg=private.read(root/'gateway.json')
    if (set(cfg)!={'format','gateway_id','mode','host','port','cluster_id','epoch','minimum_index','controllers','recovery','source_roots'} or
            type(cfg['format']) is not int or cfg['format']!=1 or cfg['mode'] not in ('core-quorum','recovery-read-only') or
            type(cfg['port']) is not int or not 1024<=cfg['port']<=65535 or type(cfg['source_roots']) is not list):
        raise ValueError('unsupported explicit gateway mode/config')
    identifier(cfg['gateway_id']);identifier(cfg['cluster_id']);identifier(cfg['epoch']);lan_host(cfg['host'])
    separate(root,[Path(p) for p in cfg['source_roots']])
    if cfg['mode']=='core-quorum':
        if cfg['recovery'] is not None:raise ValueError('mode source conflict')
        Observer(cfg['cluster_id'],cfg['epoch'],cfg['controllers'],cfg['minimum_index'])
    else:
        if cfg['controllers'] is not None or type(cfg['recovery']) is not dict or set(cfg['recovery'])!={'root','anchor'}:
            raise ValueError('mode source conflict')
        separate(root,[Path(cfg['recovery']['root'])])
        RecoveryObserver(cfg['recovery']['root'],cfg['recovery']['anchor'],cfg['cluster_id'],cfg['minimum_index'])
    for name in FILES:no_links(root/'dashboard'/name)
    for name in FILES:
        path=root/'dashboard'/name;info=path.stat()
        if info.st_uid!=os.getuid() or info.st_nlink!=1 or info.st_mode&0o077 or not path.is_file() or info.st_size>65536:
            raise ValueError('unsafe gateway TLS identity')
    openssl('verify','-CAfile',root/'dashboard/ca.crt','-purpose','sslserver','-verify_ip',cfg['host'],root/'dashboard/server.crt')
    return cfg


def public_info(root,cfg):
    return {'mode':cfg['mode'],'url':f"https://{cfg['host']}:{cfg['port']}",
        'public_ca':str(root/'dashboard/ca.crt'),'ca_sha256':fingerprint_from_pem(root/'dashboard/ca.crt'),
        'read_only':True,'writer_authority':False,'trust_required':'Verify public CA SHA independently; never bypass browser certificate errors.'}


class API:
    def __init__(self,root,cfg):
        self.root=root;self.mode=cfg['mode'];self.cfg=dict(host=cfg['host'],port=cfg['port'],max_upload_bytes=0)
        self.origin=f"https://{cfg['host']}:{cfg['port']}";self.sessions=Sessions();self.pairings=None
        # Different cookie namespace from Demo and other gateway roots on same host.
        self.cookie_name='__Host-ASC-Observer-'+cfg['gateway_id'].replace('-','')
        self.views=(Observer(cfg['cluster_id'],cfg['epoch'],cfg['controllers'],cfg['minimum_index']) if self.mode=='core-quorum' else
                    RecoveryObserver(cfg['recovery']['root'],cfg['recovery']['anchor'],cfg['cluster_id'],cfg['minimum_index']))
    def close(self):self.sessions.close()


class Runtime:
    def __init__(self,root):
        host_guard();self.root=private.directory(root)
    def __enter__(self):
        cfg=load(self.root);self.owner=private_lock(self.root,'gateway');self.owner.__enter__()
        try:
            self.api=API(self.root,cfg)
            self.server=Server((cfg['host'],cfg['port']),None,'',handler=DashboardHandler)
            self.server.api=self.api;self.server.slots=threading.BoundedSemaphore(8);self.server.daemon_threads=False
            context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.minimum_version=ssl.TLSVersion.TLSv1_2
            context.load_cert_chain(self.root/'dashboard/server.crt',self.root/'dashboard/server.key')
            self.server.tls_context=context
            self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start();return self
        except BaseException:
            if hasattr(self,'server'):self.server.server_close()
            if hasattr(self,'api'):self.api.close()
            self.owner.__exit__(None,None,None);raise
    def __exit__(self,*_):
        try:self.server.shutdown();self.server.server_close();self.thread.join();self.api.close()
        finally:self.owner.__exit__(None,None,None)


class Parser(argparse.ArgumentParser):
    def error(self,message):self.exit(2,'Invalid observer command; use --help.\n')


def main():
    parser=Parser(description=__doc__);parser.add_argument('--root',type=Path,required=True)
    commands=parser.add_subparsers(dest='command',required=True)
    setup=commands.add_parser('init');setup.add_argument('--bootstrap',type=Path);setup.add_argument('--cluster-id',required=True)
    setup.add_argument('--epoch',required=True);setup.add_argument('--host',default='127.0.0.1');setup.add_argument('--port',type=int,default=8445)
    setup.add_argument('--minimum-index',type=int,default=0);setup.add_argument('--source-root',type=Path,action='append',default=[])
    setup.add_argument('--recovery-stage',type=Path);setup.add_argument('--manifest-sha256')
    serve=commands.add_parser('serve');serve.add_argument('--issue-login-code',action='store_true')
    commands.add_parser('info');args=parser.parse_args()
    try:
        if args.command=='init':
            if bool(args.bootstrap)==bool(args.recovery_stage):raise ValueError('choose exactly one explicit source')
            endpoints=None;recovery=None
            if args.bootstrap:
                bootstrap=private.read(args.bootstrap)
                if set(bootstrap)!={'cluster_id','controllers'} or bootstrap['cluster_id']!=args.cluster_id:raise ValueError('bootstrap binding rejected')
                endpoints=bootstrap['controllers']
            else:recovery={'root':str(args.recovery_stage),'anchor':args.manifest_sha256}
            result=init(args.root,args.host,args.port,args.cluster_id,args.epoch,endpoints,recovery,args.source_root,args.minimum_index)
        elif args.command=='serve':
            stop=threading.Event()
            for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,lambda *_:stop.set())
            with Runtime(args.root) as runtime:
                # Explicit private local operator action, never shared password/public log.
                if args.issue_login_code:
                    print(json.dumps({'login_code':runtime.api.sessions.issue(),**public_info(args.root,load(args.root))}),flush=True)
                stop.wait()
            return 0
        else:result=public_info(args.root,load(args.root))
        print(json.dumps(result,sort_keys=True));return 0
    except (ValueError,OSError,KeyError,TypeError,StorageError):
        print('{"error":"gateway_refused"}');return 3
    except KeyboardInterrupt:return 0


if __name__=='__main__':raise SystemExit(main())
