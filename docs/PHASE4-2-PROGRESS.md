# Phase4.2 progress / independent handoff

Branch feature/phase4-2-android-native; verified Phase4.1 baseline
f42fffe7aa3fac8884d169bed61d884b0d777b33. GitHub200/fetch/advertised baseline match;
initial tree clean, no existing4.2 branch. No original branch changed, no reset/merge.
Read AGENTS/mandatory ordered docs then7 required4.1/API/native/operations documents.

| Checkpoint | State |
|---|---|
|4.2a|PUSH/REMOTE VERIFIED8667923 +audit follow-up a6e4d7e; build tools PASS; emulator35 now booted|
|4.2b.1|PUSH/REMOTE VERIFIED677e28ac5cff008e4b869847ac6c39bb51d71266;7 JVM/4 Android PASS|
|4.2b.2|PUSH/REMOTE VERIFIED5ac246aa27f78e0c979cd0674f127939331cce26;local Engine PASS, Node BLOCKED|
|4.2c|READY:7 JVM/5 Linux adapter/11 Android PASS;Keystore/private probe;SAF unsupported|
|4.2d|NOT STARTED|
|4.2e|NOT STARTED|

Tools/logs: /workspace/asc-android-dev (activate.sh), /workspace/work/phase4-2;
no private state/signing/SDK/cache in Git. Existing Python/Go activate.sh unchanged.
Current managed network spec87 unrestricted/enforced/current, no VPN. Proxy/CA retained.
System had only JRE21.0.12.1, no compiler/SDK/Gradle/ADB/emulator. Added Temurin
17.0.21+9 (official SHA256), Gradle8.11.1 (official SHA256), Android commandline/
SDK35/build-tools35/platform-tools37.0.1/emulator37.2.12/AOSP35x86_64 with official
repository SHA1 plus independently recorded SHA256. Official AGP8.9.2 supports API35,
requires Gradle8.11.1/JDK17/buildtools35. Kotlin2.2.20 compatibility includes these.
Android target35/min26 foundation app is not a production package.

First Gradle main APK compiled; instrumentation failed because legacy android.test
classes absent fromSDK35. Fixed to AndroidX Test runner/core/ext-junit, no tests
removed/weakened. Corrected build/unit/test APK PASS70tasks40s; wrapper checksum/
verification-metadata repeat pending. Unit2cases preserve UNKNOWN vs0/version refusal.
No emulator result reused/faked. First emulator launcher exited its parent and tools
reaped its children; fixed development harness to retain OWN Popen parent/server.
Private ADB5038/owned emulator5554 only. Missing /dev/kvm, software -accel off
attempt running. No phone/production/M51/system/Boot access or runtime guard changes.

Next only after a targeted/push/remote gate: actual private native Service/IPC and
existing Python Engine integration investigation. Read PLAN/ACCEPTANCE; keep native
FOUNDATION and mark blockers if actual Node/enrollment cannot run. Never new Kotlin
Catalog/Storage/enrollment authority, copied Termux state or mocked online proof.

4.2a final wrapper command assembleDebug/testDebugUnitTest/assembleDebugAndroidTest
--write-verification-metadata sha256: BUILD SUCCESSFUL41s. Actual corrected JVM XML:
2tests0fail/error/skip, APK and instrumentation APK exist. Pin wrapper officialSHA,
toolchain-lock records all actual checksums. Emulator35 software host process is
alive but ADB not boot-ready; missingKVM, initial parent-reaping/staleAVD and private
adb hostname-listener errors diagnosed (use default-loopback tcp:5038). These are
NOT emulator PASS; actual runtime qualification remains e. Build toolchain permits
independent native foundation work, never claims a Node. Next b after push/remote.

4.2a source8667923 pushed/remote verified. Publication review caught generated
Windows gradlew.bat CRLF as trailing whitespace; the shell did not stop before
commit. Corrected line endings in a NORMAL follow-up (no history rewrite) and
reran complete tracked/index audit before moving on. No security/test gate weakened.

## 4.2b.1 actual private Binder foundation

a6e4d7ebb684d3689d309df82d0a191c30e4ed22 pushed/remote matched BEFORE b.1.
EngineService nonexported/signature permission +per-call UID/signature; typed
version1 AIDL,8192 aggregate bound/canonical IDs/private HTTPS/pin/cluster/code/
trust input, explicit UI consent. No paths/PIDs/commands/second backend, foreign
process kill or Node lifecycle. Unqualified native runtime refuses; status is
FOUNDATION/UNKNOWN with no Node/Cluster identity. No idle mock FGS/boot/startup.

