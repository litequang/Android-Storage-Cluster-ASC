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
|4.2c|PUSH/REMOTE VERIFIED29c2985c839c6b20a0f6a6f3f4142c38b2f20847;11 Android/5 Linux/7 JVM PASS|
|4.2d|PUSH/REMOTE VERIFIED8b901310da04f33e82165756d5bcd8ac36349d82;13 Android +offline1/reconnect1;6 Python/7 JVM PASS|
|4.2e.1|PUSH/REMOTE VERIFIED67fdd0c3ef4e3c5e2e684d2dbd7f1ce5f504cd3a; limited native FOUNDATION/dev TLS only|
|4.2e.2a|Targeted fixture fix PASS; full attempt1 ERROR recorded; push/remote then fresh317 restart|
|4.2e.2|PENDING new fresh full Python/Go/fault/package; NOT ACCEPTED|

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

## 4.2d Vietnamese native UI / real pinned Controller validation

c pushed/remote matched29c2985 BEFORE d. Four responsive native pages, real Build/
RAM/CPU/network/app key/private volume sources, UNKNOWN cluster/replica/quorum/
recovery without configured authenticated observer. Explicit consent, separate
application identity vsNode/Cluster, quota/reserve probe, code hidden/no autofill/
View-state, background clearing and generation guards. Manual public bindings +
owner trust confirmation, encrypted DRAFT_NOT_SENT only. No Node enrollment/FGS/
file replicas/second backend or mock online data. App versionCode2/version0.2.0-
foundation (Core stays0.4.3). Actual Core request_json does ONLY pinned public GET,
strict mode/cluster/schema; does not send code/grant or grant writer.

First UI build caught incorrect Kotlin trailing-lambda syntax; fixed. First host
harness used adb shell argument quoting incorrectly, so public fixture write failed;
fixed one literal run-as command with JSONstdin, no secret argument/shell interpolation.
No failed run counted as PASS, no gate weakened. Final Gradle build PASS27s,7 JVM;
6 actual Python TLS/adapter PASS1.288s. Actual API35 instrumentation **13PASS81.897s**
(incl visible native page/trust gate/background code clearing), actual retained-key
Controller stopped =>**offline1PASS13.375s**, restarted same registry/cert =>
**reconnect1PASS10.946s**, no enrollment rows/credentials generated. Wrong TLS pin/
Cluster ID denied over actual embedded Core transport, public data only.
Next e only after push/remote: untrusted caller/process death/network/app upgrade,
final applicable regressions/packaged APK/secrets audit. No production/phone claim.

## 4.2e.1 security/network/upgrade gates

d pushed/remote matched8b901310da04f33e82165756d5bcd8ac36349d82 BEFORE e.
Added explicit AIDL transaction0/1 ABI, native M51/unknown pre-state fence, actual
network callback/trust clearing, CE/DE cloud+D2D backup exclusion and distinct
signer/UID fixture. Fixed-scope qualification tools only accept task-owned numeric
loopback emulator with real qemu/hardware/boot proof; private new logs/state only.

First15-case run had1FAIL: WiFi-only fault left default cellular network alive.
Corrected fault to disable BOTH WiFi/cellular, require actual onLost+secret clearing,
restore both finally and require restored network. No assertion weakened/skipped.
Final Gradle assemble/unit/testAPK/untrusted/testAPK/lint PASS47s;10JVM0fail/skip.
Lint0errors/21warnings (VN-only strings17, verified pinned dependency3, durable
synchronous consent write1); Gradle9 deprecation remains, only8.11.1 qualified.

Actual API35 emulator corrected qualification:15 Android PASS123.313s; separate
different-signer app1PASS0.231s with actual UID/signature/permission/bind denial;
Controller stop1PASS12.648s, same-registry/cert reconnect1PASS12.594s; zero enrollment
rows, no Node credential issuance. Exact raw logs private e-runtime-qualified.
Main APK inventory109 canonical Core modules from byte-identical generated inputs,
ARM64+x86_64, apksigner verifies debug signature. No private state/key/test-only
classes in main package under inventory/pattern audit; not comprehensive binary SAST.

