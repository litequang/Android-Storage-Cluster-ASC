package org.asc.foundation

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.chaquo.python.Python
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File

/** Existing original AVD only: read pre-crash proof, never seed/reset identity. */
@RunWith(AndroidJUnit4::class)
class NativeCrashRecoveryTest {
    @Test fun originalKeystoreNodeTlsVolumeAndBytesSurviveVmCrashAndNormalUpgrade() {
        val c=InstrumentationRegistry.getInstrumentation().targetContext
        val proof=JSONObject(File(c.filesDir,"native-mvp-proof.json").readText())
        val vault=ApplicationVault(c)
        assertEquals(proof.getString("app_id"),vault.requireIdentity())
        val node=NativeNodeContext(c,vault)
        assertEquals(proof.getString("tls_pin"),node.prepareTls().getString("tls_pin"))
        val python=Python.getInstance();val scope=python.builtins.callAttr("dict")
        scope.callAttr("__setitem__","context",node.engineContext())
        scope.callAttr("__setitem__","proof",python.getModule("json").callAttr("loads",proof.toString()))
        python.builtins.callAttr("exec","""
import hashlib
from asc.node.storage import NativeStorage
record=context.load()
for key in ('app_id','context_id'):
    assert record[key]==proof[key]
assert record['node']['node_id']==proof['node_id']
assert record['node']['cluster_id']==proof['cluster_id']
assert hashlib.sha256(record['node']['token'].encode()).hexdigest()==proof['token_sha256']
assert record['tls']['pin']==proof['tls_pin']
assert record['storage']['volume_id']==proof['volume_id']
with NativeStorage(context).open() as engine:
    with engine.download(proof['file_id'],proof['volume_id']) as (metadata,stream):
        body=stream.read()
        assert len(body)==proof['size']
        assert hashlib.sha256(body).hexdigest()==proof['sha256']==metadata['sha256']
""".trimIndent(),scope)
    }
}
