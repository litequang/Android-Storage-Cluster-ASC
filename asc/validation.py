"""Bounded wire validation, also used by local registry entry points."""
import json
import math
import re
import unicodedata

MAX_JSON = 65536


def name(value):
    if (not isinstance(value, str) or not 1 <= len(value) <= 64 or
            value != value.strip() or any(unicodedata.category(c).startswith('C') for c in value)):
        raise ValueError('invalid node name')
    return value


def node_id(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', value):
        raise ValueError('invalid node id')
    return value


def code(value):
    if not isinstance(value, str) or len(value) > 40:
        raise ValueError('invalid code')
    value = value.replace('-', '').replace(' ', '').strip().upper()
    if not re.fullmatch(r'[0-9A-F]{12}', value):
        raise ValueError('invalid code')
    return value


def secret(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_-]{32,128}', value):
        raise ValueError('invalid enrollment credential')
    return value


def profile(value):
    def bounded(item, depth=0):
        if depth > 6:
            raise ValueError('profile too deep')
        if isinstance(item, dict):
            if len(item) > 64:
                raise ValueError('too many profile fields')
            for key, child in item.items():
                if not isinstance(key, str) or not 1 <= len(key) <= 64:
                    raise ValueError('invalid profile field')
                bounded(key, depth + 1)
                bounded(child, depth + 1)
        elif isinstance(item, list):
            if len(item) > 64:
                raise ValueError('profile list too long')
            for child in item:
                bounded(child, depth + 1)
        elif isinstance(item, str):
            if len(item) > 1024 or any(unicodedata.category(c).startswith('C') for c in item):
                raise ValueError('invalid profile text')
        elif item is None or isinstance(item, bool):
            pass
        elif isinstance(item, (int, float)):
            if not math.isfinite(item) or abs(item) > 2**63 - 1:
                raise ValueError('invalid profile number')
        else:
            raise ValueError('invalid profile type')

    if not isinstance(value, dict):
        raise ValueError('profile must be object')
    bounded(value)
    if len(json.dumps(value, ensure_ascii=False).encode('utf-8')) > 32768:
        raise ValueError('profile too large')
    if 'profile_version' in value and (type(value['profile_version']) is not int or value['profile_version'] != 1):
        raise ValueError('unsupported profile version')
    for field in ('model', 'manufacturer', 'android', 'machine', 'recommended_role'):
        if field in value and not isinstance(value[field], str):
            raise ValueError('invalid profile text field')
    for field in ('protected', 'installation_allowed'):
        if field in value and not isinstance(value[field], bool):
            raise ValueError('invalid boolean field')
    for field, choices in (('sd_status', ('unknown', 'detected', 'writable-tested')),
                           ('device_identity_status', ('known', 'unknown')),
                           ('score_basis', ('runtime-ram', 'manufacturer-baseline', 'unknown'))):
        if field in value and value[field] not in choices:
            raise ValueError('invalid profile status')
    for field, ceiling in (('readiness_score', 100), ('memory_mb', 2**31), ('sdk', 1000)):
        item = value.get(field)
        if item is not None and (type(item) not in (int, float) or not 0 <= item <= ceiling):
            raise ValueError('invalid profile measurement')
    if 'sd_candidates' in value and (not isinstance(value['sd_candidates'], list) or
                                   any(not isinstance(x, dict) for x in value['sd_candidates'])):
        raise ValueError('invalid SD candidates')
    space = value.get('internal_app_storage')
    if space is not None:
        if not isinstance(space, dict):
            raise ValueError('invalid storage measurement')
        for field in ('total_bytes', 'free_bytes'):
            item = space.get(field)
            if item is not None and (type(item) is not int or item < 0):
                raise ValueError('invalid storage bytes')
    return value


def payload(obj, required, optional=()):
    if not isinstance(obj, dict) or not set(required) <= obj.keys() or obj.keys() - set(required) - set(optional) - {'protocol_version'}:
        raise ValueError('invalid request schema')
    if 'protocol_version' in obj and (type(obj['protocol_version']) is not int or obj['protocol_version'] != 1):
        raise ValueError('unsupported protocol version')
    return obj
