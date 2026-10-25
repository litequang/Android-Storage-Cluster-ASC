# Android foundation toolchain / reproduction

Scope: development workspace, never a phone/production/Termux installation.
Pinned artifact URLs/SHA256 in android/toolchain-lock.json. Vendor repository XML
also supplied SHA1 for SDK archives, verified before extraction. Gradle wrapper
verifies the independent official SHA256; Gradle verification-metadata records
Maven artifacts fetched over authenticated HTTPS (initial trust-on-first-fetch,
not a publisher signature). No dependency source patched/system packages installed.

Qualified BUILD tools: Temurin JDK17.0.21+9, Gradle8.11.1, AGP8.9.2, Kotlin2.2.20,
compile/target35,min26,buildtools35.0.0. ADB37.0.1/emulator37.2.12/AOSP35x86_64
binaries verified; emulator runtime is NOT yet qualified. Original system only
JRE21, not a JDK. All downloaded tools/cache/signing live outside repository under
/workspace/asc-android-dev. Keep inherited proxy/CA; no direct-network fallback.

Official requirements checked2026-10-25:
- https://developer.android.com/build/releases/past-releases/agp-8-9-0-release-notes
  AGP8.9: API35 maximum, Gradle8.11.1, JDK17, buildtools35.0.0.
- https://kotlinlang.org/docs/gradle-configure-project.html
  Kotlin2.2.20 supports Gradle7.6.3–8.14 and AGP7.3.1–8.11.1.
- https://developer.android.com/develop/background-work/services/bound-services
  Bind interface is distinct from lifecycle; per-call caller checks required.
- https://developer.android.com/guide/topics/permissions/defining
  Signature permissions are signing-certificate based, not a package-name trust rule.
- https://developer.android.com/develop/background-work/services/fgs/service-types
- https://developer.android.com/develop/background-work/services/fgs/timeout
  Android14+ declares FGS type/permission; Android15 dataSync/mediaProcessing time
  budgets and onTimeout apply; no background/boot auto-start or idle mock FGS.
- https://chaquo.com/chaquopy/doc/16.1/android.html
  Proposed embedded Python16.1, AGP7–8.13,minSDK24, Python3.13 support. Actual existing
  Engine/Node acceptance remains a separate gate, never inferred from JNI packaging.

## Build (workspace)

Select private development locations, install official matching SDK/JDK/Gradle from
checked locks with vendor tools/license review. Never copy Termux state. In this
Cloud environment existing activation selects ONLY task-local environment:

```sh
source /workspace/asc-android-dev/activate.sh
android/gradlew --no-daemon -p android :app:assembleDebug :app:testDebugUnitTest :app:assembleDebugAndroidTest
```

JDK compiler required, Java runtime alone insufficient. SDK root contains platforms/
android-35,build-tools/35.0.0 and platform-tools. ANDROID_USER_HOME/GRADLE_USER_HOME
must be private workspace dirs. Preserve debug signing key privately across app
upgrade tests; do not publish it. Debug APK has public signing certificate only,
is not production-signed or a public release. Do not uninstall/clear app data to
simulate successful state preservation. Existing Core candidate0.4.3 stays unchanged.

## Owned emulator gate

No /dev/kvm in Cloud. Software emulator is attempted with -accel off, never a KVM
permission/root/system workaround. Launcher parent must remain alive; first attempt
was reaped on parent exit and second met retained AVD lock. Preserve old AVDs and
use a NEW synthetic AVD; never delete an unknown lock. Private adb server uses
`adb -L tcp:5038 nodaemon server` (default loopback; hostname form not supported by
this adb listener). Separate retained foreground tool/session required. Never
connect/discover physical devices. Only known task-owned emulator5554/5555.

```sh
# Isolated development shell; never use a real-device serial.
export ANDROID_AVD_HOME=/workspace/asc-android-dev/user/avd
export ANDROID_EMULATOR_HOME=/workspace/asc-android-dev/user/emulator
export ANDROID_ADB_SERVER_PORT=5038
emulator -avd ASC_API35_ATTEMPT2 -port 5554 -no-window -no-audio \
  -no-boot-anim -no-snapshot -accel off -gpu swiftshader_indirect -memory 2048 -cores 2
```

A fresh AVD config points at checked system-images/android-35/default/x86_64.
Require actual boot_completed=1, install, launch and instrumentation evidence.
No emulator PASS from a running host process, build or guessed boot delay. At this
checkpoint ADB boot/runtime is NOT TESTED/NOT QUALIFIED; final status in4.2 acceptance.
No broad adb devices/USB/phone access. Keep emulator/server OWN process handles and
stop only those; retained synthetic files are private artifacts, not Git inputs.
