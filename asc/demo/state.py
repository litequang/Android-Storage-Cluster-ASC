"""Demo format 1 and read-only exact-schema checks before using Core state."""
import ipaddress
import json
import sqlite3
import uuid
from pathlib import Path
from urllib.parse import urlsplit
from ..identity import ensure_private_home, save_private
from ..storage.volumes import no_links
from .installer import private_path
from .locks import validate_lock

from . import STATE_FORMATS

FORMATS = STATE_FORMATS


def lan_host(host):
    ip = ipaddress.IPv4Address(host)
    allowed = ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16', '127.0.0.0/8')
    if not any(ip in ipaddress.IPv4Network(n) for n in allowed):
        raise ValueError('explicit RFC1918/loopback IPv4 required')
    return str(ip)


def lan_origin(origin):
    url = urlsplit(origin)
    if (url.scheme != 'https' or not url.hostname or url.username or url.password
            or url.path or url.query or url.fragment or not url.port or not 1024 <= url.port <= 65535):
        raise ValueError('explicit pinned https LAN IPv4 origin required')
    lan_host(url.hostname)
    return origin


def read_json(path):
    no_links(path)
    if path.stat().st_size > 1024 * 1024:
        raise ValueError('private configuration too large')
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise ValueError('invalid configuration')
    return value


def read_db(path, version, inspect=None):
    no_links(path)
    db = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=5)
    try:
        db.row_factory = sqlite3.Row
        if db.execute('PRAGMA user_version').fetchone()[0] != version:
            raise ValueError('unsupported schema; matching release or tested migration required')
        if db.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
            raise ValueError('database integrity check failed')
        return inspect(db) if inspect else None
    finally:
        db.close()


def inspect_state(root):
    root = private_path(root)
    marker = read_json(root / 'demo.json')
    if (set(marker) != {'format', 'track', 'mode', 'role', 'installation_id', 'state_formats', 'host', 'port'}
            or type(marker['format']) is not int or marker['format'] != 1
            or marker['track'] != 'android-demo-alpha' or marker['mode'] != 'single-writer-demo'
            or marker['role'] not in ('controller', 'node') or marker['state_formats'] != FORMATS
            or any(type(v) is not int for v in marker['state_formats'].values())
            or type(marker['port']) is not int or not 1024 <= marker['port'] <= 65535):
        raise ValueError('unsupported Demo state contract')
    uuid.UUID(marker['installation_id'])
    lan_host(marker['host'])
    for base, roles in ((root, ('demo-operation',)), (root / 'controller', ('controller', 'catalog-worker')),
                        (root / 'node', ('agent',)), (root / 'node/storage', ('storage-engine',))):
        for role in roles:
            validate_lock(base / (role + '.lock'))
    for name in ('controller', 'node'):
        home = root / name
        no_links(home)
        if not home.exists():
            continue
        if any((home / p).exists() for p in ('raft-state', 'consensus', 'bootstrap.json', 'cluster-client.json',
                                            'runtime.sqlite3', 'consensus.json', 'failover.json')):
            raise ValueError('Raft/consensus state cannot be adopted')
        if name == 'node' and not (home / 'node.json').exists() and any((home / p).exists() for p in ('agent_state.json', 'topology_snapshot.json', 'storage.json')):
            raise ValueError('node identity missing; restore private backup, never re-enroll blindly')
        for config in ('controller.json', 'node.json', 'storage.json', 'enrollment_pending.json'):
            path = home / config
            if not path.exists():
                continue
            cfg = read_json(path)
            if (type(cfg.get('config_version')) is not int or cfg['config_version'] != 1
                    or any(k in cfg for k in ('controllers', 'cluster_epoch', 'consensus_mode'))):
                raise ValueError('unsupported or distributed Core configuration')
            if config == 'node.json':
                if name != 'node':
                    raise ValueError('mixed Controller/node identity')
                lan_origin(cfg['controller'])
            if config == 'controller.json' and (name != 'controller' or marker['role'] != 'controller'):
                raise ValueError('unexpected Controller identity')
            if config == 'storage.json':
                lan_host(cfg['host'])
                if not (home / 'storage/manifest.sqlite3').is_file():
                    raise ValueError('storage manifest missing; never recreate')
        registry = home / 'registry.sqlite3'
        if registry.exists():
            if name != 'controller' or not (home / 'controller.json').is_file():
                raise ValueError('partial/misplaced registry')
            cfg = read_json(home / 'controller.json')
            def registry_check(db):
                if db.execute("SELECT 1 FROM settings WHERE key NOT IN ('cluster_id','catalog_inventory_cursor')").fetchone():
                    raise ValueError('Core extension/consensus state is outside Demo contract')
                from ..catalog.schema import validate_existing
                validate_existing(db)
                if db.execute("SELECT value FROM settings WHERE key='cluster_id'").fetchone()[0] != cfg['cluster_id']:
                    raise ValueError('cluster identity mismatch')
            read_db(registry, 4, registry_check)
        elif (home / 'controller.json').exists():
            raise ValueError('registry missing; restore instead of recreating')
        manifest = home / 'storage/manifest.sqlite3'
        if manifest.exists():
            node = read_json(home / 'node.json')
            def node_check(db):
                if db.execute("SELECT value FROM settings WHERE key='node_id'").fetchone()[0] != node['node_id']:
                    raise ValueError('manifest node identity mismatch')
            read_db(manifest, 1, node_check)
        cache = home / 'catalog-metadata.sqlite3'
        if cache.exists():
            read_db(cache, 1)
    return marker


def initialize(root, role, host, port):
    root = private_path(root)
    host = lan_host(host)
    if role not in ('controller', 'node') or type(port) is not int or not 1024 <= port <= 65535:
        raise ValueError('invalid Demo setup')
    if root.exists():
        if not (root / 'demo.json').exists():
            raise ValueError('unmarked existing state; no implicit migration')
        marker = inspect_state(root)
        if (marker['role'], marker['host'], marker['port']) != (role, host, port):
            raise ValueError('existing Demo identity/bind retained; explicit migration required')
        return marker
    ensure_private_home(root)
    marker = {'format': 1, 'track': 'android-demo-alpha', 'mode': 'single-writer-demo', 'role': role,
              'installation_id': str(uuid.uuid4()), 'state_formats': FORMATS, 'host': host, 'port': port}
    save_private(root / 'demo.json', marker)
    return marker
