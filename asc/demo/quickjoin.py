"""Guided local adapter to existing Core enrollment; no second identity engine."""
import argparse
import contextlib
import io
import json
import os
import sqlite3
from pathlib import Path
import sys
from types import SimpleNamespace


class JoinError(ValueError):
    def __init__(self,code):self.code=code


def start(root,args):
    env=dict(os.environ,ASC_HOME=str(root/'node'),PYTHONDONTWRITEBYTECODE='1')
    command=[sys.executable,'-B','-m','asc.demo.quickjoin','--state',str(root)]
    for name in ('controller','pin','name','expected_cluster_id'):
        value=getattr(args,name,None)
        if value is not None:command+=['--'+name.replace('_','-'),value]
    if args.new_code:command+=['--new-code']
    os.chdir(Path(__file__).resolve().parents[2])
    os.execve(sys.executable,command,env)


def normalized_pin(value):
    if not isinstance(value,str):raise JoinError('invalid_pin')
    value=value.replace(':','').strip().upper()
    if len(value)!=64 or any(c not in '0123456789ABCDEF' for c in value):raise JoinError('invalid_pin')
    return value


def enroll(args):
    from .installer import guard,private_path
    from .state import inspect_state,read_json,lan_origin,reject_recovery
    from .locks import private_lock
    from ..catalog.common import identifier
    from ..client import request_json,ClientError
    from .. import cli as core
    try:guard()
    except ValueError:raise JoinError('device_or_dependency_denied') from None
    root=private_path(args.state)
    try:reject_recovery(root)
    except ValueError:raise JoinError('recovery_read_only') from None
    if not (root/'demo.json').exists():raise JoinError('setup_required')
    try:inspect_state(root)
    except ValueError:raise JoinError('state_incompatible') from None
    if core.HOME!=root/'node':raise JoinError('private_home_mismatch')
    with private_lock(root,'demo-operation'):
        inspect_state(root)
        if os.environ.get('ASC_DEMO_PREFIX'):
            from .upgrade import startup_check
            startup_check(os.environ['ASC_DEMO_PREFIX'],root)
        home=root/'node';node_path=home/'node.json';pending_path=home/'enrollment_pending.json'
        current=read_json(node_path) if node_path.exists() else None
        pending=read_json(pending_path) if pending_path.exists() else None
        saved=pending or current or {}
        origin=args.controller or saved.get('controller') or input('Controller HTTPS LAN: ').strip()
        lan_origin(origin)
        pin=args.pin or saved.get('pin') or input('TLS SHA-256 PIN from owner: ').strip()
        pin=normalized_pin(pin)
        for prior in (current,pending):
            if prior and (prior['controller']!=origin or normalized_pin(prior['pin'])!=pin):
                raise JoinError('binding_mismatch')
        # Preserve legacy spelling in pending/node config; canonical comparison
        # above does not silently rewrite any saved endpoint or certificate pin.
        if saved:origin,pin=saved['controller'],saved['pin']
        expected=args.expected_cluster_id or (pending.get('expected_cluster_id') if pending else None) or (current.get('cluster_id') if current else None)
        if expected is None:expected=input('Cluster ID from owner Dashboard: ').strip()
        identifier(expected)
        if current and current['cluster_id']!=expected or pending and pending['expected_cluster_id']!=expected:
            raise JoinError('cluster_mismatch')
        try:info=request_json(origin,pin,'GET','/api/v1/info')
        except (ClientError,OSError) as exc:
            if isinstance(exc,ClientError) and str(exc).startswith('SERVER CERTIFICATE PIN MISMATCH'):raise
            if current and not pending:
                return {'quick_join_version':1,'state':'identity_present','controller_confirmation':'unknown',
                    'node_id':current['node_id'],'cluster_id':current['cluster_id'],'identity_preserved':True,
                    'storage_approved':None,'failure_domain':None}
            raise
        if (type(info.get('protocol_version')) is not int or info['protocol_version']!=1 or
                type(info.get('schema_version')) is not int or info['schema_version']!=4 or
                info.get('mode')!='single-writer-development' or info.get('raft_enabled') is not False or
                'retry-safe-enrollment-v1' not in info.get('features',[])):
            raise JoinError('unsupported_runtime')
        if info['cluster_id']!=expected:raise JoinError('cluster_mismatch')
        name=args.name or (pending['payload']['name'] if pending else 'ASC node' if current else input('Node name: ').strip())
        core.valid.name(name)
        call=SimpleNamespace(controller=origin,pin=pin,name=name,sd_test=False,new_code=args.new_code,
            node_id=None,cluster_id=None,expected_cluster_id=expected)
        # Core creates/persists the operation/token before POST and validates ACK.
        # Its private messages are replaced by the structured, redacted result.
        with contextlib.redirect_stdout(io.StringIO()):core.node_join(call)
        enrolled=read_json(node_path)
        return {'quick_join_version':1,'state':'identity_present' if current else 'registered',
            'controller_confirmation':'unknown' if current else 'confirmed_join_receipt',
            'node_id':enrolled['node_id'],'cluster_id':enrolled['cluster_id'],'identity_preserved':True,
            'storage_approved':None,'failure_domain':None,'next_step':'explicit_storage_setup_and_owner_approval'}


class Parser(argparse.ArgumentParser):
    def error(self,message):self.exit(2,'Invalid Quick Join command; use --help.\n')


def main():
    parser=Parser(description=__doc__);parser.add_argument('--state',type=Path,required=True)
    for name in ('controller','pin','name','expected-cluster-id'):parser.add_argument('--'+name)
    parser.add_argument('--new-code',action='store_true');args=parser.parse_args()
    try:
        print(json.dumps(enroll(args),sort_keys=True));return 0
    except (KeyboardInterrupt,EOFError):
        print(json.dumps({'quick_join_version':1,'state':'interrupted','identity_preserved':True}));return 3
    except Exception as exc:
        from ..client import ClientError
        from ..storage.errors import StorageError
        if not isinstance(exc,(ValueError,OSError,sqlite3.Error,KeyError,TypeError,ClientError,StorageError)):raise
        code=exc.code if isinstance(exc,JoinError) else 'operation_unconfirmed'
        if isinstance(exc,ClientError):
            code=('pairing_code_rejected' if exc.code=='invalid_or_expired_code' else
                  'cluster_mismatch' if exc.code=='cluster_mismatch' else
                  'tls_pin_mismatch' if str(exc).startswith('SERVER CERTIFICATE PIN MISMATCH') else 'network_unconfirmed')
        try:pending=(args.state/'node/enrollment_pending.json').exists()
        except OSError:pending=None
        print(json.dumps({'quick_join_version':1,'state':'resume_required' if pending else 'rejected',
            'error':code,'identity_preserved':True,'pending_preserved':pending}));return 3


if __name__=='__main__':raise SystemExit(main())
