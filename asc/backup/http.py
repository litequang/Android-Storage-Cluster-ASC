"""Owner-only Phase 3A routes; invoked inside Runtime's existing quorum/term gate."""
from .. import validation as valid


def handle(handler, parts, query):
    backups = handler.server.catalog.backups
    if handler.command == 'GET':
        if parts == ['history']:
            if set(query) != {'logical_path'}:
                raise ValueError()
            result = backups.inspect('history', query['logical_path'][0])
        else:
            if query or len(parts) != 1 or parts[0] not in ('status', 'snapshots', 'jobs', 'schedules', 'policies', 'trash'):
                raise ValueError()
            result = backups.inspect(parts[0])
        return handler._json(200, result)
    if query:
        raise ValueError()
    obj = handler._read_json()
    if parts == ['enable']:
        valid.payload(obj, ('request_id',)); result = backups.enable(obj)
    elif parts == ['snapshots']:
        valid.payload(obj, ('request_id',), ('copies', 'retention_seconds')); result = backups.snapshot(obj)
    elif parts == ['restore']:
        valid.payload(obj, ('request_id', 'file_id'), ('snapshot_id',)); result = backups.restore(obj)
    elif parts == ['delete']:
        valid.payload(obj, ('request_id', 'file_id')); result = backups.delete(obj)
    elif parts == ['policies']:
        valid.payload(obj, ('request_id', 'logical_path', 'keep_last', 'max_age_seconds', 'trash_seconds')); result = backups.policy(obj)
    elif parts == ['retention', 'run']:
        valid.payload(obj, ('request_id',)); result = backups.retention(obj)
    elif parts == ['schedules']:
        valid.payload(obj, ('request_id', 'interval_seconds'), ('retention_seconds', 'copies')); result = backups.schedule(obj)
    elif parts == ['jobs', 'run']:
        valid.payload(obj, (), ('job_id',))
        if 'job_id' in obj:
            from ..catalog.common import identifier
            identifier(obj['job_id'])
        result = backups.tick(obj.get('job_id')) or {'idle': True}
    elif len(parts) == 3 and parts[0] == 'jobs' and parts[2] == 'retry':
        valid.payload(obj, ('request_id',)); result = backups.retry(parts[1], obj)
    elif len(parts) == 2 and parts[0] == 'schedules':
        valid.payload(obj, ('request_id', 'enabled')); result = backups.configure_schedule(parts[1], obj)
    elif len(parts) == 3 and parts[0] == 'snapshots' and parts[2] == 'restore':
        valid.payload(obj, ('request_id',)); result = backups.restore_snapshot(parts[1], obj)
    else:
        return handler._json(404, {'error': 'not_found'})
    return handler._json(200, result)
