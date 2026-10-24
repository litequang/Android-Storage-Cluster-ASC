"""Explicit stopped-state runtime upgrade and Windows development entrypoint."""
import argparse
from contextlib import ExitStack
import base64
import json
import os
from pathlib import Path
import ssl
import time
import threading

from .runtime import Runtime
from .service import Service, RuntimeHandler
from . import state
from ..catalog.common import CatalogError, canonical, digest
from ..consensus.adapter import Adapter
from ..consensus.client import Client
from ..probe import inspect
from ..runtime import foreground_lock
from ..server import Server
from ..storage.runtime import StorageRuntime, validate_host
from ..store import Registry
from ..client import ClientError


def upgrade(registry, config, expected_sha):
    """Explicit conversion of a stopped, attached primary; never reset/bootstrap.

    The operator supplies the exact current committed metadata SHA reviewed for
    this upgrade. Private original SQL and all object volumes remain untouched.
    """
    reg = Registry(registry)
    if not reg.consensus_enabled():
        raise CatalogError('attached_registry_required', 409)
    client = Client.from_config(config)
    request_id = 'runtime-upgrade-'+expected_sha
    intent = digest({'upgrade': 2, 'expected_sha256': expected_sha})
    committed = client.state(strong=True)['state']
    original = committed['receipts'].get(request_id)
    if original:
        if original['intent_sha256'] != intent or original.get('error'):
            raise CatalogError('upgrade_precondition_conflict', 409)
        state.validate(json.loads(base64.b64decode(committed['document'], validate=True)))
        return original
    info = client.status()
    if info['role'] != 'Leader':
        raise CatalogError('controller_not_ready', 503)
    adapter = Adapter(reg, client).activate()
    view = adapter.sync(strong=True)
    if view['state']['document_sha256'] != expected_sha:
        raise CatalogError('upgrade_precondition_conflict', 409)
    with reg.connect() as db:
        doc = state.export(db, view['document']['revision']+1,
                           {'node_id': info['node_id'], 'term': int(info['term'])})
    # Existing grants are not portable authority. Keep original frozen rows for
    # recovery evidence; only the new runtime document invalidates them.
    doc = state.takeover({**doc, 'revision': doc['revision']-1}, info['node_id'], int(info['term']))
    state.validate(doc)
    return client.submit({'schema': 1, 'cluster_id': doc['cluster_id'], 'epoch': doc['epoch'],
        'request_id': request_id, 'intent_sha256': intent,
        'expected_sha256': expected_sha, 'authority_term': int(info['term']),
        'document': base64.b64encode(canonical(doc)).decode()})


def run(path):
    profile = inspect()
    if os.name != 'nt' or profile.get('protected') is True:
        raise ValueError('Phase 2B runtime is Windows development only; protected/Android refused')
    raw = Path(path).read_bytes()
    if len(raw) > 65536:
        raise ValueError('runtime config limit')
    cfg = json.loads(raw)
    if set(cfg) != {'schema', 'home', 'consensus_config', 'host', 'port'} or cfg['schema'] != 1:
        raise ValueError('unsupported runtime config')
    home = Path(cfg['home'])
    if not home.is_absolute() or any((p/'.git').exists() for p in [home, *home.parents]):
        raise ValueError('private HOME must be outside source')
    validate_host(cfg['host'])
    if type(cfg['port']) is not int or not 1024 <= cfg['port'] <= 65535:
        raise ValueError('invalid runtime endpoint')
    owner = json.loads((home/'controller.json').read_bytes())
    with ExitStack() as stack:
        stack.enter_context(foreground_lock(home, 'controller'))
        runtime = Runtime(cfg['consensus_config'], home/'runtime.sqlite3')
        if owner['cluster_id'] != runtime.cluster:
            raise ValueError('runtime cluster identity mismatch')
        stack.callback(runtime.close)
        runtime.start()
        deadline = time.monotonic()+30
        while True:
            try:
                view = runtime.view()  # Explicit upgrade required; schema-1 cannot enable IO.
                break
            except CatalogError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(0.25)
        go_config = json.loads(Path(cfg['consensus_config']).read_bytes())
        state.verify_attachment(Registry(home/'registry.sqlite3'), view, [p['id'] for p in go_config['peers']])
        service = Service(runtime).start()
        stack.callback(service.close)
        server = Server((cfg['host'], cfg['port']), runtime.registry, owner['admin_token'], RuntimeHandler, service)
        stack.callback(server.server_close)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(home/'server.crt', home/'server.key')
        server.tls_context = context
        if (home/'storage.json').exists():
            node = json.loads((home/'node.json').read_bytes())
            if node['cluster_id'] != runtime.cluster or 'controllers' not in node:
                raise ValueError('runtime Agent requires matching pinned bootstrap configuration')
            storage = stack.enter_context(StorageRuntime(home, node))
            from .discovery import Discovery
            discovery = Discovery(runtime.cluster, node['controllers'], node['token'])
            agent_stop = threading.Event()
            def heartbeat():
                while not agent_stop.is_set():
                    try:
                        discovery.request('POST', '/api/v1/heartbeat',
                            {'node_id': node['node_id'], 'profile': {**inspect(), 'storage': storage.engine.capabilities()}})
                    except (ValueError, CatalogError, ClientError, OSError):
                        pass
                    agent_stop.wait(10)
            thread = threading.Thread(target=heartbeat, daemon=True)
            thread.start()
            stack.callback(lambda: (agent_stop.set(), thread.join(timeout=60)))
        server.serve_forever(poll_interval=0.25)


def main():
    parser = argparse.ArgumentParser(description='ASC Phase 2B Windows development runtime')
    commands = parser.add_subparsers(dest='command', required=True)
    u = commands.add_parser('upgrade', help='Stopped development Controllers only; preserve private backups')
    u.add_argument('--registry', required=True)
    u.add_argument('--consensus-config', required=True)
    u.add_argument('--expected-sha256', required=True)
    r = commands.add_parser('run')
    r.add_argument('--config', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'upgrade':
            receipt = upgrade(args.registry, args.consensus_config, args.expected_sha256)
            print('Runtime projection committed at index', receipt['index'])
        else:
            run(args.config)
    except (ValueError, CatalogError, OSError):
        parser.exit(1, 'ASC runtime refused; preserve state and consult PHASE2B-ACCEPTANCE.md\n')


if __name__ == '__main__':
    main()
