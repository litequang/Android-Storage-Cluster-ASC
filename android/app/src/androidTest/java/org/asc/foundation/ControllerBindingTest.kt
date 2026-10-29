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
            if(info.getString("state")!="TLS_AND_CLUSTER_MATCH") {
                val py=com.chaquo.python.Python.getInstance();val scope=py.builtins.callAttr("dict")
                for((key,value) in mapOf("origin" to origin,"pin" to pin,"expected_cluster" to cluster))scope.callAttr("__setitem__",key,value)
                py.builtins.callAttr("exec", """
from asc.client import request_json
try:
    r=request_json(origin,pin,'GET','/api/v1/info',timeout=10)
    diagnostic='PUBLIC_REPLY mode='+str(r.get('mode'))+' schema='+str(r.get('schema_version'))+' protocol='+str(r.get('protocol_version'))+' cluster_match='+str(r.get('cluster_id')==expected_cluster)
except Exception as exc:
    diagnostic=type(exc).__name__
""".trimIndent(),scope)
                fail("Strict native binding UNKNOWN; direct primitive category: "+scope.callAttr("get","diagnostic"))
            }
            assertEquals("TLS_AND_CLUSTER_MATCH",info.getString("state"));assertEquals(cluster,info.getString("cluster_id"))
            assertFalse(info.getBoolean("writer_authority"));assertFalse(info.getBoolean("enrollment_performed"))
            val wrongPin=(if(pin[0]=='a')"b" else "a")+pin.substring(1)
            assertEquals("UNKNOWN",engine.inspectController(origin,wrongPin,cluster).getString("state"))
            assertEquals("UNKNOWN",engine.inspectController(origin,pin,UUID.randomUUID().toString()).getString("state"))
        }
    }
}
