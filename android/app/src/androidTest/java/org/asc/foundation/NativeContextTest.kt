package org.asc.foundation

import android.content.Context
import android.content.ContextWrapper
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.security.KeyStore
import java.util.UUID

/** Actual AndroidKeyStore/JNI/filesystem; no fake Android credentials/provider. */
@RunWith(AndroidJUnit4::class)
class NativeContextTest {
    private fun isolated():Pair<Context,ApplicationVault> {
        val base=InstrumentationRegistry.getInstrumentation().targetContext
        val privateRoot=File(base.filesDir.canonicalFile,"native-context-test-"+UUID.randomUUID())
        assertTrue(privateRoot.mkdir());android.system.Os.chmod(privateRoot.absolutePath,448)
        val context=object:ContextWrapper(base) {override fun getFilesDir():File=privateRoot}
        return context to ApplicationVault(context,"context-test-"+UUID.randomUUID())
    }
    @Test fun actualKeystoreContextRestartCiphertextAndStaleCasRefusal() {
        val (context,vault)=isolated();val app=vault.provision().getString("app_id")
        val original=NativeNodeContext(context,vault).initialize()
        assertEquals("CONTEXT_READY",original.getString("state"))
        assertEquals(app,original.getString("application_id"));assertTrue(original.isNull("node_id"))
        assertTrue(original.isNull("cluster_id"));assertFalse(original.getBoolean("runtime_start_supported"))
        val plain=vault.loadNodeContext()!!;val publicReceipt=original.getString("context_id")
        val encrypted=File(vault.root,"node-context.json").readBytes()
        assertFalse(String(encrypted).contains(publicReceipt));assertFalse(String(encrypted).contains(app))
        assertFalse(vault.state().getBoolean("key_exportable"))
        val restarted=NativeNodeContext(context,ApplicationVault(context,vault.root.name))
        assertEquals(original.toString(),restarted.status().toString())
        assertEquals(original.toString(),restarted.initialize().toString())
        assertArrayEquals(encrypted,File(vault.root,"node-context.json").readBytes())
        val update=JSONObject(plain).put("revision",1).toString()
        vault.compareNodeContext(plain,update)
        assertEquals(update,vault.loadNodeContext())
        assertThrows(IdentityLocked::class.java) {vault.compareNodeContext(plain,update)}
        assertThrows(IdentityLocked::class.java) {vault.compareNodeContext(null,plain)}
        assertEquals(publicReceipt,restarted.status().getString("context_id"))
    }
    @Test fun missingOrCorruptSealedRecordOrLostKeyCannotRegenerate() {
        for(fault in listOf("missing-record","corrupt-record","lost-key")) {
            val (context,vault)=isolated();vault.provision();NativeNodeContext(context,vault).initialize()
            val metadata=File(vault.root,"application.json").readBytes()
            val anchor=File(context.filesDir,"native-runtime-v1/native-node-v1/context.json");val before=anchor.readBytes()
            val cipher=File(vault.root,"node-context.json")
            when(fault) {
                "missing-record" -> assertTrue(cipher.renameTo(File(vault.root,"held-context.json")))
                "corrupt-record" -> cipher.writeText("{}")
                "lost-key" -> KeyStore.getInstance("AndroidKeyStore").apply {load(null);deleteEntry(vault.alias)}
            }
            assertThrows(Exception::class.java) {NativeNodeContext(context,vault).initialize()}
            assertThrows(Exception::class.java) {NativeNodeContext(context,vault).status()}
            assertArrayEquals(metadata,File(vault.root,"application.json").readBytes())
            assertArrayEquals(before,anchor.readBytes())
            if(fault=="missing-record")assertFalse(cipher.exists())
            if(fault=="corrupt-record")assertEquals("{}",cipher.readText())
            if(fault=="lost-key")assertEquals("IDENTITY_LOCKED",vault.state().getString("state"))
        }
    }
    @Test fun actualPrivateRootReplacementOrMissingAnchorPreservesIdentityAndState() {
        for(fault in listOf("replace-root","missing-anchor","recovery")) {
            val (context,vault)=isolated();vault.provision()
            val first=NativeNodeContext(context,vault).initialize();val plain=vault.loadNodeContext()
            val root=File(context.filesDir,"native-runtime-v1/native-node-v1");val anchor=File(root,"context.json")
            when(fault) {
                "replace-root" -> {
                    val retained=File(context.filesDir,"held-native-root");assertTrue(root.renameTo(retained))
                    assertTrue(root.mkdir());android.system.Os.chmod(root.absolutePath,448)
                    File(retained,"context.json").copyTo(anchor)
                }
                "missing-anchor" -> assertTrue(anchor.renameTo(File(root,"held-anchor.json")))
                "recovery" -> File(root,"RECOVERY_READ_ONLY.json").writeText("{}")
            }
            assertThrows(Exception::class.java) {NativeNodeContext(context,vault).initialize()}
            assertThrows(Exception::class.java) {NativeNodeContext(context,vault).status()}
            assertEquals(plain,vault.loadNodeContext())
            assertEquals(first.getString("application_id"),vault.requireIdentity())
            assertFalse(File(root,"node.json").exists());assertFalse(File(root,"storage.json").exists())
        }
    }
}
