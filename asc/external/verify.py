"""Anchored point-in-time verification and non-destructive external inventory."""
import time
from .engine import load, check_all, complete_receipt
from .format import decode, fail, integer, sha
from ..catalog.common import CatalogError, digest, identifier, now


def verify_tree(tree, backup_id, expected_sha256, minimum_index=0, cluster_id=None):
    manifest,metadata,doc=load(tree)
    if manifest['backup_id']!=backup_id:fail('external_snapshot_mismatch')
    if digest(manifest)!=expected_sha256:fail('external_manifest_anchor_mismatch')
    if cluster_id is not None and manifest['cluster_id']!=cluster_id:fail('external_source_identity_mismatch')
    if tree.names()!=['complete.json','manifest.json','metadata.json','objects']:
        fail('external_incomplete')
    if decode(tree.read('complete.json',4096),4096)!=complete_receipt(manifest):fail('external_completion_mismatch')
    check_all(tree,manifest)
    return manifest,metadata,doc


def verify(store,backup_id,expected_sha256,minimum_index=0,cluster_id=None):
    identifier(backup_id);sha(expected_sha256);integer(minimum_index)
    started=time.monotonic();stamp=now()
    result={'backup_id':backup_id,'state':'UNKNOWN','verified_at':None,
        'checked_at':stamp,'integrity_verified':False,'objects':None,'bytes':None,
        'writer_recovery_supported':False,'latest_history_proven':False}
    try:
        with store.open() as root, root.sub('completed') as done:
            if not done.exists(backup_id):
                with root.sub('working') as working:
                    if working.exists(backup_id):return {**result,'state':'INCOMPLETE','error':'external_incomplete'}
                return {**result,'error':'external_backup_not_found'}
            with done.sub(backup_id) as tree:
                manifest,_,doc=verify_tree(tree,backup_id,expected_sha256,minimum_index,cluster_id)
        result.update(state='STALE' if manifest['source_index']<minimum_index else 'VERIFIED',
            integrity_verified=True,verified_at=now(),manifest_sha256=expected_sha256,
            source_index=manifest['source_index'],source_term=manifest['source_term'],
            captured_at=manifest['created_at'],cluster_id=manifest['cluster_id'],
            objects=len(manifest['files']),bytes=sum(f['size'] for f in manifest['files']),
            coverage='all-catalog-versions',minimum_index=minimum_index,
            freshness='older-than-known-history' if manifest['source_index']<minimum_index else 'at-or-above-operator-floor',
            historical_lifecycle_counts={s:sum(doc.get('backup',{}).get('files',{}).get(f['file_id'],{}).get('state','LIVE')==s
                for f in manifest['files']) for s in ('LIVE','TRASH','EXPIRED')})
    except FileNotFoundError:
        result.update(state='CORRUPT',error='external_required_file_missing')
    except CatalogError as exc:
        unknown=exc.status in (403,429,503) or exc.code in ('external_directory_changed','external_file_changed')
        result.update(state='UNKNOWN' if unknown else 'CORRUPT',error=exc.code)
    except OSError:
        result.update(state='UNKNOWN',error='external_io_unavailable')
    result['elapsed_seconds']=round(time.monotonic()-started,3)
    return result


def inventory(store):
    """Never labels unanchored manifest self-hashes VERIFIED."""
    entries=[]
    try:
        with store.open() as root:
            for folder,default in (('working','INCOMPLETE'),('completed','COMPLETE_UNVERIFIED')):
                with root.sub(folder) as directory:
                    for name in directory.names():
                        try:
                            identifier(name)
                            with directory.sub(name) as tree:
                                manifest,_,_=load(tree)
                                if manifest['backup_id']!=name:fail('external_snapshot_mismatch')
                                if folder=='completed' and decode(tree.read('complete.json',4096),4096)!=complete_receipt(manifest):fail()
                                entries.append({'backup_id':name,'state':default,'manifest_sha256':digest(manifest),
                                    'captured_at':manifest['created_at'],'source_index':manifest['source_index'],
                                    'objects_expected':len(manifest['files']),'trusted_anchor':False})
                        except (OSError,CatalogError):entries.append({'backup_id':name,'state':'UNKNOWN','trusted_anchor':False})
        return {'state':'LISTED','backups':entries,'count':len(entries),'writer_recovery_supported':False}
    except (OSError,CatalogError):
        return {'state':'UNKNOWN','backups':None,'count':None,'error':'external_store_unavailable'}


def retention_preview(store):
    report=inventory(store)
    return {'dry_run':True,'deletion_supported':False,'physical_deletions':0,
        'candidates':[],'holds':None if report['backups'] is None else
        [{'backup_id':b['backup_id'],'state':b['state'],'reason':'external_retention_locked'} for b in report['backups']],
        'state':report['state'],'last_valid_backup_protection':True}
