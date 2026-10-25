package org.asc.foundation
import android.security.keystore.KeyProperties
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.chaquo.python.Python
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.security.KeyStore
import java.util.UUID

@RunWith(AndroidJUnit4::class)
class VaultStorageTest {
    private val context get()=InstrumentationRegistry.getInstrumentation().targetContext
    @Test fun actualKeystoreNonexportableRestartEncryptedDraftAndLostKeyRefusal() {
        val ns="test-"+UUID.randomUUID();val first=ApplicationVault(context,ns)
        val appId=first.provision().getString("app_id");assertFalse(first.state().getBoolean("key_exportable"))
        val id=UUID.randomUUID().toString();val cluster=UUID.randomUUID().toString();val code="123456abcdef"
        first.saveDraft(id,"https://192.168.1.2:8443","a".repeat(64),cluster,"native test",code)
        val bytes=File(first.root,"join-draft.json").readBytes();assertFalse(String(bytes).contains(code))
        val restarted=ApplicationVault(context,ns);assertEquals(appId,restarted.requireIdentity())
        val draft=restarted.draftSummary();assertEquals(id,draft.getString("request_id"));assertFalse(draft.has("code"));assertFalse(draft.getBoolean("network_enrolled"))
        assertArrayEquals(bytes,File(first.root,"join-draft.json").readBytes())
        val before=File(first.root,"application.json").readBytes()
        val store=KeyStore.getInstance("AndroidKeyStore").apply {load(null)};store.deleteEntry(first.alias)
        assertEquals("IDENTITY_LOCKED",ApplicationVault(context,ns).state().getString("state"))
        assertThrows(IdentityLocked::class.java){ApplicationVault(context,ns).provision()}
        assertFalse(store.containsAlias(first.alias));assertArrayEquals(before,File(first.root,"application.json").readBytes())
    }
    @Test fun corruptCipherAndFutureSchemaCannotRegenerateIdentity() {
        val vault=ApplicationVault(context,"test-"+UUID.randomUUID());vault.provision()
        val canary=File(vault.root,"canary.json");val original=canary.readBytes()
        canary.writeText("{}");assertEquals("IDENTITY_LOCKED",vault.state().getString("state"))
        assertThrows(IdentityLocked::class.java){vault.provision()};canary.writeBytes(original)
        val metadata=File(vault.root,"application.json");val newer=JSONObject(metadata.readText()).put("format",2)
        metadata.writeText(newer.toString());assertEquals("IDENTITY_LOCKED",vault.state().getString("state"))
        assertThrows(IdentityLocked::class.java){vault.provision()};assertEquals(2,JSONObject(metadata.readText()).getInt("format"))
    }
    @Test fun corePrivateVolumeActualProbeRestartPermissionAndCapacityRefusal() {
        EmbeddedEngine(context)
        val module=Python.getInstance().getModule("native_engine")
        val root=File(context.filesDir.canonicalFile,"probe-test-"+UUID.randomUUID());val app=UUID.randomUUID().toString()
        val configured=JSONObject(module.callAttr("approve_probe",root.absolutePath,app,1048576,0).toString())
        val id=configured.getString("volume_id")
        var probe=JSONObject(module.callAttr("probe",root.absolutePath,app).toString()).getJSONObject("volume")
        assertTrue(probe.getBoolean("writable"));assertTrue(probe.getBoolean("fsync_tested"));assertTrue(File(root,"data/staging").list()!!.isEmpty())
        assertEquals(id,JSONObject(module.callAttr("approve_probe",root.absolutePath,app,1048576,0).toString()).getString("volume_id"))
        val fresh=JSONObject(module.callAttr("volume_status",root.absolutePath,app).toString()).getJSONObject("volume")
        assertTrue(fresh.isNull("writable"));assertTrue(fresh.getLong("free_bytes")>0)
        val staging=File(root,"data/staging")
        android.system.Os.chmod(staging.absolutePath,320) //0500, ONLY this synthetic app-owned folder.
        try {
            probe=JSONObject(module.callAttr("probe",root.absolutePath,app).toString()).getJSONObject("volume")
            assertFalse(probe.getBoolean("writable"));assertTrue(probe.isNull("fsync_tested"))
        } finally {android.system.Os.chmod(staging.absolutePath,448)}
        for((quota,reserve) in listOf(1L to 0L,1048576L to (1L shl 40))) {
            val held=File(context.filesDir.canonicalFile,"budget-test-"+UUID.randomUUID())
            module.callAttr("approve_probe",held.absolutePath,app,quota,reserve)
            val denied=JSONObject(module.callAttr("probe",held.absolutePath,app).toString())
            assertEquals("DEGRADED",denied.getString("state"));assertTrue(denied.isNull("writable"))
            assertTrue(File(held,"data/staging").list()!!.isEmpty())
        }
        val marker=File(root,"data/.asc-volume.json");val markerBytes=marker.readBytes();marker.writeText("{}")
        assertEquals("DEGRADED",JSONObject(module.callAttr("probe",root.absolutePath,app).toString()).getString("state"))
        assertEquals("{}",marker.readText());marker.writeBytes(markerBytes)
    }
    @Test fun corruptedRealCoreObjectIsRetainedAndNotDeclaredVerified() {
        val root=File(context.filesDir.canonicalFile,"engine-qualification-"+UUID.randomUUID())
        val proof=EmbeddedEngine(context).selfTest(root)
        val file=File(root,"data/objects").listFiles()!!.single();file.writeBytes("corrupted synthetic fixture".toByteArray())
        val engine=Python.getInstance().getModule("asc.storage.engine").callAttr("StorageEngine",File(root,"manifest").absolutePath,"android-qualification-only")
        try {
            val state=engine.callAttr("verify",file.name.removeSuffix(".blob"),proof.getJSONObject("capabilities").getJSONArray("volumes").getJSONObject(0).getString("volume_id")).callAttr("get","state").toString()
            assertEquals("CORRUPT",state);assertTrue(file.exists())
        } finally {engine.callAttr("close")}
    }
    @Test fun replacedOrMissingPrivateVolumeCannotRecreateItsManifest() {
        EmbeddedEngine(context);val module=Python.getInstance().getModule("native_engine")
        val app=UUID.randomUUID().toString()
        for (replaceRoot in listOf(false,true)) {
            val root=File(context.filesDir.canonicalFile,"binding-test-"+UUID.randomUUID())
            module.callAttr("approve_probe",root.absolutePath,app,1048576,0)
            if(replaceRoot) {
                val retained=File(root.parentFile,root.name+"-retained");assertTrue(root.renameTo(retained));assertTrue(root.mkdir())
                File(retained,"probe-approved.json").copyTo(File(root,"probe-approved.json"))
                assertTrue(File(retained,"data/.asc-volume.json").isFile)
            } else {
                val manifest=File(root,"manifest/manifest.sqlite3")
                assertTrue(manifest.renameTo(File(root,"manifest/held.sqlite3")))
            }
            assertEquals("DEGRADED",JSONObject(module.callAttr("probe",root.absolutePath,app).toString()).getString("state"))
            assertFalse(File(root,"manifest/manifest.sqlite3").exists())
        }
    }
    @Test fun safCannotPretendDurablePosixStorage() {
        val saf=UnqualifiedSafStorage();assertEquals("NOT SUPPORTED",saf.status().getString("state"))
        assertTrue(saf.probe().isNull("fsync_tested"))
        assertThrows(UnsupportedOperationException::class.java){saf.approve(1048576,0)}
    }
}
