"""Fixed Demo adapter: existing identity, approved volumes and Quick Join worker."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
from ..catalog.common import canonical, identifier
from ..client import request_json, ClientError
from ..demo.installer import guard, private_path
from ..demo.state import inspect_state, read_json, read_db, reject_recovery
from ..demo.locks import validate_lock
from ..identity import fingerprint_from_pem
from ..runtime import running
from ..storage.volumes import LocalVolume
from ..storage.errors import StorageError
from .contract import Refused


class Engine:
    def __init__(self, root, installation_id, prefix=None, state_identity=None):
        self.root = Path(root); self.installation_id = installation_id; self.prefix = prefix
        self.state_identity = state_identity
        self.check()

    def check(self):
        try: guard()
        except ValueError: raise Refused('device_or_dependency_denied') from None
        try: reject_recovery(self.root)
        except ValueError: raise Refused('recovery_read_only') from None
        if not (self.root/'demo.json').exists(): raise Refused('setup_required')
        info = self.root.lstat()
        if self.state_identity is not None and [info.st_dev,info.st_ino] != self.state_identity:
            raise Refused('installation_mismatch')
        marker = inspect_state(self.root)
        if marker['installation_id'] != self.installation_id:
            raise Refused('installation_mismatch')
        if self.prefix:
            from ..demo.upgrade import startup_check
            startup_check(self.prefix, self.root)
            from ..demo.package import verify
            source = Path(__file__).resolve().parents[2]
            selected = read_json(Path(self.prefix)/'install.json')['release_id']
            if source != Path(self.prefix)/'releases'/selected or verify(source)['release_id'] != selected:
                raise Refused('source_selection_mismatch')
        return marker

    def status(self):
        marker = self.check(); home = self.root / 'node'
        node = read_json(home / 'node.json') if (home / 'node.json').exists() else None
        pending = (home / 'enrollment_pending.json').exists()
        def observed(base, role):
            validate_lock(base / (role + '.lock'))
            return running(base, role)
        processes = {'node_lock_held': observed(home, 'agent'),
                     'controller_lock_held': observed(self.root / 'controller', 'controller')}
        volumes = []
        manifest = home / 'storage/manifest.sqlite3'
        if manifest.exists():
            def rows(db):
                db.row_factory = sqlite3.Row
                return [dict(r) for r in db.execute('SELECT * FROM volumes')]
            records = read_db(manifest, 1, rows)
            for record in records:
                volume = LocalVolume(record)
                row = {'volume_id': record['volume_id'], 'kind': record['kind'], 'quota': record['quota'],
                       'reserve': record['reserve'], 'state': 'UNKNOWN', 'readable': None, 'writable': None,
                       'fsync_tested': None, 'free_bytes': None, 'available_bytes': None, 'checked_at': int(time.time())}
                try:
                    volume.check(); row.update(state='ONLINE', readable=True, free_bytes=volume.disk_usage().free)
                except (StorageError, OSError):
                    row['state'] = 'DEGRADED'
                # Read-only status NEVER infers write/fsync from a running process.
                volumes.append(row)
        controller = {'state': 'UNKNOWN', 'cluster_id': node['cluster_id'] if node else None,
                      'writer_authority': False, 'checked_at': int(time.time())}
        origin = node['controller'] if node else None; pin = node['pin'] if node else None
        if marker['role'] == 'controller':
            cfg = read_json(self.root / 'controller/controller.json')
            controller['cluster_id'] = cfg['cluster_id']
            origin = f"https://{marker['host']}:{marker['port']}"
            pin = fingerprint_from_pem(self.root / 'controller/server.crt')
        if origin:
            try:
                info = request_json(origin, pin, 'GET', '/api/v1/info', timeout=2)
                if info.get('cluster_id') != controller['cluster_id'] or info.get('mode') != 'single-writer-development' or info.get('raft_enabled') is not False:
                    raise Refused('controller_binding_rejected')
                controller['state'] = 'ONLINE'
            except ConnectionRefusedError:
                controller['state'] = 'OFFLINE'
            except (ClientError, OSError, Refused):
                pass
        return {'mode': 'demo-local-engine', 'as_of': int(time.time()), 'processes': processes,
                'node': {'node_id': node['node_id'] if node else None, 'cluster_id': node['cluster_id'] if node else None,
                         'identity_present': node is not None, 'pending_enrollment': pending, 'storage_approved': None,
                         'approval_state': 'UNKNOWN' if node else 'NOT_REGISTERED'},
                'controller': controller, 'volumes': volumes, 'write_probe_performed': False,
                'lifecycle_supported': False}

    def quick_join(self, params):
        self.check(); home = self.root / 'node'
        if 'code' not in params and not (home / 'enrollment_pending.json').exists() and not (home / 'node.json').exists():
            raise Refused('join_code_required')
        command = [sys.executable, '-B', '-m', 'asc.demo.quickjoin', '--state', str(self.root),
                   '--controller', params['controller'], '--pin', params['pin'],
                   '--expected-cluster-id', params['cluster_id'], '--name', params['name']]
        if params.get('replace_code'): command.append('--new-code')
        env = dict(os.environ, ASC_HOME=str(home), PYTHONDONTWRITEBYTECODE='1')
        if self.prefix: env['ASC_DEMO_PREFIX'] = self.prefix
        try:
            process = subprocess.run(command, env=env, cwd=Path(__file__).resolve().parents[2],
                input=params.get('code', '') + '\n', capture_output=True, text=True, timeout=45)
            result = json.loads(process.stdout)
        except (ValueError, OSError, subprocess.TimeoutExpired):
            raise Refused('join_unconfirmed') from None
        if process.returncode:
            known = {'tls_pin_mismatch','cluster_mismatch','unsupported_runtime','binding_mismatch','pairing_code_rejected',
                     'recovery_read_only','state_incompatible','device_or_dependency_denied'}
            raise Refused(result.get('error') if result.get('error') in known else 'join_unconfirmed')
        if result.get('quick_join_version') != 1 or result.get('state') not in ('registered', 'identity_present'):
            raise Refused('join_unconfirmed')
        # Never forward arbitrary worker output. Existing worker owns credentials.
        identifier(result['node_id']); identifier(result['cluster_id'])
        if result['cluster_id'] != params['cluster_id']: raise Refused('cluster_mismatch')
        return {'state': result['state'], 'node_id': result['node_id'], 'cluster_id': result['cluster_id'],
                'controller_confirmation': result['controller_confirmation'], 'identity_preserved': True,
                'approval_state': 'PENDING_OWNER_APPROVAL' if result['state'] == 'registered' else 'UNKNOWN',
                'storage_approved': None, 'observed_at': int(time.time())}
