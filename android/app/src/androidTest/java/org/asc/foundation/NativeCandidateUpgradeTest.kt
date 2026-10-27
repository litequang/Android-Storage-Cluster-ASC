package org.asc.foundation

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.chaquo.python.Python
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.security.MessageDigest

/** Read actual original v4 bytes after normal v5 upgrade/refused downgrade.
 * No identity creation, stale database restore or network authorization bypass. */
@RunWith(AndroidJUnit4::class)
class NativeCandidateUpgradeTest {
    @Test fun nativeV4IdentityAndCommittedBytesSurviveV5AndRefusedDowngrade() {
        val c=InstrumentationRegistry.getInstrumentation().targetContext
        val vault=ApplicationVault(c)
        val proof=JSONObject(File(c.filesDir,"native-catalog-proof.json").readText())
        val payload=vault.loadNodeContext()!!
        val digest=MessageDigest.getInstance("SHA-256").digest(payload.toByteArray()).joinToString(""){"%02x".format(it)}
        assertEquals(proof.getString("app_id"),vault.requireIdentity())
        assertEquals(proof.getString("context_sha256"),digest)
        assertEquals(5,c.packageManager.getPackageInfo(c.packageName,0).versionCode)
        EmbeddedEngine(c);val python=Python.getInstance();val scope=python.builtins.callAttr("dict")
        scope.callAttr("__setitem__","context",NativeNodeContext(c,vault).engineContext())
        scope.callAttr("__setitem__","fixture",python.getModule("json").callAttr("loads",File(c.filesDir,"native-v4-upgrade-file.json").readText()))
        python.builtins.callAttr("exec","""
import hashlib
from asc.node.storage import NativeStorage
from asc.catalog.common import identifier
identifier(fixture['file_id']); identifier(fixture['volume_id'])
with NativeStorage(context).open() as engine:
    with engine.download(fixture['file_id'],fixture['volume_id']) as (meta,stream):
        body=stream.read()
        assert len(body)==fixture['size']
        assert hashlib.sha256(body).hexdigest()==fixture['sha256']
        assert meta['sha256']==fixture['sha256']
""".trimIndent(),scope)
    }
}
