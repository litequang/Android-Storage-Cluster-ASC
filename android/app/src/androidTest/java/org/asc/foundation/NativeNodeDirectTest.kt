package org.asc.foundation

import android.content.*
import android.net.ConnectivityManager
import android.os.IBinder
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.chaquo.python.Python
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.net.Inet4Address
import java.util.UUID
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

/** Host harness sends actual bytes over standard emulator NAT port redirection.
 * ADB is control/receipt ONLY; reverse must be removed by the harness. */
@RunWith(AndroidJUnit4::class)
class NativeNodeDirectTest {
    @Test fun actualColdBinderAddressChangePreservesExistingNode() {
        assertFalse("cold process required",Python.isStarted())
        val c=InstrumentationRegistry.getInstrumentation().targetContext
        val fixture=JSONObject(File(c.filesDir,"native-mvp-network-fixture.json").readText())
        var api:ILocalEngine?=null;val ready=CountDownLatch(1)
        val connection=object:ServiceConnection {
            override fun onServiceConnected(name:ComponentName,binder:IBinder){api=ILocalEngine.Stub.asInterface(binder);ready.countDown()}
            override fun onServiceDisconnected(name:ComponentName){api=null}
        }
        assertTrue(c.bindService(Intent(c,EngineService::class.java),connection,Context.BIND_AUTO_CREATE))
        try {
            assertTrue(ready.await(15,TimeUnit.SECONDS))
            val endpoint="https://10.0.2.2:"+java.net.URI(fixture.getString("origin")).port
            val result=JSONObject(api!!.request(1,UUID.randomUUID().toString(),"change_controller",endpoint,
                fixture.getString("pin"),fixture.getString("cluster_id"),"","",true))
            assertTrue(result.toString(),result.optBoolean("ok"))
            assertEquals(fixture.getString("node_id"),result.getString("node_id"))
            assertEquals(endpoint,result.getString("enrollment_controller"))
        } finally {c.unbindService(connection)}
    }
    @Test fun actualDirectControllerAndHostToNodeTransferRetainIdentity() {
        val c=InstrumentationRegistry.getInstrumentation().targetContext
        val fixtureFile=File(c.filesDir,"native-mvp-network-fixture.json")
        val fixture=JSONObject(fixtureFile.readText());val request=fixture.getString("direct_request_id")
        val activity=ActivityScenario.launch(MainActivity::class.java)
        var api:ILocalEngine?=null;val ready=CountDownLatch(1)
        val connection=object:ServiceConnection {
            override fun onServiceConnected(name:ComponentName,binder:IBinder){api=ILocalEngine.Stub.asInterface(binder);ready.countDown()}
            override fun onServiceDisconnected(name:ComponentName){api=null}
        }
        assertTrue(c.bindService(Intent(c,EngineService::class.java),connection,Context.BIND_AUTO_CREATE))
        val core=NativeNodeContext(c,ApplicationVault(c))
        try {
            assertTrue(ready.await(15,TimeUnit.SECONDS));EmbeddedEngine(c)
            val python=Python.getInstance();val scope=python.builtins.callAttr("dict")
            scope.callAttr("__setitem__","context",core.engineContext())
            python.builtins.callAttr("exec","before=context.load()",scope)
            val port=java.net.URI(fixture.getString("origin")).port
            val endpoint="https://10.0.2.2:$port"
            val changed=JSONObject(api!!.request(1,UUID.randomUUID().toString(),"change_controller",endpoint,
                fixture.getString("pin"),fixture.getString("cluster_id"),"","",true))
            assertTrue(changed.toString(),changed.optBoolean("ok"))
            scope.callAttr("__setitem__","endpoint",endpoint)
            python.builtins.callAttr("exec","""
after=context.load()
assert after['node']==dict(before['node'],controller=endpoint)
for key in ('app_id','context_id','tls','storage','pending','binding','device_binding'):
    assert after[key]==before[key],'retained identity/storage changed'
""".trimIndent(),scope)
            fixture.put("origin",endpoint);fixtureFile.writeText(fixture.toString())
            val cm=c.getSystemService(ConnectivityManager::class.java)
            val host=cm.getLinkProperties(cm.activeNetwork)!!.linkAddresses.map {it.address}
                .first {it is Inet4Address && it.isSiteLocalAddress}.hostAddress!!
            assertEquals("RUNNING",JSONObject(api!!.startNode(1,UUID.randomUUID().toString(),host,9443)).getString("state"))
            val end=System.nanoTime()+TimeUnit.SECONDS.toNanos(20)
            var status=JSONObject()
            while(System.nanoTime()<end) {
                status=JSONObject(api!!.request(1,UUID.randomUUID().toString(),"node_status","","","","","",false))
                if(status.optString("controller")=="ONLINE")break
                Thread.sleep(100)
            }
            assertEquals("ONLINE",status.optString("controller"))
            val record=JSONObject(ApplicationVault(c).loadNodeContext()!!)
            File(c.filesDir,"direct-node-ready.json").writeText(JSONObject().put("request_id",request)
                .put("node_id",record.getJSONObject("node").getString("node_id"))
                .put("volume_id",record.getJSONObject("storage").getString("volume_id"))
                .put("pin",record.getJSONObject("tls").getString("pin")).put("guest_host",host).put("port",9443).toString())
            val resultFile=File(c.filesDir,"direct-node-result.json")
            var result=JSONObject();val deadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(90)
            while(System.nanoTime()<deadline) {
                if(resultFile.exists())try {result=JSONObject(resultFile.readText())}catch(_:Exception){}
                if(result.optString("request_id")==request)break
                Thread.sleep(200)
            }
            assertEquals(request,result.optString("request_id"));assertEquals("PASS",result.optString("state"))
            assertTrue(result.getInt("bytes")>0);assertEquals(64,result.getString("sha256").length)
            assertEquals(record.getJSONObject("storage").getString("volume_id"),result.getString("volume_id"))
        } finally {
            try {api?.request(1,UUID.randomUUID().toString(),"stop_owned","","","","","",false)}catch(_:Exception){}
            c.unbindService(connection);activity.close()
        }
    }
}