Fresh AVD ASC_UPGRADE_API35 software boot in progress, old AVD preserved and owned
process stopped through retained parent only. Exact prior c versionCode1 APK private
SHA7235444589ff0ae9fa3f56dfc4cc23bae910b46fdef27c290b021333959f6de9.
This is a private checkpoint build, NOT a released native APK or Termux archive.
Upgrade/actual process-death/version-downgrade refusal now PASS; see final receipt below.

Remaining implementation blocker: actual native Core enrollment/identity TLS/agent
provider with explicit app context (no CLI getpass/HOME/subprocess/OpenSSL bypass),
owned Node lifecycle and justified FGS. Public pinned GET +encrypted UNSENT form is
not Quick Join. Native observer unconfigured =>UNKNOWN. SAF/QR/hardware biometric
key invalidation/physical ARM64/Doze/production/Termux migration unqualified.
Full Phase4.2 NOT ACCEPTED; preserve independent qualified foundation checkpoints.

Publication review additionally caught a real UI race: a response queued before
network change could re-establish the old trust binding after the callback. Fixed
network change to advance UI generation/reset pending status; old worker callbacks
are discarded. Added controlled late Activity-worker response during ACTUAL WiFi/
cellular loss and strict no-delivery assertion (UI concurrency proof, not a mocked
Controller/Engine PASS). Rebuilt APK/unit/testAPK/lintPASS62s. All related emulator
gates will be rerun against this corrected exact APK before publication.

### Exact native upgrade final receipt

First custom runner manifest was overwritten by generated Gradle runner, so Android
could not find instrumentation; seed did NOT execute. Fixed TEST runner to extend
AndroidJUnitRunner, delegate normal JUnit when no fixed phase, select it in Gradle.
Resume requires exact installed base.apk SHA and ABSENT identity-v1/private-probe-v1/
upgrade-proof before seed; no reset/uninstall. First resume path validation correctly
refused Android randomized `~~` path; extended literal safe-character regex, no shell
interpolation. Both failed setup logs retained privately, never reported as PASS.

Final build/unit/testAPK/lintPASS65s (10JVM/0errors21lint warnings). Exact old native
0.1.0-foundation/versionCode1 checkpoint c SHA7235444589ff0ae9fa3f56dfc4cc23bae910b46fdef27c290b021333959f6de9, installed base APK SHA checked again;
new0.2.0-foundation/versionCode2 SHAab1b2da3797df93ea7fbc186866c187f8b04802f3b614fed4afcaa232fddf705.
Actual API35 fresh AVD PASS: old-APK seed, same-signer normal upgrade, exact retained
application UUID/Keystore canary/encrypted pending FORM request+bytes/Volume ID/marker/
committed object SHA and Core verify; actual force-stop/start then identical checks;
normal lower-version install refused INSTALL_FAILED_VERSION_DOWNGRADE then identical
checks. Test code never creates Node/Cluster authority, never copies Termux state.
Private e-upgrade-qualified-final/results.json records5 PASS gates; no native rollback/
Keystore restore/released APK or Termux migration claim. Main APK source/hash remained
unchanged by runner-only build. Final all-Android rerun against corrected race pending.

New upgrade AVD exposed real missing network precondition: WiFi enabled but not
connected. Initial full15 run227.242s had2FAIL (TLS +loss); corrected actual virtual
WLAN connection/observed default network/onAvailable BEFORE fault. Next full16 run
152.177s had1FAIL (TLS); actual network loss/late UI callback refusal now PASS. Direct
pinned primitive diagnostic (public error class only) confirmed ConnectionRefusedError
to10.0.2.2, INTERNET granted. No weakening/skip/HTTP/changed pin/proxy workaround.
Direct NAT remains NOT PASSED. An EXPLICIT development-only --host-transport
adb-reverse-loopback uses guest127.0.0.1, real existing Core TLS/expected pin/cluster,
owned no-rebind port mapping with scoped cleanup. Default stays NAT, no auto fallback.
Final full16 Android PASS on that dev transport; outage/reconnect finishing. This
proves native TLS/protocol in an isolated dev connection, NOT native LAN acceptance.
Main APK remainsab1b2da3797df93ea7fbc186866c187f8b04802f3b614fed4afcaa232fddf705.

### Final corrected e.1 runtime receipt

