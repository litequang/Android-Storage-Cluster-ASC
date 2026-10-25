package org.asc.foundation
import android.content.Context
import android.os.Parcel
import android.os.IBinder
import android.widget.EditText
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class NativeLifecycleTest {
    @Test fun actualDefaultNetworkChangeClearsUnsentSecretAndRestoresNetwork() {
        val instrumentation=InstrumentationRegistry.getInstrumentation()
        fun shell(cmd:String) {instrumentation.uiAutomation.executeShellCommand(cmd).use {p ->java.io.FileInputStream(p.fileDescriptor).readBytes()}}
        shell("svc wifi enable");shell("svc data enable");awaitActualDefaultNetwork()
        ActivityScenario.launch(MainActivity::class.java).use {scenario ->
            val initialEnd=System.nanoTime()+30_000_000_000L
            var available=false
            while(System.nanoTime()<initialEnd && !available) {
                scenario.onActivity {a ->available=a.networkEpoch>0}
                if(!available)Thread.sleep(200)
            }
            assertTrue("Actual initial onAvailable before fault",available)
            var baseline=0
            val started=java.util.concurrent.CountDownLatch(1)
            val release=java.util.concurrent.CountDownLatch(1)
            val staleDelivered=java.util.concurrent.CountDownLatch(1)
            scenario.onActivity {a ->baseline=a.networkLosses;a.window.decorView.findViewWithTag<EditText>("join-code").setText("123456abcdef")}
            // Exercise the actual Activity worker with a controlled late response. No fake
            // Controller/Engine result or Node acceptance is inferred from this UI gate.
            scenario.onActivity {a ->
                val task=MainActivity::class.java.getDeclaredMethod("task",kotlin.jvm.functions.Function0::class.java,kotlin.jvm.functions.Function1::class.java)
                task.isAccessible=true
                val work:()->org.json.JSONObject={started.countDown();check(release.await(30,java.util.concurrent.TimeUnit.SECONDS));org.json.JSONObject()}
                val done:(org.json.JSONObject)->Unit={staleDelivered.countDown()}
                task.invoke(a,work,done)
            }
            assertTrue(started.await(10,java.util.concurrent.TimeUnit.SECONDS))
            try {
                shell("svc wifi disable");shell("svc data disable")
                val deadline=System.nanoTime()+20_000_000_000L;var observed=false
                while(System.nanoTime()<deadline && !observed) {
                    scenario.onActivity {a ->observed=a.networkLosses>baseline && a.window.decorView.findViewWithTag<EditText>("join-code").text.isEmpty()}
                    if(!observed)Thread.sleep(200)
                }
                assertTrue("Actual network callback and secret clearing required",observed)
                release.countDown()
                assertFalse("Stale response must not re-establish UI trust",staleDelivered.await(1,java.util.concurrent.TimeUnit.SECONDS))
            } finally {release.countDown();shell("svc wifi enable");shell("svc data enable")}
            val cm=instrumentation.targetContext.getSystemService(Context.CONNECTIVITY_SERVICE) as android.net.ConnectivityManager
            val deadline=System.nanoTime()+20_000_000_000L
            while(cm.activeNetwork==null && System.nanoTime()<deadline)Thread.sleep(200)
            assertNotNull("Restore owned emulator network",cm.activeNetwork)
        }
    }
}
