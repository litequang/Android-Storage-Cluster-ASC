"""Explicit private Linux-development archive CLI, no daemon/device/writer mode."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
from .engine import BackupEngine
from .local import LocalStore, Tree
from .source import PinnedSource
from .verify import inventory, verify, retention_preview
from .format import decode, fail
from ..catalog.client import ClusterClient
from ..catalog.common import CatalogError
from ..client import ClientError


def host_guard():
    # Source-only desktop qualification; no phone/M51/unknown Android bypass.
    if (not sys.platform.startswith('linux') or hasattr(sys,'getandroidapilevel') or
            shutil.which('getprop') is not None or
            'com.termux' in os.environ.get('PREFIX','') or os.environ.get('ANDROID_ROOT')):
        fail('external_platform_not_qualified',403)


def owner_client(path):
    path=Path(path)
    with Tree(path.parent) as parent:raw=parent.read(path.name,65536)
    def unique(pairs):
        result={}
        for k,v in pairs:
            if k in result:raise ValueError('duplicate config field')
            result[k]=v
        return result
    cfg=json.loads(raw,object_pairs_hook=unique)
    # Use the existing separate-endpoint owner bootstrap, never a secret CLI flag.
    if set(cfg)!={'cluster_id','controllers'}:fail('invalid_external_owner_config',400)
    return ClusterClient(cluster_id=cfg['cluster_id'],controllers=cfg['controllers'])


def main(argv=None):
    parser=argparse.ArgumentParser(description='ASC private external data backup; recovery never grants writer authority')
    commands=parser.add_subparsers(dest='action',required=True)
    for name in ('init','create','resume','list','verify','retention-preview'):
        p=commands.add_parser(name);p.add_argument('--store',required=True)
        if name in ('init','create','resume'):p.add_argument('--source-root',action='append',required=True)
        if name in ('create','resume'):p.add_argument('--owner-config',required=True)
        if name in ('resume','verify'):p.add_argument('--backup-id',required=True)
        if name=='verify':
            p.add_argument('--expected-sha256',required=True);p.add_argument('--minimum-index',type=int,default=0)
            p.add_argument('--cluster-id')
    args=parser.parse_args(argv)
    try:
        host_guard();store=LocalStore(args.store)
        if args.action=='init':
            LocalStore.initialize(args.store,args.source_root);result={'state':'INITIALIZED','format':1}
        elif args.action in ('create','resume'):
            source=PinnedSource(owner_client(args.owner_config));engine=BackupEngine(store)
            roots=[*args.source_root,str(Path(args.owner_config).parent)]
            result=engine.create(source,roots) if args.action=='create' else engine.resume(source,args.backup_id,roots)
        elif args.action=='list':result=inventory(store)
        elif args.action=='retention-preview':result=retention_preview(store)
        else:result=verify(store,args.backup_id,args.expected_sha256,args.minimum_index,args.cluster_id)
        print(json.dumps(result,sort_keys=True))
        return 0 if result.get('state') not in ('UNKNOWN','INCOMPLETE','CORRUPT','STALE') else 1
    except (CatalogError,ClientError,OSError,ValueError,KeyError,TypeError):
        # Never print exception strings, private paths, keys, endpoint credentials.
        print(json.dumps({'state':'FAILED','error':'external_operation_failed','writer_recovery_supported':False}))
        return 1


if __name__=='__main__':raise SystemExit(main())
