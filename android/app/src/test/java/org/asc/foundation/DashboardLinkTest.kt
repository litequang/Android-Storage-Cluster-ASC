package org.asc.foundation
import org.junit.Assert.*
import org.junit.Test

class DashboardLinkTest {
    @Test fun privateHttpsRootKeepsBrowserTrustAndDoesNotCarryCredentials() {
        assertEquals("https://192.168.1.2:8444",DashboardLink.origin("https://192.168.1.2:8444/"))
        assertEquals("https://127.0.0.1:8444",DashboardLink.origin("https://127.0.0.1:8444"))
    }
    @Test fun publicCleartextSecretsAndArbitrarySchemesRefuse() {
        for(url in listOf("http://192.168.1.2:8444","https://example.com:8444","https://8.8.8.8:8444",
            "https://0.0.0.0:8444","https://192.168.1.2:8444?token=secret","https://user@192.168.1.2:8444",
            "https://192.168.1.2:8444/path","javascript:alert(1)","file:///data/data","https://192.168.1.2:8444/#code"))
            assertThrows(IllegalArgumentException::class.java){DashboardLink.origin(url)}
    }
}
