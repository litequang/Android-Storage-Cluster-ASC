package org.asc.foundation
import android.content.Context
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

/** Real guest precondition. Never treats boot_completed or WiFi-enabled as connected. */
internal fun awaitActualDefaultNetwork():ConnectivityManager {
    val c=InstrumentationRegistry.getInstrumentation().targetContext
    val cm=c.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
    val end=System.nanoTime()+60_000_000_000L
    while(System.nanoTime()<end) {
        val caps=cm.getNetworkCapabilities(cm.activeNetwork)
        if(caps!=null && caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET))return cm
        Thread.sleep(200)
    }
    fail("An actual default network is required before online or network-loss gates")
    error("unreachable")
}
@RunWith(AndroidJUnit4::class)
class NetworkReadinessTest {
    @Test fun actualDefaultNetworkBeforeOnlineFaultQualification() {assertNotNull(awaitActualDefaultNetwork().activeNetwork)}
}
