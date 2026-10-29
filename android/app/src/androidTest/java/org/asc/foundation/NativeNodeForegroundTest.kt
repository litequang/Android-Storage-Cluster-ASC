package org.asc.foundation

import android.app.ActivityManager
import android.app.NotificationManager
import android.content.*
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
import java.util.UUID
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

@RunWith(AndroidJUnit4::class)
class NativeNodeForegroundTest {
    @Test fun actualDirectNatControllerProbe() {
        val c=InstrumentationRegistry.getInstrumentation().targetContext
        val fixture=JSONObject(File(c.filesDir,"native-mvp-network-fixture.json").readText())
        val port=java.net.URI(fixture.getString("origin")).port
        val result=EmbeddedEngine(c).inspectController("https://10.0.2.2:$port",fixture.getString("pin"),fixture.getString("cluster_id"))
        assertEquals(result.toString(),"TLS_AND_CLUSTER_MATCH",result.optString("state"))
    }
    @Test fun actualBackgroundTransferAndNotificationStop() {
        val c=InstrumentationRegistry.getInstrumentation().targetContext
        val activity=ActivityScenario.launch(MainActivity::class.java)
        var api:ILocalEngine?=null;val ready=CountDownLatch(1)
        val connection=object:ServiceConnection {
            override fun onServiceConnected(name:ComponentName,binder:IBinder){api=ILocalEngine.Stub.asInterface(binder);ready.countDown()}
            override fun onServiceDisconnected(name:ComponentName){api=null}
        }
        assertTrue(c.bindService(Intent(c,EngineService::class.java),connection,Context.BIND_AUTO_CREATE))
        var bound=true
        val manager=c.getSystemService(NotificationManager::class.java)
        val processes=c.getSystemService(ActivityManager::class.java)
        fun foreground()=processes.getRunningServices(30).any {it.service.className==EngineService::class.java.name && it.foreground}
        fun await(check:()->Boolean){val end=System.nanoTime()+TimeUnit.SECONDS.toNanos(20);while(!check() && System.nanoTime()<end)Thread.sleep(100);assertTrue(check())}
        try {
            assertTrue(ready.await(15,TimeUnit.SECONDS))
            assertEquals("RUNNING",JSONObject(api!!.startNode(1,UUID.randomUUID().toString(),"127.0.0.1",9443)).getString("state"))
            await {foreground() && manager.activeNotifications.any {it.id==EngineService.NOTIFICATION_ID}}
            c.unbindService(connection);bound=false;activity.close() // No bound UI/client can keep it alive now.
            await {foreground()}
            EmbeddedEngine(c);val python=Python.getInstance();val scope=python.builtins.callAttr("dict")
            for((name,file) in listOf("fixture" to "native-mvp-network-fixture.json","proof" to "native-mvp-proof.json"))
                scope.callAttr("__setitem__",name,python.getModule("json").callAttr("loads",File(c.filesDir,file).readText()))
            python.builtins.callAttr("exec","""
import hashlib,io
from asc.client import request_json
from asc.storage.client import StorageClient
grant=request_json(fixture['origin'],fixture['pin'],'POST','/api/v1/admin/storage-grant',
    {'node_id':proof['node_id'],'volume_id':proof['volume_id'],'operations':['read']},fixture['owner_token'])['grant']
output=io.BytesIO()
StorageClient('https://127.0.0.1:9443',proof['tls_pin'],grant,proof['volume_id']).download(
    proof['file_id'],output,proof['size'],proof['sha256'])
assert hashlib.sha256(output.getvalue()).hexdigest()==proof['sha256']
""".trimIndent(),scope)
            manager.activeNotifications.single {it.id==EngineService.NOTIFICATION_ID}.notification.actions.single().actionIntent.send()
            await {!foreground() && manager.activeNotifications.none {it.id==EngineService.NOTIFICATION_ID}}
            python.builtins.callAttr("exec","""
import socket
try:peer=socket.create_connection(('127.0.0.1',9443),timeout=1)
except OSError:pass
else:
    peer.close()
    raise AssertionError('owned listener remains after notification Stop')
""".trimIndent(),scope)
        } finally {
            try {c.startService(Intent(c,EngineService::class.java).setAction("org.asc.foundation.STOP_OWNED_NODE"))}catch(_:Exception){}
            if(bound)c.unbindService(connection)
            activity.close()
        }
    }
}
