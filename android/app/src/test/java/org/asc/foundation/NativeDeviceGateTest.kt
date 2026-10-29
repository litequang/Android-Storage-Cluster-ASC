package org.asc.foundation
import org.junit.Assert.*
import org.junit.Test
class NativeDeviceGateTest {
    @Test fun protectedSecondaryPropertiesCannotHideBehindKnownOrEmulator() {
        assertEquals("PROTECTED",NativeDeviceGate.classify("zte","9045","m51","sdk","ranchu","generic/sdk",35,true))
        assertEquals("PROTECTED",NativeDeviceGate.classify("Samsung","SM-M515F","x","x","x","x",30,true))
    }
    @Test fun unknownAndReleaseEmulatorAreNotAnOverride() {
        assertEquals("UNKNOWN_DEVICE",NativeDeviceGate.classify("unknown","unknown","x","x","x","x",35,true))
        assertEquals("UNKNOWN_DEVICE",NativeDeviceGate.classify("Google","sdk model","ranchu","sdk","ranchu","generic/sdk",35,false))
        assertEquals("SYNTHETIC_EMULATOR",NativeDeviceGate.classify("Google","sdk model","ranchu","sdk","ranchu","generic/sdk",35,true))
    }
    @Test fun knownTestModelIsNotRuntimeAcceptance() {
        for ((vendor,model) in listOf("ZTE" to "9045","Bphone" to "A40","Sony" to "H9436"))
            assertEquals("KNOWN_TEST_MODEL_NOT_ACCEPTED",NativeDeviceGate.classify(vendor,model,"x","x","x","x",30,true))
    }
}
