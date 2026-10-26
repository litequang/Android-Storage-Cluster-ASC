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
|4.2e.2a|PUSH/REMOTE VERIFIEDc7dabb041ee06ed27de7077f1ceb7c51f59288a1; targeted6+repeat3+browser1 PASS|
|4.2e.2|PUSH/REMOTE VERIFIEDb5fe3de100a5ae0f7383a0126d80ad82044b5e44;317Python/11Go/62Core faults PASS; full Phase4.2 NOT ACCEPTED|

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

Fresh full attempt2 actually STARTED2026-10-25T19:20:48.301095+00:00 from
PUSH/REMOTE VERIFIEDc7dabb041ee06ed27de7077f1ceb7c51f59288a1.243 frozen
source/test/tools/project/packaged-guide/archive/APK files; no source edits during
run. Reporting docs only. Attempt1 preserved under first-failed-* outside Git;
no failure replaced by a fabricated PASS. Current full is RUNNING, not acceptance.
Go/vet/modverify/builds follow only after fresh fullPASS. Resume must read the
actual FINISHED exit/source_unchanged/fault-group receipt, otherwise rerun full317.

## Final foundation regression / next-session handoff

Actual final source freeze c7dabb041ee06ed27de7077f1ceb7c51f59288a1; native app
source67fdd0c3ef4e3c5e2e684d2dbd7f1ce5f504cd3a. Fresh Python317PASS0fail/error/
skip1817.803s; started19:20:48UTC, completed19:51:06UTC2026-10-25. Source unchanged
through run and after Go/audit; all243 files equal both frozen bytes and Git source
objects. User resumed after run finished; no duplicate full or old311 reuse.
Go actual23:50UTC:11uncached PASS/vet/modverify/Linux-Windows-Android builds PASS.
All62 mandatory fault banners checked by exact group IDs:12+20+7+3+8+3+9.
Native final16 +foreign1/network-ready1/offline1/reconnect1, JVM10, five native
upgrade gates and retained-state postfault check PASS as above; Android dev TLS
transport is explicit and NOT native LAN acceptance. APK/published checksum
ab1b2da3797df93ea7fbc186866c187f8b04802f3b614fed4afcaa232fddf705.
Independent bare remote fetch at3aa51ae4f44eab501b0b51c3156519285f1305ef matched
all243 hashes, exact APK/old0.4.3 candidate checksums, unchanged5 protected branches.
Final report docs/data only; final publication audit/fetch repeats after normal push.

Public machine-readable facts and complete public frozen inputs are in qualification/;
no raw private fixtures/keys/registries/signing/AVDs are there. Full Phase4.2 is
NOT ACCEPTED. Partial independent Foundation qualification does not close the
remaining native runtime product requirements.

### Checkpoint source/publication ledger

| Checkpoint | Pushed and advertised source commit |
|---|---|
|4.2a|86679237729947012bd26b5045f0caa7e654f9cb|
|a audit follow-up|a6e4d7ebb684d3689d309df82d0a191c30e4ed22|
|4.2b.1|677e28ac5cff008e4b869847ac6c39bb51d71266|
|4.2b.2|5ac246aa27f78e0c979cd0674f127939331cce26|
|4.2c|29c2985c839c6b20a0f6a6f3f4142c38b2f20847|
|4.2d|8b901310da04f33e82165756d5bcd8ac36349d82|
|4.2e.1 APK/fault foundation|67fdd0c3ef4e3c5e2e684d2dbd7f1ce5f504cd3a|
|e freeze receipt|bc32a2c46d171db95660a3c013a7940a43046bb0|
|e.2a fixture repair / full frozen source|c7dabb041ee06ed27de7077f1ceb7c51f59288a1|
|full restart handoff|3aa51ae4f44eab501b0b51c3156519285f1305ef|

Final reporting commit is identified by Git history/advertised feature HEAD after
fetch; no report attempts to contain its own circular commit hash. No merge/force/
reset, original branches unchanged. Core/Go/archives/packaged4.1 guides unchanged.

### Continue remaining Phase4.2; do not rebuild ASC or start Phase4.3

1. Implement a reviewed explicit native context/credential/enrollment/agent provider
   around existing Core, no global HOME/getpass/device guard monkeypatch or Kotlin
   duplicate Registry/Catalog/Storage. Current Engine LIBRARY is proven; Node is not.
2. Qualify native TLS identity/key lifecycle and real existing Core Quick Join with
   durable pending/resume, Node/Cluster ID preservation, separate owner storage and
   physical-domain approval. UNSENT encrypted app form is not that workflow.
3. Add owned Node lifecycle/justified SDK35 FGS type/notification/safe stop/process
   death/background tests. No idle mock/Termux PID kill/auto failover/boot startup.
4. Wire a separately authenticated read-only Core observer with explicit mode,
   actual quorum proof and recovery-read-only handling; absent source stays UNKNOWN.
