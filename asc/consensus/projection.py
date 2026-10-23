"""Versioned deterministic Catalog document. Private jobs/identity never exported."""
import copy
import json
import re

from ..catalog.common import (CatalogError, ZERO, canonical, content, digest, identifier,
                              key, logical_path, policy)
from ..catalog.metadata import FILE_FIELDS, REPLICA_FIELDS, aggregate

TABLES = {'files': 'catalog_files', 'replicas': 'catalog_replicas', 'events': 'catalog_events'}
PRIMARY = {'files': 'file_id', 'replicas': 'replica_id', 'events': 'revision'}
FULL_FILE = FILE_FIELDS | {'upload_key', 'upload_policy'}


def export(db):
    state = dict(db.execute('SELECT * FROM catalog_state WHERE singleton=1').fetchone())
    result = {'schema': 1, 'cluster_id': db.execute(
        "SELECT value FROM settings WHERE key='cluster_id'").fetchone()[0],
        **{k: state[k] for k in ('epoch', 'revision', 'head_digest')}}
    for field, table in TABLES.items():
        result[field] = [dict(row) for row in db.execute(f'SELECT * FROM {table} ORDER BY {PRIMARY[field]}')]
    for event in result['events']:
        event['payload'] = json.loads(event['payload'])
    return result


def validate(doc):
    if (not isinstance(doc, dict) or set(doc) != {
            'schema', 'cluster_id', 'epoch', 'revision', 'head_digest', 'files', 'replicas', 'events'} or doc['schema'] != 1):
        raise CatalogError('invalid_consensus_projection', 409)
    identifier(doc['cluster_id']); identifier(doc['epoch'])
    if (type(doc['revision']) is not int or not 0 <= doc['revision'] < 2**63 or
            not isinstance(doc['head_digest'], str) or not re.fullmatch('[0-9a-f]{64}', doc['head_digest'])):
        raise CatalogError('invalid_consensus_projection', 409)
    for name, bound in [('files', 256), ('replicas', 2048), ('events', 1024)]:
        if not isinstance(doc[name], list) or len(doc[name]) > bound:
            raise CatalogError('consensus_projection_limit', 409)
    files, paths, keys = {}, set(), set()
    for file in doc['files']:
        if not isinstance(file, dict) or set(file) != FULL_FILE:
            raise CatalogError('invalid_consensus_projection', 409)
        aggregate({'file': {k: file[k] for k in FILE_FIELDS}, 'replicas': []}, doc['revision'])
        key(file['upload_key']); policy(file['upload_policy'])
        pair = (file['logical_path'], file['version'])
        if file['file_id'] in files or pair in paths or file['upload_key'] in keys:
            raise CatalogError('consensus_projection_conflict', 409)
        files[file['file_id']] = file; paths.add(pair); keys.add(file['upload_key'])
    seen, local = set(), set()
    for replica in doc['replicas']:
        file = files.get(replica.get('file_id'))
        if file is None:
            raise CatalogError('invalid_consensus_projection', 409)
        aggregate({'file': {k: file[k] for k in FILE_FIELDS}, 'replicas': [replica]}, doc['revision'])
        reference = (replica['node_id'], replica['volume_id'], replica['local_file_id'])
        if replica['replica_id'] in seen or reference in local:
            raise CatalogError('consensus_projection_conflict', 409)
        seen.add(replica['replica_id']); local.add(reference)
    previous = None; latest = {}
    for event in doc['events']:
        if (not isinstance(event, dict) or set(event) != {
                'epoch', 'revision', 'previous_digest', 'digest', 'payload', 'created_at'} or
                event['epoch'] != doc['epoch'] or event['digest'] != digest({
                    k: v for k, v in event.items() if k != 'digest'})):
            raise CatalogError('invalid_consensus_history', 409)
        aggregate(event['payload'], event['revision'])
        if (type(event['revision']) is not int or event['payload']['file']['revision'] != event['revision'] or
                type(event['created_at']) is not int or not 0 <= event['created_at'] < 2**63 or
                event['revision'] == 1 and event['previous_digest'] != ZERO):
            raise CatalogError('invalid_consensus_history', 409)
        if previous and (event['revision'] != previous['revision'] + 1 or event['previous_digest'] != previous['digest']):
            raise CatalogError('invalid_consensus_history', 409)
        previous = event
        latest[event['payload']['file']['file_id']] = event['payload']
    if (doc['revision'] == 0 and (doc['events'] or doc['head_digest'] != ZERO or doc['files']) or
            doc['revision'] > 0 and (previous is None or previous['revision'] != doc['revision'] or
                                    previous['digest'] != doc['head_digest'])):
        raise CatalogError('invalid_consensus_history', 409)
    for file_id, payload in latest.items():
        file = files.get(file_id)
        current = {'file': {k: file[k] for k in FILE_FIELDS},
                   'replicas': sorted([r for r in doc['replicas'] if r['file_id'] == file_id], key=lambda r: r['replica_id'])} if file else None
        if current != payload:
            raise CatalogError('consensus_materialization_conflict', 409)
    if (doc['files'] != sorted(doc['files'], key=lambda f: f['file_id']) or
            doc['replicas'] != sorted(doc['replicas'], key=lambda r: r['replica_id'])):
        raise CatalogError('noncanonical_consensus_projection', 409)
    if len(canonical(doc)) > 2 * 1024**2:
        raise CatalogError('consensus_projection_limit', 409)
    return doc


def prepare(document, operation, data, request_id, file_id, stamp):
    """All nondeterminism is supplied by preparation; projection installation is pure data."""
    doc = copy.deepcopy(document); key(request_id)
    if type(stamp) is not int or not 0 <= stamp < 2**63:
        raise CatalogError('invalid_timestamp', 400)
    if operation == 'DECLARE':
        if set(data) != {'logical_path', 'version', 'size', 'sha256', 'policy'}:
            raise CatalogError('invalid_metadata_declaration', 400)
        identifier(file_id); logical_path(data['logical_path']); content(data['size'], data['sha256']); policy(data['policy'])
        if type(data['version']) is not int or not 1 <= data['version'] <= 1000000:
            raise CatalogError('invalid_file_version', 400)
        file = {'file_id': file_id, **data, 'created_at': stamp, 'updated_at': stamp,
                'revision': doc['revision'] + 1, 'upload_key': request_id, 'upload_policy': data['policy']}
        doc['files'].append(file)
    elif operation == 'POLICY':
        if set(data) != {'file_id', 'policy'}:
            raise CatalogError('invalid_policy_command', 400)
        identifier(data['file_id']); policy(data['policy'])
        file = next((f for f in doc['files'] if f['file_id'] == data['file_id']), None)
        if file is None:
            raise CatalogError('file_not_found', 404)
        if file['policy'] == data['policy']:
            return validate(doc)  # A receipt/index advances; Catalog revision does not.
        file.update(policy=data['policy'], updated_at=stamp, revision=doc['revision'] + 1)
    else:
        raise CatalogError('distributed_fencing_required', 503)
    payload = {'file': {k: file[k] for k in FILE_FIELDS},
               'replicas': sorted([r for r in doc['replicas'] if r['file_id'] == file['file_id']], key=lambda r: r['replica_id'])}
    event = {'epoch': doc['epoch'], 'revision': doc['revision'] + 1,
             'previous_digest': doc['head_digest'], 'payload': payload, 'created_at': stamp}
    event['digest'] = digest(event); doc['events'] = (doc['events'] + [event])[-1024:]
    doc.update(revision=event['revision'], head_digest=event['digest'])
    doc['files'].sort(key=lambda f: f['file_id'])
    return validate(doc)