Gradle assembleDebug/testDebugUnitTest/assembleDebugAndroidTest PASS70tasks28s;
7 JVM tests0fail/error/skip. Actual AOSP API35 software emulator boot_completed1
and installed BOTH APKs Success on task-owned127.0.0.1:5555/privateADB5038.
`adb -P 5038 -s 127.0.0.1:5555 shell am instrument -w -r
 org.asc.foundation.test/androidx.test.runner.AndroidJUnitRunner`:
**4 Android tests PASS47.602s**, own UID Binder status/consent/version/dangerous
operation/runtime refusal +Activity launch. This is actual emulator runtime,
NOT native Node/engine/enrollment acceptance. Cross-UID attacker still futuregate.
No KVM/phones/M51/Termux/system changes. a emulator earlier pending status now
superseded by observed boot +actual4 tests, not a build-based inference.
Next b.2 ONLY after normal commit/push/remote: embedded original Engine investigation.

## 4.2b.2 embedded canonical Python Engine

b.1 pushed/remote matched677e28a BEFORE b.2. Chaquopy16.1/Python3.13 copies only
existing Core public Python into generated APK assets; x86_64/arm64 ABIs. No asc/
source edit/fork/second Kotlin Engine. Native info imports actual SSL/SQLite/Core;
internal instrumentation does fresh synthetic direct existing Engine I/O/restart,
not a joined Node/network service. Existing/root/link refusal gets Linux actualI/O
coverage. Initial5-test Android run had1 real unsafe_path failure: Context path
/data/user/0 alias fails Core no_links. Fixed TEST approved new root selection to
trusted Context.canonicalFile BEFORE registration; no Core guard/marker change.

Final assembleDebug/testDebugUnitTest/assembleDebugAndroidTest BUILD PASS21s,
7 JVM PASS.3 actual Linux adapter tests PASS0skip/fail0.166s. Both APKs installed
on owned API35 emulator; **5 actual Android instrumentation PASS27.733s** incl
real Python Engine stream/commit/download SHA/verify/fsync/manifest restart. No
native Node or network enrollment claim. See ANDROID-ENGINE-INTEGRATION for exact
blocker: missing reviewed native in-process TLS identity/enrollment/agent/lifecycle
provider replacing old CLI/HOME/subprocess/OpenSSL assumptions; NEVER monkeypatch
or bypass those guards. Node start/Quick Join stay explicit unsupported. FGS/
notification/background Node remains BLOCKED, not idle fake service.
Next c only after normal commit/push/remote match: app Keystore/private probe/draft
foundation. Draft !=Core enrollment, local probe !=approved cluster Storage Node.

## 4.2c Keystore/private storage foundation

b.2 pushed/remote matched5ac246a BEFORE c. App identity explicit/independent,
AndroidKeyStoreAES256/GCM/randomIV/purpose+appAAD/canary, encrypted DRAFT_NOT_SENT,
no Node/token/Cluster creation. Lost key/corrupt ciphertext/future schema holds
identity, no automatic regen. Actual key deletion tested, hardware/biometric
invalidation NOT TESTED. Fixed app-private Core capability volume/read-only status/
quota-reserve/actual bounded probe, persistent bindings, no second Engine/Catalog.
APP_PRIVATE_PROBE_ONLY is not enrolled/approved cluster storage. SAF explicit
unsupported seam, no URI/permission/filesystem fallback. No idle FGS/Node startup.

Final Gradle build/unit/testAPK PASS30s,7 JVM PASS;5 Linux adapter PASS0.202s.
Both APKs installed on owned API35; **11 instrumentation PASS50.003s**, actual
nonexportable key/restart/encrypted draft/key deletion/no regen, future schema/
corrupt cipher, real probe/fsync/identity, quota/reserve/no-write denials, actual
unprivileged private staging0500EACCES (only own fixture, restored0700), marker
mismatch, missing manifest/replaced root cannot recreate state, corrupt committed
Core object retained, SAF refusal. Earlier9case PASS53.572s before extra root/SAF
cases; final11 is the checkpoint evidence. No tests weakened/skipped. Native c
versionCode1 APK retained PRIVATELY for later exact app upgrade test; not a release.
Node/enrollment/TLS runtime and FGS remain BLOCKED. Next d ONLY after push/remote:
Vietnamese native UI +public pinned Controller validation, no fake cluster data.
