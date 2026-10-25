package org.asc.foundation
import org.junit.Assert.*
import org.junit.Test
class RequestPolicyTest {
    private val id="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    private fun call(op:String="status",ep:String="",pin:String="",cluster:String="",name:String="",code:String="",trust:Boolean=false)=RequestPolicy.validate(1,id,op,ep,pin,cluster,name,code,trust)
    @Test fun foreignUidAndSignerRefuse() {
        RequestPolicy.caller(100,100,true)
        for ((uid,signer) in listOf(101 to true,100 to false,101 to false))
            assertThrows(SecurityException::class.java) {RequestPolicy.caller(uid,100,signer)}
    }
    @Test fun managementEscapeIsNotAnOperation() {
        for(op in listOf("shell","init","approve","gc","promote","recovery_activate","node_stop_pid"))
            assertThrows(IllegalArgumentException::class.java) {call(op)}
    }
    @Test fun statusCannotSmuggleJoinOrTrustFields() {
        assertThrows(IllegalArgumentException::class.java) {call(ep="/tmp")}
        assertThrows(IllegalArgumentException::class.java) {call(trust=true)}
        call()
    }
    @Test fun numericPrivateHttpsAndExplicitTrustRequired() {
        fun join(endpoint:String="https://192.168.1.2:8443",trust:Boolean=true)=call("quick_join",endpoint,"a".repeat(64),id,"test","123456abcdef",trust)
        join()
        for(ep in listOf("http://192.168.1.2:8443","https://8.8.8.8:8443","https://host:8443","https://192.168.1.2:8443/../x","https://user@192.168.1.2:8443","https://192.168.1.2:8443?code=secret","https://192.168.001.2:8443"))
            assertThrows(IllegalArgumentException::class.java) {join(ep)}
        assertThrows(IllegalArgumentException::class.java) {join(trust=false)}
    }
    @Test fun oversizedSecretsAndMalformedIdsRefuse() {
        assertThrows(IllegalArgumentException::class.java) {call("quick_join",code="x".repeat(9000))}
        assertThrows(IllegalArgumentException::class.java) {RequestPolicy.validate(1,"1-1-1-1-1","status","","","","","",false)}
    }
}
