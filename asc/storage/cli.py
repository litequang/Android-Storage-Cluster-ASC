"""CLI routing for explicit node storage setup, inspection and owner transfer."""
import hashlib
import json
import os
from pathlib import Path
from .client import StorageClient
from .engine import StorageEngine
from .errors import StorageError
from .runtime import load_config, setup


def register(parser, handlers, cli):
    def guard():
        # Windows local development is explicit; Android keeps the existing fail-closed guard.
        profile = cli.inspect()
        if profile.get('protected') or os.name != 'nt':
            cli._must_not_protected('storage administration')

    def node():
        guard()
        if (cli.HOME / 'enrollment_pending.json').exists():
            raise ValueError('complete pending enrollment before storage setup')
        return cli.read_private('node.json')

    def init(args):
        cfg = node()
        cli._show(setup(cli.HOME, cfg, args.root or cli.HOME / 'storage-data',
                        args.kind, args.quota, args.reserve, args.port, args.host,
                        args.max_upload, args.rate))

    def inspect_storage(args):
        cfg = node()
        settings = load_config(cli.HOME)
        with StorageEngine(cli.HOME / 'storage', cfg['node_id'], settings['max_upload'], settings['rate']) as engine:
            if args.action == 'storage-add-volume':
                result = engine.volumes.register(args.root, args.kind, args.quota, args.reserve)
                cli._show({'volume_id': result['volume_id']})
            elif args.action == 'storage-cleanup':
                cli._show({'cleanup': engine.cleanup(args.older_than, dry_run=not args.apply)})
            else:
                cli._show({'capabilities': engine.capabilities(),
                           'candidates': engine.volumes.discover(cli.HOME), 'inventory': engine.inventory()})

    def grant(args):
        reply = cli._admin_request('POST', '/api/v1/admin/storage-grant',
                                  {'node_id': args.node_id, 'volume_id': args.volume_id,
                                   'operations': args.operations.split(','), 'ttl': args.ttl})
        path = Path(args.out).absolute()
        cli.ensure_private_home(path.parent)
        cli.save_private(path, reply)
        cli._show({'saved': True, 'expires_at': reply['expires_at']})

    def transfer(args):
        guard()
        cfg = json.loads(Path(args.grant_file).read_text(encoding='utf-8'))
        client = StorageClient(args.origin, args.pin, cfg['grant'], cfg['volume_id'])
        if args.action == 'storage-upload':
            # Reopen the source only once; detect mutation by the node's expected hash/size.
            with Path(args.source).open('rb') as stream:
                digest, size = hashlib.sha256(), 0
                while chunk := stream.read(65536):
                    digest.update(chunk); size += len(chunk)
                row = client.initiate(args.key, args.logical_path, size, digest.hexdigest())
                if row['state'] != 'COMMITTED':
                    stream.seek(0); client.upload(row['session_id'], stream, size)
                cli._show(client.commit(row['session_id']))
        else:
            row = client.json('GET', 'files/' + args.file_id)['file']
            # Failed/interrupted output is retained for inspection and never replaces another file.
            with Path(args.output).open('xb') as output:
                result = client.download(args.file_id, output, row['size'], row['sha256'])
                output.flush(); os.fsync(output.fileno())
            cli._show(result)

    for command in ('storage-init', 'storage-add-volume'):
        a = parser.add_parser(command)
        a.add_argument('--root', type=Path, required=command == 'storage-add-volume')
        a.add_argument('--kind', choices=['directory', 'internal', 'termux_sd'], default='directory')
        a.add_argument('--quota', type=int, default=64 * 1024**2)
        a.add_argument('--reserve', type=int, default=64 * 1024**2)
        if command == 'storage-init':
            a.add_argument('--host', default='127.0.0.1')
            a.add_argument('--port', type=int, default=9443)
            a.add_argument('--max-upload', type=int, default=64 * 1024**2)
            a.add_argument('--rate', type=int, default=8 * 1024**2)
        handlers[command] = init if command == 'storage-init' else inspect_storage
    parser.add_parser('storage-status')
    a = parser.add_parser('storage-cleanup')
    a.add_argument('--older-than', type=int, default=86400)
    a.add_argument('--apply', action='store_true')
    handlers.update({'storage-status': inspect_storage, 'storage-cleanup': inspect_storage})
    a = parser.add_parser('controller-storage-grant')
    a.add_argument('node_id'); a.add_argument('volume_id')
    a.add_argument('--operations', default='read,list,write,verify')
    a.add_argument('--ttl', type=int, default=300)
    a.add_argument('--out', required=True)
    handlers['controller-storage-grant'] = grant
    for command in ('storage-upload', 'storage-download'):
        a = parser.add_parser(command)
        a.add_argument('--origin', required=True); a.add_argument('--pin', required=True)
        a.add_argument('--grant-file', required=True)
        if command == 'storage-upload':
            a.add_argument('source'); a.add_argument('logical_path'); a.add_argument('--key', required=True)
        else:
            a.add_argument('file_id'); a.add_argument('output')
        handlers[command] = transfer
