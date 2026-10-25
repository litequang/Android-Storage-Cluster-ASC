"""Offline existing-Engine qualification; NOT Node runtime/enrollment or a new Engine."""
import hashlib
import io
import json
from pathlib import Path
from asc.storage.engine import StorageEngine
from asc.storage.errors import StorageError


def info():
    import ssl, sqlite3, sys
    return json.dumps({'python':sys.version.split()[0],'ssl':ssl.OPENSSL_VERSION,
        'sqlite':sqlite3.sqlite_version,'implementation':StorageEngine.__module__,
        'node_runtime_supported':False,'writer_authority':False})


def self_test(root):
    # Called only by Android instrumentation with a NEW target-app-private root.
    # Fixed synthetic ID is NOT network Node identity. No server/CLI/device guard
    # monkeypatch, certificate generation, token, enrollment or physical deletion.
    root=Path(root)
    if not root.is_absolute() or root.is_symlink():raise ValueError('unsafe_test_root')
    root.mkdir(mode=0o700,parents=False,exist_ok=False)
    data=b'ASC existing Android Engine qualification\0'*4096
    sha=hashlib.sha256(data).hexdigest()
    with StorageEngine(root/'manifest','android-qualification-only') as engine:
        volume=engine.volumes.register(root/'data',quota=4*1024**2,reserve=0)['volume_id']
        row=engine.initiate('qualification',volume,'android_qualification_1','qualification/file.bin',len(data),sha)
        engine.upload(row['session_id'],'qualification',volume,io.BytesIO(data),len(data))
        saved=engine.commit(row['session_id'],'qualification',volume)
        capabilities=engine.capabilities()
    with StorageEngine(root/'manifest','android-qualification-only') as engine:
        with engine.download(saved['file_id'],volume) as (metadata,stream):
            actual=hashlib.sha256(stream.read()).hexdigest()
        if actual!=sha or metadata['sha256']!=sha:raise ValueError('checksum_mismatch')
        if engine.verify(saved['file_id'],volume)['state']!='COMMITTED':raise ValueError('verify_failed')
        rows=engine.manifest.connect()
        with rows as db:
            assert db.execute('SELECT COUNT(*) FROM files').fetchone()[0]==1
    return json.dumps({'state':'LOCAL_ENGINE_SELF_TEST_PASS','sha256':sha,'bytes':len(data),
        'restart_sha_match':True,'capabilities':capabilities,'node_runtime_supported':False,
        'network_enrolled':False,'writer_authority':False})

# App-private capability volume only, never a joined Node/approved cluster replica.
def _approved(root, app_id):
    import os
    from asc.bridge.contract import decode
    from asc.catalog.common import identifier
    from asc.storage.volumes import no_links
    identifier(app_id);root=Path(root);no_links(root)
    cfg=decode((root/'probe-approved.json').read_bytes())
    if (set(cfg)!={'format','app_id','volume_id','quota','reserve','root_device','root_inode'} or
            type(cfg['format']) is not int or cfg['format']!=1 or cfg['app_id']!=app_id or
            type(cfg['quota']) is not int or cfg['quota']<1 or type(cfg['reserve']) is not int or cfg['reserve']<0 or
            [root.stat().st_dev,root.stat().st_ino]!=[cfg['root_device'],cfg['root_inode']] or
            not (root/'manifest/manifest.sqlite3').is_file()):raise ValueError('probe_state_incompatible')
    identifier(cfg['volume_id']);return root,cfg


def approve_probe(root, app_id, quota, reserve):
    from asc.catalog.common import identifier
    from asc.identity import save_private
    from asc.storage.volumes import no_links
    identifier(app_id)
    if type(quota) is not int or type(reserve) is not int or not 1<=quota<=2**40 or not 0<=reserve<=2**40:raise ValueError('invalid_budget')
    root=Path(root);no_links(root)
    if root.exists():
        _,cfg=_approved(root,app_id)
        if (cfg['quota'],cfg['reserve'])!=(quota,reserve):raise ValueError('probe_configuration_conflict')
        return json.dumps({'volume_id':cfg['volume_id'],'scope':'APP_PRIVATE_PROBE_ONLY','cluster_storage_approved':None})
    root.mkdir(mode=0o700)
    with StorageEngine(root/'manifest','app-probe-'+app_id) as engine:
        record=engine.volumes.register(root/'data',kind='internal',quota=quota,reserve=reserve)
        cfg={'format':1,'app_id':app_id,'volume_id':record['volume_id'],'quota':quota,'reserve':reserve,
            'root_device':root.stat().st_dev,'root_inode':root.stat().st_ino}
        save_private(root/'probe-approved.json',cfg)
    return json.dumps({'volume_id':cfg['volume_id'],'scope':'APP_PRIVATE_PROBE_ONLY','cluster_storage_approved':None})


def probe(root, app_id):
    import time
    try:
        root,cfg=_approved(root,app_id)
        with StorageEngine(root/'manifest','app-probe-'+app_id) as engine:
            volume=engine.volumes.get(cfg['volume_id']);volume.check()
            if (volume.record['quota'],volume.record['reserve'])!=(cfg['quota'],cfg['reserve']):raise ValueError('probe_configuration_conflict')
            if engine._quota_usage(volume)+128>cfg['quota']:raise StorageError('quota_exceeded',507)
            engine._space(volume,128)
            report=engine.volumes.inspect(probe=True,volume_id=cfg['volume_id'])[0]
            report.pop('node_id',None)
        return json.dumps({'scope':'APP_PRIVATE_PROBE_ONLY','volume':report,'cluster_storage_approved':None,'writer_authority':False})
    except (OSError,StorageError,ValueError,KeyError):
        # Keep detailed failures private; never infer writable/zero/free capacity.
        return json.dumps({'scope':'APP_PRIVATE_PROBE_ONLY','state':'DEGRADED','error':'private_probe_refused',
            'writable':None,'fsync_tested':None,'available_bytes':None,'writer_authority':False})


def volume_status(root, app_id):
    try:
        from asc.demo.state import read_db
        from asc.storage.volumes import LocalVolume
        root,cfg=_approved(root,app_id)
        def row(db):
            db.row_factory=__import__('sqlite3').Row
            r=db.execute('SELECT * FROM volumes WHERE volume_id=?',(cfg['volume_id'],)).fetchone()
            if r is None:raise ValueError('volume_missing')
            return dict(r)
        record=read_db(root/'manifest/manifest.sqlite3',1,row)
        if (record['node_id']!='app-probe-'+app_id or (record['quota'],record['reserve'])!=(cfg['quota'],cfg['reserve'])):raise ValueError('binding_changed')
        volume=LocalVolume(record);volume.check();space=volume.disk_usage()
        return json.dumps({'scope':'APP_PRIVATE_PROBE_ONLY','volume':{
            'volume_id':cfg['volume_id'],'kind':'internal','quota':cfg['quota'],'reserve':cfg['reserve'],
            'free_bytes':space.free,'total_bytes':space.total,'readable':True,'writable':None,'fsync_tested':None,
            'state':'online'},'cluster_storage_approved':None,'writer_authority':False})
    except (OSError,StorageError,ValueError,KeyError):
        return json.dumps({'scope':'APP_PRIVATE_PROBE_ONLY','state':'UNKNOWN','volumes':[],
            'writable':None,'fsync_tested':None,'available_bytes':None,'writer_authority':False})
