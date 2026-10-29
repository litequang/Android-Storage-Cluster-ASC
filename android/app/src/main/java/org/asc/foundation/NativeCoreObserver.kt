package org.asc.foundation

import android.content.Context
import com.chaquo.python.PyObject
import com.chaquo.python.Python
import org.json.JSONObject

/** Existing canonical Python gateway client. Only volatile owner session in RAM. */
class NativeCoreObserver(private val context:Context) {
    private var client:PyObject?=null
    private fun result(value:PyObject):JSONObject {
        val encoded=Python.getInstance().getModule("json").callAttr("dumps",value).toString()
        // Keep Binder payload safely bounded; never silently truncate healthy data.
        if(encoded.toByteArray().size>192*1024)return unknown("observer_view_too_large")
        return JSONObject(encoded)
    }
    fun login(endpoint:String,pin:String,cluster:String,epoch:String,mode:String,code:String):JSONObject {
        ApplicationVault(context).requireIdentity() // Check existing key, never provision.
        EmbeddedEngine(context)
        close()
        val candidate=Python.getInstance().getModule("asc.observability.native")
            .callAttr("NativeObserver",endpoint,pin,cluster,epoch,mode)
        return try {
            val view=result(candidate.callAttr("login",code))
            client=candidate;view
        }catch(_:Exception){try {candidate.callAttr("close")}catch(_:Exception){};unknown("observer_login_unconfirmed")}
    }
    fun state():JSONObject {
        ApplicationVault(context).requireIdentity()
        return client?.let {result(it.callAttr("state"))} ?: unknown("observer_login_required")
    }
    fun close():JSONObject {
        val previous=client;client=null
        try {previous?.callAttr("close")}catch(_:Exception){}
        return unknown("observer_logged_out")
    }
    companion object {
        fun unknown(reason:String)=JSONObject().put("observer_version",1).put("read_only",true)
            .put("writer_authority",false).put("runtime",JSONObject().put("state","UNKNOWN")
                .put("quorum_available",JSONObject.NULL).put("leader_confirmed",false))
            .put("native_observer",JSONObject().put("state","UNKNOWN").put("error",reason).put("session_persistence","RAM_ONLY"))
    }
}
