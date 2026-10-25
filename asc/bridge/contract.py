"""Versioned bounded IPC contract. No caller-selected paths, commands or PIDs."""
import json
from .. import validation
from ..catalog.common import identifier
from ..demo.state import lan_origin
from ..demo.quickjoin import normalized_pin
from ..server import _unique_object
from ..storage.errors import StorageError

VERSION = 1
MAX_FRAME = 8192
SCOPES = {'status': 'read', 'quick_join': 'join', 'node_start': 'lifecycle', 'node_stop': 'lifecycle'}
STATES = {'ONLINE', 'OFFLINE', 'DEGRADED', 'UNKNOWN', 'QUORUM UNAVAILABLE', 'RECOVERY READ-ONLY'}


class Refused(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)  # Fixed label only; never secret-bearing input.


def decode(raw):
    try:
        if not isinstance(raw, bytes) or not 1 <= len(raw) <= MAX_FRAME:
            raise ValueError()
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=_unique_object,
                           parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        if type(value) is not dict:
            raise ValueError()
        return value
    except (ValueError, UnicodeError, RecursionError):
        raise Refused('invalid_frame') from None


def request(value):
    try:
        if type(value) is not dict or set(value) != {'api_version', 'request_id', 'app_id', 'authorization', 'operation', 'params'}:
            raise ValueError()
        if type(value['api_version']) is not int or value['api_version'] != VERSION:
            raise ValueError()
        identifier(value['request_id']); identifier(value['app_id'])
        validation.secret(value['authorization'])
        op, params = value['operation'], value['params']
        if not isinstance(op, str) or op not in SCOPES or type(params) is not dict:
            raise ValueError()
        if op != 'quick_join':
            if params:
                raise ValueError()
        else:
            if set(params) - {'controller', 'pin', 'cluster_id', 'name', 'code', 'replace_code'} or not {'controller', 'pin', 'cluster_id', 'name'} <= set(params):
                raise ValueError()
            lan_origin(params['controller']); normalized_pin(params['pin'])
            identifier(params['cluster_id']); validation.name(params['name'])
            if 'code' in params:
                validation.code(params['code'])
            if 'replace_code' in params and type(params['replace_code']) is not bool:
                raise ValueError()
            if params.get('replace_code') and 'code' not in params:
                raise ValueError()
        return value
    except (ValueError, TypeError, KeyError, AttributeError, StorageError):
        raise Refused('invalid_request') from None
