"""Linux x86 isolated-test executor. Ordinary Engine/Agent has no instance of it."""
import os
import stat
import time

from .arena import NodeTestVolume,fixture_node_capability
from .journal import Journal
from ..catalog.common import content,digest,identifier,key
from ..storage.errors import StorageError
from ..storage.volumes import no_links

IDENTITY_FIELDS={'gc_job_id','retired_replica_id','node_id','volume_id','local_file_id','file_id',
                 'logical_path','size','sha256','cluster_id','epoch','plan_sha256'}
CONTRACT_FIELDS=IDENTITY_FIELDS|{'kind','permit_term','run_id','permit_expires_at'}


class Executor:
    def __init__(self,engine,capability):
        if type(capability) is not NodeTestVolume:raise StorageError('physical_gc_locked',403)
        self.engine,self.capability=engine,capability
        capability.validate(engine)
        self.journal=Journal(engine.home/('gc-journal-'+capability.record['volume_id']+'.sqlite3'),capability.binding)
        self.fault_hook=None

    def _hook(self,point):
        if self.fault_hook:self.fault_hook(point)

    def _contract(self,contract):
        if (not isinstance(contract,dict) or set(contract)!=CONTRACT_FIELDS or contract['kind']!='gc' or
                contract['node_id']!=self.engine.node_id or contract['volume_id']!=self.capability.record['volume_id']):
            raise StorageError('invalid_gc_authorization',403)
        for field in ('gc_job_id','retired_replica_id','volume_id','local_file_id','file_id','cluster_id','epoch','run_id'):identifier(contract[field])
        content(contract['size'],contract['sha256']);content(0,contract['plan_sha256'])
        if (type(contract['permit_term']) is not int or contract['permit_term']<1 or
                type(contract['permit_expires_at']) is not int or not int(time.time())<contract['permit_expires_at'] or
                contract['logical_path']!='_asc-global/'+contract['file_id']+'/'+contract['retired_replica_id']):
            raise StorageError('invalid_gc_authorization',403)
        return {k:contract[k] for k in IDENTITY_FIELDS}|{'arena_sha256':digest(self.capability.binding)}

    def _authorize(self,contract,authorize):
        if not callable(authorize):raise StorageError('gc_fresh_authorization_required',403)
        reply=authorize()
        if not isinstance(reply,dict) or reply.get('constraints')!=contract:
            raise StorageError('gc_fresh_authorization_required',403)
        proof=reply.get('authority',{})
        if (proof.get('term')!=contract['permit_term'] or type(proof.get('index')) is not int or proof['index']<1 or
                proof.get('cluster_id')!=contract['cluster_id'] or proof.get('epoch')!=contract['epoch']):
            raise StorageError('gc_fresh_authorization_required',403)
        key(proof.get('nonce'))
        if not int(time.time())<contract['permit_expires_at']:raise StorageError('invalid_gc_authorization',403)
        return time.monotonic()

    def _unlink(self,volume,stream,relative,contract,authorize):
        # Walk from filesystem anchor with no-follow descriptors and approved root identity.
        folder,name=volume._parts(relative)
        if folder!='objects':raise StorageError('invalid_gc_object',403)
        parent=os.open(volume.root.anchor,os.O_RDONLY|os.O_DIRECTORY)
        try:
            for part in volume.root.parts[1:]:
                child=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=parent)
                os.close(parent);parent=child
            root_info=os.fstat(parent)
            if f'{root_info.st_dev}:{root_info.st_ino}'!=volume.record['medium']:raise StorageError('volume_identity_changed',409)
            child=os.open('objects',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=parent)
            os.close(parent);parent=child
            original=os.fstat(stream.fileno())
            self._hook('before_final_authorize')
            received=self._authorize(contract,authorize)
            volume.check()
            directory=os.stat(volume.root/'objects',follow_symlinks=False)
            current=os.stat(name,dir_fd=parent,follow_symlinks=False)
            opened=os.fstat(stream.fileno());held_directory=os.fstat(parent)
            if ((directory.st_dev,directory.st_ino)!=(held_directory.st_dev,held_directory.st_ino) or
                    not stat.S_ISREG(current.st_mode) or current.st_nlink!=1 or
                    any(getattr(current,k)!=getattr(original,k) or getattr(opened,k)!=getattr(original,k)
                        for k in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns'))):
                raise StorageError('gc_object_identity_changed',409)
            if time.monotonic()-received>.25:raise StorageError('gc_authority_budget_expired',409)
            os.unlink(name,dir_fd=parent)
            os.fsync(parent)
            self._hook('after_unlink')
        finally:os.close(parent)

    def execute(self,contract,authorize):
        identity=self._contract(contract)
        with self.engine.transfer():
            volume=self.capability.validate(self.engine)
            previous=self.journal.get(contract['gc_job_id'])
            if previous and previous['identity']!=identity:raise StorageError('gc_journal_conflict',409)
            relative='objects/'+contract['local_file_id']+'.blob'
            no_links(volume.root/relative)
            unlinked=False
            if previous and previous['phase']=='DONE':
                try:
                    with volume.open(relative):raise StorageError('gc_deleted_object_reappeared',409)
                except FileNotFoundError:pass
                self._authorize(contract,authorize)
                return self._result(contract,False)
            with self.engine.manifest.connect() as db:
                row=db.execute('SELECT * FROM files WHERE file_id=?',(contract['local_file_id'],)).fetchone()
            if row is not None:
                row=self.engine.file(contract['local_file_id'],contract['volume_id'])
                if (row['logical_path'],row['size'],row['sha256'],row['relative_path'])!=(
                        contract['logical_path'],contract['size'],contract['sha256'],relative):
                    raise StorageError('gc_manifest_changed',409)
            elif not previous or previous['phase']!='DELETING':raise StorageError('gc_manifest_not_proven',409)
            if previous is None:
                self.journal.put(contract['gc_job_id'],identity,'PREPARED')
                self._hook('after_journal_prepare')
            try:
                with volume.open(relative) as stream:
                    if row is None:raise StorageError('gc_manifest_changed',409)
                    size,sha=self.engine._hash(stream)
                    if (size,sha)!=(contract['size'],contract['sha256']):raise StorageError('gc_checksum_mismatch',422)
                    self.journal.put(contract['gc_job_id'],identity,'DELETING')
                    self._hook('after_delete_intent')
                    self._unlink(volume,stream,relative,contract,authorize);unlinked=True
            except FileNotFoundError:
                self.capability.validate(self.engine)
                try:
                    with volume.open(relative):raise StorageError('gc_object_identity_changed',409)
                except FileNotFoundError:pass
                current=self.journal.get(contract['gc_job_id'])
                if not current or current['phase']!='DELETING':raise StorageError('gc_unknown_absence',409)
                self._authorize(contract,authorize)
                volume.sync_directory('objects')
            with self.engine.manifest.connect() as db:
                db.execute('DELETE FROM files WHERE file_id=? AND volume_id=?',(contract['local_file_id'],contract['volume_id']))
            self._hook('after_manifest_update')
            self.journal.put(contract['gc_job_id'],identity,'DONE')
            self._hook('after_journal_done')
            return self._result(contract,unlinked)

    @staticmethod
    def _result(contract,unlinked):
        return {k:contract[k] for k in ('gc_job_id','node_id','volume_id','local_file_id','size','sha256')}|{
            'state':'DONE','physical_deletions':1,'unlinked_now':unlinked,
            'logical_bytes_removed_now':contract['size'] if unlinked else 0,'replayed':not unlinked}


def fixture_executor(engine,volume_id):
    return Executor(engine,fixture_node_capability(engine,volume_id))
