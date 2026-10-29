package org.asc.foundation
import org.junit.Assert.*
import org.junit.Test
class ContractTest {
    @Test fun unsupportedVersionsRefuse() {
        Contract.version(1)
        for (version in listOf(-1,0,2,Int.MAX_VALUE)) {
            assertThrows(IllegalArgumentException::class.java) { Contract.version(version) }
        }
    }
    @Test fun absentMetricsAreNotZero() {
        assertEquals("UNKNOWN", Contract.measured(null))
        assertEquals("0", Contract.measured(0L))
    }
}