5. Resolve direct emulator host/LAN transport gate (current10.0.2.2 ConnectionRefused)
   without proxy/TLS bypass. Keep ADB dev transport evidence separate. Then close
   real Native Node/enrollment/permission/provider/Doze/QR/hardware key gates as
   applicable; physical ZTE/Bphone acceptance remains owner-only/future.
6. SAF/media semantics, production signer custody/rotation, native rollback and
   Termux→APK export/import/authority/volume migration require separate implemented
   contracts and tests; do not adopt/copy old private state or activate DR staging.

Use ANDROID-NATIVE-OPERATIONS for qualified tools/exact build/emulator commands and
rollback limits, ANDROID-NATIVE-IPC for version1/explicit0-1 transactions, STATE for
format1/AES/private probe. Signer remains PRIVATE /workspace/asc-android-dev/user/
debug.keystore; a new account/key cannot update the published APK in place. Never
put key/password in GitHub or uninstall/clear data to bypass signature/version.
No real phone/M51/production/system/Termux access performed or authorized for Codex.

### Final payload publication receipt

b5fe3de100a5ae0f7383a0126d80ad82044b5e44 normal push/advertised HEAD/independent
bare fetch matched. Exact published APK SHAab1b2da3797df93ea7fbc186866c187f8b04802f3b614fed4afcaa232fddf705 and all243 frozen inputs matched again; old0.4.3 candidate
checksum and5 protected branch heads unchanged.303 tracked/index paths reviewed,
0 findings under bounded scanner/inventory scope. Tree clean before this DOC/receipt
follow-up, no source/tests/guides/APK changes. Public machine evidence includes that
verified payload receipt. Final documentation-only feature HEAD follows in Git log;
normal push/remote check repeats, never force/merge/reset. Full Phase4.2 NOT ACCEPTED
and remaining4.2 work above still applies; no Node/phone/production readiness claim.

## 4.2f.1 — explicit native context/provider (2026-10-26)

Resumed verified445bd3193824fea7e4bb944b583b7a3b9199c34f, clean tree; GitHub200/
fetch equal, managed spec101 current/enforced/unrestricted. Mandatory docs read
in order then all ten requested native/current4.2 contracts. No original branch
change/reset/merge; inherited proxy/CA retained, no proxy:8080 failure.

Implemented asc.node.context explicit private parent/device/sealed-provider contract,
original inode/public receipt, no-follow descriptor creation/fsync/CAS and guarded
OS operation ownership. ApplicationVault supplies a fixed AES-GCM/Keystore record
with deletion witness, not a generic Binder secret API. NativeNodeContext uses
NEW native-runtime-v1(0700)/native-node-v1 below canonical app Context, never
changes existing filesDir0771. Additive private IPC init/status still requires
own UID/signature/consent/device/existing app key. No global HOME/getpass/
subprocess/OpenSSL, Node/Cluster creation or source/state adoption. Context UUID
is only a local receipt. Node/pending/TLS/storage remain explicitly null.

First actual Android14 run had3 failures: official AOSP manufacturer=unknown.
Separated strictly identified DEBUG SDK/ranchu/fingerprint SYNTHETIC fixture from
unknown real phones; all M51 secondary fields still dominate/refuse, old Core
guards unchanged. Also measured actual filesDir0771; create ONLY a new private0700
parent rather than chmod/adopt existing paths. Both corrected intermediate14 runs
PASS; final added actual Binder/private-parent gate rerun is the receipt below.
No failed run relabeled/skip/assertion weakening.

Final targeted:24 Python PASS0skip (context10/engine5/identity4/bridge-contract5);
11 JVM PASS0fail/error/skip; Gradle assembleDebug/testDebugUnitTest/
assembleDebugAndroidTest/lintDebug PASS36s. Actual retained-state API35 x86_64
software emulator, qemu1/ranchu/boot1 verified, privateADB5038/numericloopback only.
**15 Android instrumentation PASS45.226s**, actual Keystore encrypted CAS/restart/
corruption/missing record+key/refused regeneration/private root/receipt/recovery
plus unchanged Engine/private-volume/Binder gates. Actual fixed context seed ->
force-stop ->cold Activity restart ->verify PASS: app UUID/context receipt/Keystore/
exact ciphertext/anchor preserved. Retained exact prior-checkpoint upgrade proof
from old version1 through version2 ->normal same-signer version3 verified AGAIN:
appUUID/cipher/volume marker/original committed Core bytes unchanged. No uninstall/
clear/-d/stale DB restore or native Node identity claim.

New versionCode3/0.3.0-native-context debug build SHA
1c75c43390490edaf9a4f5dba20a3a62cba99665b96979e58c3dc48822118f12; same signer
bba77b68e43ecfe885705442d2224977208bf77a397c216393c26fc151a6bc30. Private
checkpoint artifact only, not a new public release. APK inventory111 canonical
Core modules/2ABIs/unchanged3permissions/no private/test-only findings PASS.
Old public APK/source archives/Go and EVERY preexisting asc file byte-identical
to445bd31; only new asc/node module. Public bounded report: qualification/phase4-2f1-
context.json. Full317/Go11/62 faults above remain HISTORICAL baseline, not rerun
for this new partial checkpoint and not a new full acceptance.

