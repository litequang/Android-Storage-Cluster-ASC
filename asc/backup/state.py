"""Versioned bounded backup projection; no filesystem paths or physical deletion."""
import copy

from ..catalog.common import CatalogError, content, digest, identifier, key, logical_path

LIMITS = {'files': 256, 'snapshots': 64, 'jobs': 256, 'schedules': 32,
          'policies': 256, 'requests': 512}


def empty():
    return {'schema': 1, **{name: {} for name in LIMITS}}


def integer(value, low=0, high=2**63-1):
    if type(value) is not int or not low <= value <= high:
        raise ValueError('invalid backup integer')
    return value


def status(backup, file_id):
    return backup['files'].get(file_id, {}).get('state', 'LIVE')


def pinned(backup):
    result = {f['file_id'] for s in backup['snapshots'].values() if s['state'] != 'EXPIRED'
              for f in s['files']}
    result.update(j['source_file_id'] for j in backup['jobs'].values()
                  if j['kind'] == 'RESTORE' and j['state'] not in ('COMPLETED', 'FAILED'))
    return result


def heads(catalog):
    result = {}
    for file in catalog['files']:
        if file['logical_path'] not in result or file['version'] > result[file['logical_path']]['version']:
            result[file['logical_path']] = file
    return sorted(result.values(), key=lambda f: f['logical_path'])


def capture(view, backup, stamp, retention):
    """Capture one exact committed projection, never label a later index as its source."""
    files = []
    catalog = view['document']['catalog']
    for file in heads(catalog):
        if status(backup, file['file_id']) != 'LIVE':
            continue
        if not any(r['file_id'] == file['file_id'] and r['state'] == 'VERIFIED' for r in catalog['replicas']):
            raise CatalogError('snapshot_unverified_head', 409)
        files.append({k: file[k] for k in ('file_id', 'logical_path', 'version', 'size', 'sha256')})
    value = {'schema': 1, 'cluster_id': catalog['cluster_id'], 'epoch': catalog['epoch'],
             'source_index': view['state']['index'], 'source_term': view['state']['term'],
             'control_revision': view['document']['revision'], 'catalog_revision': catalog['revision'],
             'catalog_digest': catalog['head_digest'], 'created_at': stamp, 'files': files}
    return {'manifest': value, 'manifest_sha256': digest(value), 'files': files,
            'state': 'UNVERIFIED', 'verified_at': None, 'retain_until': stamp + retention}


