package org.asc.foundation
import org.junit.Assert.*
import org.junit.Test

class NativeTLSListenerPolicyTest {
    @Test fun explicitNumericPrivateBindOnlyWithoutDnsOrWildcard() {
        for(host in listOf("127.0.0.1","10.2.3.4","172.16.0.1","192.168.2.3"))
            assertEquals(host,NativeTLSListener.approvedAddress(host).hostAddress)
        for(host in listOf("0.0.0.0","8.8.8.8","192.0.2.1","172.32.0.1","localhost","::","::1","192.168.01.2"," 127.0.0.1","127.0.0.1/24"))
            assertThrows(IllegalArgumentException::class.java) {NativeTLSListener.approvedAddress(host)}
    }
}
