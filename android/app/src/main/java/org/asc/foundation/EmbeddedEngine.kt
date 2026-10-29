package org.asc.foundation
import android.content.Context
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import org.json.JSONObject

/** Actual canonical Python library; never launches CLI/subprocess/Node or reads Termux. */
class EmbeddedEngine(private val context:Context) {
    init { synchronized(EmbeddedEngine::class.java) {
        if(!Python.isStarted())Python.start(AndroidPlatform(context.applicationContext))
    } }
    fun inspectController(endpoint:String,pin:String,cluster:String):JSONObject=JSONObject(Python.getInstance().getModule("native_engine").callAttr("inspect_controller",endpoint,pin,cluster).toString())
    fun info():JSONObject=JSONObject(Python.getInstance().getModule("native_engine").callAttr("info").toString())
    fun approveProbe(appId:String,quota:Long,reserve:Long):JSONObject=JSONObject(Python.getInstance().getModule("native_engine").callAttr("approve_probe",java.io.File(context.filesDir.canonicalFile,"private-probe-v1").absolutePath,appId,quota,reserve).toString())
    fun volumeStatus(appId:String):JSONObject=JSONObject(Python.getInstance().getModule("native_engine").callAttr("volume_status",java.io.File(context.filesDir.canonicalFile,"private-probe-v1").absolutePath,appId).toString())
    fun probe(appId:String):JSONObject=JSONObject(Python.getInstance().getModule("native_engine").callAttr("probe",java.io.File(context.filesDir.canonicalFile,"private-probe-v1").absolutePath,appId).toString())
    // SAF is deliberately not mapped to a POSIX path/provider with assumed fsync.
    fun safCapabilities()=JSONObject().put("state","NOT SUPPORTED").put("fsync_tested",JSONObject.NULL).put("identity",JSONObject.NULL)
    // Internal instrumentation only; NOT an IPC method or user-selected path.
    internal fun selfTest(root:java.io.File):JSONObject = JSONObject(Python.getInstance().getModule("native_engine").callAttr("self_test",root.absolutePath).toString())
}
