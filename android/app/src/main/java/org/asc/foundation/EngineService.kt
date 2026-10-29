package org.asc.foundation
import android.app.Service
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Intent
import android.content.pm.PackageManager
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.Binder
import android.os.IBinder
import android.os.Process
import org.json.JSONObject
import java.util.Timer
import java.util.TimerTask

/** Private application bridge. No Node runtime is started by binding/restart. */
class EngineService : Service() {
    private fun caller() {
        val uid=Binder.getCallingUid()
        RequestPolicy.caller(uid,Process.myUid(),packageManager.checkSignatures(uid,Process.myUid())==PackageManager.SIGNATURE_MATCH)
    }
    private val operations=Any()
    private val observerOperations=Any()
    private var coreObserver:NativeCoreObserver?=null
    private var nodeSession:NativeNodeSession?=null
    private var watcher:Timer?=null
    @Volatile private var foreground=false
    private fun stopNode() {synchronized(operations) {
        nodeSession?.close();nodeSession=null
        watcher?.cancel();watcher=null
        foreground=false;stopForeground(STOP_FOREGROUND_REMOVE);stopSelf()
    }}
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
        override fun observeCore(version:Int,requestId:String,operation:String,endpoint:String,pin:String,
            clusterId:String,epoch:String,mode:String,code:String,trustConfirmed:Boolean):String {
            caller()
            return synchronized(observerOperations) {try {
                ObserverPolicy.validate(version,requestId,operation,endpoint,pin,clusterId,epoch,mode,code,trustConfirmed)
                if(operation=="logout")return@synchronized (coreObserver?.close() ?: NativeCoreObserver.unknown("observer_logged_out")).toString()
                if(!NativeDeviceGate.allowed())return@synchronized error("device_not_qualified")
                if(!getSharedPreferences("local-consent",MODE_PRIVATE).getBoolean("granted",false))return@synchronized error("consent_required")
                val observer=coreObserver ?: NativeCoreObserver(this@EngineService).also {coreObserver=it}
                (if(operation=="login")observer.login(endpoint,pin,clusterId,epoch,mode,code) else observer.state()).toString()
            }catch(_:IdentityLocked){NativeCoreObserver.unknown("identity_locked").toString()}
            catch(_:IllegalArgumentException){error("invalid_request")}
            catch(_:Exception){NativeCoreObserver.unknown("observer_unavailable").toString()}}
        }
        override fun configureNodeStorage(version:Int,requestId:String,quotaBytes:Long,reserveBytes:Long):String =
            nodeAction(version,requestId) {it.configure(quotaBytes,reserveBytes)}
        override fun startNode(version:Int,requestId:String,host:String,port:Int):String =
            nodeAction(version,requestId) {session ->
                if(Build.VERSION.SDK_INT>=33 && checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED)
                    return@nodeAction JSONObject(error("notification_required"))
                val result=session.start(host,port)
                try {startForegroundService(Intent(this@EngineService,EngineService::class.java).setAction(RUN_NODE))}
                catch(e:Exception){session.close();throw e}
                result
            }
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
                    "change_controller" -> if(nodeSession?.status()?.optString("state") in setOf("RUNNING","STOPPING"))error("stop_node_before_controller_change")
                        else NativeNodeContext(this@EngineService,vault).changeController(controller,pin,clusterId).toString()
                    "save_join_draft" -> vault.saveDraft(requestId,controller,pin,clusterId,name,code).toString()
                    "draft_status" -> vault.draftSummary().toString()
                    "probe_private_volume" -> PrivateProbeStorage(this@EngineService,vault).probe().toString()
                    "volumes" -> PrivateProbeStorage(this@EngineService,vault).status().toString()
                    "node_status" -> (nodeSession?.status() ?: JSONObject().put("state","STOPPED")).put("foreground_service",foreground).toString()
                    "stop_owned" -> {stopNode();JSONObject().put("owned",false).put("state","STOPPED").toString()}
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
        watcher?.cancel();watcher=null
        Thread({synchronized(operations) {try {nodeSession?.close()}catch(_:Exception){};nodeSession=null}},"asc-owned-node-stop").start()
        Thread({synchronized(observerOperations) {coreObserver?.close();coreObserver=null}},"asc-observer-logout").start()
        super.onDestroy()
    }
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if(intent?.action==STOP_NODE) {
            Thread({try {stopNode()}catch(_:Exception){}},"asc-notification-stop").start()
        } else if(intent?.action==RUN_NODE && nodeSession!=null) {
            val manager=getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(NotificationChannel(CHANNEL,"ASC Storage Node",NotificationManager.IMPORTANCE_LOW))
            val stop=PendingIntent.getService(this,0,Intent(this,EngineService::class.java).setAction(STOP_NODE),PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
            val open=PendingIntent.getActivity(this,0,Intent(this,MainActivity::class.java),PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
            val notification=Notification.Builder(this,CHANNEL).setSmallIcon(android.R.drawable.stat_notify_sync)
                .setContentTitle("ASC Storage Node").setContentText("Phiên Node đang hoạt động · quyền ghi do Controller cấp")
                .setContentIntent(open).setOngoing(true).addAction(Notification.Action.Builder(null,"Dừng Node",stop).build()).build()
            if(Build.VERSION.SDK_INT>=29)startForeground(NOTIFICATION_ID,notification,ServiceInfo.FOREGROUND_SERVICE_TYPE_CONNECTED_DEVICE)
            else startForeground(NOTIFICATION_ID,notification)
            foreground=true
            if(watcher==null)watcher=Timer("asc-owned-node-health",true).apply {schedule(object:TimerTask(){override fun run(){
                try {synchronized(operations) {if(nodeSession?.status()?.optString("state")!="RUNNING")stopNode()}}
                catch(_:Exception){try {stopNode()}catch(_:Exception){}}
            }},5000,5000)}
        } else stopSelf(startId) // Restart/unknown intent never provisions or starts an Engine.
        return START_NOT_STICKY
    }
    companion object {
        const val CHANNEL="asc-native-node"
        const val NOTIFICATION_ID=42
        private const val RUN_NODE="org.asc.foundation.RUN_OWNED_NODE"
        private const val STOP_NODE="org.asc.foundation.STOP_OWNED_NODE"
    }
}
