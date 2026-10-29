package org.asc.untrusted
import android.content.*
import android.content.pm.PackageManager
import android.os.IBinder
import android.os.Process
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class ForeignCallerTest {
    @Test fun actualDifferentUidSignerAndUnGrantedPermissionCannotBind() {
        val context=InstrumentationRegistry.getInstrumentation().targetContext
        val owner=context.packageManager.getApplicationInfo("org.asc.foundation",0).uid
        assertNotEquals(owner,Process.myUid())
        assertEquals(PackageManager.SIGNATURE_NO_MATCH,context.packageManager.checkSignatures(owner,Process.myUid()))
        assertEquals(PackageManager.PERMISSION_DENIED,context.packageManager.checkPermission("org.asc.foundation.permission.LOCAL_ENGINE",context.packageName))
        var denied=false
        val c=object:ServiceConnection {override fun onServiceConnected(n:ComponentName,b:IBinder){fail("Foreign Binder delivered")};override fun onServiceDisconnected(n:ComponentName){}}
        try {
            val accepted=context.bindService(Intent().setComponent(ComponentName("org.asc.foundation","org.asc.foundation.EngineService")),c,Context.BIND_AUTO_CREATE)
            denied=!accepted
            if(accepted){context.unbindService(c);fail("Foreign bind accepted")}
        }catch(_:SecurityException){denied=true}
        assertTrue("Require explicit OS denial, not timeout",denied)
    }
}
