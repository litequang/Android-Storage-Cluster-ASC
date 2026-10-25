"""Strict immutable manifest binding to an exact validated runtime projection."""
import json
import re
from ..catalog.common import CatalogError, canonical, digest, identifier
from ..failover.state import validate as runtime_validate

MAX_METADATA = 2 * 1024**2
MAX_MANIFEST = 2 * 1024**2
FIELDS = ('file_id', 'logical_path', 'version', 'size', 'sha256')


def fail(code='external_corrupt', status=409):
    raise CatalogError(code, status)


def sha(value):
    if not isinstance(value, str) or not re.fullmatch('[a-f0-9]{64}', value):
        fail('invalid_external_digest', 400)
    return value


def integer(value, minimum=0):
    if type(value) is not int or not minimum <= value < 2**63:
        fail('invalid_external_integer', 400)
    return value


def decode(raw, limit):
    if len(raw) > limit:
        fail('external_metadata_limit', 413)
    try:
        obj = json.loads(raw)
        if canonical(obj) != raw:
            fail()
        return obj
    except (ValueError, TypeError, UnicodeError, RecursionError):
        fail()


def descriptors(document):
    return sorted(({k: f[k] for k in FIELDS} for f in document['catalog']['files']),
                  key=lambda f: f['file_id'])


def capture(view, backup_id, created_at):
    """Only a trusted live Source may supply view; this function grants no authority."""
    identifier(backup_id); integer(created_at)
    doc = runtime_validate(view['document'])
    # Runtime.validate validates in place and returns the document.
    raw = canonical(doc)
    if len(raw) > MAX_METADATA:
        fail('external_metadata_limit', 413)
    state = view['state']
    if state['document_sha256'] != digest(doc):
        fail('external_snapshot_mismatch')
    manifest = {'format': 1, 'kind': 'asc-external-data', 'backup_id': backup_id,
        'created_at': created_at, 'cluster_id': doc['cluster_id'], 'epoch': doc['epoch'],
        'source_index': integer(state['index'], 1), 'source_term': integer(state['term'], 1),
        'source_authority': doc['authority'], 'control_revision': doc['revision'],
        'catalog_revision': doc['catalog']['revision'], 'catalog_digest': doc['catalog']['head_digest'],
        'metadata_sha256': digest(doc), 'coverage': 'all-catalog-versions',
        'files': descriptors(doc), 'writer_recovery_supported': False,
        'secrets_included': False}
    validate(manifest, raw)
    return manifest, raw


def validate(manifest, metadata):
    try:
        expected = {'format','kind','backup_id','created_at','cluster_id','epoch','source_index',
            'source_term','source_authority','control_revision','catalog_revision','catalog_digest',
            'metadata_sha256','coverage','files','writer_recovery_supported','secrets_included'}
        if (type(manifest) is not dict or set(manifest) != expected or
                type(manifest['format']) is not int or manifest['format'] != 1 or
                manifest['kind'] != 'asc-external-data' or
                manifest['coverage'] != 'all-catalog-versions' or
                manifest['writer_recovery_supported'] is not False or manifest['secrets_included'] is not False):
            fail()
        identifier(manifest['backup_id'])
        doc = decode(metadata, MAX_METADATA); runtime_validate(doc)
        for name in ('created_at','control_revision','catalog_revision'):
            integer(manifest[name])
        integer(manifest['source_index'], 1); integer(manifest['source_term'], 1)
        if (manifest['metadata_sha256'] != digest(doc) or
                manifest['cluster_id'] != doc['cluster_id'] or manifest['epoch'] != doc['epoch'] or
                manifest['source_authority'] != doc['authority'] or
                doc['authority']['term'] > manifest['source_term'] or
                manifest['control_revision'] != doc['revision'] or
                manifest['catalog_revision'] != doc['catalog']['revision'] or
                manifest['catalog_digest'] != doc['catalog']['head_digest'] or
                manifest['files'] != descriptors(doc) or len(canonical(manifest)) > MAX_MANIFEST):
            fail('external_snapshot_mismatch')
        return doc
    except (KeyError, TypeError, ValueError, AttributeError):
        fail()
