package org.asc.foundation

import android.content.*
import android.os.IBinder
import android.view.View
import android.widget.*
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.util.UUID
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

/** Actual existing Core gateway +task-owned emulator; no mock view or Node reset. */
@RunWith(AndroidJUnit4::class)
class NativeObserverTest {
    @Test fun actualPinnedOwnerUiQuorumLossReconnectAndRetainedNode() {
        val c=InstrumentationRegistry.getInstrumentation().targetContext
        val fixture=JSONObject(File(c.filesDir,"native-observer-fixture.json").readText())
        val vault=ApplicationVault(c);val app=vault.requireIdentity();val node=vault.loadNodeContext()
        assertNotNull("existing enrolled Node required",node)
        c.getSharedPreferences("local-consent",Context.MODE_PRIVATE).edit().putBoolean("granted",true).commit()
        var api:ILocalEngine?=null;val ready=CountDownLatch(1)
        val connection=object:ServiceConnection {
            override fun onServiceConnected(name:ComponentName,b:IBinder){api=ILocalEngine.Stub.asInterface(b);ready.countDown()}
            override fun onServiceDisconnected(name:ComponentName){api=null}
        }
        assertTrue(c.bindService(Intent(c,EngineService::class.java),connection,Context.BIND_AUTO_CREATE))
        val scenario=ActivityScenario.launch(MainActivity::class.java)
        fun call(op:String,ep:String="",pin:String="",cid:String="",epoch:String="",mode:String="",code:String="",trust:Boolean=false,version:Int=1)=
            JSONObject(api!!.observeCore(version,UUID.randomUUID().toString(),op,ep,pin,cid,epoch,mode,code,trust))
        fun waitUi(expected:String) {
            val deadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(120)
            while(System.nanoTime()<deadline) {
                var observed=""
                scenario.onActivity {observed=it.window.decorView.findViewWithTag<TextView>("cluster-status").text.toString()}
                if(observed.contains(expected))return
                Thread.sleep(100)
            }
            fail("actual observer UI did not establish required state: $expected")
        }
        fun phase(name:String) {
            File(c.filesDir,"native-observer-request.json").writeText(JSONObject().put("request_id",fixture.getString("request_id")).put("phase",name).toString())
            val deadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(90)
            while(System.nanoTime()<deadline) {
                val ack=File(c.filesDir,"native-observer-ack.json")
                if(ack.isFile) {
                    val received=JSONObject(ack.readText())
                    if(received.optString("request_id")==fixture.getString("request_id") && received.optString("phase")==name)return
                }
                Thread.sleep(100)
            }
            fail("host did not execute required actual fault: $name")
        }
        try {
            assertTrue(ready.await(20,TimeUnit.SECONDS))
            val networkDeadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(30)
            var networkObserved=false
            while(!networkObserved && System.nanoTime()<networkDeadline) {
                scenario.onActivity {networkObserved=it.networkEpoch>0}
                if(!networkObserved)Thread.sleep(100)
            }
            assertTrue("actual initial Android network callback required",networkObserved)
            assertEquals("UNKNOWN",call("state").getJSONObject("runtime").getString("state"))
            assertEquals("invalid_request",call("promote").getString("error"))
            assertEquals("invalid_request",call("state",version=99).getString("error"))
            assertEquals("invalid_request",call("state",ep=fixture.getString("endpoint")).getString("error"))
            val wrong=call("login",fixture.getString("endpoint"),"0".repeat(64),fixture.getString("cluster_id"),
                fixture.getString("epoch"),"core-quorum",fixture.getString("code"),true)
            assertEquals("UNKNOWN",wrong.getJSONObject("runtime").getString("state"))
            scenario.onActivity {a ->
                val root=a.window.decorView;root.findViewWithTag<Button>("tab-3").performClick()
                assertEquals(View.VISIBLE,root.findViewWithTag<View>("page-3").visibility)
                for((tag,key) in listOf("observer-endpoint" to "endpoint","observer-pin" to "pin","observer-cluster" to "cluster_id","observer-epoch" to "epoch","observer-code" to "code"))
                    root.findViewWithTag<EditText>(tag).setText(fixture.getString(key))
                assertFalse(root.findViewWithTag<EditText>("observer-code").isSaveEnabled)
                root.findViewWithTag<CheckBox>("observer-trust").isChecked=true
                root.findViewWithTag<Button>("observer-login").performClick()
                assertEquals("",root.findViewWithTag<EditText>("observer-code").text.toString())
            }
            waitUi("Quorum: true")
            scenario.onActivity {a ->
                val text=a.window.decorView.findViewWithTag<TextView>("cluster-status").text.toString()
                assertTrue(text.contains("Node: 3"));assertTrue(text.contains(fixture.getString("logical_path")))
                assertTrue(text.contains("replica desired/verified/available 3/3/3"))
                assertTrue(text.contains("Writer authority: false"));assertTrue(text.contains("voter ONLINE"))
                assertFalse(text.contains(fixture.getString("code")))
            }
            phase("partition")
            scenario.onActivity {it.window.decorView.findViewWithTag<Button>("observer-refresh").performClick()}
            waitUi("QUORUM UNAVAILABLE")
            scenario.onActivity {
                val text=it.window.decorView.findViewWithTag<TextView>("cluster-status").text.toString()
                assertTrue(text.contains("Quorum: false"));assertTrue(text.contains("Leader: UNKNOWN"))
                assertFalse(text.contains("replica desired/verified/available 3/3/3"))
            }
            phase("heal")
            scenario.onActivity {it.window.decorView.findViewWithTag<Button>("observer-refresh").performClick()}
            waitUi("Quorum: true")
            val state=call("state")
            assertTrue(state.getBoolean("read_only"));assertFalse(state.getBoolean("writer_authority"))
            assertTrue(state.getJSONObject("runtime").getBoolean("strong_read_confirmed"))
            scenario.onActivity {it.window.decorView.findViewWithTag<Button>("observer-logout").performClick()}
            waitUi("observer_logged_out")
            assertEquals("UNKNOWN",call("state").getJSONObject("runtime").getString("state"))
            assertEquals(app,vault.requireIdentity())
            assertTrue("observer changed retained encrypted Node record",node==vault.loadNodeContext())
        } finally {
            try {call("logout")}finally {scenario.close();c.unbindService(connection)}
        }
    }
}
