"""Bounded read projections over the canonical Catalog, never a filesystem browser."""
import time
from ...catalog.common import identifier, logical_path

PAGE = 50


def offset(value):
    if type(value) is not int or not 0 <= value <= 10000:
        raise ValueError('invalid offset')
    return value


class Files:
    def __init__(self, views):
        self.views, self.service = views, views.service

    def query(self, obj):
        fields = {'browse_api_version', 'offset', 'search', 'folder', 'recursive', 'sort', 'versions'}
        if type(obj) is not dict or set(obj) - {'history_file_id'} != fields:
            raise ValueError('invalid file query')
        if (type(obj['browse_api_version']) is not int or obj['browse_api_version'] != 1
                or type(obj['search']) is not str or len(obj['search']) > 128
                or any(ord(c) < 32 for c in obj['search']) or type(obj['folder']) is not str
                or type(obj['recursive']) is not bool or obj['sort'] not in ('name', 'newest', 'size')
                or obj['versions'] not in ('all', 'latest')):
            raise ValueError('invalid file query')
        start = offset(obj['offset']); folder = obj['folder']
        if folder:
            logical_path(folder)
        history = obj.get('history_file_id')
        if history is not None:
            identifier(history)
        prefix = folder + '/' if folder else ''
        # Parameterized predicates, Unicode literal substring search (not SQL LIKE
        # wildcards), and logical folder components; no request-derived disk path.
        with self.service.registry.connect() as db:
            db.execute('BEGIN')
            db.create_function('asc_casefold', 1, str.casefold, deterministic=True)
            where = 'substr(f.logical_path,1,?)=? AND instr(asc_casefold(f.logical_path),?)>0'
            args = [len(prefix), prefix, obj['search'].casefold()]
            if history is not None:
                row = db.execute('SELECT logical_path FROM catalog_files WHERE file_id=?', (history,)).fetchone()
                if row is None:
                    from ...catalog.common import CatalogError
                    raise CatalogError('file_not_found', 404)
                where, args = 'f.logical_path=?', [row[0]]
            elif obj['versions'] == 'latest':
                where += ' AND NOT EXISTS(SELECT 1 FROM catalog_files newer WHERE newer.logical_path=f.logical_path AND newer.version>f.version)'
            folders = not obj['recursive'] and not obj['search'] and history is None
            source = ('WITH selected AS (SELECT f.*,substr(f.logical_path,?) tail FROM catalog_files f WHERE ' + where + '), '
                      'entries AS (SELECT \'file\' kind,file_id,logical_path name,size,created_at,version FROM selected ')
            if folders:
                source += ("WHERE instr(tail,'/')=0 UNION ALL SELECT 'folder',NULL,"
                           "?||substr(tail,1,instr(tail,'/')-1),NULL,MAX(created_at),NULL FROM selected "
                           "WHERE instr(tail,'/')>0 GROUP BY substr(tail,1,instr(tail,'/')-1)) ")
            else:
                source += ') '
            params = [len(prefix)+1, *args] + ([prefix] if folders else [])
            order = ('kind DESC,name COLLATE NOCASE,version DESC,file_id' if obj['sort'] == 'name' else
                     'kind DESC,created_at DESC,name,version DESC,file_id' if obj['sort'] == 'newest' else
                     'kind DESC,size DESC,name,version DESC,file_id')
            total = db.execute(source + 'SELECT COUNT(*) FROM entries', params).fetchone()[0]
            rows = db.execute(source + 'SELECT * FROM entries ORDER BY ' + order + ' LIMIT ? OFFSET ?',
                              [*params, PAGE+1, start]).fetchall()
            state = dict(db.execute('SELECT epoch,revision,head_digest FROM catalog_state').fetchone())
        nodes = self.views._nodes()
        entries = [dict(kind='folder', logical_path=r['name']) if r['kind'] == 'folder' else
                   dict(kind='file', **self.views.file(r['file_id'], nodes)) for r in rows[:PAGE]]
        more = len(rows) > PAGE
        return dict(browse_api_version=1, entries=entries, total=total, offset=start,
                    next_offset=start+PAGE if more and start+PAGE <= 10000 else None,
                    query_limit_reached=more and start+PAGE > 10000, page_size=PAGE,
                    metadata_point=state, as_of=int(time.time()),
                    note='Metadata listing point only; availability is observed separately, not writer authority.')


JOB_FIELDS = ('job_id', 'file_id', 'replica_id', 'kind', 'state', 'target_node_id',
              'target_volume_id', 'attempts', 'next_attempt_at', 'created_at', 'updated_at')
JOB_ERRORS = {'job_timeout', 'no_verified_source', 'stale_job_lease', 'node_credential_changed',
              'replica_missing', 'replica_corrupt', 'replica_metadata_mismatch', 'source_checksum_mismatch',
              'transfer_unavailable', 'controller_restart', 'owner_retry'}


def public_job(row):
    return {**{k: row.get(k) for k in JOB_FIELDS},
            'last_error': row.get('last_error') if row.get('last_error') in JOB_ERRORS else
            'transfer_unavailable' if row.get('last_error') else None,
            'retryable': row.get('state') in ('FAILED', 'RETRY') and not row.get('archived', False)}