4.2f remains IN PROGRESS, full4.2 NOT ACCEPTED. Next f.2: reviewed in-process TLS
identity/certificate/config provider and its real Android gates, then g actual
existing Core enrollment/pending/resume; h Agent/FGS; i observer; j direct network/
end-to-end/fresh full. No Node listener, enrollment, FGS or LAN proof exists at f.1.
No phone/M51/Termux/production/writableDR/Raft/GC/failover changes. Normal source
checkpoint commit/push/fetch receipt follows; do not start f.2 before it matches.

## Executor interruption handoff — 4.2f.2 NOT QUALIFIED (2026-10-26)

**Verified source checkpoint4.2f.1:
4df6ad6676de2a441991455c71d2e8e2d3aa2685.**
Normal Git push completed, fetch HEAD and advertised remote matched exactly before
starting f.2. Targeted24Python/11JVM/15Android and real process-death/retained old
native upgrade state proofs above are the f.1 evidence. Bounded WORK+INDEX secret
audit completed before that source commit. Full4.2 NOT ACCEPTED.

Cloud executor disconnected during f.2 work: exec-server transport closed, then
No usable execution environment is available; attached environment unavailable.
Cloud configuration service still reported running/current spec102, but that is
NOT proof of a usable executor. Retained network diagnostics had no records.
No proxy:8080 error or proxy/CA alteration occurred. Do not infer the cause of
executor loss or test success. GitHub connector remained usable; this append is
a DOC-ONLY interruption receipt, not publication of unqualified runtime source.
No source rollback/reset/force/original-branch mutation was attempted.

### f.2 draft implementation / state to preserve

Uncommitted f.2 source may remain in the stopped workspace. It is NOT in the
verified f.1 commit and has NOT passed final Android/TLS/security gates. Preserve
and inspect all dirty files before updating the branch. Known draft paths:

- asc/node/tls.py (new): SSLContext with key/cert in sealed anonymous memfd only,
  no plaintext disk-key/OpenSSL executable/provider fallback on actual OS denial.
- asc/node/context.py: strict optional TLS identity component, prepare_tls under
  existing operation lock/CAS, tls_context and sanitized public pin; Node/pending/
  storage still null, no Node identity or authority.
- NativeTLSIdentity.kt (new): standard BouncyCastle/JCA EC secp256r1 +SHA256withECDSA
  self-signed X.509 server cert. Software TLS key is exportable in RAM and sealed
  by existing nonexportable Keystore wrapping key; NOT hardware-backed TLS signing.
- NativeNodeContext.kt, EngineService.kt, RequestPolicy.kt: fixed trusted in-process
  provider plus consent-gated native_tls_prepare; no arbitrary path/provider API.
- android/app/build.gradle.kts: bcpkix-jdk18on1.83 ->bcutil/bcprov1.83, verification
  metadata initial TLS/TOFU SHA pins. Exclude ONLY duplicate
  META-INF/versions/9/OSGI-INF/MANIFEST.MF (Java9 OSGi metadata, not crypto classes).
- android/gradle/verification-metadata.xml: new BC artifact hashes; review them.
- tests/test_native_tls.py (new six-case Linux fixture) and NativeTLSTest.kt
  (actual Android platform/X.509/TLS tests); RequestPolicyTest additional operation.
- UpgradeQualificationRunner.kt: fixed tls-seed/tls-verify phases on the existing
  isolated native-context-process-proof namespace, intended to verify stable
  cert/pin/cipher after process death. Those phases were NOT confirmed executed.

Private work/logs: /workspace/work/phase4-2-continuation. f.1 private APK preserved
there as f1-version3.apk (SHA1c75c43390490edaf9a4f5dba20a3a62cba99665b96979e58c3dc48822118f12).
SDK/AVDs/signer remain under /workspace/asc-android-dev if workspace survives.
No private state/key/test APK/logs are in Git. Do NOT publish a replacement APK or
claim same-signer upgrade if the original private signer is unavailable.

### Actual f.2 failures / diagnosis (not final acceptance)

1. First BC dependency build failed duplicate Java9 OSGi descriptor; exact
   resource-only exclusion above fixed strict build (39s observed).
2. Initial Linux TLS six-case run failed one handshake timeout after wrong-pin
   client closed. TLS1.3 server ticket write can observe BrokenPipeError before
   recv; the test server ended its accept loop before the valid second client.
   Corrected fixture records expected first-peer reset as CLOSED_BEFORE_DATA
   (never a successful read), requires actual wrong-pin ClientError, and still
   requires valid second handshake/body/SHA. Corrected six Linux tests PASS0skip
   in0.566s before the later Bionic-specific source change.
3. Actual Android integrated TLS preparation FAILED (ContextLocked). Independent
   standard BC/JCA X.509 generation test actually PASS. Platform diagnostic FAILED
   Python-wrapper precondition and reported:
   python_memfd=false, os_flags=false, fcntl_seals=true, bionic_memfd=true.
   This is implementation/platform-wrapper evidence, NOT TLS handshake PASS.