|actual-controller-offline|1 PASS /0skip|11.861s|
|actual-controller-reconnect|1 PASS /0skip|11.298s|
|actual-default-network-ready|1 PASS /0skip|0.315s|
|foreign-uid-signer-permission-denied|1 PASS /0skip|0.254s|
|full-android-online|16 PASS /0skip|121.122s|

Final six-gate pipeline PASS including zero enrollment mutation. Explicit dev
transport adb-reverse-loopback only, not LAN. Earlier reconnect harness attempted
a second no-rebind mapping on the retained port and correctly failed BEFORE
reconnect test; fixed to retain the existing owned mapping, then reran the ENTIRE
pipeline above. No gate skipped or substituted from failed runs. Native APK exact
SHAab1b2da3797df93ea7fbc186866c187f8b04802f3b614fed4afcaa232fddf705; same artifact used for upgrade+final16.
Next normal commit/push/advertised remote verification BEFORE fresh Python/Go.
No source/test/packaged-guide/archive edits after that source freeze. Main source
asc/, Go consensus, old source archives and old packaged Phase4.1 guides unchanged.
Full Phase4.2 NOT ACCEPTED: native Node/enrollment/FGS/observer providers and native
LAN remain outstanding; use the exact remaining-gate table in ACCEPTANCE.

Fresh Gradle :app:testDebugUnitTest :app:lintDebug --rerun-tasks after owned emulator
stop: BUILD SUCCESSFUL40s,40tasks actually executed,10JVM/0fail/error/skip. Lint
0errors21warnings. Exact upgraded identity/marker/bytes/KeyStore/form verified AGAIN
after the complete Android fault pipeline, PASS. Main APK still unchanged.

### GitHub source freeze / fresh regression start

67fdd0c3ef4e3c5e2e684d2dbd7f1ce5f504cd3a normal push completed; git ls-remote
feature/phase4-2-android-native matched EXACTLY before final regression. Tree was
clean.301 tracked/index paths reviewed,0 secret-pattern/private-path findings;
APK nested/module/test-class/signature/SHA audit repeated PASS. Original Core/Go/
archive/packaged4.1 guide diff remains empty. Source/test/tools/Android/project/APK/
packaged guide hashes frozen in private frozen-source-sha256.json.

Fresh `python -B -m unittest discover -s tests -v -f` actually STARTED
2026-10-25T19:11:12.270509+00:00 from that verified source commit.317 unique cases
discovered. No result inferred while RUNNING. Private full log/result under
/workspace/work/phase4-2; core activation /workspace/asc-cloud/activate.sh.
Source must not change; final reporting docs only. After PythonPASS run uncached
Go/vet/modverify/Linux-Windows-Android builds, assert all retained fault banners,
recheck frozen hashes and remote APK/protected branches. If interrupted without
FINISHED/PASS evidence, keep full gate PENDING and run fresh again; never reuse
old4.1 full311 as a new4.2 full result. Full native Phase4.2 still NOT ACCEPTED.

### Fresh full attempt1 failed — no acceptance inferred

Source67fdd0c first fresh full stopped after76cases/275.808s,1ERROR/0skip:
Dashboard unknown-capacity/restart session gate ConnectionRefusedError. Frozen
source unchanged. Core API readiness preceded separate Dashboard TLS listener;
original fixture probed only Core then immediately queried Dashboard. Fix TEST
precondition: wait CA-verified TLS handshake on Dashboard, no HTTP request/cookie,
then keep original FIRST response401 and exact retained key assertions unchanged.
No production/asc/consensus/archive changes, no weakened security or skipped test.
Preserved failed log/result privately before a new fresh full. Targeted Dashboard
suite and strict restart case repeats pending; normal commit/push/remote BEFORE
restarting full317. Full e.2 remains NOT ACCEPTED.

Fixture targeted final:6 Dashboard PASS29.498s; strict old-session401/restart repeated
3times PASS20.901s; real trusted-TLS browser upload/mobile/XSS/replicaSHA/offline
integration1PASS9.671s.0skip/fail/error. No original assertions changed; TLS handshake
precondition stronger than TCP-listening alone and sends no HTTP/cookie. No runtime/
Core/native APK/archive change. Normal commit/push/remote before fresh full restart.
