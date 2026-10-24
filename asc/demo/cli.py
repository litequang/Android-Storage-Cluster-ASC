"""ASC Demo entry point: explicit single-writer LAN commands, no Raft/GC fallback."""
import argparse
import json
import os
from pathlib import Path
import sqlite3
import sys
import time
from .installer import install, preflight, guard
from .state import initialize, inspect_state, lan_origin, lan_host, read_json
from ..identity import ensure_private_home
from .locks import private_lock as foreground_lock
from ..client import ClientError
from ..storage.errors import StorageError


def execute(args):
    from .lan import core_call, owner, lifecycle_request, ControllerRuntime, run_node, upload
    root = args.state.expanduser().absolute()
    guard()
    from . import upgrade
    prefix = Path(os.environ.get('ASC_DEMO_PREFIX', str(Path.home() / '.local/share/asc-demo')))
    prefix = getattr(args, 'prefix', prefix).expanduser().absolute()
    if args.command == 'init':
        if os.environ.get('ASC_DEMO_PREFIX'):
            bound = prefix / 'state-binding.json'
            if bound.exists() and read_json(bound)['state'] != str(root):
                raise ValueError('prefix belongs to another state; preserve identity')
            journal = prefix / 'upgrade-journal.json'
            if journal.exists() and upgrade.read_journal(prefix)['status'] == 'PREPARED':
                raise ValueError('explicit upgrade recovery required')
        initialize(root, args.role, args.host, args.port)
        with foreground_lock(root, 'demo-operation'):
            inspect_state(root)
            if args.role == 'controller':
                core_call(root / 'controller', ['controller-init', '--name', args.name, '--port', str(args.port)])
            if os.environ.get('ASC_DEMO_PREFIX'):
                upgrade.binding(prefix, root, create=True)
        return {'initialized': True, 'mode': 'single-writer-demo', 'private_state_retained': True}
    inspect_state(root)
    if args.command == 'recover-upgrade':
        return upgrade.recover(root, prefix)
    if os.environ.get('ASC_DEMO_PREFIX'):
        upgrade.startup_check(prefix, root)
    if args.command == 'diagnose':
        return upgrade.diagnose(root)
    if args.command == 'stage':
        return upgrade.stage(args.source, prefix)
    if args.command == 'upgrade-preflight':
        release = upgrade.verify(upgrade.release_path(prefix, args.release_id))
        return upgrade.compatibility(release, root)
    if args.command == 'backup':
        with upgrade.stopped(root):
            return upgrade.backup_locked(root, args.destination, prefix)
    if args.command == 'verify-backup':
        report = upgrade.verify_backup(args.destination)
        return {'verified': True, 'backup_sha256': report['backup_sha256']}
    if args.command in ('upgrade', 'rollback'):
        return upgrade.activate(root, prefix, args.release_id, args.backup, args.command)
    if args.command == 'dashboard-init':
        from .dashboard.tls import setup
        return setup(root, args.port, args.max_upload)
    if args.command == 'dashboard-trust':
        from .dashboard.tls import export_ca
        return export_ca(root, args.out)
    if args.command == 'run-controller':
        with ControllerRuntime(root, dashboard=args.dashboard):
            print('Demo Controller foreground; Ctrl+C stops. No automatic failover.', flush=True)
            while True:
                time.sleep(1)
    if args.command == 'run-node':
        # Re-exec only to bind Core import-time HOME; never change a running module global.
        if os.environ.get('ASC_HOME') != str(root / 'node'):
            env = dict(os.environ, ASC_HOME=str(root / 'node'), PYTHONDONTWRITEBYTECODE='1')
            os.chdir(Path(__file__).resolve().parents[2])
            os.execve(sys.executable, [sys.executable, '-B', '-m', 'asc.demo.cli', *sys.argv[1:]], env)
        run_node(root, args.interval, args.once)
        return {'stopped': True}
    if args.command == 'join':
        lan_origin(args.controller)
        with foreground_lock(root, 'demo-operation'):
            if os.environ.get('ASC_DEMO_PREFIX'):
                upgrade.startup_check(prefix, root)
            prior = root / 'node/node.json'
            if prior.exists():
                cfg = read_json(prior)
                if (cfg['controller'], cfg['pin']) != (args.controller, args.pin):
                    raise ValueError('existing pinned enrollment differs; preserve identity')
            core_call(root / 'node', ['node-join', '--controller', args.controller, '--pin', args.pin, '--name', args.name])
        return {'enrolled': True, 'identity_preserved': True}
    if args.command == 'storage-init':
        from ..storage.runtime import setup, load_config
        from ..storage.engine import StorageEngine
        home = root / 'node'
        with foreground_lock(root, 'demo-operation'), foreground_lock(home, 'agent'):
            if os.environ.get('ASC_DEMO_PREFIX'):
                upgrade.startup_check(prefix, root)
            cfg = read_json(home / 'node.json')
            lan_host(args.host)
            if (root / 'dashboard/dashboard.json').exists() and read_json(root / 'dashboard/dashboard.json')['port'] == args.port:
                raise ValueError('Dashboard/storage port conflict')
            volume_root = (args.root or home / 'data').expanduser().absolute()
            # Internal means private dedicated Demo data only; microSD requires Core app-folder approval.
            if args.kind == 'internal' and volume_root != home / 'data':
                raise ValueError('internal Demo data must be its dedicated private node/data')
            if (home / 'storage.json').exists():
                settings = load_config(home)
                if (settings['host'], settings['port'], settings['max_upload']) != (args.host, args.port, args.max_upload):
                    raise ValueError('existing storage configuration preserved')
                with StorageEngine(home / 'storage', cfg['node_id'], settings['max_upload'], settings['rate']) as engine:
                    record = engine.volumes.register(volume_root, args.kind, args.quota, args.reserve)
                    from ..identity import fingerprint_from_pem
                    return {'volume_id': record['volume_id'], 'pin': fingerprint_from_pem(home / 'storage.crt'),
                            'capabilities': engine.capabilities(), 'identity_preserved': True}
            return setup(home, cfg, volume_root, args.kind, args.quota, args.reserve, args.port, args.host, args.max_upload)
    client = owner(root)
    if args.command == 'dashboard-code':
        from ..client import request_json
        return request_json(client.origin, client.pin, 'POST', '/demo/v1/dashboard/code', {}, client.token)
    if args.command == 'pair':
        reply = lifecycle_request(client, 'POST', 'admin/pair', {'ttl': 600})
        return {'code': reply['code'], 'pin': client.pin, 'origin': client.origin,
                'warning': 'private one-time code; enter interactively on the joining node'}
    if args.command == 'approve':
        lan_origin(args.origin)
        return client.request('POST', 'nodes/register', {'node_id': args.node_id, 'origin': args.origin,
               'pin': args.pin, 'device_id': args.domain, 'volume_ids': [args.volume_id]})
    if args.command == 'nodes':
        return lifecycle_request(client, 'GET', 'nodes')
    if args.command == 'files':
        return client.request('GET', 'files?offset=' + str(args.offset))
    if args.command == 'replicas':
        client.request('POST', 'reconcile', {})
        return client.request('GET', 'files/' + args.file_id)
    if args.command == 'upload':
        return upload(client, args.source, args.logical_path, args.key, args.wait)
    if args.command == 'download':
        with Path(args.output).open('xb+') as stream:
            result = client.download(args.file_id, stream)
            stream.flush()
            os.fsync(stream.fileno())
        return result
    raise ValueError('unsupported Demo command')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, default=Path.home() / '.asc-demo', help='dedicated marked private Demo state')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('preflight')
    setup = commands.add_parser('install')
    setup.add_argument('--prefix', type=Path, default=Path.home() / '.local/share/asc-demo')
    setup.add_argument('--dry-run', action='store_true')
    init = commands.add_parser('init')
    init.add_argument('--role', choices=['controller', 'node'], required=True)
    init.add_argument('--host', required=True)
    init.add_argument('--port', type=int, default=8443)
    init.add_argument('--name', default='ASC-Demo-Controller')
    controller = commands.add_parser('run-controller')
    controller.add_argument('--dashboard', action='store_true', help='explicit optional browser HTTPS listener')
    browser = commands.add_parser('dashboard-init')
    browser.add_argument('--port', type=int, default=8444)
    browser.add_argument('--max-upload', type=int, default=32 * 1024**2)
    commands.add_parser('dashboard-code')
    trust = commands.add_parser('dashboard-trust')
    trust.add_argument('--out', type=Path, required=True)
    node = commands.add_parser('run-node')
    node.add_argument('--interval', type=int, default=10)
    node.add_argument('--once', action='store_true')
    join = commands.add_parser('join')
    join.add_argument('--controller', required=True)
    join.add_argument('--pin', required=True)
    join.add_argument('--name', required=True)
    storage = commands.add_parser('storage-init')
    storage.add_argument('--root', type=Path)
    storage.add_argument('--kind', choices=['internal', 'termux_sd'], default='internal')
    storage.add_argument('--host', required=True)
    storage.add_argument('--port', type=int, default=9443)
    storage.add_argument('--quota', type=int, default=64 * 1024**2)
    storage.add_argument('--reserve', type=int, default=64 * 1024**2)
    storage.add_argument('--max-upload', type=int, default=64 * 1024**2)
    commands.add_parser('pair')
    approval = commands.add_parser('approve')
    for field in ('node-id', 'volume-id', 'origin', 'pin', 'domain'):
        approval.add_argument('--' + field, required=True)
    commands.add_parser('nodes')
    files = commands.add_parser('files')
    files.add_argument('--offset', type=int, default=0)
    replicas = commands.add_parser('replicas')
    replicas.add_argument('file_id')
    up = commands.add_parser('upload')
    up.add_argument('source', type=Path)
    up.add_argument('logical_path')
    up.add_argument('--key', required=True)
    up.add_argument('--wait', type=int, default=120)
    down = commands.add_parser('download')
    down.add_argument('file_id')
    down.add_argument('output', type=Path)
    commands.add_parser('diagnose')
    commands.add_parser('recover-upgrade')
    for command in ('stage', 'upgrade-preflight', 'backup', 'verify-backup', 'upgrade', 'rollback'):
        item = commands.add_parser(command)
        item.add_argument('--prefix', type=Path, default=Path(os.environ.get('ASC_DEMO_PREFIX', str(Path.home() / '.local/share/asc-demo'))))
        if command == 'stage':
            item.add_argument('source', type=Path)
        elif command in ('backup', 'verify-backup'):
            item.add_argument('destination', type=Path)
        else:
            item.add_argument('release_id')
        if command in ('upgrade', 'rollback'):
            item.add_argument('--backup', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'preflight':
            result = preflight()
            print(json.dumps(result, indent=2))
            return 0 if result['allowed'] else 3
        if args.command == 'install':
            result = install(Path(__file__).resolve().parents[2], args.prefix, args.dry_run)
        else:
            result = execute(args)
        print(json.dumps(result, indent=2))
        return 4 if isinstance(result, dict) and result.get('protected') is False else 0
    except KeyboardInterrupt:
        print('ASC Demo stopped; identities and data retained.')
        return 0
    except (ValueError, OSError, KeyError, TypeError, sqlite3.Error, ClientError, StorageError):
        print('ASC Demo refused: device/dependency, TLS, state, path or network validation failed. '
              'Preserve state; see DEMO-QUICKSTART.', file=sys.stderr)
        return 3


if __name__ == '__main__':
    sys.exit(main())
