package org.asc.foundation

import org.junit.Assert.assertThrows
import org.junit.Test

class ObserverPolicyTest {
    private val id="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    private fun call(op:String="login",ep:String="https://192.168.1.2:8445",pin:String="a".repeat(64),cluster:String=id,epoch:String=id,mode:String="core-quorum",code:String="owner_code_not_a_node_code",trust:Boolean=true)=
        ObserverPolicy.validate(1,id,op,ep,pin,cluster,epoch,mode,code,trust)
    @Test fun exactReadOnlyModeTrustAndPublicBindingRequired() {
        call();call(mode="recovery-read-only")
        for(mode in listOf("single-writer-demo","core","auto",""))assertThrows(IllegalArgumentException::class.java){call(mode=mode)}
        assertThrows(IllegalArgumentException::class.java){call(trust=false)}
        assertThrows(IllegalArgumentException::class.java){call(epoch="1-1-1-1-1")}
        assertThrows(IllegalArgumentException::class.java){call(code="123456abcdef")}
        for(ep in listOf("http://192.168.1.2:8445","https://8.8.8.8:8445","https://host:8445","https://192.168.1.2:8445/api/state"))
            assertThrows(IllegalArgumentException::class.java){call(ep=ep)}
    }
    @Test fun refreshLogoutCannotSmuggleCredentialsOrMutations() {
        for(op in listOf("state","logout")) {
            call(op,"","","","","","",false)
            assertThrows(IllegalArgumentException::class.java){call(op)}
        }
        for(op in listOf("approve","gc","upload","download","promote","membership","recovery_activate","shell"))
            assertThrows(IllegalArgumentException::class.java){call(op)}
    }
}
