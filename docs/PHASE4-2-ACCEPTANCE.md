# Phase4.2 acceptance

**NOT ACCEPTED — development/toolchain qualification in progress.**
Branch feature/phase4-2-android-native fromf42fffe Phase4.1. No production release.
Tool build PASS !=emulator runtime PASS !=physical-device PASS. Full final Python/
Go/Android/security/package/fault gates still pending. No historical full reused.

Required: versioned private Binder/scopes/consent/UID+signature denial; existing real
Engine packaging/actual Android I/O proof before any native Node claim; Keystore
loss/restart/no identity regeneration; approved private storage probe/readback/SHA/
fsync/quota/identity/refusal; pinned TLS/Quick Join/pending/Controller loss if supported;
actual UI/network/background/foreground/upgrade/lifecycle/ownership/emulator tests.
Anything unavailable is BLOCKED/NOT TESTED, never mock PASS. See progress exact runs.

All real phones/ZTE/Bphone/M51, physical media/power loss, Termux->APK migration,
Android Raft/GC/failover and writable disaster recovery remain NOT TESTED/BLOCKED.
No cross-UID Termux access or state copying. No quorum/Leader/fencing reconstruction.

4.2a BUILD toolchain qualified: corrected APK/test APK/2 JVM tests PASS, wrapper
SHA/dependency inventory present. Emulator35 software boot/ADB NOT QUALIFIED,
missing KVM; see ANDROID-TOOLCHAIN and progress for actual attempts. Native runtime
qualification remains mandatory before any runtime/Node claim. Full scope NOT ACCEPTED.

4.2b.1 actual API35 emulator: boot1, APKs installed,4 Android instrumentation
PASS47.602s;7 JVM PASS/build PASS. Actual private own-UID Binder/consent/denial
and Activity launch only. Native Node/embedded Engine/Keystore/storage/enrollment/
foreign caller/lifecycle/network/upgrade/full final gates remain PENDING.
