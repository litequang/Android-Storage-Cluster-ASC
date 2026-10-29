"""Owner-only preview/confirmation over existing pinned lifecycle/Catalog APIs."""
import json
import re
import threading
import time
import uuid

from ... import validation as valid
from ...catalog.common import CatalogError, digest, identifier
from ...catalog.service import approval_stamp
from ..lan import lifecycle_request
from ..pairing import PairingError
from ..state import lan_origin


class Management:
    def __init__(self, api, clock=time.monotonic):
        self.api, self.clock = api, clock
        self.lock = threading.Lock()
        self.previews = {}

    def _read(self, node_id):
        self.api.pairings._ready()  # Existing exact Demo/root/cluster/owner binding.
        valid.node_id(node_id)
        with self.api.service.registry.connect() as db:
            node = db.execute('SELECT node_id,name,state,profile,token_version FROM nodes WHERE node_id=?', (node_id,)).fetchone()
            approval = db.execute('SELECT * FROM catalog_nodes WHERE node_id=?', (node_id,)).fetchone()
            count = db.execute('SELECT COUNT(*) FROM catalog_replicas WHERE node_id=?', (node_id,)).fetchone()[0]
        if node is None or node_id == 'local-controller':
            raise PairingError(404, 'node_not_manageable')
        node = dict(node)
        if json.loads(node['profile']).get('protected') is True:
            raise PairingError(403, 'node_not_manageable')
        return node, dict(approval) if approval else None, count

    def detail(self, node_id):
        node, approval, replicas = self._read(node_id)
        # Heartbeat hints are NOT a Controller probe or storage approval.
        profile = json.loads(node['profile'])
        reported = []
        storage = profile.get('storage')
        if isinstance(storage, dict) and isinstance(storage.get('volumes'), list):
            for volume in storage['volumes'][:8]:
                try:
                    value = identifier(volume['volume_id'])
                except (CatalogError, TypeError, KeyError):
                    continue
                if value not in reported:
                    reported.append(value)
        return {'management_version': 1, 'node_id': node_id, 'name': node['name'],
                'state': node['state'], 'credential_generation': node['token_version'],
                'recorded_replicas': replicas, 'reported_volume_ids': reported,
                'reported_volumes_verified': False,
                'approval': ({k: approval[k] for k in ('origin', 'pin', 'device_id', 'storage_allowed')} |
                             {'volume_ids': json.loads(approval['volume_ids'])}) if approval else None}

    def preview(self, node_id, obj, owner, session_expires):
        if type(obj) is not dict or set(obj) != {'management_version', 'action', 'parameters'} or type(obj['management_version']) is not int or obj['management_version'] != 1:
            raise ValueError('invalid management request')
        action, parameters = obj['action'], obj['parameters']
        if type(action) is not str or type(parameters) is not dict:
            raise ValueError('invalid management action')
        node, approval, replicas = self._read(node_id)
        if node['state'] != 'active':
            raise PairingError(409, 'node_state_changed')
        if action == 'approve':
            if set(parameters) != {'origin', 'pin', 'volume_ids', 'failure_domain'}:
                raise ValueError('invalid storage approval')
            lan_origin(parameters['origin']); valid.name(parameters['failure_domain'])
            pin = parameters['pin']
            if type(pin) is not str or not re.fullmatch('[0-9a-f]{64}', pin):
                raise ValueError('invalid public pin')
            volumes = parameters['volume_ids']
            if type(volumes) is not list or not 1 <= len(volumes) <= 8 or len(set(volumes)) != len(volumes):
                raise ValueError('invalid volume list')
            for volume in volumes:
                identifier(volume)
        elif action == 'rename':
            if set(parameters) != {'name'}:
                raise ValueError('invalid node name')
            valid.name(parameters['name'])
        elif action == 'revoke':
            if parameters != {}:
                raise ValueError('invalid revoke request')
        else:
            raise ValueError('unsupported management action')
        intent = {'node_id': node_id, 'action': action, 'parameters': parameters,
                  'expected_generation': node['token_version'], 'expected_approval': approval_stamp(approval)}
        with self.lock:
            self.previews = {k: v for k, v in self.previews.items() if v['expires'] > self.clock()}
            if session_expires <= self.clock():
                raise PairingError(401, 'login_required')
            if len(self.previews) >= 32 or sum(v['owner'] == owner for v in self.previews.values()) >= 8:
                raise PairingError(429, 'management_limit')
            preview_id = str(uuid.uuid4())
            self.previews[preview_id] = dict(intent=json.loads(json.dumps(intent)), owner=owner,
                expires=min(session_expires, self.clock()+120), result=None)
        return {'management_version': 1, 'preview_id': preview_id, 'intent_sha256': digest(intent),
                'node_id': node_id, 'node_name': node['name'], 'action': action, 'parameters': parameters,
                'recorded_replicas': replicas, 'storage_verified': False, 'expires_in': 120,
                'warning': 'Owner must verify endpoint/pin/volumes and truthful physical domain. Revocation prevents access; bytes are retained.'}

    def apply(self, preview_id, obj, owner):
        identifier(preview_id)
        if (type(obj) is not dict or set(obj) != {'management_version', 'intent_sha256', 'confirmation_node_id', 'physical_domain_confirmed'}
                or type(obj['management_version']) is not int or obj['management_version'] != 1
                or type(obj['physical_domain_confirmed']) is not bool):
            raise ValueError('invalid confirmation')
        with self.lock:
            preview = self.previews.get(preview_id)
            if not preview or preview['owner'] != owner or preview['expires'] <= self.clock():
                raise PairingError(404, 'management_preview_expired')
            intent = preview['intent']
            if (obj['intent_sha256'] != digest(intent) or obj['confirmation_node_id'] != intent['node_id']
                    or intent['action'] == 'approve' and not obj['physical_domain_confirmed']):
                raise PairingError(409, 'management_confirmation_required')
            self.api.pairings._ready()
            if preview['result'] is not None:
                return dict(preview['result'], replayed=True)
            p = intent['parameters']
            fields = {'node_id': intent['node_id'], 'expected_generation': intent['expected_generation']}
            if intent['action'] == 'approve':
                self.api.client.request('POST', 'nodes/register', fields | {
                    'origin': p['origin'], 'pin': p['pin'], 'device_id': p['failure_domain'],
                    'volume_ids': p['volume_ids'], 'expected_approval': intent['expected_approval']})
            else:
                lifecycle_request(self.api.client, 'POST', 'admin/'+intent['action'],
                                  fields | ({'name': p['name']} if intent['action'] == 'rename' else {}))
            preview['result'] = {'management_version': 1, 'applied': True, 'replayed': False,
                                 'node_id': intent['node_id'], 'action': intent['action'],
                                 'confirmed_at': int(time.time()), 'storage_verified': False}
            return dict(preview['result'])

    def forget(self, owner):
        with self.lock:
            self.previews = {k: v for k, v in self.previews.items() if v['owner'] != owner}

    def close(self):
        with self.lock:
            self.previews.clear()