4. Official Android Bionic header inspected via authenticated public HTTPS:
   https://android.googlesource.com/platform/bionic/+/refs/heads/main/libc/include/sys/mman.h
   documents public memfd_create since API30; official UAPI
   libc/kernel/uapi/linux/memfd.h defines CLOEXEC0x0001/ALLOW_SEALING0x0002.
   Latest draft uses Python os.memfd_create where present; ONLY if that wrapper
   is absent on Android, ctypes loads the documented libc.so memfd_create symbol
   with explicit ABI types, same app UID/ordinary kernel/SELinux policy. No raw
   syscall, elevation, filesystem key fallback or switch after a denied syscall.
   Absent public API/failed sealing/proc access must refuse. Node TLS on API26–29
   is NOT qualified; do not infer support from app minSDK26.
5. Latest Android platform test was strengthened to actual memfd write/read,
   all four F_SEAL bits, denied mutation and closed fd; it no longer mistakes
   absent Python wrapper for absent public OS functionality. Full real handshake
   plus wrong-pin refusal remains mandatory, no fake provider.
6. New Linux6/context10 ->strict build/install/three Android TLS tests was launched
   with latest Bionic draft (private session9191). Executor vanished before its
   result was read. Treat latest run/build/Android tests as UNKNOWN/UNCONFIRMED.
   Do not stitch prior Linux PASS/BC generation PASS into complete TLS acceptance.
   A following attempted patch adding seal-failure/no-fallback/corrupt-record tests
   failed at file-read with exec-server transport closed; its application is NOT
   confirmed. Inspect actual files rather than assuming that patch exists.

### Resume safely

- Restore a usable workspace, read AGENTS/current docs, fetch this SAME feature
  branch and inspect dirty f.2 files. This receipt advances remote docs only;
  fast-forward the same branch only if compatible with retained local changes.
  Never reset/overwrite those changes, original branches or private state.
- Verify owned AVD/ADB identity before any command. Owned retained-state emulator
  was ASC_UPGRADE_API35/privateADB5038/127.0.0.1:5555; start harness retained parent
  session27513, qemuPID500147 was the recorded handle before loss. Those handles
  are HISTORICAL, not authority to kill a later/reused PID. New owner verification
  is required. No cleanup/termination could be confirmed after executor loss.
- Inspect latest f2-bionic-* logs/results if preserved; otherwise run fresh gates.
  Keep real memfd/sealing/proc/key-match/TLS/pin/corruption/no-regeneration and
  process-restart tests. No plaintext disk or unsupported-OS workaround.
- Rebuild with strict dependency verification, targeted Linux/JVM/Android tests,
  f.1 regression/Binder/Keystore/probe/upgrade proof; update protocol/state/security
  docs and source CODEMAP. Audit actual tracked+staged contents/new dependencies/
  APK before a normal f.2 commit/push/fetch verification.
- Only after qualified f.2 proceed g Core enrollment/resume, h actual Agent+FGS,
  i read-only observer, j direct network/end-to-end/fresh full regression and new
  debug candidate. None of g–j was started or accepted here. No Native Node,
  enrollment, replica, FGS, observer/direct LAN or phone acceptance is claimed.
  WritableDR/AndroidRaft/GC/failover remain forbidden.

The current public APK stays0.2.0-foundation/ab1b2da3...; f.1 source is durable on
GitHub, f.2 source durability depends on recovering the original dirty workspace.
This receipt records the exact limit instead of claiming all unfinished source
was published or tested.

## 4.2f.2 recovery / fresh native TLS qualification (2026-10-26)

Workspace recovered at4df6ad6 with all12 dirty TLS files; none lost. Saved exact
public source copies/tracked+staged patches/SHA manifest outside Git before fetch.
Remote161e833 was docs-only; safe same-branch fast-forward preserved every dirty
source byte. No reset/clean/force/whole merge. Original signer/AVD/userdata retained.
Historical qemu500147 was a verified zombie with empty cmdline; both OS file locks
were free. Moved ONLY its exact owned hardware PID lock to private recovery backup,
kept multiinstance lock and all AVD data. Retained-state AVD cold boot verified
qemu1/ranchu/boot1 before install. No old PID was killed or blindly reused.

Recovered interrupted Bionic log contains3tests/2FAIL (proc reopen EACCES), supporting
diagnosis only. Overall interrupted qualification stays UNKNOWN and contributes
NO fresh PASS. Failed last seal/corrupt/no-fallback patch was absent; implemented
those tests now. All original12 files retained and selectively completed; added
NativeTLSLoader.kt and native TLS doc instead of reconstructing the project.

