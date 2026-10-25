package org.asc.foundation
import android.content.Context
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import org.json.JSONObject

/** Actual canonical Python library; never launches CLI/subprocess/Node or reads Termux. */
class EmbeddedEngine(context:Context) {
    init { synchronized(EmbeddedEngine::class.java) {
        if(!Python.isStarted())Python.start(AndroidPlatform(context.applicationContext))
    } }
    fun info():JSONObject=JSONObject(Python.getInstance().getModule("native_engine").callAttr("info").toString())
    // Internal instrumentation only; NOT an IPC method or user-selected path.
    internal fun selfTest(root:java.io.File):JSONObject = JSONObject(Python.getInstance().getModule("native_engine").callAttr("self_test",root.absolutePath).toString())
}
