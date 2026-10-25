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

4.2b.2 actual API35:5 instrumentation PASS27.733s,7 JVM PASS,3 Linux adapter
PASS0.166s. Real canonical StorageEngine stream/commit/SHA/fsync/restart proven
without Core edits/guard bypass. First unsafe_path failure retained in progress;
new-root canonical Context selection fixed. Native Node/Quick Join/TLS identity/
agent/FGS provider still BLOCKED; library proof does not authorize runtime.

4.2c:11 actual API35 Android instrumentation PASS50.003s;7 JVM/5 Linux adapter
PASS (0.202s). Keystore/probe/root/corruption/capacity/realEACCES gates in progress.
SAF/nativeNode/FGS/network/upgrade/finalfull still unsupported/pending, not PASS.
Actual key deletion/loss PASS; biometric/hardware invalidation NOT TESTED.

4.2d actual API35:13 instrumentation PASS81.897s +offline1PASS13.375s/reconnect
1PASS10.946s,6 Python actual adapter/TLS PASS1.288s,7 JVM/build PASS. Public
Controller GET only, wrong pin/cluster refusal and no enrollment mutation. Native
UI uses measured sources/UNKNOWN, code clearing/trust guard; actual Node/enrollment/
cluster observer/FGS remains unsupported. Final e/source freeze/full gates pending.
