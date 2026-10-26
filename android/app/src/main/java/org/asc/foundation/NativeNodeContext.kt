package org.asc.foundation

import android.content.Context
import android.os.Build
import com.chaquo.python.Python
import org.json.JSONObject

/** Fixed app-private native context. No node/cluster creation, paths or tokens in IPC. */
class NativeNodeContext(private val context:Context, private val vault:ApplicationVault) {
    private val parent get()=java.io.File(context.filesDir.canonicalFile,"native-runtime-v1")
    // Java callbacks are callable ONLY by trusted embedded Core in this process.
    class Credentials(private val vault:ApplicationVault) {
        fun load():String?=vault.loadNodeContext()
        fun compare_exchange(expected:String?,replacement:String) {vault.compareNodeContext(expected,replacement)}
    }
    private fun core():com.chaquo.python.PyObject {
        if(!NativeDeviceGate.allowed())throw SecurityException("device_not_qualified")
        val app=vault.requireIdentity()
        EmbeddedEngine(context)
        val build=JSONObject().put("manufacturer",Build.MANUFACTURER).put("model",Build.MODEL)
            .put("device",Build.DEVICE).put("product",Build.PRODUCT).put("hardware",Build.HARDWARE)
            .put("fingerprint",Build.FINGERPRINT).put("sdk",Build.VERSION.SDK_INT).put("debug",BuildConfig.DEBUG)
        val python=Python.getInstance()
        return python.getModule("asc.node.context").callAttr("NodeContext",parent.absolutePath,
            Credentials(vault),app,python.getModule("json").callAttr("loads",build.toString()),NativeTLSLoader())
    }
    private fun result(operation:String):JSONObject {
        val value=core().callAttr(operation)
        return JSONObject(Python.getInstance().getModule("json").callAttr("dumps",value).toString())
    }
    fun initialize():JSONObject {
        if(!NativeDeviceGate.allowed())throw SecurityException("device_not_qualified")
        vault.requireIdentity()
        // Android filesDir is normally0771 under the OS-isolated app sandbox.
        // Create ONLY our NEW dedicated0700 parent; never chmod existing folders.
        if(!parent.exists()) {
            if(vault.loadNodeContext()!=null || java.nio.file.Files.isSymbolicLink(parent.toPath()))throw IdentityLocked()
            if(!parent.mkdir())throw IdentityLocked()
            android.system.Os.chmod(parent.absolutePath,448)
        }
        return result("initialize")
    }
    fun status():JSONObject=result("public_status")
    fun prepareTls():JSONObject {
        check(Build.VERSION.SDK_INT>=30) {"native_tls_api_not_qualified"}
        val value=core().callAttr("prepare_tls",NativeTLSIdentity())
        return JSONObject(Python.getInstance().getModule("json").callAttr("dumps",value).toString())
    }
    internal fun serverTLSContext():com.chaquo.python.PyObject=core().callAttr("tls_context")
}
