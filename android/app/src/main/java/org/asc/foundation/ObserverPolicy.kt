package org.asc.foundation

/** Separate owner observation session, never a Node credential or writer operation. */
object ObserverPolicy {
    fun validate(version:Int,id:String,operation:String,endpoint:String,pin:String,
                 cluster:String,epoch:String,mode:String,code:String,trusted:Boolean) {
        RequestPolicy.validate(version,id,"status","","","","","",false)
        require(operation in setOf("login","state","logout")) {"unsupported_observer_operation"}
        require(listOf(id,operation,endpoint,pin,cluster,epoch,mode,code).sumOf {it.toByteArray().size}<=8192) {"request_limit"}
        if(operation!="login") {
            require(listOf(endpoint,pin,cluster,epoch,mode,code).all {it.isEmpty()} && !trusted) {"unexpected_fields"}
            return
        }
        RequestPolicy.validate(version,id,"check_controller",endpoint,pin,cluster,"","",false)
        require(java.util.UUID.fromString(epoch).toString()==epoch) {"invalid_epoch"}
        require(mode in setOf("core-quorum","recovery-read-only")) {"invalid_observer_mode"}
        require(trusted && code.matches(Regex("[A-Za-z0-9_-]{16,128}"))) {"observer_trust_or_code_required"}
    }
}
