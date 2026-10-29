package org.asc.foundation

import java.net.URI

/** Navigation to an existing owner Dashboard, not a browser/local-engine bridge. */
object DashboardLink {
    fun origin(value:String):String {
        require(value.length in 1..2048)
        val uri=URI.create(value)
        require(uri.scheme=="https" && uri.rawUserInfo==null && uri.rawQuery==null && uri.rawFragment==null &&
            uri.rawPath in listOf("","/") && uri.port in 1024..65535)
        NativeTLSListener.approvedAddress(uri.host ?: "")
        return "https://${uri.host}:${uri.port}"
    }
}