def validate(backup, catalog):
    """Reject malformed/corrupt extensions before any runtime preparation or IO."""
    try:
        if not isinstance(backup, dict) or set(backup) != {'schema', *LIMITS} or type(backup['schema']) is not int or backup['schema'] != 1:
            raise ValueError()
        for name, bound in LIMITS.items():
            if not isinstance(backup[name], dict) or len(backup[name]) > bound:
                raise ValueError()
        files = {f['file_id']: f for f in catalog['files']}
        for file_id, row in backup['files'].items():
            identifier(file_id)
            if file_id not in files or set(row) != {'state', 'changed_at', 'retain_until'} or row['state'] not in ('TRASH', 'EXPIRED'):
                raise ValueError()
            integer(row['changed_at']); integer(row['retain_until'])
        for path, row in backup['policies'].items():
            logical_path(path)
            if set(row) != {'keep_last', 'max_age_seconds', 'trash_seconds'}:
                raise ValueError()
            integer(row['keep_last'], 1, 256); integer(row['max_age_seconds'], 60, 315360000)
            integer(row['trash_seconds'], 60, 315360000)
        for snapshot_id, row in backup['snapshots'].items():
            identifier(snapshot_id)
            if set(row) != {'manifest', 'manifest_sha256', 'files', 'state', 'verified_at', 'retain_until'}:
                raise ValueError()
            manifest = row['manifest']
            if set(manifest) != {'schema', 'cluster_id', 'epoch', 'source_index', 'source_term', 'control_revision',
                                 'catalog_revision', 'catalog_digest', 'created_at', 'files'} or manifest['schema'] != 1:
                raise ValueError()
            if ((manifest['cluster_id'], manifest['epoch']) != (catalog['cluster_id'], catalog['epoch']) or
                    row['manifest_sha256'] != digest(manifest) or manifest['files'] != row['files'] or
                    row['state'] not in ('UNVERIFIED', 'VERIFIED', 'EXPIRED')):
                raise ValueError()
            for field in ('source_index', 'source_term', 'control_revision', 'catalog_revision', 'created_at'):
                integer(manifest[field])
            if manifest['catalog_revision'] > catalog['revision']:
                raise ValueError()
            content(0, manifest['catalog_digest']); integer(row['retain_until'])
            if row['verified_at'] is not None:
                integer(row['verified_at'])
            if row['state'] == 'VERIFIED' and row['verified_at'] is None:
                raise ValueError()
            if len(row['files']) > 256 or len({f['file_id'] for f in row['files']}) != len(row['files']):
                raise ValueError()
            for file in row['files']:
                if set(file) != {'file_id', 'logical_path', 'version', 'size', 'sha256'} or file['file_id'] not in files:
                    raise ValueError()
                if file != {k: files[file['file_id']][k] for k in file}:
                    raise ValueError()
        for job_id, job in backup['jobs'].items():
            identifier(job_id)
            if set(job) != {'kind', 'state', 'snapshot_id', 'source_file_id', 'target_version', 'target_file_id',
                            'copies', 'cursor', 'proofs', 'attempts', 'next_attempt_at', 'run_token', 'lease_until',
                            'last_error', 'created_at', 'updated_at'}:
                raise ValueError()
            if job['kind'] not in ('BACKUP', 'RESTORE') or job['state'] not in ('PENDING', 'RUNNING', 'RETRY', 'COMPLETED', 'FAILED'):
                raise ValueError()
            integer(job['copies'], 1, 3); integer(job['attempts'], 0, 1000000)
            integer(job['cursor'], 0, 256)
            for field in ('next_attempt_at', 'created_at', 'updated_at'):
                integer(job[field])
            if job['kind'] == 'BACKUP':
                if job['snapshot_id'] not in backup['snapshots'] or job['source_file_id'] is not None or job['target_version'] is not None:
                    raise ValueError()
                if job['cursor'] > len(backup['snapshots'][job['snapshot_id']]['files']):
                    raise ValueError()
            else:
                if job['source_file_id'] not in files or job['snapshot_id'] is not None:
                    raise ValueError()
                integer(job['target_version'], 1, 1000000)
            if job['target_file_id'] is not None and job['target_file_id'] not in files:
                raise ValueError()
            if job['state'] == 'RUNNING':
                identifier(job['run_token']); integer(job['lease_until'], 1)
            elif job['run_token'] is not None or job['lease_until'] is not None:
                raise ValueError()
            if job['last_error'] not in (None, 'controller_restart', 'lease_expired', 'backup_unavailable',
                                         'copies_pending', 'restore_unavailable'):
                raise ValueError()
            if not isinstance(job['proofs'], list) or len(job['proofs']) > 256:
                raise ValueError()
            for proof in job['proofs']:
                if set(proof) != {'file_id', 'sha256', 'size', 'domains', 'verified_at'} or proof['file_id'] not in files:
                    raise ValueError()
                content(proof['size'], proof['sha256']); integer(proof['verified_at'])
                if not isinstance(proof['domains'], list) or len(set(proof['domains'])) != len(proof['domains']) or not 1 <= len(proof['domains']) <= 3:
                    raise ValueError()
                if any(not isinstance(d, str) or not 1 <= len(d) <= 64 for d in proof['domains']):
                    raise ValueError()
                file = files[proof['file_id']]
                if (proof['size'], proof['sha256']) != (file['size'], file['sha256']):
                    raise ValueError()
            if job['kind'] == 'BACKUP':
                captured = backup['snapshots'][job['snapshot_id']]['files']
                if (job['cursor'] != len(job['proofs']) or
                        [p['file_id'] for p in job['proofs']] != [f['file_id'] for f in captured[:job['cursor']]] or
                        any(len(p['domains']) < job['copies'] for p in job['proofs']) or
                        job['state'] == 'COMPLETED' and job['cursor'] != len(captured)):
                    raise ValueError()
            elif job['state'] == 'COMPLETED':
                target = files.get(job['target_file_id'])
                source = files[job['source_file_id']]
                if (target is None or target['file_id'] == source['file_id'] or
                        target['version'] != job['target_version'] or
                        (target['logical_path'], target['size'], target['sha256']) !=
                        (source['logical_path'], source['size'], source['sha256']) or
                        len(job['proofs']) != 1 or job['proofs'][0]['file_id'] != target['file_id']):
                    raise ValueError()
        for snapshot_id, snapshot in backup['snapshots'].items():
            if snapshot['state'] == 'VERIFIED' and not any(j['kind'] == 'BACKUP' and
                    j['snapshot_id'] == snapshot_id and j['state'] == 'COMPLETED' for j in backup['jobs'].values()):
                raise ValueError()
        for schedule_id, row in backup['schedules'].items():
            identifier(schedule_id)
            if set(row) != {'interval_seconds', 'retention_seconds', 'copies', 'next_run_at', 'enabled', 'last_error'} or type(row['enabled']) is not bool:
                raise ValueError()
            if row['last_error'] not in (None, 'snapshot_unverified_head', 'backup_limit'):
                raise ValueError()
            integer(row['interval_seconds'], 60, 86400); integer(row['retention_seconds'], 60, 315360000)
            integer(row['copies'], 1, 3); integer(row['next_run_at'])
        for request_id, row in backup['requests'].items():
            key(request_id)
            if set(row) != {'intent', 'result'} or not isinstance(row['result'], dict):
                raise ValueError()
            content(0, row['intent'])
        return backup
    except (ValueError, KeyError, TypeError, AttributeError):
        raise CatalogError('invalid_backup_projection', 409) from None


def takeover(backup):
    result = copy.deepcopy(backup)
    for job in result['jobs'].values():
        if job['state'] in ('PENDING', 'RUNNING', 'RETRY'):
            job.update(state='RETRY', run_token=None, lease_until=None, next_attempt_at=0,
                       cursor=0, proofs=[], last_error='controller_restart')
    return result
