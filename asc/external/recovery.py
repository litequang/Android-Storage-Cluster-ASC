"""Passive recovery data staging. No registry/log import or writer activation."""
import hashlib
import os
import time
from contextlib import contextmanager
from .local import Tree, separate
from .engine import check_body, check_all, load
from .verify import verify_tree
from .format import MAX_MANIFEST, MAX_METADATA, decode, fail, integer, sha
from ..catalog.common import canonical, digest, identifier


def write_exact(tree,name,raw):
    if tree.exists(name):
        if tree.read(name,len(raw))!=raw:fail('external_recovery_intent_conflict')
    else:tree.write_new(name,raw)


@contextmanager
def stage_owner(root):
    if not root.exists('RECOVERY_READ_ONLY.json') and set(root.names())-{'owner.lock'}:
        fail('external_recovery_destination_not_empty')
    try:root.write_new('owner.lock',b'')
    except FileExistsError:pass
    with root.file('owner.lock',os.O_RDWR) as lock:
        import fcntl
        try:fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:fail('external_recovery_busy',429)
        try:yield
        finally:fcntl.flock(lock.fileno(),fcntl.LOCK_UN)


def ready_receipt(intent,manifest):
    return {'format':1,'state':'VERIFIED_RECOVERY_STAGING','intent_sha256':digest(intent),
        'manifest_sha256':digest(manifest),'objects':len(manifest['files']),
        'bytes':sum(f['size'] for f in manifest['files']),'writer_authority':False,
        'credentials_restored':False}


def verify_stage_tree(root,expected_sha256):
    intent=decode(root.read('RECOVERY_READ_ONLY.json',4096),4096)
    if (set(intent)!={'format','kind','backup_id','manifest_sha256','cluster_id','minimum_index','source_index',
        'writer_authority','credentials_restored'} or type(intent['format']) is not int or intent['format']!=1 or
        intent['kind']!='asc-recovery-read-only' or intent['writer_authority'] is not False or
        intent['credentials_restored'] is not False):fail('external_recovery_intent_conflict')
    manifest,metadata,doc=load(root)
    if (digest(manifest)!=sha(expected_sha256) or intent['manifest_sha256']!=expected_sha256 or
            intent['backup_id']!=manifest['backup_id'] or intent['cluster_id']!=manifest['cluster_id'] or
            intent['source_index']!=manifest['source_index'] or
            manifest['source_index']<integer(intent['minimum_index'])):fail('external_recovery_intent_conflict')
    check_all(root,manifest)
    if root.names()!=['READY.json','RECOVERY_READ_ONLY.json','manifest.json','metadata.json','objects','owner.lock']:
        fail('external_recovery_incomplete')
    expected=ready_receipt(intent,manifest)
    if decode(root.read('READY.json',4096),4096)!=expected:fail('external_recovery_incomplete')
    return expected


def verify_stage(destination,expected_sha256):
    with Tree(destination) as root, root.file('owner.lock') as lock:
        import fcntl
        try:fcntl.flock(lock.fileno(),fcntl.LOCK_SH|fcntl.LOCK_NB)
        except BlockingIOError:fail('external_recovery_busy',429)
        try:return verify_stage_tree(root,expected_sha256)
        finally:fcntl.flock(lock.fileno(),fcntl.LOCK_UN)


def stage(store,backup_id,expected_sha256,destination,source_roots,cluster_id,minimum_index):
    """Entire source validated BEFORE new destination mutation; fresh check at end."""
    identifier(backup_id);sha(expected_sha256);integer(minimum_index)
    separate(destination,source_roots)
    separate(destination,[store.path,*source_roots])
    started=time.monotonic()
    with store.open() as store_root, store_root.sub('completed') as done, done.sub(backup_id) as source:
        manifest,metadata,_=verify_tree(source,backup_id,expected_sha256,minimum_index,cluster_id)
        if manifest['source_index']<minimum_index:fail('external_backup_stale')
        if manifest['cluster_id']!=cluster_id:fail('external_source_identity_mismatch')
        intent={'format':1,'kind':'asc-recovery-read-only','backup_id':backup_id,
            'manifest_sha256':expected_sha256,'cluster_id':cluster_id,'minimum_index':minimum_index,
            'source_index':manifest['source_index'],'writer_authority':False,'credentials_restored':False}
        with Tree(destination) as root, stage_owner(root):
            if not root.exists('RECOVERY_READ_ONLY.json'):
                if root.names()!=['owner.lock']:fail('external_recovery_destination_not_empty')
            write_exact(root,'RECOVERY_READ_ONLY.json',canonical(intent))
            if root.exists('READY.json'):
                return {**verify_stage_tree(root,expected_sha256),'replayed':True}
            if set(root.names())-{'owner.lock','RECOVERY_READ_ONLY.json','manifest.json','metadata.json','objects'}:
                fail('external_recovery_destination_not_empty')
            write_exact(root,'manifest.json',canonical(manifest));write_exact(root,'metadata.json',metadata)
            with root.sub('objects',not root.exists('objects')) as objects, source.sub('objects') as originals:
                for file in manifest['files']:
                    final=file['file_id']+'.blob';part=file['file_id']+'.part'
                    if objects.exists(final):
                        if objects.exists(part):
                            check_body(objects,final,file,2);check_body(objects,part,file,2)
                            objects.finish_link(part,final)
                        check_body(objects,final,file);continue
                    with originals.file(final) as reader:
                        if objects.exists(part):
                            with objects.file(part) as old:
                                s=os.fstat(old.fileno());bound=(s.st_dev,s.st_ino)
                            objects.unlink_partial(part,bound)
                        count=0;checksum=hashlib.sha256()
                        with objects.file(part,os.O_CREAT|os.O_EXCL|os.O_RDWR) as output:
                            while chunk:=reader.read(65536):
                                count+=len(chunk)
                                if count>file['size']:fail('external_object_corrupt')
                                checksum.update(chunk);output.write(chunk)
                            if (count,checksum.hexdigest())!=(file['size'],file['sha256']):fail('external_object_corrupt')
                            output.flush();os.fsync(output.fileno())
                    check_body(objects,part,file);objects.publish(part,final)
            check_all(root,manifest)
            if root.read('metadata.json',MAX_METADATA)!=metadata or root.read('manifest.json',MAX_MANIFEST)!=canonical(manifest):
                fail('external_snapshot_mismatch')
            verify_tree(source,backup_id,expected_sha256,minimum_index,cluster_id)
            root.write_new('READY.json',canonical(ready_receipt(intent,manifest)))
            result=verify_stage_tree(root,expected_sha256)
            return {**result,'replayed':False,'elapsed_seconds':round(time.monotonic()-started,3)}
