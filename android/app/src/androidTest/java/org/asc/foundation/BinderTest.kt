package org.asc.foundation
import android.content.*
import android.os.IBinder
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.util.UUID
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

@RunWith(AndroidJUnit4::class)
class BinderTest {
    private fun withService(test:(ILocalEngine,Context)->Unit) {
        val context=InstrumentationRegistry.getInstrumentation().targetContext
        var binder:ILocalEngine?=null;val ready=CountDownLatch(1)
        val connection=object:ServiceConnection {
            override fun onServiceConnected(name:ComponentName,service:IBinder) {binder=ILocalEngine.Stub.asInterface(service);ready.countDown()}
            override fun onServiceDisconnected(name:ComponentName) {}
        }
        assertTrue(context.bindService(Intent(context,EngineService::class.java),connection,Context.BIND_AUTO_CREATE))
        try {assertTrue(ready.await(20,TimeUnit.SECONDS));test(binder!!,context)} finally {context.unbindService(connection)}
    }
    private fun request(b:ILocalEngine,op:String,version:Int=1)=JSONObject(b.request(version,UUID.randomUUID().toString(),op,"","","","","",false))
    @Test fun authenticatedOwnUidReadsFoundationWithoutIdentityCreation()=withService {b,_ ->
        val status=request(b,"status");assertEquals("FOUNDATION",status.getString("state"));assertFalse(status.getBoolean("writer_authority"))
        assertTrue(status.isNull("node_id"));assertFalse(status.getBoolean("runtime_start_supported"))
    }
    @Test fun consentGateAndUnsupportedRuntimeNeverStartNode()=withService {b,c ->
        c.getSharedPreferences("local-consent",Context.MODE_PRIVATE).edit().putBoolean("granted",false).commit()
        assertEquals("consent_required",request(b,"node_start").getString("error"))
        c.getSharedPreferences("local-consent",Context.MODE_PRIVATE).edit().putBoolean("granted",true).commit()
        assertEquals("native_runtime_unqualified",request(b,"node_start").getString("error"))
        assertFalse(request(b,"stop_owned").getBoolean("owned"))
    }
    @Test fun invalidVersionAndDangerousOperationRefuse()=withService {b,_ ->
        assertEquals("invalid_request",request(b,"status",99).getString("error"))
        assertEquals("invalid_request",request(b,"shell").getString("error"))
    }
    @Test fun nativeContextUsesActualPrivateParentAndConsentWithoutNodeIdentity()=withService {b,c ->
        c.getSharedPreferences("local-consent",Context.MODE_PRIVATE).edit().putBoolean("granted",false).commit()
        for(op in listOf("native_context_init","native_context_status"))
            assertEquals("consent_required",request(b,op).getString("error"))
        c.getSharedPreferences("local-consent",Context.MODE_PRIVATE).edit().putBoolean("granted",true).commit()
        val app=request(b,"app_provision").getString("app_id")
        val first=request(b,"native_context_init")
        assertEquals("CONTEXT_READY",first.getString("state"));assertEquals(app,first.getString("application_id"))
        assertTrue(first.isNull("node_id"));assertTrue(first.isNull("cluster_id"))
        assertFalse(first.getBoolean("runtime_start_supported"));assertFalse(first.getBoolean("writer_authority"))
        assertEquals(first.toString(),request(b,"native_context_status").toString())
        assertEquals(first.toString(),request(b,"native_context_init").toString())
        val root=java.io.File(c.filesDir.canonicalFile,"native-runtime-v1/native-node-v1")
        assertTrue(java.io.File(root,"context.json").isFile)
        assertFalse(java.io.File(root,"node.json").exists());assertFalse(java.io.File(root,"storage.json").exists())
    }
    @Test fun fixedV1ParcelCodeRemainsCompatible()=withService {b,_ ->
        val data=android.os.Parcel.obtain();val reply=android.os.Parcel.obtain()
        try {
            data.writeInterfaceToken("org.asc.foundation.ILocalEngine");data.writeInt(1)
            data.writeString(UUID.randomUUID().toString());data.writeString("status")
            repeat(5){data.writeString("")};data.writeInt(0)
            assertTrue(b.asBinder().transact(android.os.IBinder.FIRST_CALL_TRANSACTION+1,data,reply,0))
            reply.readException();assertEquals("FOUNDATION",JSONObject(reply.readString()!!).getString("state"))
        }finally{data.recycle();reply.recycle()}
    }
}
