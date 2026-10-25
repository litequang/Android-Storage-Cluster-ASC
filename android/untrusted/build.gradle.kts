plugins { id("com.android.application"); id("org.jetbrains.kotlin.android") }
android {
    namespace="org.asc.untrusted"
    compileSdk=35
    defaultConfig {applicationId="org.asc.untrusted";minSdk=26;targetSdk=35;versionCode=1;testInstrumentationRunner="androidx.test.runner.AndroidJUnitRunner"}
    val passwordFile=System.getenv("ASC_ANDROID_UNTRUSTED_PASSWORD_FILE")
    if(passwordFile!=null) {
        signingConfigs.create("untrusted") {
            storeFile=file(System.getenv("ASC_ANDROID_UNTRUSTED_STORE"))
            storePassword=file(passwordFile).readText().trim();keyPassword=storePassword;keyAlias="untrusted"
        }
        buildTypes.getByName("debug").signingConfig=signingConfigs.getByName("untrusted")
    }
    compileOptions {sourceCompatibility=JavaVersion.VERSION_17;targetCompatibility=JavaVersion.VERSION_17}
    kotlinOptions {jvmTarget="17"}
}
dependencies {androidTestImplementation("androidx.test:runner:1.6.2");androidTestImplementation("androidx.test.ext:junit:1.2.1")}