Android explicitly uses standard JSSE/KeyFactory/Signature/in-memory PKCS12 +
KeyManagerFactory on bytes read from already-open sealed fd. No proc reopen on
Android, disk PEM/PKCS12, external OpenSSL, raw syscall, SELinux/permission or global
provider change. Bionic public API30+ only if Python wrapper absent; verified
actual seals/CLOEXEC/readback/zero links/cleanup, fail closed without fallback.
Linux CPython route remains explicit. Typed TLS component and public-pin-only IPC
reuse existing context/Keystore CAS; no Node/Cluster/storage/pending identity added.
Native TLS on26–29 NOT QUALIFIED; actual platform proof is API35 x86_64 only.

Fresh targeted Linux34 PASS0skip: TLS9/context10/Engine5/ControllerBinding1/identity4/
bridge-contract5. Actual Gradle/JVM11 PASS0fail/error/skip; build/lint/testAPK PASS.
Actual final Android20 PASS106.286s0skip, plus foreign-UID/signature/permission/bind
denial1 PASS. Final20 includes real BC/JCA certificate/key match +mismatch, actual
Bionic ABI/seals/denied mutation/fd-close, Keystore sealing/cipher and missing record/
witness/wrapping-key hold, JSSE-to-Core-pinned-client handshake/wrong-pin/SHA,
DEFAULT SYSTEM TRUST rejects untrusted self-signed peer, existing context/Binder/
canonical Storage Engine read/write/readback/fsync/corruption/identity gates.
Preliminary19 PASS97.185s preceded added default-trust negative test; final20 is
the new complete targeted set, not19+20 or old interrupted results.

Fixed TLS seed ->actual force-stop/cold Activity start ->TLS verify PASS: original
application/context IDs, exact encrypted TLS bytes and certificate fingerprint
preserved. Retained exact old-native upgrade receipt verify-v3 PASS: original
app Keystore/draft/VolumeID+marker/committed Core bytes preserved. UID unchanged
across normal install-r; no uninstall/clear/-d or database restore. An initial
postboot install-r exited1 before tests (stderr not retained by first harness);
normal same-APK retry succeeded without bypass flags. No root cause fabricated.

Dependency review:3 new BC1.83 components/6 JAR+POM SHA256 match cache, every old
verification pin unchanged (old AGP BC entries are retained). Strict build, no
updated system tools/proxy/CA. Original signer SHA
bba77b68e43ecfe885705442d2224977208bf77a397c216393c26fc151a6bc30. Private
version3 APK SHA88435153fda9493bf13bd75a2d4e6a0cd3bc6c833e179e275b5f0faa511f2aa3,
112 canonical modules/2ABIs/unchanged3permissions and bounded inventory PASS.
NO public APK/release/archive changed. Lint0errors22warnings:17VN strings,3pinned
dependency notices,1durable consent commit,1unused BC EST trust-all helper warning.
Warning remains unsuppressed; app has no EST/helper reference, uses default platform
trust and actual negative handshake. Read native TLS dependency review; not full SAST.

Public bounded evidence: qualification/phase4-2f2-tls.json; ANDROID-NATIVE-TLS owns
API/threat/format/compatibility and next Agent transport requirement. No product
listener/Node/FGS/enrollment/LAN claim. Guest loopback is NOT direct LAN or Android
phone acceptance. Source-only f.2 targeted scope qualified; full4.2 NOT ACCEPTED.
Fresh whole Python/Go/Core-fault gates belong to later final qualification after
g–j runtime work; historical full317/Go11 are NOT reused as fresh changed-source gates.

Normal checkpoint commit/push/fetch receipt follows, before moving to4.2g.
Private recovery logs retained under /workspace/work/phase4-2f2-recovery-*; original
signer/state under /workspace/asc-android-dev. Preserve them if moving accounts.

### f.2 source publication receipt
486a4d26fae487bab33aff2804ddb9db44e936b3 normal push/fetch/advertised remote
matched exactly, clean tree BEFORE g.1. Final20/postfault process TLS identity/old
upgrade receipt/foreign caller PASS; frozen source hashes unchanged.317 WORK+INDEX
paths plus all31 dirty/untracked source paths reviewed; no leftover untracked, no
secret findings. Postfinal APK audit PASS, original signer/public artifact unchanged.

## 4.2g.1 — shared client contract extraction (Linux only)
Native g is split into safe source reuse then actual native encrypted-pending/IPC/
UI +Android network qualification. New asc/enrollment.py contains ONLY the exact
existing CLI pending factory and ACK acceptance. CLI reuses them; no Registry/
Catalog/Storage/enrollment-server duplication, global HOME/device/repair/locking
behavior change or wire/schema change. Pending op/token remain original CSPRNG
values, profile/controller lists copied defensively, target/cluster/token checks
before identity publication. No native Node or network authority is introduced.

Fresh42 targeted Linux PASS0skip:4 contract/29 original lifecycle/9 original actual
TLS QuickJoin. Original lost successful ACK/code replacement/one-use/concurrency/
identity/re-pair/revoke/guard/schema assertions retained. Contract/lifecycle rerun
after removing now-unused CLI import. This is NOT Android enrollment acceptance.
f.2 native APK remains private/unmodified; g.1 has not been built into a new APK.

