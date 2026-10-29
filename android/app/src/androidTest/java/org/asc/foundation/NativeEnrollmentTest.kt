package org.asc.foundation

import android.content.Context
import android.content.ContextWrapper
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.util.UUID

/** Real AndroidKeyStore + embedded Core + external synthetic pinned TLS Controller.
 * Private fixture is written by the owned-emulator harness, never shipped in APK.
 * Explicit dev ADB loopback is NOT direct LAN/phone acceptance. */
@RunWith(AndroidJUnit4::class)
class NativeEnrollmentTest {
    private val base get()=InstrumentationRegistry.getInstrumentation().targetContext
    private val config get()=JSONObject(File(base.filesDir,"native-join-fixture.json").readText())
    private data class Fixture(val context:Context,val vault:ApplicationVault,val node:NativeNodeContext)
    private fun ready():Fixture {
        val root=File(base.filesDir,"native-join-test-"+UUID.randomUUID())
        assertTrue(root.mkdir());android.system.Os.chmod(root.absolutePath,448)
        val c=object:ContextWrapper(base) {override fun getFilesDir():File=root}
        val v=ApplicationVault(c,"native-join-test-"+UUID.randomUUID());v.provision()
        val node=NativeNodeContext(c,v);node.initialize();node.prepareTls()
        return Fixture(c,v,node)
    }
    private fun join(f:Fixture,code:String,origin:String=config.getString("origin"),
                     pin:String=config.getString("pin"),cluster:String=config.getString("cluster_id"))=
        f.node.join(UUID.randomUUID().toString(),origin,pin,cluster,"Android native qualification",code)
    private fun payload(v:ApplicationVault)=JSONObject(v.loadNodeContext()!!)
        .getJSONObject("pending").getJSONObject("operation").getJSONObject("payload")
    private fun accepted(result:JSONObject) {
        assertTrue(result.toString(),result.getBoolean("ok"))
        assertEquals("ENROLLED_PENDING_APPROVAL",result.getString("enrollment"))
        assertEquals("HISTORICAL_JOIN_RECEIPT",result.getString("controller_confirmation"))
        assertTrue(result.isNull("storage_approved"));assertTrue(result.isNull("failure_domain_approved"))
        assertFalse(result.getBoolean("runtime_start_supported"));assertFalse(result.getBoolean("writer_authority"))
    }
    @Test fun realTlsEnrollmentKeystoreRestartAndPrivateIdentity() {
        val f=ready();val before=f.node.status();val code=config.getString("fresh_code")
        val result=join(f,code);accepted(result)
        val node=JSONObject(f.vault.loadNodeContext()!!).getJSONObject("node")
        assertEquals(config.getString("cluster_id"),result.getString("cluster_id"))
        assertEquals(node.getString("node_id"),result.getString("node_id"))
        val ciphertext=File(f.vault.root,"node-context.json").readBytes()
        for(secret in listOf(code,node.getString("token"))) {
            assertFalse(result.toString().contains(secret));assertFalse(String(ciphertext).contains(secret))
        }
        val restarted=NativeNodeContext(f.context,ApplicationVault(f.context,f.vault.root.name))
        accepted(restarted.resume())
        assertEquals(before.getString("application_id"),restarted.status().getString("application_id"))
        assertEquals(before.getString("context_id"),restarted.status().getString("context_id"))
        assertEquals(before.getString("tls_pin"),restarted.status().getString("tls_pin"))
        assertArrayEquals(ciphertext,File(f.vault.root,"node-context.json").readBytes())
        val home=File(f.context.filesDir,"native-runtime-v1/native-node-v1")
        assertFalse(File(home,"node.json").exists());assertFalse(File(home,"enrollment_pending.json").exists())
    }
    @Test fun actualLostSuccessfulTlsAckResumesSameKeystoreOperation() {
        val f=ready();val result=join(f,config.getString("drop_code"),config.getString("drop_origin"))
        assertFalse(result.getBoolean("ok"));assertEquals("PENDING_RECEIPT",result.getString("enrollment"))
        val pending=payload(f.vault);val token=pending.getString("enrollment_token")
        assertFalse(result.toString().contains(token));assertFalse(result.toString().contains(pending.getString("enrollment_id")))
        val resumed=NativeNodeContext(f.context,ApplicationVault(f.context,f.vault.root.name)).resume();accepted(resumed)
        assertEquals(token,JSONObject(f.vault.loadNodeContext()!!).getJSONObject("node").getString("token"))
        assertTrue(JSONObject(f.vault.loadNodeContext()!!).isNull("pending"))
    }
    @Test fun pinClusterUnsupportedModeAndOfflineRefuseBeforePending() {
        val f=ready();val original=f.vault.loadNodeContext()
        val pin=config.getString("pin");val wrong=(if(pin[0]=='a')"b" else "a")+pin.substring(1)
        val attempts=listOf(
            join(f,config.getString("negative_code"),pin=wrong),
            join(f,config.getString("negative_code"),cluster=UUID.randomUUID().toString()),
            join(f,config.getString("negative_code"),origin=config.getString("quorum_origin")),
            join(f,config.getString("negative_code"),origin=config.getString("offline_origin")))
        for(result in attempts) {assertFalse(result.getBoolean("ok"));assertTrue(result.isNull("node_id"));assertEquals("NOT_CONFIGURED",result.getString("enrollment"))}
        assertEquals("controller_unverified",attempts[0].getString("error"))
        assertEquals("cluster_mismatch",attempts[1].getString("error"))
        assertEquals("unsupported_runtime",attempts[2].getString("error"))
        assertEquals(original,f.vault.loadNodeContext())
    }
    @Test fun expiredCodeReplacementAndUsedCodeNeverResetIdentity() {
        val f=ready();val expired=join(f,config.getString("expired_code"))
        assertFalse(expired.getBoolean("ok"));assertEquals("invalid_or_expired_code",expired.getString("error"))
        val pending=payload(f.vault);val token=pending.getString("enrollment_token")
        val newCode=config.getString("replacement_code");accepted(f.node.replaceCode(newCode))
        val committed=JSONObject(f.vault.loadNodeContext()!!).getJSONObject("node")
        assertEquals(token,committed.getString("token"))
        val another=ready();val used=join(another,newCode)
        assertFalse(used.getBoolean("ok"));assertEquals("invalid_or_expired_code",used.getString("error"))
        assertEquals("PENDING_RECEIPT",used.getString("enrollment"));assertTrue(used.isNull("node_id"))
        val before=f.vault.loadNodeContext();assertFalse(f.node.replaceCode(config.getString("negative_code")).getBoolean("ok"))
        assertEquals(before,f.vault.loadNodeContext());accepted(f.node.resume())
    }
    @Test fun corruptPendingIsHeldWithoutApplicationOrNodeRecreation() {
        val f=ready();assertFalse(join(f,config.getString("expired_code")).getBoolean("ok"))
        val id=f.vault.requireIdentity();val anchor=File(f.context.filesDir,"native-runtime-v1/native-node-v1/context.json").readBytes()
        val cipher=File(f.vault.root,"node-context.json");val held=File(f.vault.root,"held-pending.json")
        assertTrue(cipher.renameTo(held));cipher.writeText("{}")
        val denied=f.node.resume();assertFalse(denied.getBoolean("ok"));assertEquals("native_context_locked",denied.getString("error"))
        assertThrows(Exception::class.java) {f.node.initialize()}
        assertEquals(id,f.vault.requireIdentity());assertEquals("{}",cipher.readText())
        assertArrayEquals(anchor,File(f.context.filesDir,"native-runtime-v1/native-node-v1/context.json").readBytes())
        assertTrue(held.isFile)
    }
}
