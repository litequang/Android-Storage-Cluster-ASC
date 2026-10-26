package org.asc.foundation

import android.content.Context
import com.chaquo.python.Python
import com.chaquo.python.PyObject
import org.json.JSONObject
import javax.net.ssl.SSLContext

/** App-owned session only. Existing Core implements Storage/HTTP/heartbeat. */
internal class NativeListenerFactory {
    fun open(tls:SSLContext,host:String,port:Int):NativeTLSListener=NativeTLSListener(tls,host,port)
}

internal class NativeNodeSession(context:Context,vault:ApplicationVault) {
    init {EmbeddedEngine(context)}
    private val core=NativeNodeContext(context,vault)
    private var runtime:PyObject?=null
    private fun json(value:PyObject)=JSONObject(Python.getInstance().getModule("json").callAttr("dumps",value).toString())
    fun configure(quota:Long,reserve:Long):JSONObject {
        check(runtime==null) {"stop_node_before_configure"}
        return json(Python.getInstance().getModule("asc.node.storage").callAttr("NativeStorage",core.engineContext())
            .callAttr("configure",quota,reserve))
    }
    fun start(host:String,port:Int):JSONObject {
        if(runtime!=null)return status()
        require(port in 1024..65535)
        val python=Python.getInstance()
        val node=python.getModule("asc.node.runtime").callAttr("NativeRuntime",core.engineContext(),NativeListenerFactory(),core.runtimeProfile())
        val result=node.callAttr("start",host,port)
        runtime=node
        return json(result)
    }
    fun status():JSONObject=runtime?.let {json(it.callAttr("status"))}
        ?:JSONObject().put("state","STOPPED").put("writer_authority",false)
    fun close() {runtime?.callAttr("close");runtime=null}
}
