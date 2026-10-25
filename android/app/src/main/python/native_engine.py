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
