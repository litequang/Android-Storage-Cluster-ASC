package org.asc.foundation

import android.content.Context
import android.os.Build
import com.chaquo.python.Python
import org.json.JSONObject

/** Fixed app-private context. Core issues Node ID; no paths or tokens in IPC. */
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
    private fun enrollment(operation:String,vararg arguments:Any):JSONObject {
        val python=Python.getInstance()
        val value=python.getModule("asc.node.enrollment").callAttr("public_request",core(),operation,*arguments)
        return JSONObject(python.getModule("json").callAttr("dumps",value).toString())
    }
    fun join(request:String,endpoint:String,pin:String,cluster:String,name:String,code:String):JSONObject {
        // Trusted Build/OS measurements, NEVER caller-supplied device/profile overrides.
        // Scores/free bytes do not grant storage, domain, voter or writer authority.
        if(!NativeDeviceGate.allowed())throw SecurityException("device_not_qualified")
        EmbeddedEngine(context)
        val memory=android.app.ActivityManager.MemoryInfo()
        (context.getSystemService(Context.ACTIVITY_SERVICE) as android.app.ActivityManager).getMemoryInfo(memory)
        val profile=JSONObject().put("profile_version",1).put("model",Build.MODEL)
            .put("manufacturer",Build.MANUFACTURER).put("android",Build.VERSION.RELEASE)
            .put("sdk",Build.VERSION.SDK_INT).put("machine",Build.SUPPORTED_ABIS.firstOrNull() ?: "unknown")
            .put("protected",false).put("memory_mb",memory.totalMem/1048576)
            .put("score_basis","runtime-ram").put("sd_status","unknown")
        val python=Python.getInstance()
        return enrollment("join",request,endpoint,pin,cluster,name,code,
            python.getModule("json").callAttr("loads",profile.toString()))
    }
    fun resume():JSONObject {EmbeddedEngine(context);return enrollment("resume")}
    fun replaceCode(code:String):JSONObject {EmbeddedEngine(context);return enrollment("replace_code",code)}
}
