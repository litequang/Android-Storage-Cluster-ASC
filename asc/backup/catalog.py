"""Live namespace view over immutable Catalog versions; history remains retained."""
import json

from ..catalog.common import CatalogError
from ..catalog.state import Catalog
from .state import heads, status


class VersionedCatalog(Catalog):
    def file(self, file_id):
        result = super().file(file_id)
        with self.registry.connect() as db:
            row = db.execute("SELECT value FROM settings WHERE key='phase3a_backup'").fetchone()
        if row:
            result['version_state'] = status(json.loads(row[0]), file_id)
        return result

    def files(self, offset=0):
        if type(offset) is not int or not 0 <= offset <= 10000:
            raise CatalogError('invalid_offset', 400)
        with self.registry.connect() as db:
            row = db.execute("SELECT value FROM settings WHERE key='phase3a_backup'").fetchone()
            if row:
                backup = json.loads(row[0])
                files = [dict(f) for f in db.execute('SELECT * FROM catalog_files')]
        if not row:
            return super().files(offset)
        live = [f for f in heads({'files': files}) if status(backup, f['file_id']) == 'LIVE']
        ids = [f['file_id'] for f in live[offset:offset+51]]
        return {'files': [self.file(i) for i in ids[:50]], 'next_offset': offset+50 if len(ids)>50 else None}
