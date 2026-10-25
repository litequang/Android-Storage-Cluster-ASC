"""Streaming external backup transaction, durable per-object resume and readback."""
import hashlib
import os
import time
from .format import MAX_MANIFEST, MAX_METADATA, capture, decode, fail, validate
from ..catalog.common import CatalogError, canonical, digest, identifier, now, uid
from ..client import ClientError


def check_body(tree, name, file, links=1):
    with tree.file(name,links=links) as stream:
        before=os.fstat(stream.fileno()); count=0;sha=hashlib.sha256()
        while chunk:=stream.read(65536):
            count+=len(chunk)
            if count>file['size']:fail('external_object_corrupt')
            sha.update(chunk)
        after=os.fstat(stream.fileno())
        if (count,sha.hexdigest())!=(file['size'],file['sha256']):fail('external_object_corrupt')
        if (before.st_size,before.st_mtime_ns,before.st_ctime_ns)!=(after.st_size,after.st_mtime_ns,after.st_ctime_ns):
            fail('external_file_changed')
    return count


def load(tree):
    raw=tree.read('manifest.json',MAX_MANIFEST)
    manifest=decode(raw,MAX_MANIFEST)
    metadata=tree.read('metadata.json',MAX_METADATA)
    doc=validate(manifest,metadata)
    return manifest,metadata,doc


def check_all(tree,manifest):
    with tree.sub('objects') as objects:
        for file in manifest['files']:
            check_body(objects,file['file_id']+'.blob',file)
        if objects.names()!=sorted(f['file_id']+'.blob' for f in manifest['files']):
            fail('external_unexpected_object')


def complete_receipt(manifest):
    return {'format':1,'state':'COMPLETE','manifest_sha256':digest(manifest),
            'objects':len(manifest['files']),'bytes':sum(f['size'] for f in manifest['files'])}


class BackupEngine:
    """Source: capture(), stream(file, capture), revalidate(capture).

    A source must independently enforce current authority. Captured metadata grants
    nothing; old completed objects are rehashed, never trusted through a journal.
    """
    def __init__(self,store):self.store=store

    def create(self,source,source_roots):
        with self.store.open(source_roots) as root:
            view=source.capture()
            backup_id=uid();manifest,metadata=capture(view,backup_id,now())
            with root.sub('working') as working, working.sub(backup_id,True) as job:
                job.write_new('metadata.json',metadata)
                job.write_new('manifest.json',canonical(manifest))
                with job.sub('objects',True):pass
        # Durable immutable capture exists before any object IO; expose ID before
        # attempting transfer so an interrupted operator can list/resume it.
        return self.resume(source,backup_id,source_roots)

    def resume(self,source,backup_id,source_roots):
        identifier(backup_id)
        started=time.monotonic()
        with self.store.open(source_roots) as root, root.sub('completed') as done, root.sub('working') as work:
            if done.exists(backup_id):
                with done.sub(backup_id) as job:
                    manifest,_,_=load(job);check_all(job,manifest)
                    if decode(job.read('complete.json',4096),4096)!=complete_receipt(manifest):fail()
                    os.fsync(done.fd);os.fsync(work.fd)
                    return self._result(manifest,started,True)
            with work.sub(backup_id) as job:
                manifest,_,_=load(job)
                if manifest['backup_id']!=backup_id:fail()
                with job.sub('objects') as objects:
                    for file in manifest['files']:
                        name=file['file_id']+'.blob';part=file['file_id']+'.part'
                        if objects.exists(name):
                            # A process can die between link and removal of its
                            # exact .part. Prove both names/hash, then finish only
                            # that owned temporary link. Never accept other links.
                            if objects.exists(part):
                                check_body(objects,name,file,2);check_body(objects,part,file,2)
                                objects.finish_link(part,name)
                            check_body(objects,name,file);continue
                        streams=(source.streams(file,manifest) if hasattr(source,'streams') else
                                 [lambda:source.stream(file,manifest)])
                        copied=False
                        for attempt in streams:
                            try:
                                with attempt() as reader:
                                    if objects.exists(part):
                                        with objects.file(part) as old:
                                            bound=os.fstat(old.fileno());expected=(bound.st_dev,bound.st_ino)
                                        objects.unlink_partial(part,expected)
                                    sha=hashlib.sha256();count=0
                                    with objects.file(part,os.O_RDWR|os.O_CREAT|os.O_EXCL) as output:
                                        while chunk:=reader.read(65536):
                                            count+=len(chunk)
                                            if count>file['size']:fail('external_source_mismatch')
                                            sha.update(chunk);output.write(chunk)
                                        if (count,sha.hexdigest())!=(file['size'],file['sha256']):fail('external_source_mismatch')
                                        output.flush();os.fsync(output.fileno())
                                check_body(objects,part,file)
                            except (ClientError,CatalogError,OSError,ValueError):
                                # Only unpublished transaction-owned .part may be
                                # retried on another source. No Catalog mutation.
                                if not hasattr(source,'streams'):raise
                                continue
                            objects.publish(part,name);copied=True;break
                        if not copied:fail('external_source_unavailable',503)

                # Re-read exact persisted metadata/manifest and every body; source
                # failures cannot publish COMPLETE. Existing COMPLETE is immutable.
                repeated,_,_=load(job)
                if repeated!=manifest:fail('external_snapshot_mismatch')
                check_all(job,manifest);source.revalidate(manifest)
                receipt=canonical(complete_receipt(manifest))
                if job.exists('complete.json'):
                    if job.read('complete.json',4096)!=receipt:fail()
                else:job.write_new('complete.json',receipt)
                job.check();work.check();done.check()
                if done.exists(backup_id):fail('external_backup_exists',409)
                os.rename(backup_id,backup_id,src_dir_fd=work.fd,dst_dir_fd=done.fd)
                # job path binding has intentionally moved; don't use old Tree.
                os.fsync(done.fd);os.fsync(work.fd);root.check()
            return self._result(manifest,started,False)

    @staticmethod
    def _result(manifest,started,replayed):
        return {'backup_id':manifest['backup_id'],'state':'COMPLETE',
            'manifest_sha256':digest(manifest),'source_index':manifest['source_index'],
            'objects':len(manifest['files']),'bytes':sum(f['size'] for f in manifest['files']),
            'elapsed_seconds':round(time.monotonic()-started,3),'replayed':replayed,
            'writer_recovery_supported':False}