Next g.2 must reuse this same Core contract with typed encrypted pending/Node
configuration, real pinned Controller join and lostACK/resume on actual Android;
no token/code in public state, no auto storage/domain approval or identity reset.
Only then h native transport/Agent/FGS, i observer, j direct LAN/fresh full gates.
Full Phase4.2 NOT ACCEPTED. Normal g.1 push/fetch before further source work.

### g.1 publication receipt
f423e9f5f75f0263805574e3228085b459d3afce normal push/fetch/advertised remote
matched exactly before g.2a work. All original branches and public APK unchanged.

## 4.2g.2a — typed sealed-state enrollment adapter (Linux only)
NativeEnrollment reuses asc/enrollment.py +Core pinned transport and Registry.join.
Context1 strictly validates optional pending/node components. Initial pin/cluster/
mode check precedes credential creation; pending CAS precedes POST. Accepted node
and pending removal are one CAS, retained original token/operation on lost ACK or
local publication failure. Explicit code replacement never re-pairs an enrolled
node. Historical receipt +UNKNOWN approval only, runtime/writer remain false.
No plaintext node/pending config, global HOME/getpass/CLI or Kotlin server logic.

Fresh9 actual Linux Core/TLS adapter tests PASS0skip, including successful201 ACK
loss, Controller disconnect/reconnect, local CAS failure after committed join,
authenticated reply mismatch, expired code replacement, wrong pin/cluster/mode/
protected profile, pending conflict/missing/corrupt provider and revoked credential
without identity recreation. MemoryCredentials is TEST ONLY, not Keystore proof.
Native Android g.2b Binder/UI and actual encrypted pending/Controller/emulator
qualification have NOT run. No APK changed/published at g.1 or g.2a. Full4.2 NOT
ACCEPTED; h Agent/FGS, i observer, j direct LAN/fresh full gates remain.

Rollback: f.2 rejects populated enrollment slots. Preserve new record/state; use
compatible code, no stale database restore or identity deletion. Existing app/
probe/TLS identity and old draft are independent and retained. Next g.2b must wire
private native IPC to this adapter with trusted device profile and real Keystore
CAS, real pinned Controller/wrong pin/cluster/expired/used/offline/ACK-loss/restart
gates. Never count Linux provider tests as Android enrollment acceptance.

Additional fresh61 Linux regression PASS0skip (context10/TLS9/shared contract4/
original lifecycle29/actual TLS QuickJoin9), total70 distinct targeted tests.
Commands: PYTHONPATH=tests python -m unittest test_native_context test_native_tls
test_enrollment_contract test_lifecycle test_quick_join -v; python -m unittest
discover -s tests -p test_native_enrollment.py -v. Logs retained privately alongside
f.2 recovery logs. No historical whole-suite count reused as current PASS.

### g.2a publication receipt
857165ba5c2dc5c3b6653d7973915a3d67d4fadd normal push/fetch/advertised remote
matched exactly before further g.2b source edits.70 distinct Linux targeted PASS.

## 4.2g.2b — native sealed-provider/IPC enrollment qualification
Private NativeNodeContext now calls the canonical Core adapter with trusted native
Build/RAM profile. Existing Binder ownUID/signature/consent/device gates apply to
quick_join/resume_join/replace_join_code; no path/profile/identity override. Native
UI explicit context/TLS preparation +fresh owner trust/binding check, actual join/
redacted pending/receipt/resume/code replacement; old encrypted draft independent.
Safe fixed errors, no raw exception/code/token/key in public state or logging.
No Node listener/Agent/FGS/volume approval or writer authority was introduced.

Fresh33 Linux PASS0skip: enrollment10/context10/TLS9/shared contract4. Gradle main/
testAPK build +JVM12 PASS0fail/error/skip; strict dependency checks unchanged.
Lint0errors25warnings: prior unused BC EST helper/dependency/durable-consent notices
and Vietnamese string notices (not suppressed). Package audit PASS114 canonical
Core modules/2ABIs/unchanged3permissions; no test class, private-state/credential
findings. Original debug signer SHA
bba77b68e43ecfe885705442d2224977208bf77a397c216393c26fc151a6bc30 retained.
Private version3/0.3.0-native-context APK SHA
59541e41afe010a9ca7c6041c96d16549b727666d4430fedafdf717d88bb62bd. No public
APK/archive/release/version change; final candidate version increment belongs to j.
Exact installed f.2 APK backed up privately before install; hash88435153... matched.

Actual retained ASC_UPGRADE_API35 owned emulator:28 targeted PASS244.749s0skip,
including5 new real Keystore/Core/TLS enrollment cases, actual Binder pin-failure/
consent/strict fields1, existing20 TLS/context/Engine/Keystore/Binder gates and
UI2. Original assertions retained. Positive joins in these tests use trusted
NativeNodeContext with an isolated private provider; Binder refusal and UI trust
gates are actual service/UI tests. Positive UI->Binder->Core end-to-end on a new
sandbox remains g.2c, avoiding mutation of retained foundation fixtures.

