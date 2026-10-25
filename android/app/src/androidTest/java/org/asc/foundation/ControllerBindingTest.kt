package org.asc.foundation
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.util.UUID

@RunWith(AndroidJUnit4::class)
class ControllerBindingTest {
    @Test fun realPinnedPublicControllerSourceAndNoEnrollment() {
        val c=InstrumentationRegistry.getInstrumentation().targetContext
        val config=JSONObject(File(c.filesDir,"controller-fixture.json").readText())
        val engine=EmbeddedEngine(c)
        val origin=config.getString("origin");val pin=config.getString("pin");val cluster=config.getString("cluster_id")
        val info=engine.inspectController(origin,pin,cluster)
        if(config.getString("phase")=="offline") {
            assertEquals("UNKNOWN",info.getString("state"));assertFalse(info.getBoolean("enrollment_performed"))
        } else {
            assertEquals("online",config.getString("phase"))
            assertEquals("TLS_AND_CLUSTER_MATCH",info.getString("state"));assertEquals(cluster,info.getString("cluster_id"))
            assertFalse(info.getBoolean("writer_authority"));assertFalse(info.getBoolean("enrollment_performed"))
            val wrongPin=(if(pin[0]=='a')"b" else "a")+pin.substring(1)
            assertEquals("UNKNOWN",engine.inspectController(origin,wrongPin,cluster).getString("state"))
            assertEquals("UNKNOWN",engine.inspectController(origin,pin,UUID.randomUUID().toString()).getString("state"))
        }
    }
}
