"""Canonical bounded metadata and public validation."""
import hashlib
import ipaddress
import json
import re
import time
import uuid
from urllib.parse import urlsplit
from ..storage.errors import StorageError
from ..storage.volumes import identifier as _identifier, logical_path as _logical_path

POLICIES = {'single': 1, 'replicated_2': 2, 'replicated_3': 3}
ZERO = '0' * 64
MAX_SNAPSHOT = 2 * 1024**2


class CatalogError(StorageError):
    pass


def identifier(value):
    try:return _identifier(value)
    except StorageError as exc:raise CatalogError(exc.code,exc.status) from None


def logical_path(value):
    try:return _logical_path(value)
    except StorageError as exc:raise CatalogError(exc.code,exc.status) from None


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def now():
    return int(time.time())


def uid():
    return str(uuid.uuid4())


def policy(value):
    if not isinstance(value, str) or value not in POLICIES:
        raise CatalogError('invalid_policy', 400)
    return value


def content(size, sha256):
    if type(size) is not int or not 0 <= size <= 1024**3:
        raise CatalogError('invalid_size', 400)
    if not isinstance(sha256, str) or not re.fullmatch('[a-f0-9]{64}', sha256):
        raise CatalogError('invalid_sha256', 400)


def key(value):
    if not isinstance(value, str) or not re.fullmatch('[A-Za-z0-9_-]{8,128}', value):
        raise CatalogError('invalid_idempotency_key', 400)
    return value


def origin(value, pin):
    try:
        url = urlsplit(value)
        ip = ipaddress.ip_address(url.hostname)
        if (url.scheme != 'https' or url.path not in ('', '/') or url.query or url.fragment or
                url.username or url.password or ip.is_unspecified or ip.is_multicast or
                not (ip.is_private or ip.is_loopback) or not 1024 <= (url.port or 443) <= 65535):
            raise ValueError()
    except (ValueError, TypeError, AttributeError):
        raise CatalogError('invalid_private_origin', 400) from None
    if not isinstance(pin, str) or not re.fullmatch('[a-fA-F0-9]{64}', pin):
        raise CatalogError('invalid_pin', 400)
    return value.rstrip('/'), pin.upper()
