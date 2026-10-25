package org.asc.foundation
import android.os.Build

/** Additional native entry fence. NEVER authorizes Node/Leader/GC or overrides Core. */
object NativeDeviceGate {
    fun classify(manufacturer:String,model:String,device:String,product:String,hardware:String,fingerprint:String,sdk:Int,debug:Boolean):String {
        val fields=listOf(manufacturer,model,device,product).map {it.lowercase()}
        if(fields.any {it.contains("m51") || it.contains("sm-m515")})return "PROTECTED"
        if(sdk<26)return "UNKNOWN_DEVICE"
        if(debug && hardware.lowercase() in setOf("ranchu","goldfish") && product.lowercase().contains("sdk") &&
            (fingerprint.lowercase().contains("generic") || fingerprint.lowercase().contains("sdk")))return "SYNTHETIC_EMULATOR"
        val m=model.lowercase();val vendor=manufacturer.lowercase()
        if(m.isBlank() || vendor.isBlank() || m=="unknown" || vendor=="unknown")return "UNKNOWN_DEVICE"
        val known=(vendor.contains("zte") && (m in setOf("9045","zte9045","zte 9045") || m.contains("v40"))) ||
            ((vendor.contains("bphone") || vendor.contains("bkav")) && m.contains("a40")) ||
            (vendor.contains("sony") && (m.contains("xz3") || m in setOf("h8416","h9436","h9493")))
        return if(known)"KNOWN_TEST_MODEL_NOT_ACCEPTED" else "UNKNOWN_DEVICE"
    }
    fun state()=classify(Build.MANUFACTURER,Build.MODEL,Build.DEVICE,Build.PRODUCT,Build.HARDWARE,Build.FINGERPRINT,Build.VERSION.SDK_INT,BuildConfig.DEBUG)
    fun allowed()=state() in setOf("SYNTHETIC_EMULATOR","KNOWN_TEST_MODEL_NOT_ACCEPTED")
}
