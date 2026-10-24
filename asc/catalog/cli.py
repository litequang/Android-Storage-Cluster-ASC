"""Explicit owner operations and local read-only metadata lookup."""
import os
from pathlib import Path
from .client import ClusterClient
from .metadata import MetadataReplica,synchronize


def register(parser,handlers,cli):
    def guard():
        if os.name!='nt' or cli.inspect().get('protected'):
            cli._must_not_protected('catalog administration')

    def client():
        guard()
        bootstrap=cli.HOME/'cluster-client.json'
        if bootstrap.exists():
            cfg=cli._read_path(bootstrap)
            return ClusterClient(cluster_id=cfg['cluster_id'],controllers=cfg['controllers'])
        cfg=cli.read_private('controller.json')
        return ClusterClient('https://127.0.0.1:'+str(cfg['listen_port']),
                             cli.fingerprint_from_pem(cli.HOME/'server.crt'),cfg['admin_token'])

    def execute(args):
        action=args.action
        if action.startswith('catalog-local-'):
            cfg=cli.read_private('node.json')
            cache=MetadataReplica(cli.HOME/'catalog-metadata.sqlite3',cfg['cluster_id'],read_only=True)
            cli._show(cache.file(args.file_id) if action=='catalog-local-file' else cache.files() if action=='catalog-local-files' else cache.status())
            return
        if action=='catalog-sync':
            guard();cli._show(synchronize(cli.HOME,cli.read_private('node.json')));return
        api=client()
        if action=='catalog-register-node':
            result=api.request('POST','nodes/register',{'node_id':args.node_id,'origin':args.origin,'pin':args.pin,
                'device_id':args.device_id,'volume_ids':args.volume_id,'metadata_allowed':True,
                'storage_allowed':not args.metadata_only})
        elif action=='catalog-upload':
            with Path(args.source).open('rb') as stream:
                result=api.upload(stream,args.logical_path,args.key,args.policy,args.version)
        elif action=='catalog-download':
            with Path(args.output).open('xb+') as output:
                result=api.download(args.file_id,output);output.flush();os.fsync(output.fileno())
        elif action=='catalog-policy':
            result=api.request('POST','files/'+args.file_id+'/policy',{'policy':args.policy})
        elif action=='catalog-retry-job':
            result=api.request('POST','jobs/'+args.job_id+'/retry',{})
        elif action=='catalog-run-job':
            result=api.request('POST','jobs/run',{'job_id':args.job_id} if args.job_id else {})
        elif action=='catalog-reconcile':
            result=api.request('POST','reconcile',{})
        else:
            path={'catalog-files':'files','catalog-jobs':'jobs','catalog-status':'metadata/status'}.get(action)
            if action=='catalog-file':path='files/'+args.file_id
            if action=='catalog-replicas':path='files/'+args.file_id+'/replicas'
            if action=='catalog-job':path='jobs/'+args.job_id
            result=api.request('GET',path)
        cli._show(result)

    simple=('catalog-files','catalog-jobs','catalog-status','catalog-reconcile','catalog-sync','catalog-local-files','catalog-local-status')
    for command in simple:parser.add_parser(command);handlers[command]=execute
    for command in ('catalog-file','catalog-replicas','catalog-local-file','catalog-download','catalog-policy'):
        a=parser.add_parser(command);a.add_argument('file_id')
        if command=='catalog-download':a.add_argument('output')
        if command=='catalog-policy':a.add_argument('--policy',choices=['single','replicated_2','replicated_3'],required=True)
        handlers[command]=execute
    for command in ('catalog-job','catalog-retry-job','catalog-run-job'):
        a=parser.add_parser(command)
        if command=='catalog-run-job':a.add_argument('job_id',nargs='?')
        else:a.add_argument('job_id')
        handlers[command]=execute
    a=parser.add_parser('catalog-upload')
    a.add_argument('source');a.add_argument('logical_path');a.add_argument('--key',required=True)
    a.add_argument('--policy',choices=['single','replicated_2','replicated_3'],default='replicated_2')
    a.add_argument('--version',type=int,default=1);handlers['catalog-upload']=execute
    a=parser.add_parser('catalog-register-node')
    a.add_argument('node_id');a.add_argument('--origin');a.add_argument('--pin')
    a.add_argument('--device-id',required=True);a.add_argument('--volume-id',action='append',default=[])
    a.add_argument('--metadata-only',action='store_true');handlers['catalog-register-node']=execute

    from ..backup.cli import register as register_backup
    register_backup(parser, handlers, client, cli)
