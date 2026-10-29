package org.asc.foundation

import android.content.*
import android.os.IBinder
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

@RunWith(AndroidJUnit4::class)
class BinderEnrollmentTest {
    @Test fun realPrivateBinderGatesEnrollmentAndDelegatesPinnedCoreFailure() {
        val context=InstrumentationRegistry.getInstrumentation().targetContext
        val fixture=JSONObject(File(context.filesDir,"native-join-fixture.json").readText())
        val ready=CountDownLatch(1);var api:ILocalEngine?=null
        val connection=object:ServiceConnection {
            override fun onServiceConnected(name:ComponentName,binder:IBinder) {api=ILocalEngine.Stub.asInterface(binder);ready.countDown()}
            override fun onServiceDisconnected(name:ComponentName) {}
        }
        val prefs=context.getSharedPreferences("local-consent",Context.MODE_PRIVATE);val consent=prefs.getBoolean("granted",false)
        assertTrue(context.bindService(Intent(context,EngineService::class.java),connection,Context.BIND_AUTO_CREATE))
        try {
            assertTrue(ready.await(20,TimeUnit.SECONDS));val b=api!!
            fun request(op:String,endpoint:String="",pin:String="",cluster:String="",name:String="",code:String="",trust:Boolean=false)=
                JSONObject(b.request(1,UUID.randomUUID().toString(),op,endpoint,pin,cluster,name,code,trust))
            prefs.edit().putBoolean("granted",false).commit()
            assertEquals("consent_required",request("resume_join").getString("error"))
            prefs.edit().putBoolean("granted",true).commit()
            request("app_provision");request("native_context_init");request("native_tls_prepare")
            val vault=ApplicationVault(context);val original=vault.loadNodeContext()
            val pin=fixture.getString("pin");val wrong=(if(pin[0]=='a')"b" else "a")+pin.substring(1)
            val result=request("quick_join",fixture.getString("origin"),wrong,fixture.getString("cluster_id"),"Binder refusal proof",fixture.getString("negative_code"),true)
            assertFalse(result.toString(),result.getBoolean("ok"));assertEquals("controller_unverified",result.getString("error"))
            assertEquals("NOT_CONFIGURED",result.getString("enrollment"));assertTrue(result.isNull("node_id"))
            assertEquals(original,vault.loadNodeContext());assertFalse(result.toString().contains(fixture.getString("negative_code")))
            assertEquals("invalid_request",request("replace_join_code",endpoint="/private/escape",code="123456abcdef",trust=true).getString("error"))
            assertFalse(request("stop_owned").getBoolean("owned"))
        } finally {prefs.edit().putBoolean("granted",consent).commit();context.unbindService(connection)}
    }
}
