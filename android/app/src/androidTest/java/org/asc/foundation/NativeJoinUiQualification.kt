package org.asc.foundation

import android.content.Context
import android.os.SystemClock
import android.view.View
import android.widget.*
import androidx.test.core.app.ActivityScenario
import androidx.test.platform.app.InstrumentationRegistry
import org.json.JSONObject
import java.io.File
import java.security.MessageDigest

/** Fixed multi-process UI scenario, invoked ONLY by explicit qualification phases.
 * Fresh separate owned AVD; no old fixture, identity, signer or data is cleared. */
object NativeJoinUiQualification {
    fun run(phase:String) {
        val context=InstrumentationRegistry.getInstrumentation().targetContext
        val fixture=JSONObject(File(context.filesDir,"native-ui-join-fixture.json").readText())
        val proofFile=File(context.filesDir,"native-ui-join-proof.json")
        val vault=ApplicationVault(context)
        fun digest(value:ByteArray)=MessageDigest.getInstance("SHA-256").digest(value).joinToString(""){"%02x".format(it)}
        fun cipherSha()=digest(File(vault.root,"node-context.json").readBytes())
        ActivityScenario.launch(MainActivity::class.java).use {scenario ->
            fun ui(work:(View)->Unit) {scenario.onActivity {work(it.window.decorView)}}
            fun text(tag:String):String {var text="";ui {text=it.findViewWithTag<TextView>(tag).text.toString()};return text}
            fun waitFor(tag:String,expected:String) {
                val deadline=SystemClock.elapsedRealtime()+180000
                while(SystemClock.elapsedRealtime()<deadline) {
                    if(text(tag).contains(expected))return
                    SystemClock.sleep(200)
                }
                // Never include actual text or fixture credentials in failure output.
                error("native_ui_expected_state_unconfirmed")
            }
            fun click(tag:String) {ui {check(it.findViewWithTag<Button>(tag).performClick())}}
            waitFor("runtime-status","FOUNDATION")
            if(phase=="ui-join-seed") {
                check(!proofFile.exists())
                check(vault.state().getString("state")=="NOT_PROVISIONED")
                ui {root ->root.findViewWithTag<CheckBox>("consent").isChecked=true}
                click("provision");waitFor("runtime-status","READY")
                click("tab-1");click("prepare-native-join");waitFor("join-result","TLS identity đã sẵn sàng")
                ui {root ->
                    root.findViewWithTag<EditText>("controller").setText(fixture.getString("origin"))
                    root.findViewWithTag<EditText>("pin").setText(fixture.getString("pin"))
                    root.findViewWithTag<EditText>("cluster").setText(fixture.getString("cluster_id"))
                    root.findViewWithTag<EditText>("node-name").setText("Native UI Binder qualification")
                    root.findViewWithTag<EditText>("join-code").setText(fixture.getString("code"))
                }
                click("check-controller");waitFor("join-result","TLS PIN và Cluster ID khớp")
                ui {root ->
                    val found=ArrayList<View>()
                    root.findViewsWithText(found,"Tôi đã đối chiếu endpoint, PIN và Cluster ID với owner.",View.FIND_VIEWS_WITH_TEXT)
                    check(found.size==1);(found.single() as CheckBox).isChecked=true
                }
                click("native-join");waitFor("join-result","PENDING_RECEIPT")
                ui {check(it.findViewWithTag<EditText>("join-code").text.isEmpty())}
                val state=NativeNodeContext(context,vault).status()
                check(state.getString("enrollment")=="PENDING_RECEIPT" && state.isNull("node_id"))
                val payload=JSONObject(vault.loadNodeContext()!!).getJSONObject("pending").getJSONObject("operation").getJSONObject("payload")
                check(!text("join-result").contains(payload.getString("enrollment_token")))
                proofFile.writeText(JSONObject().put("application_id",state.getString("application_id"))
                    .put("context_id",state.getString("context_id")).put("tls_pin",state.getString("tls_pin"))
                    .put("request_id",state.getString("join_request_id"))
                    .put("operation_sha",digest(payload.getString("enrollment_id").toByteArray()))
                    .put("token_sha",digest(payload.getString("enrollment_token").toByteArray()))
                    .put("pending_cipher_sha",cipherSha()).toString())
            } else {
                check(phase=="ui-join-resume" || phase=="ui-join-verify")
                val proof=JSONObject(proofFile.readText());val node=NativeNodeContext(context,vault)
                val before=node.status()
                check(before.getString("application_id")==proof.getString("application_id"))
                check(before.getString("context_id")==proof.getString("context_id"))
                check(before.getString("tls_pin")==proof.getString("tls_pin"))
                click("tab-1");click("native-join-status")
                if(phase=="ui-join-resume") {
                    check(before.getString("enrollment")=="PENDING_RECEIPT")
                    check(cipherSha()==proof.getString("pending_cipher_sha"))
                    val saved=JSONObject(vault.loadNodeContext()!!).getJSONObject("pending")
                    check(saved.getString("request_id")==proof.getString("request_id"))
                    check(digest(saved.getJSONObject("operation").getJSONObject("payload").getString("enrollment_id").toByteArray())==proof.getString("operation_sha"))
                    waitFor("join-result","PENDING_RECEIPT");click("resume-native-join")
                }
                waitFor("join-result","Có receipt enrollment")
                val state=node.status();val config=JSONObject(vault.loadNodeContext()!!).getJSONObject("node")
                check(state.getString("enrollment")=="ENROLLED_PENDING_APPROVAL")
                check(state.getString("cluster_id")==fixture.getString("cluster_id"))
                check(state.isNull("storage_approved") && state.isNull("failure_domain_approved"))
                check(!state.getBoolean("runtime_start_supported") && !state.getBoolean("writer_authority"))
                check(digest(config.getString("token").toByteArray())==proof.getString("token_sha"))
                check(!text("join-result").contains(config.getString("token")))
                if(phase=="ui-join-resume") {
                    proof.put("node_id",state.getString("node_id")).put("node_cipher_sha",cipherSha())
                    proofFile.writeText(proof.toString())
                } else {
                    check(state.getString("node_id")==proof.getString("node_id"))
                    check(cipherSha()==proof.getString("node_cipher_sha"))
                }
            }
            check(!File(context.filesDir,"node.json").exists())
            check(!File(context.filesDir,"native-runtime-v1/native-node-v1/node.json").exists())
        }
    }
}
