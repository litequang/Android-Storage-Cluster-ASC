"""Owner-local stopped Demo maintenance. No network listener, SSH or shell runner."""
import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import uuid
from ..bridge import private
from ..catalog.common import CatalogError
from ..demo import upgrade
from ..demo.installer import guard, private_path
from ..demo.locks import private_lock
from ..demo.package import digest, encoded
from ..demo.state import FORMATS, inspect_state, read_json
from ..storage.errors import StorageError

FIELDS={'format','kind','mode','action','installation_id','role','current_release_id',
        'target_release_id','backup_sha256','state_formats','plan_sha256'}


def platform_guard():
    if (not sys.platform.startswith('linux') or hasattr(sys,'getandroidapilevel')
            or 'com.termux' in os.environ.get('PREFIX','') or os.environ.get('ANDROID_ROOT')):
        raise ValueError('maintenance platform not qualified')
    # Keep the existing protected/unknown-device and dependency rules. Linux
    # tests use the original explicitly synthetic Demo device/dependency fixture.
    guard()


def validate(plan,confirmation=None):
    if (type(plan) is not dict or set(plan)!=FIELDS or type(plan['format']) is not int or plan['format']!=1
            or plan['kind']!='asc-private-maintenance' or plan['mode']!='single-writer-demo'
            or plan['action'] not in ('upgrade','rollback') or plan['role'] not in ('controller','node')
            or plan['state_formats']!=FORMATS or any(type(v) is not int for v in plan['state_formats'].values())):
        raise ValueError('unsupported maintenance plan')
    if type(plan['installation_id']) is not str or str(uuid.UUID(plan['installation_id']))!=plan['installation_id']:
        raise ValueError('invalid installation binding')
    for key in ('current_release_id','target_release_id','backup_sha256','plan_sha256'):
        if type(plan[key]) is not str or not re.fullmatch('[0-9a-f]{64}',plan[key]):raise ValueError('invalid maintenance digest')
    body={k:v for k,v in plan.items() if k!='plan_sha256'}
    if (digest(encoded(body))!=plan['plan_sha256'] or plan['current_release_id']==plan['target_release_id']
            or confirmation is not None and confirmation!=plan['plan_sha256']):
        raise ValueError('maintenance confirmation or plan mismatch')
    return plan


@contextmanager
def locked(root,prefix):
    platform_guard();root=private_path(root);prefix=private_path(prefix,code_prefix=True)
    with upgrade.stopped(root),private_lock(prefix,'install'):
        upgrade.startup_check(prefix,root)
        yield root,prefix


def prepare_locked(root,prefix,target,backup,action):
    marker=inspect_state(root);pointer=read_json(prefix/'install.json')
    upgrade.verify(upgrade.release_path(prefix,pointer['release_id']))
    release=upgrade.verify(upgrade.release_path(prefix,target));upgrade.compatibility(release,root)
    report=upgrade.verify_backup(backup,root)
    body=dict(format=1,kind='asc-private-maintenance',mode='single-writer-demo',action=action,
        installation_id=marker['installation_id'],role=marker['role'],current_release_id=pointer['release_id'],
        target_release_id=target,backup_sha256=report['backup_sha256'],state_formats=dict(FORMATS))
    return validate(dict(body,plan_sha256=digest(encoded(body))))


def preflight(root,prefix,target,backup,action='upgrade'):
    with locked(root,prefix) as (root,prefix):return prepare_locked(root,prefix,target,backup,action)


def apply(root,prefix,plan,backup,new_backup,confirmation):
    validate(plan,confirmation)
    if confirmation is None:raise ValueError('explicit confirmation required')
    with locked(root,prefix) as (root,prefix):
        marker=inspect_state(root)
        if (marker['installation_id'],marker['role'])!=(plan['installation_id'],plan['role']):
            raise ValueError('maintenance installation changed')
        current=read_json(prefix/'install.json')['release_id']
        if current==plan['target_release_id']:
            # A lost successful LOCAL ACK must never activate twice or restore an
            # old DB. Require actual matching existing journal + complete bytes.
            journal=upgrade.read_journal(prefix)
            expected={'status':'COMPLETED','action':plan['action'],'installation_id':plan['installation_id'],
                'old_release':plan['current_release_id'],'new_release':plan['target_release_id'],
                'backup_sha256':plan['backup_sha256']}
            if any(journal.get(k)!=v for k,v in expected.items()) or private_path(new_backup)!=private_path(journal['backup']):
                raise ValueError('maintenance outcome not proven')
            saved=upgrade.verify_backup(journal['backup'])
            if saved['backup_sha256']!=plan['backup_sha256']:raise ValueError('maintenance backup changed')
            upgrade.verify(upgrade.release_path(prefix,current))
            return {'format':1,'applied':True,'already_applied':True,'release_id':current,
                'plan_sha256':plan['plan_sha256'],'runtime_started':False,'state_restored':False}
        fresh=prepare_locked(root,prefix,plan['target_release_id'],backup,plan['action'])
        if fresh!=plan:raise ValueError('maintenance preflight stale')
    # Activate reacquires original stopped/install locks and repeats the exact
    # current-release/installation/backup CAS; no check-then-act lock gap.
    result=upgrade.activate(root,prefix,plan['target_release_id'],new_backup,plan['action'],
        expected_current=(plan['installation_id'],plan['current_release_id']),
        verified_backup=(backup,plan['backup_sha256']))
    return dict(result,format=1,applied=True,already_applied=False,plan_sha256=plan['plan_sha256'],
        runtime_started=False,state_restored=False)


class Parser(argparse.ArgumentParser):
    def error(self,message):self.exit(2,'Invalid private maintenance command; use --help.\n')


def main():
    parser=Parser(description=__doc__);parser.add_argument('--state',type=Path,required=True)
    parser.add_argument('--prefix',type=Path,required=True)
    commands=parser.add_subparsers(dest='command',required=True)
    ready=commands.add_parser('preflight');ready.add_argument('--target',required=True)
    ready.add_argument('--action',choices=('upgrade','rollback'),default='upgrade')
    ready.add_argument('--backup',type=Path,required=True)
    commit=commands.add_parser('apply');commit.add_argument('--plan',type=Path,required=True)
    commit.add_argument('--backup',type=Path,required=True);commit.add_argument('--new-backup',type=Path,required=True)
    commit.add_argument('--confirm-plan',required=True)
    args=parser.parse_args()
    try:
        if args.command=='preflight':reply=preflight(args.state,args.prefix,args.target,args.backup,args.action)
        else:reply=apply(args.state,args.prefix,private.read(args.plan),args.backup,args.new_backup,args.confirm_plan)
        print(json.dumps(reply,sort_keys=True));return 0
    except (ValueError,OSError,TypeError,KeyError,CatalogError,StorageError,sqlite3.Error):
        print('{"format":1,"error":"maintenance_refused","state":"UNKNOWN","runtime_started":false}');return 1


if __name__=='__main__':raise SystemExit(main())