Actual fixed proof phases join-pending-seed ->force-stop/cold Activity ->
join-pending-resume ->force-stop/cold Activity ->join-receipt-verify PASS. Original
app/context/TLS IDs, original pending operation/token hashes and accepted Node/
Cluster identity retained; exact pending/committed ciphertext checked. Additional
tls-verify +verify-v3 PASS preserve all earlier TLS/app/Keystore/draft/VolumeID/
marker/committed Core bytes. Actual foreign UID/signer/permission/bind denial1
PASS. UID10148/test10149 unchanged; original signer, no uninstall/clear/-d/db reset.

Host actual Registry ends with exactly4 accepted Nodes,0 catalog storage approvals.
Both TLS proxies dropped REAL successful201 ACK once and saw exactly one retry
(twoPOSTs each), not a simulated successful join. Wrong pin/cluster/quorum mode,
offline endpoint, expired/used code, pending corruption and identity-preservation
gates PASS. Explicit development ADB reverse-loopback only; NOT direct NAT/LAN.
Tool initially refused TCP-connected serial's unsupported adb emu console BEFORE
any install/state change; replaced the console query with live owned PID/UID/
cmdline receipt +guest qemu/hardware/AVD/boot checks, no ownership weakening.

Private logs/Controller fixture/keys/retained prior APK/process proof under
/workspace/work/phase4-2g2b-qualification and original task-owned AVD. Do not delete
proof/fixture to rerun seed. tools/qualify_native_enrollment.py +ANDROID-NATIVE-
ENROLLMENT specify scope/repeatability/retained-state limits. Public bounded source
receipt qualification/phase4-2g2b-enrollment.json. No phones/Termux/production.

Next g.2c positive UI/private Binder path on separate task-owned synthetic app/AVD,
then h actual native socket adapter/Storage Agent/FGS, i observer, j direct LAN +
fresh full Python/Go/Core faults/candidate upgrade/package gates. Full4.2 NOT
ACCEPTED; whole-suite historical results are not fresh g.2b qualification. Before
next source checkpoint: normal commit/push/fetch verification below/next receipt.
Rollback: older f.2 refuses populated optional slots; keep NEW records/bytes/signer
and compatible code, never restore stale state or regenerate Node/app/volume IDs.

### g.2b publication receipt
b49f5fb6c05e1eb366ba4041ad9020a7eca7725a normal push/fetch/advertised remote
matched exactly before g.2c. All original refs/public archives retained.

## 4.2g.2c — positive native UI -> Binder -> Core (scoped)
Added test-only NativeJoinUiQualification/fixed runner phases +explicit owned-
emulator qualification tool. Main source/APK unchanged from g.2b (SHA59541e41...);
original signer bba77b68... preserved. New testAPK builds PASS with existing strict
dependencies. JVM12 unchanged from g.2b reused (UP-TO-DATE), not12 new tests. No
new Core/Android main source means earlier33/28 scope remains the frozen g.2b
receipt, not relabeled as fresh g.2c regression. No public APK/release.

Actual three UI phases PASS: ui-join-seed ->force-stop/cold Activity ->ui-join-resume
->force-stop/cold Activity ->ui-join-verify. MainActivity input/trust/preparation/
send and resume View callbacks invoke production private Binder +Core over real
pinned TLS. Server dropped one REAL successful201 ACK; exactly2 joinPOSTs,1 Node,
0 catalog approvals. Actual app/context/TLS pin/request UUID/op/token hash/accepted
Node ID/ciphertext kept across process death, no direct adapter substitutes for
UI send/resume. Approval UNKNOWN, runtime/writer false. Separate fresh app/AVD: no
in-place upgrade claim for this scenario (retained original receipt is separate).

Owned ASC_JOIN_UI_API35 created under existing workspace SDK with NEW userdata,
not a clone of old app/Termux state. avdmanager create failed because this SDK's
registered emulator package metadata is missing; executable/system image were
already qualified. Wrote only a NEW standard AVD config pointing to that existing
image. Actual boot465.4s TCG, no KVM. Initial install suffered qemu SIGABRT(-6)
BEFORE UI tests; initial stderr was not retained by first helper, not fabricated.
Old qualification AVD gracefully stopped through its verified Popen parent only
after all g.2b gates, original userdata/signer kept. New failed AVD offline
userdata/config/key backing saved (~570MB); exact NUL-terminated historical PID
lock verified absent process +both free OS locks, then moved into backup, never
killed blindly or deleted multiinstance lock. Same userdata restarted with1 TCG
core (239.001s boot); no wipe/reset/root/proxy/CA changes. Crash cause unproven.

