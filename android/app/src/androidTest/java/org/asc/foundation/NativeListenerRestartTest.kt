package org.asc.foundation

import android.content.ContextWrapper
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.net.BindException
import java.net.Socket
import java.util.UUID
import javax.net.ssl.SSLContext

/** Actual TCP close/rebind; unrelated disposable private context, never Node state. */
@RunWith(AndroidJUnit4::class)
class NativeListenerRestartTest {
    private fun tls(): SSLContext {
        val base=InstrumentationRegistry.getInstrumentation().targetContext
        val folder=File(base.filesDir,"listener-restart-"+UUID.randomUUID())
        assertTrue(folder.mkdir());android.system.Os.chmod(folder.absolutePath,448)
        val local=object:ContextWrapper(base) {override fun getFilesDir():File=folder}
        val vault=ApplicationVault(local,"listener-restart-"+UUID.randomUUID())
        vault.provision()
        val node=NativeNodeContext(local,vault);node.initialize();node.prepareTls()
        return node.serverTLSContext().toJava(SSLContext::class.java)
    }

    @Test fun closedListenerImmediatelyRebindsOwnEndpointAfterAcceptedConnection() {
        val context=tls()
        val first=NativeTLSListener(context,"127.0.0.1",0)
        val port=first.port()
        try {
            Socket("127.0.0.1",port).use {peer ->
                peer.soTimeout=10000
                val connection=first.accept() ?: error("connected TCP peer not accepted")
                connection.close() // Server actively closes: exercise actual TCP TIME_WAIT.
                assertEquals(-1,peer.getInputStream().read())
            }
        } finally {first.close()}
        assertTrue(first.isClosed())
        NativeTLSListener(context,"127.0.0.1",port).use {again ->
            assertEquals(port,again.port())
        }
    }

    @Test fun activeListenerRejectsConcurrentOwnerOnSameEndpoint() {
        val context=tls()
        NativeTLSListener(context,"127.0.0.1",0).use {first ->
            try {
                NativeTLSListener(context,"127.0.0.1",first.port()).use {
                    fail("another active listener bound the same approved endpoint")
                }
            } catch(expected:BindException) {
                assertFalse(first.isClosed())
            }
        }
    }
}
