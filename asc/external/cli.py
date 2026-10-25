"""Explicit private Linux-development archive CLI, no daemon/device/writer mode."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
from .local import Tree
from .source import PinnedSource
from .destination import LocalDirectory
from .recovery import verify_stage
from .format import fail
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


class PrivateParser(argparse.ArgumentParser):
    def error(self,message):
        self.exit(2,'Invalid external command; use --help.\n')


SAFE_ERRORS={'unsafe_external_path','external_destination_overlaps_source',
    'external_destination_not_empty','external_store_busy','external_recovery_busy',
    'external_backup_stale','external_recovery_intent_conflict','external_recovery_destination_not_empty',
    'external_source_unavailable','external_source_mismatch','external_snapshot_mismatch',
    'external_object_corrupt','external_filesystem_unsupported','external_platform_not_qualified',
    'external_directory_changed','external_file_changed','external_entry_limit',
    'invalid_external_owner_config','external_source_identity_mismatch','external_source_roots_required'}


def main(argv=None):
    parser=PrivateParser(description='ASC private external data backup; recovery never grants writer authority')
    commands=parser.add_subparsers(dest='action',required=True)
    for name in ('init','create','resume','list','verify','retention-preview','stage','stage-verify'):
        p=commands.add_parser(name)
        if name!='stage-verify':p.add_argument('--store',required=True)
        if name in ('init','create','resume','stage'):p.add_argument('--source-root',action='append',required=True)
        if name in ('create','resume'):p.add_argument('--owner-config',required=True)
        if name in ('resume','verify','stage'):p.add_argument('--backup-id',required=True)
        if name=='verify':
            p.add_argument('--expected-sha256',required=True);p.add_argument('--minimum-index',type=int,default=0)
            p.add_argument('--cluster-id')
        if name in ('stage','stage-verify'):
            p.add_argument('--destination',required=True);p.add_argument('--expected-sha256',required=True)
        if name=='stage':
            p.add_argument('--cluster-id',required=True);p.add_argument('--minimum-index',required=True,type=int)
    args=parser.parse_args(argv)
    try:
        host_guard()
        if args.action=='stage-verify':
            print(json.dumps(verify_stage(args.destination,args.expected_sha256),sort_keys=True));return 0
        adapter=LocalDirectory(args.store)
        if args.action=='init':
            adapter.initialize(args.source_root);result={'state':'INITIALIZED','format':1}
        elif args.action in ('create','resume'):
            source=PinnedSource(owner_client(args.owner_config))
            roots=[*args.source_root,str(Path(args.owner_config).parent)]
            result=adapter.create(source,roots) if args.action=='create' else adapter.resume(source,args.backup_id,roots)
        elif args.action=='stage':
            result=adapter.stage(args.backup_id,args.expected_sha256,args.destination,args.source_root,args.cluster_id,args.minimum_index)
        elif args.action=='list':result=adapter.inventory()
        elif args.action=='retention-preview':result=adapter.retention_preview()
        else:result=adapter.verify(args.backup_id,args.expected_sha256,args.minimum_index,args.cluster_id)
        print(json.dumps(result,sort_keys=True))
        return 0 if result.get('state') not in ('UNKNOWN','INCOMPLETE','CORRUPT','STALE') else 1
    except (CatalogError,ClientError,OSError,ValueError,KeyError,TypeError) as exc:
        # Never print exception strings, private paths, keys, endpoint credentials.
        label=exc.code if isinstance(exc,CatalogError) and exc.code in SAFE_ERRORS else 'external_operation_failed'
        print(json.dumps({'state':'FAILED','error':label,'writer_recovery_supported':False}))
        return 1


if __name__=='__main__':raise SystemExit(main())
