"""Private FULL SQLite GC journal; known intents only, immutable object identity."""
from contextlib import closing
import json
import sqlite3

from ..catalog.common import canonical, digest
from ..storage.errors import StorageError
from ..storage.volumes import no_links


class Journal:
    def __init__(self,path,binding):
        self.path=path
        self.binding=digest(binding)
        no_links(path)
        if path.exists() and path.stat().st_nlink!=1:raise StorageError('gc_journal_quarantined',409)
        try:
            with closing(sqlite3.connect(path,timeout=15)) as db,db:
                db.execute('PRAGMA synchronous=FULL')
                db.execute('BEGIN IMMEDIATE')
                version=db.execute('PRAGMA user_version').fetchone()[0]
                if version not in (0,1):raise StorageError('gc_journal_quarantined',409)
                db.execute('CREATE TABLE IF NOT EXISTS settings(binding TEXT NOT NULL)')
                rows=db.execute('SELECT binding FROM settings').fetchall()
                if rows and rows!=[(self.binding,)]:raise StorageError('gc_journal_quarantined',409)
                if not rows:db.execute('INSERT INTO settings VALUES(?)',(self.binding,))
                db.execute('CREATE TABLE IF NOT EXISTS entries(job_id TEXT PRIMARY KEY,identity BLOB NOT NULL,sha256 TEXT NOT NULL,phase TEXT NOT NULL)')
                db.execute('PRAGMA user_version=1')
        except sqlite3.Error:raise StorageError('gc_journal_quarantined',409) from None

    def get(self,job_id):
        no_links(self.path)
        if self.path.exists() and self.path.stat().st_nlink!=1:raise StorageError('gc_journal_quarantined',409)
        try:
            with closing(sqlite3.connect(self.path,timeout=15)) as db:
                if db.execute('PRAGMA user_version').fetchone()[0]!=1 or db.execute('SELECT binding FROM settings').fetchall()!=[(self.binding,)]:
                    raise StorageError('gc_journal_quarantined',409)
                row=db.execute('SELECT identity,sha256,phase FROM entries WHERE job_id=?',(job_id,)).fetchone()
            if row is None:return None
            identity=json.loads(row[0])
            if digest(identity)!=row[1] or canonical(identity)!=row[0] or row[2] not in ('PREPARED','DELETING','DONE'):
                raise StorageError('gc_journal_quarantined',409)
            return {'identity':identity,'phase':row[2]}
        except (sqlite3.Error,ValueError,TypeError):raise StorageError('gc_journal_quarantined',409) from None

    def put(self,job_id,identity,phase):
        old=self.get(job_id)
        phases={'PREPARED':0,'DELETING':1,'DONE':2}
        if phase not in phases or old and (old['identity']!=identity or phases[phase]<phases[old['phase']]):
            raise StorageError('gc_journal_conflict',409)
        try:
            with closing(sqlite3.connect(self.path,timeout=15)) as db,db:
                db.execute('PRAGMA synchronous=FULL');db.execute('BEGIN IMMEDIATE')
                if old is None and db.execute('SELECT COUNT(*) FROM entries').fetchone()[0]>=256:
                    raise StorageError('gc_journal_limit',409)
                db.execute('INSERT OR REPLACE INTO entries VALUES(?,?,?,?)',(job_id,canonical(identity),digest(identity),phase))
        except sqlite3.Error:raise StorageError('gc_journal_quarantined',409) from None
