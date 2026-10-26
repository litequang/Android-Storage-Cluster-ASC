"""Native sealed-state adapter to the SAME Core client/Registry enrollment.

No CLI/global HOME/interactive input or plaintext node config. Storage/domain
approval, re-pair, Controller/quorum bootstrap and runtime startup are not here.
"""
import re
import uuid

from .. import validation as valid
from ..catalog.common import canonical
from ..client import request_json
from ..demo.state import lan_origin
from ..enrollment import new_pending, accepted_identity
from .context import ContextLocked


class EnrollmentRefused(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _uuid(value):
    if not isinstance(value, str) or str(uuid.UUID(value)) != value:
        raise ContextLocked()


def _binding(origin, pin, cluster):
    lan_origin(origin)
    _uuid(cluster)
    if not isinstance(pin, str) or not re.fullmatch('[a-f0-9]{64}', pin):
        raise ContextLocked()


def validate_components(record):
    """Strict native formats. Legacy CLI repair/Controller configs never adopted."""
    pending, node = record['pending'], record['node']
    if pending is not None and node is not None:
        raise ContextLocked()
    if pending is not None or node is not None:
        if record['tls'] is None:
            raise ContextLocked()
    if node is not None:
        if (not isinstance(node, dict) or set(node) != {'config_version', 'controller', 'pin',
                'node_id', 'token', 'token_version', 'cluster_id'} or
                type(node['config_version']) is not int or node['config_version'] != 1 or
                type(node['token_version']) is not int or not 1 <= node['token_version'] <= 2**31):
            raise ContextLocked()
        _binding(node['controller'], node['pin'], node['cluster_id'])
        _uuid(node['node_id']); valid.secret(node['token'])
    if pending is not None:
        if not isinstance(pending, dict) or set(pending) != {'request_id', 'operation'}:
            raise ContextLocked()
        _uuid(pending['request_id'])
        op = pending['operation']
        if (not isinstance(op, dict) or set(op) != {'config_version', 'controller', 'pin',
                'target_node_id', 'cluster_id', 'expected_cluster_id', 'payload'} or
                type(op['config_version']) is not int or op['config_version'] != 1 or
                op['target_node_id'] is not None or op['cluster_id'] is not None):
            raise ContextLocked()
        _binding(op['controller'], op['pin'], op['expected_cluster_id'])
        body = op['payload']
        if (not isinstance(body, dict) or set(body) != {'protocol_version', 'code', 'name',
                'profile', 'enrollment_id', 'enrollment_token'} or
                type(body['protocol_version']) is not int or body['protocol_version'] != 1):
            raise ContextLocked()
        valid.name(body['name']); valid.profile(body['profile'])
        if valid.code(body['code']) != body['code'] or body['profile'].get('protected') is not False:
            raise ContextLocked()
        valid.secret(body['enrollment_id']); valid.secret(body['enrollment_token'])


class NativeEnrollment:
    """Owned context supplies guard/Keystore/lock. Only Core's pinned transport."""
    def __init__(self, context):
        self.context = context

    def _snapshot(self):
        raw = self.context.provider.load()
        return raw, self.context._validate(raw)

    def _publish(self, raw, record):
        record['revision'] += 1
        updated = canonical(record).decode()
        self.context._validate(updated)
        self.context.provider.compare_exchange(raw, updated)

    @staticmethod
    def _info(origin, pin, cluster):
        info = request_json(origin, pin, 'GET', '/api/v1/info')
        if (type(info.get('protocol_version')) is not int or info['protocol_version'] != 1 or
                type(info.get('schema_version')) is not int or info['schema_version'] != 4 or
                info.get('mode') != 'single-writer-development' or info.get('raft_enabled') is not False or
                not isinstance(info.get('features'), list) or
                'retry-safe-enrollment-v1' not in info['features']):
            raise EnrollmentRefused('unsupported_runtime')
        if info.get('cluster_id') != cluster:
            raise EnrollmentRefused('cluster_mismatch')

    def _send(self):
        raw, record = self._snapshot()
        if record['node'] is not None:
            return self.context.public_status()  # Historical receipt, never live approval.
        if record['pending'] is None:
            raise EnrollmentRefused('no_pending_enrollment')
        op = record['pending']['operation']
        self._info(op['controller'], op['pin'], op['expected_cluster_id'])
        reply = request_json(op['controller'], op['pin'], 'POST', '/api/v1/join', op['payload'])
        node = accepted_identity(op, reply)  # SAME Core CLI acceptance, not Kotlin logic.
        record['node'], record['pending'] = node, None
        self._publish(raw, record)  # Atomic identity+pending transition, no two-file gap.
        return self.context.public_status()

    def join(self, request_id, origin, pin, cluster, name, code, profile):
        _uuid(request_id); _binding(origin, pin, cluster)
        valid.name(name); code = valid.code(code); valid.profile(profile)
        if profile.get('protected') is not False:
            raise EnrollmentRefused('device_not_qualified')
        with self.context.operation():
            raw, record = self._snapshot()
            if record['tls'] is None:
                raise EnrollmentRefused('tls_identity_required')
            node = record['node']
            if node is not None:
                if (node['controller'], node['pin'], node['cluster_id']) != (origin, pin, cluster):
                    raise EnrollmentRefused('binding_mismatch')
                return self.context.public_status()
            pending = record['pending']
            if pending is not None:
                op = pending['operation']
                if (pending['request_id'], op['controller'], op['pin'], op['expected_cluster_id'],
                        op['payload']['name'], op['payload']['code']) != (request_id, origin, pin, cluster, name, code):
                    raise EnrollmentRefused('resume_required')
            else:
                self._info(origin, pin, cluster)  # Pin/cluster/mode BEFORE creating private credentials.
                record['pending'] = {'request_id': request_id,
                    'operation': new_pending(origin, pin, cluster, name, profile, code)}
                self._publish(raw, record)  # Durable BEFORE POST, same op/token after any lost ACK.
            return self._send()

    def resume(self):
        with self.context.operation():
            return self._send()

    def replace_code(self, code):
        """Explicit new owner grant, SAME operation/token, never re-pair an enrolled ID."""
        code = valid.code(code)
        with self.context.operation():
            raw, record = self._snapshot()
            if record['node'] is not None or record['pending'] is None:
                raise EnrollmentRefused('no_pending_enrollment')
            op = record['pending']['operation']
            self._info(op['controller'], op['pin'], op['expected_cluster_id'])
            op['payload']['code'] = code
            self._publish(raw, record)
            return self._send()
