package org.asc.foundation
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.util.UUID

@RunWith(AndroidJUnit4::class)
class EmbeddedEngineTest {
    @Test fun realPythonCoreStreamsCommitsFsyncAndRestartsOnAndroid() {
        val c=InstrumentationRegistry.getInstrumentation().targetContext
        val engine=EmbeddedEngine(c)
        assertEquals("asc.storage.engine",engine.info().getString("implementation"))
        val proof=engine.selfTest(File(c.filesDir.canonicalFile,"engine-qualification-"+UUID.randomUUID()))
        assertEquals("LOCAL_ENGINE_SELF_TEST_PASS",proof.getString("state"))
        assertTrue(proof.getBoolean("restart_sha_match"));assertFalse(proof.getBoolean("network_enrolled"))
        assertFalse(proof.getBoolean("node_runtime_supported"));assertFalse(proof.getBoolean("writer_authority"))
        val volume=proof.getJSONObject("capabilities").getJSONArray("volumes").getJSONObject(0)
        assertTrue(volume.getBoolean("writable"));assertTrue(volume.getBoolean("fsync_tested"))
    }
}
