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
            if(phase=="seed") {
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
            } else if(phase=="verify") {
                check(version==2);val saved=JSONObject(receipt.readText());val id=vault.requireIdentity()
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
