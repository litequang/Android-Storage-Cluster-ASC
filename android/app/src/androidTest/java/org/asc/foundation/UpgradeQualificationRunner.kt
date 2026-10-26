package org.asc.foundation
import android.app.Activity
import android.app.Instrumentation
import android.content.Context
import android.os.Bundle
import org.json.JSONObject
import java.io.File
import java.security.MessageDigest
import java.util.UUID

/** Explicit test-only fixed scenario, excluded from normal JUnit discovery and main APK. */
class UpgradeQualificationRunner:androidx.test.runner.AndroidJUnitRunner() {
    private var phase=""
    override fun onCreate(arguments:Bundle?) {phase=arguments?.getString("phase") ?: "";super.onCreate(arguments)}
    private fun sha(file:File)=MessageDigest.getInstance("SHA-256").digest(file.readBytes()).joinToString(""){"%02x".format(it)}
    override fun onStart() {
        if(phase.isEmpty()){super.onStart();return}
        val result=Bundle()
        try {
            val c=targetContext
            val version=c.packageManager.getPackageInfo(c.packageName,0).versionCode
            val vault=ApplicationVault(c);val engine=EmbeddedEngine(c)
            val receipt=File(c.filesDir.canonicalFile,"upgrade-proof.json")
            if(phase=="tls-seed" || phase=="tls-verify") {
                check(version==3)
                val folder=File(c.filesDir.canonicalFile,"native-context-process-proof")
                check(folder.isDirectory)
                val local=object:android.content.ContextWrapper(c) {override fun getFilesDir():File=folder}
                val localVault=ApplicationVault(local,"native-context-process-proof")
                val node=NativeNodeContext(local,localVault)
                val original=JSONObject(File(folder,"process-proof.json").readText())
                val proofFile=File(folder,"tls-proof.json")
                if(phase=="tls-seed") {
                    check(!proofFile.exists())
                    val state=node.prepareTls()
                    check(state.getString("application_id")==original.getString("application_id"))
                    check(state.getString("context_id")==original.getString("context_id"))
                    proofFile.writeText(JSONObject().put("application_id",state.getString("application_id"))
                        .put("context_id",state.getString("context_id")).put("tls_pin",state.getString("tls_pin"))
                        .put("cipher_sha",sha(File(localVault.root,"node-context.json"))).toString())
                } else {
                    val saved=JSONObject(proofFile.readText());val state=node.prepareTls()
                    check(state.getString("application_id")==saved.getString("application_id"))
                    check(state.getString("context_id")==saved.getString("context_id"))
                    check(state.getString("tls_pin")==saved.getString("tls_pin"))
                    check(sha(File(localVault.root,"node-context.json"))==saved.getString("cipher_sha"))
                    node.serverTLSContext()
                    check(state.isNull("node_id") && state.isNull("cluster_id"))
                }
            } else if(phase=="context-seed" || phase=="context-verify") {
                check(version==3)
                val folder=File(c.filesDir.canonicalFile,"native-context-process-proof")
                if(phase=="context-seed") {check(!folder.exists());check(folder.mkdir());android.system.Os.chmod(folder.absolutePath,448)}
                check(folder.isDirectory)
                val local=object:android.content.ContextWrapper(c) {override fun getFilesDir():File=folder}
                val localVault=ApplicationVault(local,"native-context-process-proof")
                val proofFile=File(folder,"process-proof.json")
                if(phase=="context-seed") {
                    localVault.provision();val state=NativeNodeContext(local,localVault).initialize()
                    proofFile.writeText(JSONObject().put("application_id",state.getString("application_id"))
                        .put("context_id",state.getString("context_id"))
                        .put("cipher_sha",sha(File(localVault.root,"node-context.json")))
                        .put("anchor_sha",sha(File(folder,"native-runtime-v1/native-node-v1/context.json"))).toString())
                } else {
                    val saved=JSONObject(proofFile.readText());val state=NativeNodeContext(local,localVault).status()
                    check(state.getString("application_id")==saved.getString("application_id"))
                    check(state.getString("context_id")==saved.getString("context_id"))
                    check(sha(File(localVault.root,"node-context.json"))==saved.getString("cipher_sha"))
                    check(sha(File(folder,"native-runtime-v1/native-node-v1/context.json"))==saved.getString("anchor_sha"))
                    check(state.isNull("node_id") && state.isNull("cluster_id"))
                }
            } else if(phase=="seed") {
                check(version==1);check(!receipt.exists())
                c.getSharedPreferences("local-consent",Context.MODE_PRIVATE).edit().putBoolean("granted",true).commit()
                val id=vault.provision().getString("app_id");val request=UUID.randomUUID().toString()
                vault.saveDraft(request,"https://192.168.1.2:8443","a".repeat(64),UUID.randomUUID().toString(),"upgrade fixture","123456abcdef")
                val volume=engine.approveProbe(id,8388608,0).getString("volume_id")
                val root=File(c.filesDir.canonicalFile,"engine-qualification-upgrade-"+UUID.randomUUID())
                val proof=engine.selfTest(root)
                val body=File(root,"data/objects").listFiles()!!.single()
                val record=JSONObject().put("app_id",id).put("draft_request",request).put("volume_id",volume)
                    .put("cipher_sha",sha(File(vault.root,"join-draft.json")))
                    .put("marker_sha",sha(File(c.filesDir.canonicalFile,"private-probe-v1/data/.asc-volume.json")))
                    .put("body_root",root.name).put("body_name",body.name).put("body_sha",sha(body))
                    .put("body_volume",proof.getJSONObject("capabilities").getJSONArray("volumes").getJSONObject(0).getString("volume_id"))
                receipt.writeText(record.toString())
            } else if(phase=="verify" || phase=="verify-v3") {
                check(version==if(phase=="verify")2 else 3);val saved=JSONObject(receipt.readText());val id=vault.requireIdentity()
                check(id==saved.getString("app_id"))
                check(vault.draftSummary().getString("request_id")==saved.getString("draft_request"))
                check(sha(File(vault.root,"join-draft.json"))==saved.getString("cipher_sha"))
                check(sha(File(c.filesDir.canonicalFile,"private-probe-v1/data/.asc-volume.json"))==saved.getString("marker_sha"))
                check(engine.volumeStatus(id).getJSONObject("volume").getString("volume_id")==saved.getString("volume_id"))
                val root=File(c.filesDir.canonicalFile,saved.getString("body_root"));val body=File(root,"data/objects/"+saved.getString("body_name"))
                check(sha(body)==saved.getString("body_sha"));check(File(root,"manifest/manifest.sqlite3").isFile)
                val actual=com.chaquo.python.Python.getInstance().getModule("asc.storage.engine").callAttr("StorageEngine",File(root,"manifest").absolutePath,"android-qualification-only")
                try {check(actual.callAttr("verify",body.name.removeSuffix(".blob"),saved.getString("body_volume")).callAttr("get","state").toString()=="COMMITTED")}
                finally {actual.callAttr("close")}
                check(!File(c.filesDir,"node.json").exists())
            } else error("unsupported fixed phase")
            result.putString("qualification","PASS");result.putString("phase",phase)
            finish(Activity.RESULT_OK,result)
        }catch(_:Throwable){result.putString("qualification","FAIL");result.putString("phase",phase);finish(Activity.RESULT_CANCELED,result)}
    }
}
