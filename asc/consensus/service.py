"""Metadata-only service facade; no worker, grants, placement or file transfers."""
from .adapter import Adapter
from .client import Client


class Service:
    distributed = True

    def __init__(self, registry, config):
        self.registry = registry
        self.adapter = Adapter(registry, Client.from_config(config)).activate()

    def start(self, background=False):
        self.adapter.sync()
        return self

    def close(self):
        pass


def handle(handler):
    from urllib.parse import urlsplit, parse_qs
    from ..catalog.common import CatalogError
    from ..catalog.metadata import FILE_FIELDS
    from .. import validation as valid
    from ..server import PayloadTooLarge
    import sqlite3
    try:
        if not handler._admin():
            return
        adapter = handler.server.catalog.adapter
        url = urlsplit(handler.path); parts = url.path.removeprefix('/catalog/v1/').split('/')
        query = parse_qs(url.query, strict_parsing=True)
        if set(query) - {'consistency'} or any(len(v) != 1 for v in query.values()) or url.fragment:
            raise ValueError()
        consistency = query.get('consistency', ['local'])[0]
        if consistency not in ('local', 'strong'):
            raise ValueError()
        if handler.command == 'GET':
            view = adapter.sync(strong=consistency == 'strong')
            common = {k: view[k] for k in ('stale', 'read_only', 'revision', 'applied_index', 'metadata_only')}
            if parts == ['metadata', 'status']:
                return handler._json(200, {**common, **adapter.client.status(), 'automatic_failover': False})
            def public(file):
                return {'file': {k: file[k] for k in FILE_FIELDS},
                        'replicas': [r for r in view['document']['replicas'] if r['file_id'] == file['file_id']],
                        'available_replicas': None, 'availability': 'UNKNOWN', **common}
            if parts == ['files']:
                return handler._json(200, {'files': [public(f) for f in view['document']['files']], **common})
            if len(parts) == 2 and parts[0] == 'files':
                file = next((f for f in view['document']['files'] if f['file_id'] == parts[1]), None)
                if file is None:
                    raise CatalogError('file_not_found', 404)
                return handler._json(200, public(file))
        if handler.command == 'POST':
            if query:
                raise ValueError()
            if parts == ['metadata', 'declare']:
                obj = handler._read_json()
                valid.payload(obj, ('request_id', 'logical_path', 'size', 'sha256', 'policy', 'version'))
                request_id = obj.pop('request_id')
                result = adapter.submit('DECLARE', obj, request_id)
            elif len(parts) == 3 and parts[0] == 'files' and parts[2] == 'policy':
                obj = handler._read_json(); valid.payload(obj, ('request_id', 'policy'))
                result = adapter.submit('POLICY', {'file_id': parts[1], 'policy': obj['policy']}, obj['request_id'])
            else:
                raise CatalogError('distributed_fencing_required', 503)
            return handler._json(200, {k: result[k] for k in ('receipt', 'stale', 'revision', 'applied_index', 'metadata_only')})
        raise CatalogError('distributed_fencing_required', 503)
    except CatalogError as exc:
        return handler._json(exc.status, {'error': exc.code})
    except PayloadTooLarge:
        return handler._json(413, {'error': 'payload_too_large'})
    except (ValueError, KeyError, TypeError, UnicodeError, RecursionError, OverflowError):
        return handler._json(400, {'error': 'bad_request'})
    except (sqlite3.Error, OSError):
        return handler._json(503, {'error': 'consensus_projection_unavailable'})
