plugins { id("com.android.application"); id("org.jetbrains.kotlin.android"); id("com.chaquo.python") }
android {
    namespace = "org.asc.foundation"
    compileSdk = 35
    defaultConfig {
        applicationId = "org.asc.foundation"
        minSdk = 26
        targetSdk = 35
        ndk { abiFilters += listOf("arm64-v8a", "x86_64") }
        versionCode = 2
        versionName = "0.2.0-foundation"
        testInstrumentationRunner = "org.asc.foundation.UpgradeQualificationRunner"
    }
    buildFeatures { aidl = true; buildConfig = true }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    kotlinOptions { jvmTarget = "17" }
}
dependencies {
    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test:runner:1.6.2")
    androidTestImplementation("androidx.test:core:1.6.1")
    androidTestImplementation("androidx.test.ext:junit:1.2.1")
}

// Copy ONLY canonical public Core Python into generated build assets. No fork,
// tests, private state, source mutation or Termux files enter the APK.
val syncAscSources by tasks.registering(Sync::class) {
    from(rootProject.projectDir.parentFile.resolve("asc")) { include("**/*.py"); into("asc") }
    into(layout.buildDirectory.dir("generated/asc-python"))
}
chaquopy {
    defaultConfig {
        version = "3.13"
        buildPython(System.getenv("ASC_ANDROID_BUILD_PYTHON") ?: "python3.13")
    }
    sourceSets { getByName("main") { srcDir(layout.buildDirectory.dir("generated/asc-python")) } }
}
tasks.matching { it.name.contains("Python") }.configureEach { dependsOn(syncAscSources) }
