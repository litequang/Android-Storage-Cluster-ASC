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
    private fun caller() {
        val uid=Binder.getCallingUid()
        RequestPolicy.caller(uid,Process.myUid(),packageManager.checkSignatures(uid,Process.myUid())==PackageManager.SIGNATURE_MATCH)
    }
    private val operations=Any()
    private var nodeSession:NativeNodeSession?=null
    private fun nodeAction(version:Int,id:String,action:(NativeNodeSession)->JSONObject):String {
        caller()
        return synchronized(operations) {try {
            RequestPolicy.validate(version,id,"node_status","","","","","",false)
            if(!NativeDeviceGate.allowed())return@synchronized error("device_not_qualified")
            if(!getSharedPreferences("local-consent",MODE_PRIVATE).getBoolean("granted",false))return@synchronized error("consent_required")
            val session=nodeSession ?: NativeNodeSession(this,ApplicationVault(this)).also {nodeSession=it}
            action(session).toString()
        }catch(_:IdentityLocked){error("identity_locked")}catch(_:Exception){error("node_operation_unavailable")}}
    }
    private val binder = object : ILocalEngine.Stub() {
        override fun configureNodeStorage(version:Int,requestId:String,quotaBytes:Long,reserveBytes:Long):String =
            nodeAction(version,requestId) {it.configure(quotaBytes,reserveBytes)}
        override fun startNode(version:Int,requestId:String,host:String,port:Int):String =
            nodeAction(version,requestId) {it.start(host,port)}
        override fun approvePrivateProbe(version:Int,requestId:String,quotaBytes:Long,reserveBytes:Long):String {
            caller()
            return synchronized(operations) {try {
                RequestPolicy.validate(version,requestId,"status","","","","","",false)
                if(!NativeDeviceGate.allowed())return@synchronized error("device_not_qualified")
                if(!getSharedPreferences("local-consent",MODE_PRIVATE).getBoolean("granted",false))return@synchronized error("consent_required")
                require(quotaBytes in 1..(1L shl 40) && reserveBytes in 0..(1L shl 40))
                PrivateProbeStorage(this@EngineService,ApplicationVault(this@EngineService)).approve(quotaBytes,reserveBytes).toString()
            }catch(_:IdentityLocked){error("identity_locked")}catch(_:Exception){error("private_probe_refused")}}
        }

        override fun request(version: Int, requestId: String, operation: String,
            controller: String, pin: String, clusterId: String, name: String, code: String,
            trustConfirmed: Boolean): String {
            caller()
            try {
                RequestPolicy.validate(version,requestId,operation,controller,pin,clusterId,name,code,trustConfirmed)
                if (operation=="status") return status().toString()
                if(!NativeDeviceGate.allowed())return error("device_not_qualified")
                if (operation!="stop_owned" && !getSharedPreferences("local-consent",MODE_PRIVATE).getBoolean("granted",false))
                    return error("consent_required")
                val vault=ApplicationVault(this@EngineService)
                return synchronized(operations) {when(operation) {
                    "check_controller" -> EmbeddedEngine(this@EngineService).inspectController(controller,pin,clusterId).toString()
                    "engine_info" -> EmbeddedEngine(this@EngineService).info().toString()
                    "app_provision" -> vault.provision().toString()
                    "native_context_init" -> NativeNodeContext(this@EngineService,vault).initialize().toString()
                    "native_context_status" -> NativeNodeContext(this@EngineService,vault).status().toString()
                    "native_tls_prepare" -> NativeNodeContext(this@EngineService,vault).prepareTls().toString()
                    "quick_join" -> NativeNodeContext(this@EngineService,vault).join(requestId,controller,pin,clusterId,name,code).toString()
                    "resume_join" -> NativeNodeContext(this@EngineService,vault).resume().toString()
                    "replace_join_code" -> NativeNodeContext(this@EngineService,vault).replaceCode(code).toString()
                    "save_join_draft" -> vault.saveDraft(requestId,controller,pin,clusterId,name,code).toString()
                    "draft_status" -> vault.draftSummary().toString()
                    "probe_private_volume" -> PrivateProbeStorage(this@EngineService,vault).probe().toString()
                    "volumes" -> PrivateProbeStorage(this@EngineService,vault).status().toString()
                    "node_status" -> (nodeSession?.status() ?: JSONObject().put("state","STOPPED")).toString()
                    "stop_owned" -> {nodeSession?.close();nodeSession=null;JSONObject().put("owned",false).put("state","STOPPED").toString()}
                    else -> error("native_runtime_unqualified")
                }}
            } catch (_: IdentityLocked) { return error("identity_locked") }
            catch (_: IllegalArgumentException) { return error("invalid_request") }
            catch (_: Exception) { return error("operation_unavailable") }
        }
    }
    private fun error(code: String)=JSONObject().put("ipc_version",1).put("ok",false).put("error",code).toString()
    private fun status()=JSONObject().put("ipc_version",1).put("state","FOUNDATION")
        .put("engine","NOT SUPPORTED").put("controller","UNKNOWN").put("node","UNKNOWN")
        .put("node_id",JSONObject.NULL).put("cluster_id",JSONObject.NULL).put("writer_authority",false)
        .put("storage_approved",JSONObject.NULL).put("failure_domain_approved",JSONObject.NULL)
        .put("owned_node",false).put("runtime_start_supported",false)
        .put("device_policy",NativeDeviceGate.state())
        .put("application_identity",if(NativeDeviceGate.allowed())ApplicationVault(this).state() else JSONObject().put("state","NOT_ACCESSED"))
    override fun onBind(intent: Intent): IBinder=binder
    override fun onDestroy() {
        val owned=synchronized(operations) {nodeSession.also {nodeSession=null}}
        Thread({try {owned?.close()}catch(_:Exception){}},"asc-owned-node-stop").start()
        super.onDestroy()
    }
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        stopSelf(startId) // No background/boot/node launch; unqualified FGS stays absent.
        return START_NOT_STICKY
    }
}
