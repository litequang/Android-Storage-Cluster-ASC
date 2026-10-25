package org.asc.foundation
import android.app.Service
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Binder
import android.os.IBinder
import android.os.Process
import org.json.JSONObject

/** Private application bridge. No Node runtime is started by binding/restart. */
class EngineService : Service() {
    private val binder = object : ILocalEngine.Stub() {
        override fun request(version: Int, requestId: String, operation: String,
            controller: String, pin: String, clusterId: String, name: String, code: String,
            trustConfirmed: Boolean): String {
            val uid=Binder.getCallingUid()
            RequestPolicy.caller(uid,Process.myUid(),packageManager.checkSignatures(uid,Process.myUid())==PackageManager.SIGNATURE_MATCH)
            try {
                RequestPolicy.validate(version,requestId,operation,controller,pin,clusterId,name,code,trustConfirmed)
                if (operation=="status") return status().toString()
                if (!getSharedPreferences("local-consent",MODE_PRIVATE).getBoolean("granted",false))
                    return error("consent_required")
                return when(operation) {
                    "volumes" -> JSONObject().put("state","UNKNOWN").put("source","NOT_CONFIGURED").put("volumes",org.json.JSONArray()).toString()
                    "stop_owned" -> JSONObject().put("owned",false).put("node","UNKNOWN").put("state","NOT_RUNNING").toString()
                    else -> error("native_runtime_unqualified")
                }
            } catch (_: IllegalArgumentException) { return error("invalid_request") }
            catch (_: Exception) { return error("operation_unavailable") }
        }
    }
    private fun error(code: String)=JSONObject().put("ipc_version",1).put("ok",false).put("error",code).toString()
    private fun status()=JSONObject().put("ipc_version",1).put("state","FOUNDATION")
        .put("engine","NOT SUPPORTED").put("controller","UNKNOWN").put("node","UNKNOWN")
        .put("node_id",JSONObject.NULL).put("cluster_id",JSONObject.NULL).put("writer_authority",false)
        .put("storage_approved",JSONObject.NULL).put("failure_domain_approved",JSONObject.NULL)
        .put("owned_node",false).put("runtime_start_supported",false)
    override fun onBind(intent: Intent): IBinder=binder
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        stopSelf(startId) // No background/boot/node launch; unqualified FGS stays absent.
        return START_NOT_STICKY
    }
}