New APK install then passed. Two pre-seed fixture setup attempts failed because
filesDir was not yet created; am start -W is insufficient for async Binder status.
Fixed actual-directory readiness wait, not identity initialization/guard bypass.
Explicit --resume-setup reuses exact private Registry/cluster/cert/pin/code only
with zero Nodes/approvals and no UI phase logs; seed asserts actual vault
NOT_PROVISIONED before user consent/provision. No existing app/Node identity was
reset. Actual successful run used canonical emulator-5556/privateADB5038; earlier
TCP alias127.0.0.1:5557 also targets this same verified guest. These are dev
transports, NOT direct NAT/LAN. Initial/setup failures are not added to PASS.

LIMIT: private UI hierarchy captured an Android Quickstep launcher ANR overlay.
The tests execute actual programmatic View event callbacks/Binder/Core, not
physical taps; interactive UX NOT QUALIFIED. No claimed phone/ARM64 runtime,
Doze/OEM or Native Storage Agent/FGS/direct LAN qualification. Full4.2 NOT ACCEPTED.
Public source receipt qualification/phase4-2g2c-native-ui.json. Private logs/AVD
owner receipt/proof under /workspace/work/phase4-2g2c-ui (qualification-retry).
Retain all files; never rerun seed over existing proof. Original ASC_UPGRADE_API35
userdata/signing key/f.2 and g.2b backups remain under documented private paths.

Next after normal push/fetch: h should be split shared explicit Core Agent
contract, native TLS socket adapter to SAME StorageHandler/Engine, owned storage
configuration and real Agent/FGS lifecycle/authorized byte transfers. Retained UI
Node is enrolled with no approved storage; do not reinitialize it. g Controller
fixture is stopped but Registry/cert/Node token bindings are retained privately;
restart exact isolated fixture only for further tests, no writer/raft bootstrap.
Then i read-only observer and j direct LAN/fresh full regression/new candidate.
Do not relabel source integration as full Native Node or Phase4.2 ACCEPTED.

Final-source negative re-seed guard PASS: --resume-setup against the completed UI
fixture refuses BEFORE reinstall/server mutation; exact encrypted Node context
and UI proof hashes unchanged. Public source SHA receipt verified before staging.

### g.2c publication receipt
01958c34db2de8f34743b781f86da9d11d448c3e normal push/fetch/advertised remote
matched exactly before h.1. All three actual UI/Binder/Core fixed phases +negative
re-seed/unchanged ciphertext guard PASS, with launcher/TCG limits recorded.

## 4.2h.1 — shared explicit Core Agent contract (Linux only)
Extracted unchanged heartbeat network/direct-pin-or-existing-Discovery +cluster
checks into asc.agent.heartbeat. Explicit config/profile, optional trusted
in-process direct sender; no HOME/getpass/hardware discovery/FS/identity/thread/
lifecycle. CLI agent_once retains original device/M51/capability checks,401/403
repair-required status without Node identity changes, verified metadata sync and
private snapshot/agent-state persistence. Same wire fields/routes/tokens and
expected-cluster refusal; no new Android operation, runtime or approval.

Final fresh57 targeted Linux PASS0skip/fail55.804s: new real TLS Agent contract5,
original lifecycle29, all original storage-cluster/distributed suites and4 retained
failover RuntimeState tests. Actual pinned heartbeat/UNKNOWN null profile, wrong
pin before metadata mutation, cluster mismatch, revoked token, real disconnect/
reconnect +same Node cfg; existing physical bytes/transfer scopes/storage leases/
metadata/discovery assertions retained. No original test/assertion modified. New
wrong-pin test compares durable Node rows rather than unrelated snapshot clock.
Command: PYTHONPATH=tests python -m unittest test_agent_contract test_lifecycle
test_storage_cluster test_distributed test_failover.RuntimeStateTests -v. Private
log /workspace/work/phase4-2g2c-ui/h1-regression-final.log. Not a fresh whole-suite
or Android runtime result. Previous smaller preliminary run not added to57.

No APK rebuilt/released for h.1; frozen g.2b/g.2c private APK remains SHA59541e41...
with114 modules. Current source now adds shared Agent module; next native build
must resync canonical source/audit inventory, never count old APK as h runtime
acceptance. Original public artifacts, signer, old AVD/probe/volume/Node identities
and Core3D guards untouched. Full4.2 NOT ACCEPTED. Core/Go/full faults stay for
remaining runtime safety/final gates, not historical PASS relabeling.

Next h.2: actual native JSSE socket adaptation (not CPython SSLContext substitute)
to SAME StorageHandler/Engine, bounds/deadlines/pinning/introspection, binary
read/write/close/failure tests. Then explicit app-owned network volume configuration
(no probe adoption/reinitialization), real Agent/heartbeat +Foreground Service/
notification/Stop and authorized I/O/restart/network/revocation tests. Only then
i observer/j direct LAN/full fresh gates/new debug candidate. Avoid duplicate
Kotlin storage/Agent/Registry or global HOME/getpass monkeypatch. No Raft/GC/writerDR.
Normal h.1 commit/push/fetch verification must precede next source checkpoint.
Rollback h.1 is code-only compatible (no schema/data change); keep newer native
enrollment state and original signer, do not restore stale records or older f.2
code that rejects populated slots.
