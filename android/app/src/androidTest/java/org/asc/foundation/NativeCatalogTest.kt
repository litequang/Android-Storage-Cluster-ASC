package org.asc.foundation

import android.content.*
import android.net.ConnectivityManager
import android.os.IBinder
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.net.Inet4Address
import java.security.MessageDigest
import java.util.UUID
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

/** Real fresh Demo enrollment +Node serving the existing Catalog/Dashboard.
 * Private host harness controls only this task-owned AVD; no mock byte engine. */
@RunWith(AndroidJUnit4::class)
class NativeCatalogTest {
    @Test fun enrollAndServeActualDashboardReplicas()=run(false)
    @Test fun retainedNodeServesSameCatalogAfterProcessDeath()=run(true)

    private fun run(retained:Boolean) {
        val c=InstrumentationRegistry.getInstrumentation().targetContext
        fun stage(value:String) {File(c.filesDir,"native-catalog-stage.json").writeText(JSONObject().put("stage",value).toString())}
        stage("fixture")
        val fixture=JSONObject(File(c.filesDir,"native-catalog-fixture.json").readText())
        val proofFile=File(c.filesDir,"native-catalog-proof.json")
        val vault=ApplicationVault(c)
        stage("activity")
        val scenario=ActivityScenario.launch(MainActivity::class.java)
        var api:ILocalEngine?=null;val ready=CountDownLatch(1)
        val connection=object:ServiceConnection {
            override fun onServiceConnected(name:ComponentName,b:IBinder){api=ILocalEngine.Stub.asInterface(b);ready.countDown()}
            override fun onServiceDisconnected(name:ComponentName){api=null}
        }
        assertTrue(c.bindService(Intent(c,EngineService::class.java),connection,Context.BIND_AUTO_CREATE))
        fun call(op:String)=JSONObject(api!!.request(1,UUID.randomUUID().toString(),op,"","","","","",false))
        fun hash(text:String)=MessageDigest.getInstance("SHA-256").digest(text.toByteArray()).joinToString(""){"%02x".format(it)}
        fun publish(name:String,value:JSONObject) {
            val destination=File(c.filesDir,name);val pending=File(c.filesDir,name+".pending")
            pending.writeText(value.toString());check(pending.renameTo(destination))
        }
        try {
            stage("binder")
            assertTrue(ready.await(30,TimeUnit.SECONDS))
            c.getSharedPreferences("local-consent",Context.MODE_PRIVATE).edit().putBoolean("granted",true).commit()
            if(!retained) {
                stage("provision")
                assertFalse("never overwrite prior qualification identity",proofFile.exists())
                assertEquals("NOT_PROVISIONED",vault.state().getString("state"))
                assertEquals("READY",call("app_provision").getString("state"))
                stage("context");assertEquals("CONTEXT_READY",call("native_context_init").getString("state"))
                stage("tls")
                assertEquals("IDENTITY_READY",call("native_tls_prepare").getString("tls"))
                stage("enrollment")
                val joined=JSONObject(api!!.request(1,fixture.getString("join_request_id"),"quick_join",
                    fixture.getString("origin"),fixture.getString("pin"),fixture.getString("cluster_id"),
                    "Native APK Catalog qualification",fixture.getString("code"),true))
                assertEquals("ENROLLED_PENDING_APPROVAL",joined.getString("enrollment"))
                assertTrue(joined.isNull("storage_approved"));assertTrue(joined.isNull("failure_domain_approved"))
                stage("storage")
                val storage=JSONObject(api!!.configureNodeStorage(1,UUID.randomUUID().toString(),64L*1024*1024,0))
                assertEquals("LOCAL_VOLUME_READY",storage.getString("state"))
                val volume=storage.getJSONObject("storage").getJSONArray("volumes").getJSONObject(0)
                assertTrue(volume.getBoolean("writable"));assertTrue(volume.getBoolean("fsync_tested"))
                val record=JSONObject(vault.loadNodeContext()!!)
                publish("native-catalog-proof.json",JSONObject().put("app_id",vault.requireIdentity())
                    .put("node_id",record.getJSONObject("node").getString("node_id"))
                    .put("cluster_id",record.getJSONObject("node").getString("cluster_id"))
                    .put("volume_id",record.getJSONObject("storage").getString("volume_id"))
                    .put("pin",record.getJSONObject("tls").getString("pin"))
                    .put("context_sha256",hash(vault.loadNodeContext()!!)))
            }
            stage("identity-check")
            val proof=JSONObject(proofFile.readText())
            fun preserved() {
                assertEquals(proof.getString("app_id"),vault.requireIdentity())
                assertEquals(proof.getString("cluster_id"),fixture.getString("cluster_id"))
                assertEquals(proof.getString("context_sha256"),hash(vault.loadNodeContext()!!))
            }
            preserved()
            val cm=c.getSystemService(ConnectivityManager::class.java)
            val host=cm.getLinkProperties(cm.activeNetwork)!!.linkAddresses.map {it.address}
                .first {it is Inet4Address && it.isSiteLocalAddress}.hostAddress!!
            fun start() {
                stage("node-start")
                assertEquals("RUNNING",JSONObject(api!!.startNode(1,UUID.randomUUID().toString(),host,9443)).getString("state"))
                stage("heartbeat")
                val deadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(30)
                while(System.nanoTime()<deadline && call("node_status").optString("controller")!="ONLINE")Thread.sleep(200)
                assertEquals("ONLINE",call("node_status").getString("controller"));preserved()
            }
            start()
            stage("ready")
            publish("native-catalog-ready.json",JSONObject(proof.toString()).put("request_id",fixture.getString("request_id"))
                .put("guest_host",host).put("retained",retained))
            val deadline=System.nanoTime()+TimeUnit.MINUTES.toNanos(12)
            var last="";var finished=false
            while(System.nanoTime()<deadline && !finished) {
                val file=File(c.filesDir,"native-catalog-control.json")
                if(file.isFile) {
                    val control=JSONObject(file.readText())
                    if(control.optString("request_id")==fixture.getString("request_id") && control.getString("operation_id")!=last) {
                        when(control.getString("action")) {
                            "stop"->{assertEquals("STOPPED",call("stop_owned").getString("state"));preserved()}
                            "start"->start()
                            "finish"->{call("stop_owned");preserved();finished=true}
                            else->fail("unsupported test-only host control")
                        }
                        last=control.getString("operation_id")
                        publish("native-catalog-ack.json",JSONObject().put("request_id",fixture.getString("request_id"))
                            .put("operation_id",last).put("state","PASS"))
                    }
                }
                Thread.sleep(100)
            }
            assertTrue("actual host Catalog/Dashboard qualification did not finish",finished)
        } finally {
            try {call("stop_owned")}finally {scenario.close();c.unbindService(connection)}
        }
    }
}
