"""Safe foreground CLI for the single-writer LAN development registry."""
import argparse
from contextlib import ExitStack
import os
import getpass
import json
import sqlite3
import sys
import threading
import time
import uuid
from .client import ClientError, request_json
from .enrollment import new_pending, accepted_identity
from .identity import (HOME, ensure_private_home, fingerprint_from_pem, make_cert,
                       new_admin_token, read_private, replace_private, save_private)
from .probe import inspect
from .runtime import foreground_lock, running
from .store import Registry, SCHEMA_VERSION
from .server import serve
from . import validation as valid
from .storage.errors import StorageError
from . import __version__


def _show(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


def _must_not_protected(action):
    profile = inspect()
    if profile['protected'] or not profile.get('installation_allowed', False):
        raise ValueError(f'M51 PRODUCTION PROTECTED / DEVICE IDENTITY UNKNOWN: refusing {action}; '
                         'only read-only audit is allowed. No service or package changes made.')


def _registry(cfg):
    path = HOME / 'registry.sqlite3'
    if not path.is_file():
        raise ValueError('registry missing; restore private backup, do not recreate identity')
    reg = Registry(path)
    if reg.cluster_id() != cfg['cluster_id']:
        raise ValueError('registry identity missing/mismatched; restore backup instead of recreating state')
    reg.initialize(cfg['cluster_id'])
    return reg


def controller_init(args):
    _must_not_protected('controller initialization')
    ensure_private_home(HOME)
    if (HOME / 'controller.json').exists():
        read_private('controller.json')
        print('Controller already initialized; identity preserved. Migration occurs at controller-run.')
        return
    with foreground_lock(HOME, 'controller'):
        if (HOME / 'controller.json').exists():
            print('Controller already initialized; identity preserved. Migration occurs at controller-run.')
            return
        if (HOME / 'node.json').exists() or (HOME / 'enrollment_pending.json').exists():
            raise ValueError('existing node identity/enrollment; refusing controller initialization')
        valid.name(args.name)
        if not 1024 <= args.port <= 65535:
            raise ValueError('port must be 1024..65535')
        cert, key = HOME / 'server.crt', HOME / 'server.key'
        if any(p.exists() for p in (cert, key, HOME / 'registry.sqlite3')):
            raise ValueError('existing TLS/registry without controller state; restore backup instead of overwriting')
        make_cert(cert, key)
        cluster = str(uuid.uuid4())
        reg = Registry(HOME / 'registry.sqlite3')
        reg.initialize(cluster)
        reg.seed_self(args.name, inspect())
        save_private(HOME / 'controller.json', {'config_version': 1, 'cluster_id': cluster,
                     'admin_token': new_admin_token(), 'listen_port': args.port, 'node_name': args.name})
    print('Controller initialized: SINGLE-WRITER DEVELOPMENT (NOT Raft).')
    print('Cluster ID:', cluster)
    print('Certificate SHA256 PIN:', fingerprint_from_pem(cert))
    print('Start: python3 -m asc.cli controller-run')


def controller_run(args):
    consensus_config = getattr(args, 'consensus_config', None)
    # Explicit Windows metadata development follows the existing storage CLI
    # boundary. Protected profiles and all Android paths retain the hard guard.
    if not consensus_config or os.name != 'nt' or inspect().get('protected'):
        _must_not_protected('controller runtime')
    ensure_private_home(HOME)
    with foreground_lock(HOME, 'controller'):
        cfg = read_private('controller.json')
        reg = _registry(cfg)
        if consensus_config:
            from .consensus.service import Service
            catalog = Service(reg, consensus_config)
            try:
                catalog.start()
                serve('127.0.0.1', cfg['listen_port'], reg, cfg['admin_token'],
                      HOME / 'server.crt', HOME / 'server.key', catalog=catalog)
            finally:
                catalog.close()
            return
        if reg.consensus_enabled():
            raise ValueError('consensus configuration required; single-writer fallback refused')
        reg.update_self(inspect())
        stop = threading.Event()

        def refresh():
            while not stop.wait(30):
                try:
                    reg.update_self(inspect())
                except (OSError, ValueError, sqlite3.Error):
                    print('Local profile refresh failed; preserving registry.', flush=True)

        worker = threading.Thread(target=refresh, daemon=True)
        worker.start()
        from .catalog.service import CatalogService
        catalog=CatalogService(reg,getattr(args,'catalog_rate',4*1024**2),getattr(args,'job_timeout',300))
        try:
            catalog.start(background=True)
            serve('0.0.0.0', cfg['listen_port'], reg, cfg['admin_token'], HOME / 'server.crt', HOME / 'server.key',catalog=catalog)
        finally:
            catalog.close()
            stop.set()
            worker.join(timeout=5)


def _admin_request(method, path, obj=None):
    bootstrap=HOME/'cluster-client.json'
    if bootstrap.exists() and os.name=='nt' and not inspect().get('protected'):
        from .failover.discovery import Discovery
        cfg=_read_path(bootstrap)
        return Discovery(cfg['cluster_id'],cfg['controllers']).request(method,path,obj)
    _must_not_protected('controller administration')
    cfg = read_private('controller.json')
    # No token CLI flag or output. Node installations have no controller credential.
    return request_json(f"https://127.0.0.1:{cfg['listen_port']}",
                        fingerprint_from_pem(HOME / 'server.crt'), method, path, obj, cfg['admin_token'])


def controller_pair(args):
    obj = {'ttl': max(60, min(1800, args.ttl))}
    if args.node_id:
        obj['node_id'] = valid.node_id(args.node_id)
    reply = _admin_request('POST', '/api/v1/admin/pair', obj)
    code = reply['code']
    print('One-time join code (private):', '-'.join(code[i:i+4] for i in range(0, len(code), 4)))
    print('Expires after:', reply['ttl'], 'seconds')
    print('Server certificate PIN:', fingerprint_from_pem(HOME / 'server.crt'))
    print('Controller port:', read_private('controller.json')['listen_port'])
    if args.node_id:
        print('RE-PAIR target:', args.node_id, '(same ID; old token rejected after successful re-pair)')
    print('Use Android Wi-Fi settings for LAN IP. Do not use public IP.')


def controller_nodes(_args):
    _show(_admin_request('GET', '/api/v1/nodes'))


def controller_node(args):
    _show(_admin_request('GET', '/api/v1/nodes/' + valid.node_id(args.node_id)))


def controller_rename(args):
    _show(_admin_request('POST', '/api/v1/admin/rename',
                         {'node_id': valid.node_id(args.node_id), 'name': valid.name(args.name)}))


def controller_revoke(args):
    _show(_admin_request('POST', '/api/v1/admin/revoke', {'node_id': valid.node_id(args.node_id)}))


def _read_path(path):
    obj = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(obj, dict):
        raise ValueError('invalid private state')
    if 'config_version' in obj and (type(obj['config_version']) is not int or obj['config_version'] != 1):
        raise ValueError('unsupported private state version; use matching release')
    return obj


def _enroll(args, repair=False):
    _must_not_protected('node re-pair' if repair else 'node enrollment')
    expected_cluster = getattr(args, 'expected_cluster_id', None)
    if expected_cluster is not None:
        from .catalog.common import identifier
        identifier(expected_cluster)
    ensure_private_home(HOME)
    # Reinstall is read-only for an enrolled node, even while its agent holds the lock.
    if (not repair and (HOME / 'node.json').exists() and
            not (HOME / 'enrollment_pending.json').exists() and not (HOME / 'controller.json').exists()):
        saved = _read_path(HOME / 'node.json')
        if expected_cluster is not None and saved['cluster_id'] != expected_cluster:
            raise ClientError('Cluster ID mismatch; identity retained',409,'cluster_mismatch')
        print('Already joined. Existing identity preserved; no duplicate enrollment.')
        print('Use status; if credential rejected, use explicit node-repair with a targeted admin code.')
        return
    with foreground_lock(HOME, 'agent'):
        if (HOME / 'controller.json').exists():
            raise ValueError('controller identity exists; refusing node enrollment')
        node_path = HOME / 'node.json'
        current = _read_path(node_path) if node_path.exists() else None
        if expected_cluster is not None and current and current['cluster_id'] != expected_cluster:
            raise ClientError('Cluster ID mismatch; identity retained',409,'cluster_mismatch')
        if current and not repair:
            pending_path = HOME / 'enrollment_pending.json'
            if pending_path.exists():
                pending = _read_path(pending_path)
                if (pending['payload']['enrollment_token'] == current['token'] and
                        pending['expected_cluster_id'] == current['cluster_id']):
                    pending_path.unlink()  # Crash after node.json saved, before cleanup.
                else:
                    raise ValueError('pending re-pair exists; complete node-repair before starting agent')
            print('Already joined. Existing identity preserved; no duplicate enrollment.')
            print('Use status; if credential rejected, use explicit node-repair with a targeted admin code.')
            return
        target = (current['node_id'] if current else args.node_id) if repair else None
        cluster = (current['cluster_id'] if current else args.cluster_id) if repair else None
        origin = current['controller'] if current else args.controller
        pin = current['pin'] if current else args.pin
        controllers = current.get('controllers') if current else None
        if controllers:
            from .catalog.common import identifier
            if not current.get('cluster_epoch'):
                raise ValueError('pinned cluster epoch required for distributed re-pair')
            identifier(current['cluster_epoch'])
        def enrollment_request(method, path, payload=None):
            if not controllers:
                return request_json(origin, pin, method, path, payload)
            from .failover.discovery import Discovery
            trusted = Discovery(cluster, controllers, current['token'])
            last = None
            for endpoint in trusted.endpoints:
                try:
                    result = request_json(endpoint['origin'], endpoint['pin'], method, path, payload, timeout=20)
                    if result.get('cluster_id') != cluster:
                        raise ClientError('Cluster ID mismatch; refusing re-pair')
                    return result
                except ClientError as exc:
                    if exc.status not in (None, 429, 502, 503, 504):
                        raise
                    last = exc
                except OSError as exc:
                    last = exc
            raise last or ClientError('no pinned Controller for enrollment', 503)
        if repair and (not target or not cluster):
            raise ValueError('lost identity: node-repair requires --node-id and --cluster-id from controller')
        if not origin or not pin:
            raise ValueError('--controller and --pin required for first enrollment / lost identity')
        if target:
            valid.node_id(target)
        pending_path = HOME / 'enrollment_pending.json'
        if pending_path.exists() and repair and args.new_code:
            # Explicit replacement preserves the old operation for administrator recovery.
            pending_path.rename(HOME / ('enrollment_abandoned-' + uuid.uuid4().hex + '.json'))
        if pending_path.exists():
            pending = _read_path(pending_path)
            if expected_cluster is not None and pending['expected_cluster_id'] != expected_cluster:
                raise ClientError('Cluster ID mismatch; pending retained',409,'cluster_mismatch')
            if (pending['controller'] != origin or pending['pin'] != pin or
                    pending.get('target_node_id') != target or pending.get('cluster_id') != cluster or
                    controllers and pending.get('controllers') != controllers):
                raise ValueError('pending operation differs; preserve it and use controlled node-repair --new-code')
            if args.new_code and not repair:
                # Keep operation ID/token: even a replacement grant cannot create a duplicate.
                replacement_code = valid.code(getpass.getpass('Enter replacement one-time join code: '))
                save_private(HOME / ('enrollment_abandoned-' + uuid.uuid4().hex + '.json'), pending)
                pending['payload']['code'] = replacement_code
                replace_private(pending_path, pending)
            print('Retrying saved enrollment operation; no new identity generated.')
        else:
            info = enrollment_request('GET', '/api/v1/info')
            if expected_cluster is not None and info['cluster_id'] != expected_cluster:
                raise ClientError('Cluster ID mismatch; enrollment refused',409,'cluster_mismatch')
            if 'retry-safe-enrollment-v1' not in info.get('features', []):
                raise ValueError('upgrade controller to Phase 1.1 before new enrollment; existing v0.4 heartbeats remain supported')
            if cluster and info['cluster_id'] != cluster:
                raise ClientError('Cluster ID mismatch; refusing re-pair')
            profile = inspect(sd_write=args.sd_test)
            node_name = valid.name(args.name or profile['model'])
            code = valid.code(getpass.getpass('Enter one-time join code: '))
            if current:
                save_private(HOME / ('node_before_repair-' + uuid.uuid4().hex + '.json'), current)
            pending = new_pending(origin, pin, info['cluster_id'], node_name, profile, code,
                                  target=target, cluster=cluster, controllers=controllers)
            save_private(pending_path, pending)
        reply = enrollment_request('POST', '/api/v1/join', pending['payload'])
        state = accepted_identity(pending, reply)
        if controllers:
            state.update(controllers=controllers, cluster_epoch=current['cluster_epoch'])
        if repair and current:
            replace_private(node_path, state)
        else:
            save_private(node_path, state)
        replace_private(HOME / 'agent_state.json', {'credential_status': 'active', 'checked_at': int(time.time())})
        pending_path.unlink()
        print('Node enrolled/re-paired:', reply['node_id'], '(private token saved; not displayed)')
        print('Start: python3 -m asc.cli agent-run. Topology only; no NAS/Raft.')


def node_join(args):
    _enroll(args)


def node_repair(args):
    _enroll(args, repair=True)


def agent_once(cfg, sd_test=False, storage_engine=None):
    profile = inspect(sd_write=sd_test)
    if storage_engine is not None and profile.get('protected'):
        raise ValueError('M51 PRODUCTION PROTECTED: storage capability probe refused')
    if storage_engine is not None:
        profile['storage'] = storage_engine.capabilities()
    try:
        if 'controllers' in cfg:
            from .failover.discovery import Discovery
            snap = Discovery(cfg['cluster_id'], cfg['controllers'], cfg['token']).request(
                'POST', '/api/v1/heartbeat', {'node_id': cfg['node_id'], 'profile': profile})
        else:
            snap = request_json(cfg['controller'], cfg['pin'], 'POST', '/api/v1/heartbeat',
                                {'node_id': cfg['node_id'], 'profile': profile}, token=cfg['token'])
    except ClientError as exc:
        if exc.status in (401, 403):
            replace_private(HOME / 'agent_state.json',
                            {'credential_status': 'repair-required', 'checked_at': int(time.time())})
        raise
    if snap['cluster_id'] != cfg['cluster_id']:
        raise ClientError('Cluster ID mismatch; refusing snapshot')
    if snap.get('catalog_metadata_enabled'):
        try:
            from .catalog.metadata import synchronize
            status=synchronize(HOME,cfg)
            replace_private(HOME / 'metadata_sync_state.json',{'status':'verified','revision':status['revision'],'checked_at':int(time.time())})
        except (ClientError,OSError,ValueError,StorageError,sqlite3.Error):
            replace_private(HOME / 'metadata_sync_state.json',{'status':'unavailable','checked_at':int(time.time())})
    replace_private(HOME / 'topology_snapshot.json', snap)
    replace_private(HOME / 'agent_state.json', {'credential_status': 'active', 'checked_at': int(time.time())})
    return snap


def agent_run(args):
    if os.name == 'nt' and (HOME / 'storage.json').exists() and not inspect().get('protected'):
        pass  # Explicit local Windows storage configuration; never an Android guard bypass.
    else:
        _must_not_protected('agent runtime')
    ensure_private_home(HOME)
    if not 5 <= args.interval <= 3600:
        raise ValueError('heartbeat interval must be 5..3600 seconds')
    with foreground_lock(HOME, 'agent'):
        if (HOME / 'enrollment_pending.json').exists():
            raise ValueError('pending enrollment/re-pair; complete it before starting agent')
        cfg = read_private('node.json')
        with ExitStack() as stack:
            runtime = None
            if (HOME / 'storage.json').exists():
                from .storage.runtime import StorageRuntime
                runtime = stack.enter_context(StorageRuntime(HOME, cfg))
            print('ASC Agent foreground; Ctrl+C to stop.', flush=True)
            while True:
                try:
                    snapshot = agent_once(cfg, args.sd_test, runtime.engine if runtime else None)
                    print('Heartbeat OK, nodes:', len(snapshot['nodes']), flush=True)
                except ClientError as exc:
                    if exc.status in (401, 403):
                        raise ValueError('Credential rejected (revoked/rotated/invalid). Re-pair required; agent stopped, identity retained.') from None
                    if args.once:
                        raise
                    print('Heartbeat failed; preserving last topology:', str(exc), flush=True)
                except (OSError, ValueError):
                    if args.once:
                        raise
                    print('Heartbeat unavailable; preserving last topology. Check LAN/controller.', flush=True)
                if args.once:
                    return
                time.sleep(args.interval)


def local_status(_args):
    result = {'home': str(HOME), 'profile': inspect(),
              'foreground': {role: running(HOME, role) for role in ('controller', 'agent')},
              'credential_status': 'unknown'}
    if (HOME / 'controller.json').exists():
        result['mode'] = 'local-controller (development, not Raft)'
        path = HOME / 'registry.sqlite3'
        if path.exists():
            with Registry(path).connect() as db:
                version = db.execute('PRAGMA user_version').fetchone()[0]
            if version == SCHEMA_VERSION:
                result['topology'] = Registry(path).snapshot()
            else:
                result['registry_schema'] = version
                result['migration'] = 'back up private state; controller-run migrates to schema 4'
    elif (HOME / 'node.json').exists():
        result['mode'] = 'enrolled-node'
        cfg = read_private('node.json')
        result['node_id'] = cfg['node_id']
        result['cluster_id'] = cfg['cluster_id']
        if (HOME / 'agent_state.json').exists():
            state = _read_path(HOME / 'agent_state.json')
            result['credential_status'] = state.get('credential_status', 'unknown')
            result['checked_at'] = state.get('checked_at')
        if (HOME / 'topology_snapshot.json').exists():
            result['last_saved_topology'] = _read_path(HOME / 'topology_snapshot.json')
            result['snapshot_is_cached'] = True
    else:
        result['mode'] = 'not-enrolled'
    result['pending_enrollment'] = (HOME / 'enrollment_pending.json').exists()
    _show(result)


def main():
    p = argparse.ArgumentParser(description=f'ASC {__version__} / single-writer storage or opt-in metadata consensus')
    sub = p.add_subparsers(dest='action', required=True)
    a = sub.add_parser('inspect', help='Read-only unless --sd-write explicitly requested')
    a.add_argument('--sd-write', action='store_true')
    a = sub.add_parser('controller-init')
    a.add_argument('--name', default='ASC-Primary')
    a.add_argument('--port', type=int, default=8443)
    a=sub.add_parser('controller-run')
    a.add_argument('--catalog-rate',type=int,default=4*1024**2)
    a.add_argument('--job-timeout',type=int,default=300)
    a.add_argument('--consensus-config', help='Private Go config; opt-in metadata-only consensus, loopback API')
    a = sub.add_parser('controller-pair')
    a.add_argument('--ttl', type=int, default=600)
    a.add_argument('--node-id', help='Target existing node for explicit rotation/re-pair')
    sub.add_parser('controller-nodes')
    for command in ('controller-node', 'controller-rename', 'controller-revoke'):
        a = sub.add_parser(command)
        a.add_argument('node_id')
        if command == 'controller-rename':
            a.add_argument('name')
    for command in ('node-join', 'node-repair'):
        a = sub.add_parser(command)
        a.add_argument('--controller', help='https://LAN_IP:8443')
        a.add_argument('--pin', help='SHA256 certificate fingerprint')
        a.add_argument('--name')
        a.add_argument('--sd-test', action='store_true')
        a.set_defaults(node_id=None, cluster_id=None)
        a.add_argument('--expected-cluster-id', help='Optional trusted owner cluster binding; preserves pending format')
        a.add_argument('--new-code', action='store_true', help='Explicitly replace a pending grant; preserve recovery state')
        if command == 'node-repair':
            a.add_argument('--node-id', help='Required only when private identity was lost')
            a.add_argument('--cluster-id', help='Required only when private identity was lost')
    a = sub.add_parser('agent-run')
    a.add_argument('--interval', type=int, default=30)
    a.add_argument('--once', action='store_true')
    a.add_argument('--sd-test', action='store_true')
    sub.add_parser('status')
    handlers = {'controller-init': controller_init, 'controller-run': controller_run,
                'controller-pair': controller_pair, 'controller-nodes': controller_nodes,
                'controller-node': controller_node, 'controller-rename': controller_rename,
                'controller-revoke': controller_revoke, 'node-join': node_join,
                'node-repair': node_repair, 'agent-run': agent_run, 'status': local_status}
    from .storage.cli import register
    register(sub, handlers, sys.modules[__name__])
    from .catalog.cli import register as register_catalog
    register_catalog(sub,handlers,sys.modules[__name__])
    args = p.parse_args()
    try:
        if args.action == 'inspect':
            _show(inspect(args.sd_write))
        else:
            handlers[args.action](args)
    except KeyboardInterrupt:
        print('ASC foreground stopped; identity retained.')
    except (OSError, ClientError, ValueError, KeyError, sqlite3.Error, StorageError) as exc:
        # Never print arbitrary OS/server exception text that could contain private input.
        message = str(exc) if isinstance(exc, (ClientError, ValueError, StorageError)) and not isinstance(exc, json.JSONDecodeError) else 'local state/dependency unavailable; preserve private files and check troubleshooting'
        print(f'ASC error: {message}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
