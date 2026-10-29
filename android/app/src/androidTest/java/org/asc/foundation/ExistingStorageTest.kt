package org.asc.foundation

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.chaquo.python.Python
import com.chaquo.python.PyObject
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.util.UUID

/** Real canonical Engine on Android; prior exact h.2a APK committed the fixture.
 * This is isolated app-private test storage, NOT an enrolled volume/replica. */
@RunWith(AndroidJUnit4::class)
class ExistingStorageTest {
    private fun scope():Pair<Python,PyObject> {
        val c=InstrumentationRegistry.getInstrumentation().targetContext
        EmbeddedEngine(c);val python=Python.getInstance();val scope=python.builtins.callAttr("dict")
        val proof=JSONObject(File(c.filesDir,"existing-engine-fixture.json").readText())
        check(proof.getInt("format")==1)
        check(proof.getString("source_apk_sha256")=="89a2c9a29a6b41e1d198519eb67e4b87aed91b2e32f3f0282914f367c1da54b4")
        check(proof.getString("root").matches(Regex("engine-qualification-[a-f0-9-]{36}")))
        scope.callAttr("__setitem__","root",File(c.filesDir.canonicalFile,proof.getString("root")).absolutePath)
        scope.callAttr("__setitem__","proof",python.getModule("json").callAttr("loads",proof.toString()))
        return python to scope
    }
    @Test fun exactPreviousApkBytesVolumeMarkerAndManifestIdentityRemainReadable() {
        val (p,s)=scope()
        p.builtins.callAttr("exec","""
from pathlib import Path
import hashlib
from asc.storage.engine import StorageEngine
from asc.storage.manifest import existing_identity
root=Path(root)
with StorageEngine(root/'manifest','android-qualification-only',existing_only=True,
                   manifest_identity=proof['manifest_identity']) as engine:
    assert engine.manifest.existing_only
    assert engine.volumes.get(proof['volume_id']).record['node_id']=='android-qualification-only'
    with engine.download(proof['file_id'],proof['volume_id']) as (metadata,stream):
        body=stream.read()
        assert len(body)==proof['bytes'] and hashlib.sha256(body).hexdigest()==proof['sha256']
        assert metadata['sha256']==proof['sha256']
    assert engine.verify(proof['file_id'],proof['volume_id'])['state']=='COMMITTED'
assert hashlib.sha256((root/'data/.asc-volume.json').read_bytes()).hexdigest()==proof['marker_sha256']
assert list(existing_identity(root/'manifest/manifest.sqlite3'))==proof['manifest_identity']
""".trimIndent(),s)
    }
    @Test fun missingOrEmptyMetadataCannotInitializeAnyDatabaseOrIdentity() {
        val (p,s)=scope();val c=InstrumentationRegistry.getInstrumentation().targetContext
        val folder=File(c.filesDir.canonicalFile,"existing-storage-negative-"+UUID.randomUUID())
        assertTrue(folder.mkdir());android.system.Os.chmod(folder.absolutePath,448)
        s.callAttr("__setitem__","negative",folder.absolutePath)
        p.builtins.callAttr("exec","""
from pathlib import Path
from asc.storage.engine import StorageEngine
root=Path(negative);missing=root/'never-created'
try:StorageEngine(missing,'isolated-negative',existing_only=True)
except (OSError,ValueError):pass
else:raise AssertionError('missing storage initialized')
assert not missing.exists()
empty=root/'empty';empty.mkdir(mode=0o700);db=empty/'manifest.sqlite3';db.touch()
try:StorageEngine(empty,'isolated-negative',existing_only=True)
except ValueError:pass
else:raise AssertionError('empty manifest adopted')
assert db.read_bytes()==b''
assert not (empty/'node.json').exists()
assert not (empty/'data').exists()
""".trimIndent(),s)
    }
    @Test fun wrongNodeIdentityDoesNotRepairOrReplaceOldCommittedState() {
        val (p,s)=scope()
        p.builtins.callAttr("exec","""
from pathlib import Path
from asc.storage.engine import StorageEngine
root=Path(root);manifest=root/'manifest/manifest.sqlite3'
before=manifest.read_bytes();marker=(root/'data/.asc-volume.json').read_bytes()
try:StorageEngine(root/'manifest','wrong-private-actor',existing_only=True,
                  manifest_identity=proof['manifest_identity'])
except ValueError:pass
else:raise AssertionError('wrong Node identity adopted')
assert manifest.read_bytes()==before
assert (root/'data/.asc-volume.json').read_bytes()==marker
""".trimIndent(),s)
    }
}
