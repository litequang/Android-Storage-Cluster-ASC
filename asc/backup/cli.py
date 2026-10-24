"""Explicit owner CLI; persistent request IDs allow safe retries after lost replies."""
from urllib.parse import quote


def register(parser, handlers, client, cli):
    def execute(args):
        action = args.action.removeprefix('backup-')
        api = client()
        if action in ('status', 'snapshots', 'jobs', 'schedules', 'trash'):
            result = api.request('GET', 'backup/'+action)
        elif action == 'history':
            result = api.request('GET', 'backup/history?logical_path='+quote(args.logical_path, safe=''))
        else:
            obj = {'request_id': args.request_id}
            path = {'snapshot': 'snapshots', 'policy': 'policies', 'run-retention': 'retention/run',
                    'schedule': 'schedules'}.get(action, action)
            if action in ('restore', 'delete'):
                obj['file_id'] = args.file_id
                if action == 'restore' and args.snapshot_id:
                    obj['snapshot_id'] = args.snapshot_id
            if action in ('snapshot', 'schedule'):
                obj.update(copies=args.copies, retention_seconds=args.retention_seconds)
            if action == 'schedule':
                obj['interval_seconds'] = args.interval_seconds
            if action == 'policy':
                obj.update(logical_path=args.logical_path, keep_last=args.keep_last,
                           max_age_seconds=args.max_age_seconds, trash_seconds=args.trash_seconds)
            if action == 'retry-job':
                path = 'jobs/'+args.job_id+'/retry'
            if action == 'restore-snapshot':
                path = 'snapshots/'+args.snapshot_id+'/restore'
            result = api.request('POST', 'backup/'+path, obj)
        cli._show(result)

    for command in ('status', 'snapshots', 'jobs', 'schedules', 'trash', 'history', 'enable', 'snapshot',
                    'restore', 'delete', 'policy', 'run-retention', 'schedule', 'retry-job', 'restore-snapshot'):
        name = 'backup-'+command
        a = parser.add_parser(name)
        if command not in ('status', 'snapshots', 'jobs', 'schedules', 'trash', 'history'):
            a.add_argument('--request-id', required=True)
        if command in ('history', 'policy'):
            a.add_argument('logical_path')
        if command in ('restore', 'delete'):
            a.add_argument('file_id')
        if command == 'restore':
            a.add_argument('--snapshot-id')
        if command == 'restore-snapshot':
            a.add_argument('snapshot_id')
        if command in ('snapshot', 'schedule'):
            a.add_argument('--copies', type=int, choices=(1, 2, 3), default=2)
            a.add_argument('--retention-seconds', type=int, default=604800)
        if command == 'schedule':
            a.add_argument('--interval-seconds', type=int, required=True)
        if command == 'policy':
            a.add_argument('--keep-last', type=int, required=True)
            a.add_argument('--max-age-seconds', type=int, required=True)
            a.add_argument('--trash-seconds', type=int, required=True)
        if command == 'retry-job':
            a.add_argument('job_id')
        handlers[name] = execute
