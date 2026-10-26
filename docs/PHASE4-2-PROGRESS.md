# Phase4.2 progress / independent handoff

Current continuation: Native Node/Quick Join/TLS/FGS/direct emulator NAT are
qualified under h/g scoped receipts below; i.1 observer client published92f4ed2.
i.2 adds the real native read-only Core view (targeted PASS; receipt below).
Next remaining major checkpoint is j: integrated faults/full regressions and a
version-increased same-signer candidate/upgrade. Full4.2 NOT ACCEPTED; physical
phones/ARM64/Doze/OEM/two independent hardware domains and writable DR unqualified.
The early a–e table/FOUNDATION statements below are historical, not current gaps.

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

### h.1 publication receipt
0d745a3beec4fb7394dc4817f4d990a6c5c9d93f normal push/fetch/advertised remote
matched exactly before h.2a.57 targeted Linux PASS, no uncommitted work carried.

## 4.2h.2a — native JSSE socket facade (transport only)
New NativeTLSListener/Connection +asc.node.socket provide owned public Java TLS
stream ->Python binary makefile/read1/readinto/sendall/timeout/close. Existing
Node TLS context/provider, SDK30+/M51/unknown guard, explicit numeric private bind,
TLS1.2/1.3 only. Bounded32 connections/65536-byte callbacks; scheduled absolute
deadline closes only its exact owned socket, not reset by trickle/read timeout.
Actual closed cause atomic, timers cancelled idempotently, listener closes owned
connections. No hidden FD/proc/key file/plaintext tunnel/external executable,
new crypto library, permission, management operation or app startup hook.

Fresh Linux23 PASS0skip: facade4 +TLS9 +context10. Fake Linux stream fixture is
contract-only, NOT Android TLS proof. Gradle/JVM13 PASS0fail/error/skip; main/test
build +strict dependency checks PASS, lint0errors25 retained warnings. Final source
frozen before runtime tests; preliminary builds/runs not added to counts.

Actual owned ASC_JOIN_UI_API35/API35 x86_64 TCG:3 native socket tests PASS153.045s,
real canonical pinned-client handshake/wrong-pin no application bytes, all256
byte values/1MiB buffered JNI stream SHA, actual idle TLS-read deadline and actual
blocked write while pinned peer does not consume bytes. Write gate requires some
bytes sent, less than64MiB, actual OSError, actual deadline/peer closed, no live
worker and0 active sockets. Public JSSE close genuinely unblocked I/O; not a fake
timer flag. No Node/HTTP/physical file/protection claim from the raw echo frame.

Additional fresh15 Android PASS294.004s0skip: original TLS5/context3/canonical
Engine1/Keystore+storage6. Actual MFD seals/key mismatch/trust/pin failures, record/
key loss/corruption, identity and real approved probe write/read/SHA/fsync/marker
gates retained. Actual distinct-signer foreign UID/permission/bind denial1 PASS
0.165s. Existing assertions unchanged. Retained enrolled primary UI proof
ui-join-verify PASS before and after faults/normal install-r: original app/context/
TLS/Node/token hash/committed ciphertext intact; target UID unchanged. No uninstall/
clear/-d, stale DB restore, app identity/Volume ID regeneration or original AVD
change. Exact prior g APK59541e41... backed up privately before h installation.

Private version3/0.3.0-native-context APK SHA
89a2c9a29a6b41e1d198519eb67e4b87aed91b2e32f3f0282914f367c1da54b4, original signer
bba77b68e43ecfe885705442d2224977208bf77a397c216393c26fc151a6bc30;116 canonical
Core modules/arm64+x86_64/unchanged3permissions, bounded APK/secrets inventory PASS.
No public APK/archive/release. Private logs/source snapshot/prior artifact under
/workspace/work/phase4-2h2a-socket. Public bounded receipt qualification/phase4-2h2a-
socket.json; API/thread/deadline/limits in ANDROID-NATIVE-TRANSPORT.

Scope: actual Android guest loopback only, not ADB reverse/direct NAT/LAN, ARM64/
phone/OEM/Doze or interactive-touch usability. Earlier Quickstep ANR remains an
explicit UX limit. No product Storage Handler/listener/Agent/FGS/approved network
volume/real replica via this adapter yet. Full4.2 NOT ACCEPTED; writableDR blocked.
No fresh full Python/Go/Core-fault run claimed at this scoped transport checkpoint.

Next h.2b must reuse SAME StorageHandler/StorageEngine with actual authorized
bytes/fsync/readback/SHA, explicit private Node-volume config/partial-setup/marker/
identity/space guards; no probe adoption or absent-manifest recreation. Core
storage/domain approval remains explicit owner action. Then real owned Agent/FGS
notification/Stop/lifecycle/revocation/outage, i observer, j direct LAN/full fresh
gates/new candidate. Preserve current enrolled Node/Keystore/private signer; no
re-seed/reset. Publish normal h.2a commit and verify fetch before next checkpoint.

### h.2a publication receipt
66634a6cfb29468d8efeb0662f111c1e81231a65 normal push/fetch/advertised remote
matched exactly before h.2b.1a source changes. Scoped native transport qualified;
NOT Native Storage Agent. Original signer/old AVD/new enrolled AVD preserved.

## h.2b.1a — existing-only Manifest/Engine gate (IN QUALIFICATION)
Before native approved-volume/runtime work, add opt-in POSIX private existing-only
constructor: no mkdir/chmod/missing DB creation/schema or identity repair. SQLite
mode=rw +owner/single-link/no-symlink/dev+inode checks; same canonical format1 DDL
reused in RAM for structural comparison, whitespace normalized to accept older
indentation. Old default creation, IDs, tables and constraints unchanged. This
is not an fd-pinned SQLite VFS for malicious same-UID/untrusted shared metadata.
Native configuration must constrain approved app-private roots; SAF/shared media
unsupported. No Node volume config/approval/Handler/Agent/FGS yet.

Fresh8 targeted actual Linux tests PASS0skip. New symlink negative initially
expected ValueError but original Core no_links correctly raised StorageError
unsafe_path; fixed this NEW test to assert that exact existing guard, no original
test or runtime assertion weakened. Exact h.2a installed APK89a2c9a2... retained
privately; its committed Engine body/Volume ID/marker/manifest inode captured
before upgrade, no DB copied/adopted and no Node/app identity reset. New actual
Android tests must open/read this previous private test dataset, not fabricate
compatibility with a newly generated object.

Core/source/Native test files will be frozen for full Python safety regression +
Android/Go checks. Current results pending below; NOT a completed checkpoint or
new Phase acceptance. Private work/proofs: /workspace/work/phase4-2h2b1-existing.
No public APK/release; normal checkpoint push only after required gates PASS.

### h.2b.1a retained qualification / interrupted full runs
Fresh Linux8 PASS0skip; actual API35 x86_64 existing-only tests3 PASS9.327s,
additional original TLS/context/Engine/Keystore/socket18 PASS380.244s and foreign
UID/signer denial1 PASS0.218s. Retained enrolled primary app proof PASS before and
after normal same-signer install-r; original app/context/TLS/Node/token/committed
cipher identity and UID preserved. No uninstall/clear/reseed. New Android negative
fixture initially used filesDir's Android symlink alias: original Core unsafe_path
guard correctly refused it. Only this NEW fixture changed to canonical filesDir;
final3 tests all rerun. First failed run remains diagnostic, not added to PASS.

Strict dependency build/main+testAPK/lint PASS (0errors25 retained warnings).
Unchanged JVM13 results retained from h.2a; Gradle test task was UP-TO-DATE, not
13 fresh executions. No new JVM source/dependency/permission. Private internal
version3 APK SHA61eb0323b40021df192ebccb6f3089425bac1fd8eaac1e6cfbea551fae052821,
original signer bba77b68e43ecfe885705442d2224977208bf77a397c216393c26fc151a6bc30;
116 canonical modules/arm64+x86_64, bounded APK inventory PASS. No public artifact.

Fresh Go11/vet/modules/Linux+Windows+Android builds PASS; latter two cross-builds,
not runtime proof. First full Python run failed after73 at original consensus
child shutdown20s; unchanged exact consensus retry PASS23.568s. No timeout/assertion
weakened. Second full run reached288 completed ok lines and60 fault PASS markers,
then SIGKILL before completion (no final receipt); NOT full PASS. Cgroup reports
0 OOM kills; cause of external SIGKILL not established. All failures/logs retained.

Both owned AVDs stopped with userdata/private signer intact. Latest emulator stop
returned SIGSEGV(-11), not clean-stop/power-loss proof; offline userdata backup
retained without restoring/replacing active state. Fresh full Python started
2026-10-26 09:56:19 UTC through owned detached supervisor so completion can be read
independently of interactive session lifetime. Original discovery/tests unchanged,
source hashes frozen, no concurrent emulator/Go/Gradle. Receipt pending at
/workspace/work/phase4-2h2b1-existing/full-python-durable/receipt.json, log tests.log.
NOT qualified until full gate completes; no next checkpoint started. Preserve the
current source/tests/docs in a normal source-only WIP commit while that gate runs;
this does NOT close h.2b.1a or authorize transition to h.2b.1b. Public bounded status
qualification/phase4-2h2b1-existing.json explicitly records pending full regression.
On resume, inspect durable receipt/log and frozen hashes before any source edits.

### Source preservation and compatibility gate repair
WIP b6b1ee1e59de8804cd7f60b758301dd9e2d243cf normal push/fetch/advertised remote
matched exactly. This preserved all Engine/Manifest/new tests/docs before the long
full gate; NOT a completed h.2b.1a checkpoint.

09:56 durable run finished 10:28:12 UTC:309 tests,1FAIL, no SKIP. Original Core
GC/backup/quorum/observer fault gates reached61 PASS markers, but full FAILED at
Phase41UpgradeTests: it compared a new current-source package to the immutable
published0.4.3-dev bytes. No runtime corruption or proof of complete regression
PASS inferred. Full log/receipt retained under full-python-durable.

Fix the fixture's source contract without weakening its gates: independently
rebuild historical0.4.3 from qualified0a3ea839217156b69209a073f5d836ee1db4452b;
assert exact equality to published archive and hardcoded SHA
96260f1709f6a9db6cb98869fbef8fc2313feaf68a4f12da354665ad04693c04. Preserve the
entire original upgrade/pending/bridge/identity/new bytes/code-only rollback test
body. Additional CurrentSourceUpgradeTests executes that same entire body on a
fresh cluster using this workspace's independently rebuilt/current-inventory- and
byte-checked package. Old candidates/releases unchanged, no new archive published.
This separates historical evidence from qualification of today's changed source.

Fresh final targeted10 PASS44.775s0skip: both complete upgrade paths +existing-only8.
New negative fixtures now close their SQLite connections explicitly; no suppressed
warning/assertion. New existing-only tests scoped POSIX (provider rejects Windows);
all8 still execute on Linux, no original fault test skipped or weakened. Windows
runtime not tested/qualified here.

Fresh full retry now under /workspace/work/phase4-2h2b1-existing/full-python-final:
368 discovered tests,230 source/test/native/script/packaged-guide hashes frozen;
owned detached supervisor persists receipt independent of interactive shell. All
tests run without fail-fast so any further failure and remaining gates are recorded.
No source modifications or concurrent emulator/Go/Gradle while this gate runs.
Still IN QUALIFICATION; do not move to native volume config/Handler/Agent/FGS until
full PASS, security review, qualification commit/push and exact remote verification.

### h.2b.1a final scoped qualification
Source923c5558b92c0acd473109b19857cbf3b56c00e5 normal-pushed/fetched/advertised
remote exactly before qualification ended. Fresh full368 Python PASS0fail/error/
skip in1991.896s, ended2026-10-26 11:07:14 UTC; all230 frozen inputs unchanged.
Original Core3A–3D/quorum/physical-GC/observer/browser/compatibility gates run,
including historical AND current-source upgrade/rollback; no failed prior run
counted as PASS. Raw logs/freeze/receipt remain private under full-python-final.
Public bounded receipt qualification/phase4-2h2b1-existing.json. Existing-only8
plus both complete upgrade scenarios targeted10 PASS44.775s. Android existing3/
regression18/foreign1 and retained identity proof, Go11/vet/verify/builds, strict
APK/signature inventory results above apply to unchanged Engine/native source.
JVM13 retained unchanged, not fresh executions. No new public APK/release.

This qualifies only canonical existing-metadata open policy on Linux/API35 private
storage, not Native Storage Agent/FGS or full4.2. Android26–29/ARM64/phones/Doze/OEM/
direct LAN remain unqualified; writableDR blocked. No second Catalog/Engine, schema
migration, Node ID regeneration, physical GC unlock or old DB rollback.

Owner steering2026-10-26: prioritize working Native Node over additional hardening.
From here implement minimum existing Engine/enrollment/Node TLS/heartbeat path and
actual file SHA/restart; use targeted changed-path tests. Defer extra hardening and
another full regression until integrated qualification, reuse current full evidence
for unchanged code. Keep existing TLS/pinning/identity/data guards; no test weakening
or fake runtime PASS. Next h.2b minimal approved private Node volume +same canonical
StorageHandler over existing JSSE adapter, then owned Agent/FGS and actual transfer.
No more repeated full Core suites for each small adapter-only checkpoint.

## h.2b MVP session source — IN ANDROID QUALIFICATION
Prior prerequisite qualifier fa593325b308dd49a3a4e77f6fc3b805eb0e0dc8 normal
push/fetch/advertised remote matched before these changes. Following owner request,
implement working Node path first, targeted tests only; no new full Core run.

New NativeStorage fixed private approved volume +NativeRuntime reuse SAME canonical
Engine/StorageHandler/Core heartbeat, no parallel Registry/Catalog/backend. Native
JSSE enters unbound Python handler. Existing Node/TLS/app identity reused; missing
manifest/marker refuses, partial setup held. Local approval never remote/domain
approval. AIDL2 configure,3 start; node_status/stop_owned; minimal Vietnamese UI.
Stop works after consent revocation. Activity-bound session, FGS not implemented.

Fresh targeted Native43 PASS14.859s0skip +original storage cluster4 PASS10.586s0skip.
The4 NEW Node tests prove actual Linux TLS/Controller-introspected upload/verify/
SHA download, real heartbeat, stop/restart same bytes/Node/Volume, missing-state
refusal, held interruption and Controller-loss denial. Linux platform socket
fixture is NOT Android JSSE evidence. No original assertions/tests weakened.
Gradle main/testAPK/JVM build PASS30s; private APK audit original signer,118 Core
modules, unchanged3permissions/no inventory findings. New source APK SHA
2d843e1be727782105f092396a2620a5ba7c2ef76daa11477c3eb4fd46ee8d60. No public
APK/release. Full368 earlier applies to source923c5558, NOT this new runtime.

Next: preserve prior primary app/Node/enrollment/TLS/Keystore state and original
signer, owned AVD restart only; actual Binder/configure/JSSE HTTP/Node I/O targeted
Android qualification, then owned Foreground Service and direct-network E2E.
No uninstall/clear/reseed/Termux adoption. Original old cipher proof must not be
overwritten to hide the legitimate new storage/revision mutation; compare retained
identity/token/TLS and old committed bytes separately. Full4.2 NOT ACCEPTED.

### h.2b actual Android Native Node MVP qualification
Source9001f152daaddeda70ea50dcea57669dadd1bccf normal push/fetch/advertised
remote matched. Owner requested fewer broad/security gates; focused actual Node
path only, no new full Core run or additional hardening layer.

Owned ASC_JOIN_UI_API35 x86_64 TCG resumed original userdata (boot262.266s). First
launch failed AVD discovery before boot; corrected ONLY task development AVD_HOME,
no HOME/proxy/CA/system/identity change. Original installed APK61eb0323... pulled
and preserved, updated normal install-r to same-signer2d843e1b.../version3. UID
unchanged, no uninstall/clear/-d/identity reset. Synthetic Controller restored
original g.2c Registry/cert at the same pinned endpoint;1 enrolled Node, no re-join.
Private fixture owner credential generated only for isolated test operator, not
node credentials/authority reconstruction; no Raft/quorum/DR involved.

Actual NativeNodeMVPTest binder session PASS30.023s: same UID private Binder ->
production NativeNodeSession ->canonical Python Runtime/StorageHandler/Engine over
actual JSSE; real write/read/SHA/fsync probe; real pinned heartbeat, explicit owner
storage grant;256KiB/all256-byte upload/commit/verify/download; stop/start same
port, old exact bytes and same app/context/Node/token/TLS/Volume identity. No Kotlin
mock backend, no fabricated Replica VERIFIED/replicated_2. Core Catalog approval
is NOT auto granted: this is an explicit legacy owner-delegated local object.

Then force-stop ONLY owned task app, confirm old process absent; independent fresh
process case PASS13.499s: same Keystore/context/Node/token hash/TLS/Volume/file ID,
actual new Node TLS listener and authenticated download of prior SHA bytes. Two
actual tests0skip/fail. Original old cipher proof untouched: legitimate storage/
revision publication changes encrypted record, retained identities verified.
Initial wrong runner command did not execute a test; retained separately, never
counted as PASS. Main APK unchanged, testAPK build PASS. Public bounded receipt
qualification/phase4-2h2b-mvp.json; private raw logs/fixture under phase4-2h2b-mvp.

Scope: API35 x86_64 emulator guest-loopback Node +explicit dev reverse to Controller,
NOT direct LAN/ARM64/phone/Doze/OEM, two protected independent replicas or production.
Activity-bound Node only; FGS/notification Stop/background lifecycle next. Observer
and direct-network qualification remain. Full4.2 NOT ACCEPTED, writableDR BLOCKED.

## h.3 Foreground Node — actual API35 targeted PASS
Prior Android MVP checkpoint2c2edd81c3b00e1047807509c076ede88eb15d9e normal
push/fetch/advertised remote matched before these changes. Owner MVP priority kept:
no additional hardening layer/full Core repeat; actual functionality focused.

Same EngineService promotes ONLY the explicitly started real Node to connectedDevice
FGS;4 standard manifest permissions (base/type/normal network prerequisite/visible
notifications). Android docs verified; no proxy/CA/system-network edits, new crypto/
Catalog/Engine. Existing UID/consent/device/TLS/data guards reused. UI permission
request before start; no actor left on promotion failure. Notification Stop and
health cleanup close only owned resources; START_NOT_STICKY/no boot auto-start.

Fresh NativeNodeForegroundTest actual API35 x86_64 PASS58.326s0skip/fail: launch real
Activity, own private Binder starts existing Node, actual OS service foreground
flag and own notification asserted; remove BOTH UI and test service bindings,
close Activity; actual pinned/granted old-file SHA download succeeds in background.
Invoke actual notification PendingIntent Stop, require notification/foreground
gone AND actual TLS port closed. No mocked service flag/idle keepalive success.
Runtime notification permission was operator-granted on owned emulator; permission
dialog/OEM/Doze/phones/ARM64 not qualified. Explicit dev Controller reverse/Node
guest loopback remains NOT direct LAN. Current data was retained across normal
same-signer install-r; prior2d843e... APK backed up, no uninstall/clear/-d.

Main/testAPK Gradle build PASS36s/JVM13 PASS (main build executed tests; subsequent
test-only syntax correction reused same results). Initial NEW Android test had a
Kotlin destructuring syntax error; corrected, no assertion removed, final build
and actual runtime rerun passed. No current Python/Go code changes or new full
regression claimed. Inventory/signature118modules/7exact documented permissions/
no findings/original signer PASS; private version3 APK SHA
55bec3d9a9a9590ef6b35d70c37e164eed76ed4b2d56021175e96bc9fb44a4d5. Public bounded
receipt qualification/phase4-2h3-foreground.json, private logs phase4-2h2b-mvp.
No public APK/release, full4.2 NOT ACCEPTED. Remaining read-only observer, direct
network/E2E/independent replica qualification and final integrated fresh gates;
extra hardening deferred per owner preference, existing data guards retained.

## h.4 Native direct networking / address setting — targeted PASS
Prior FGS checkpoint f566915088a790929e680b795f7d33d482239df3 normal push/fetch/
advertised remote exactly matched before this checkpoint. Continue owner MVP
priority: actual file path first, no repeated full Core suite/extra hardening.

Actual current owned AVD direct10.0.2.2 TLS PIN+Cluster probe PASS9.935s with reverse
removed. Historical other-AVD ConnectionRefused is not relabelled/root cause proven;
this is fresh evidence on ASC_JOIN_UI_API35, no proxy/CA/network-policy changes.
Explicit production API now changes Controller address using existing Core info/
CAS, SAME PIN/CID/Node/token/TLS/volume, stopped Node only; no re-enrollment or
automatic failover. UI public Node PIN display supports explicit owner approval.

Fresh targeted Native46 PASS14.632s0skip/fail (3new alias/pending/identity/storage
tests+43existing); Gradle/JVM13/main/testAPK PASS. Actual cold-process Binder address
setting PASS14.730s, existing Node retained. On final APK, public repository driver
and NativeNodeDirectTest PASS84.213s: remove reverse; Node binds measured guest
10.0.2.15, heartbeat/introspection to Controller10.0.2.2; actual host uploads256KiB
through loopback-bound standard SDK NAT redirect, commits, asks real Node verify,
downloads exact SHA2312394bd99545d9de131c24efb781e765ac1aec243f2ed9347597a793a415e9.
ADB is test control/receipt only, NOT bytes transport. Original app/context/Node/
token/TLS/Volume/storage retained. No second Catalog/Engine, no new permission/
dependency. Metadata writer/GC/Raft/approval still not granted.

First new two-sided attempt FAIL84.887s: host90s overall-startup deadline expired
before Node READY,0direct uploads confirmed in synthetic manifest. Fixed ONLY
harness startup allowance180s, Android result wait90/data/TLS deadlines/assertions
unchanged. Final public driver confirmed actual data and JUnit success; no failure
counted as PASS. Startup84.949s includes cold instrumented UI/TCG; not file throughput.
Private logs/readiness/receipts retained under phase4-2h2b-mvp. Public bounded proof
qualification/phase4-2h4-direct-network.json, reproducible tool documented in native
operations. Main APK internal version3/original signer, no public release.

Remaining: Native Core quorum observer/read-only UI, final integrated gates and
version-increased debug candidate/upgrade qualification. Physical phones/ARM64/
Doze/OEM/real LAN and two independent-domain replica/fallback NOT TESTED. Standard
emulator NAT success is not those acceptances. Full4.2 NOT ACCEPTED, writableDR
BLOCKED. Preserve active AVD, signer, original stopped upgrade AVD and all private
Node state; no resets or old cipher-proof overwrite.

## i.1 Native observer client — Linux synthetic targeted PASS
Started from clean de9767364d7daa195399da1b4670f286d1c63bbe; fresh WIP feature
fetch matched HEAD. Existing mandatory contracts read, owner MVP priority retained:
targeted changed paths, no repeated full Core or additional security subsystem.

Added canonical asc.observability.native.NativeObserver consuming ONLY existing
Phase4.1 HTTPS owner gateway. Uses existing pin transport and one-use owner login/
session/CSRF, explicit mode/Cluster/epoch/index, RAM-only observer credentials.
Node context/credentials, Core3D source, Engine/Catalog/schema untouched. Fixed
read-only routes and existing gateway projection; no duplicate backend. Login ACK
loss requires NEW owner code, not blind replay. Offline/expired sessions UNKNOWN;
stale Leader flags alone cannot supply quorum/protection. Full-byte recovery view
remains passive/read-only, never writer activation.

Fresh final targeted command: python -B -m unittest tests.test_native_observer
tests.test_observer_gateway.GatewayHTTPTests
tests.test_observer_gateway.RecoveryGatewayTests
tests.test_observability.ObservationUnitTests -v -f
**12 PASS /0FAIL/0ERROR/0SKIP,40.877s**. Includes new8 tests, actual three-voter TLS
partition/stale Leader/quorum loss/Controller death/reconnect, actual owner cookie/
CSRF, wrong pin/mode before code consumption, Cluster/epoch/floor rejection,
process/server session loss, corrupt byte staging and retained gateway mutation
denial. Earlier development7PASS4.838s+Core1PASS23.844s are separate, not added to12.
Existing redacted handler messages on intentionally rejected/missing login are
expected; no credential/raw exception printed. No old test weakened/removed.

i.1 is Linux client qualification, NOT Android observer acceptance. No APK build/
install/source UI change, no new published artifact, no fresh full Python/Go claim.
Rollback: compatible prior source retains existing Node/app state unchanged;
observer credentials are ephemeral, new owner login needed after restart.
Next i.2: private typed Binder +minimal Cụm page, actual gateway/TLS on preserved
owned emulator, same signer/Node/volume/bytes. Full4.2 NOT ACCEPTED; phones/ARM64/
Doze/OEM/independent two-domain replicas/final integrated gates still outstanding.
Writable DR remains BLOCKED. Publish normal feature-only push and fetch verification
before i.2; this receipt's exact commit is available in Git history.

## i.2 Native Core observer / Cụm UI — targeted PASS
i.1 commit92f4ed2c5e9d3b92a43608aa0330bedbbb51df81 normal push/fetch/advertised
remote matched before i.2. Keep owner MVP scope: changed-path tests only, no new
security subsystem/full Core repeat. Actual functionality over decorative UI.

New private AIDL observeCore transaction4 retains0–3, existing caller UID/signature/
consent/device/app-key gates. NativeCoreObserver reuses canonical Python client,
separate owner gateway session in RAM, not Node credential/context. Fixed login/
state/logout, explicit public binding/mode/owner trust,192KiB Binder result bound;
no source bootstrap/private key/URL-method passthrough. Node lifecycle lock stays
independent. Minimal Vietnamese Cụm page shows actual Core controllers/voters,
confirmed Leader/quorum, nodes/volumes, file replica counts/protection/jobs and
historical backup; UNKNOWN stays UNKNOWN. Network/background clears transient
code/trust/displayed health. No new schema, Keystore alias, permissions or dependency.
Optional observed Core cluster does not migrate the active single-writer Node.

Fresh Gradle build/JVM15 PASS0skip/fail (original13+2 observer policy tests); main/
testAPK builds PASS29s, final test-only rebuild PASS25s. Main APK unchanged during
tests: SHA d1847ce8e73a7af44ad5b830875e4877143dd0b3c0486489de8613daceb2672a,
internal versionCode3, original signer bba77b68e43ecfe885705442d2224977208bf77a397c216393c26fc151a6bc30.
Prior exact installed h.4 APK8df08b... preserved privately; normal install-r only,
app/test UIDs10148/10149 unchanged, no uninstall/clear/-d. Final bounded inventory/
signature audit119 canonical modules/7 unchanged permissions/no findings PASS.

Actual API35 x86_64 NativeObserverTest **1 PASS90.332s**, public driver113.234s
including startup (host harness1PASS126.813s including source fixture/cleanup).
Real existing3-voter Core/Storage Engine uploads a replicated_3 file; APK's actual
UI/private Binder/canonical Python connects to existing gateway over task-host
private IP HTTPS DIRECTLY (not ADB reverse). Wrong pin refuses without consuming
grant; real owner UI login displays3nodes/3verified+available replicas. Actual
three-island Raft transport partition yields QUORUM UNAVAILABLE/false quorum,
UNKNOWN Leader/current availability; actual heal restores strong read. Logout
clears session; same app Keystore identity and exact decrypted Node-context payload
retained (no plaintext credential returned/logged; not a ciphertext-byte assertion).
Native app is an observer here, NOT a Core voter or the3 synthetic storage nodes.
Same-host source domains simulate, never prove independent phone hardware.

Initial new Android case FAIL79.910s (host harness152.836s): ACK control JSON was
read during non-atomic host write after actual partition. Main APK/source and ALL
Android/data/fault assertions unchanged; host-only fixture ACK now temp+rename.
Fresh complete rerun above PASS; failure remains private actual-gateway logs and
is not counted as successful fault qualification. No timeout/assertion weakened.

Then **12 Android regression PASS136.452s0skip/fail**: existing Vietnamese UI2,
private Binder4 tests (consent/version/dangerous-op/golden transaction1), canonical Engine
actual write/SHA/fsync/restart1, exact previous-APK existing manifest/volume/body
integrity and refusal3, actual original Native Node old-file SHA download/retained
identity1, actual default-network loss/recovery1. The network case additionally
asserts owner observer code/trust/healthy view clear; original assertions retained.
Total current i.2 Android13 PASS across two runs, not an invented single suite.
Fresh Linux12 PASS40.877s belongs unchanged i.1 client; no new full Python/Go result
is claimed. No older/broken run counted or historical fault gate removed.

Private artifacts/logs: /workspace/work/phase4-2i-native-observer. Public contract
ANDROID-CORE-OBSERVER; reproducible tools/qualify_native_observer.py requires OWNED
AVD, existing app/test APK and explicit task-host private IP, never a phone. No
new public APK/release. Rollback contract keeps NEW app/Node/volume/bytes (no
observer persisted schema), original signer and Android version rules; observer
session requires fresh owner code. No new APK rollback execution is claimed here.
Do not restore old databases, uninstall or force a downgrade/signer replacement.

Next j: integrated Node/enrollment/lifecycle/network/fault qualification, increase
APK versionCode, preserve signer/state and prove upgrade, fresh applicable Python/
Go/fault/build/package checks once final candidate is ready. Physical phones/LAN/
ARM64/Doze/OEM/two truly independent-domain replicas/fallback remain NOT TESTED;
Core3D writableDR BLOCKED, full Phase4.2 NOT ACCEPTED. No original branch/archive
changed. Normal feature-only commit/push/fetch verification before any next source
checkpoint; publication receipt follows without retesting unchanged source.

### i publication / resume receipt
- i.1 code/docs92f4ed2c5e9d3b92a43608aa0330bedbbb51df81: normal push, fetch and
  advertised feature remote HEAD matched before i.2 began.
- i.2 source/qualification78d4b08b056ad4324ad512b94d8d5e6b02e5c826: normal push,
  fresh fetch and ls-remote HEAD all EXACTLY matched; working tree clean.
- This follow-up changes only reporting docs/evidence, not qualified source/APK;
  targeted results reused unchanged, no redundant full regression. Original
  Core/Demo/Phase4.0/4.1 branches and old artifacts are untouched.
- Resume j from current feature HEAD. Read this progress/acceptance plus
  ANDROID-CORE-OBSERVER/operations. Preserve original debug signer and current
  ASC_JOIN_UI_API35 AVD/app/Keystore/Node/volume/old bytes; verify fresh ownership
  before ADB. Private current work: /workspace/work/phase4-2i-native-observer;
  existing emulator/Controller ownership receipts remain in phase4-2h2b-mvp.
  No real-phone/M51 operation, reset, signer recreation, data clear or forced
  downgrade. Current APK stays private version3; no new public candidate yet.

## j.1 actual Native Node +Demo Catalog/File Manager — targeted PASS
Baseline c4ece1e5201c8bcdee108605f64c183042727ae0 clean/fetch equal. No product
Engine/Catalog/enrollment/runtime/authentication source changes: existing main APK
d1847ce8e73a7af44ad5b830875e4877143dd0b3c0486489de8613daceb2672a/version3/
original signer reused. This checkpoint adds actual mixed-runtime qualification,
not another Storage Engine, native File Manager or Core-to-Demo migration.

Separate NEW ASC_NATIVE_CATALOG_API35 AVD/serial emulator-5560 on private ADB5038,
official existing API35 x86_64 image/TCG. Original AVD/identities were not adopted.
Actual marked Demo Controller +Linux peer use existing synthetic getprop/pkg/CLI
fixture outside Git; Android app uses its REAL Build/context/Keystore/Engine. No
Android/Core runtime guard override. Public tool validates task QEMU UID/AVD,
original signer and exact installed APK, never discovers phones. Native joins
through pinned HTTPS10.0.2.2. Host Node endpoint uses loopback-only standard SDK
NAT; ADB is control/receipts only. No ADB reverse/file-byte transport or proxy/CA
changes. Owner explicitly approves native volume/domain via existing API, with
metadata permission false; app does NOT self-approve. Linux and AVD domains are
asserted synthetic labels on ONE host, NOT independent physical devices.

Final complete retained-state run e0c7166f8fc949cdaa633667a432be17 PASS: existing
trusted-CA Chromium Dashboard owner login ->upload256KiB/all256-byte values ->two
actual Core-scoped/independently hashed replicas including APK Engine. Existing
390px/XSS/literal name/HTTPS/session/unknown/offline/download-SHA assertions retained.
Stop actual APK Node via private Binder; browser download falls back to Linux peer
and matches SHA2312394bd99545d9de131c24efb781e765ac1aec243f2ed9347597a793a415e9;
new upload denied with only one eligible domain, no ghost file. Restart native,
wait actual verified+available2, then directly read Native copy with scoped grant.

Stop actual Controller; Native TLS listener remains reachable but old read grant
gets EXACT503 authorization_unavailable, not just connection refusal/expired auth.
Restart same Controller identity. Complete first Android holder, actual own-app
force-stop then second instrumentation process; same app/Node/Cluster/TLS/Volume/
decrypted context hash, fresh Core proof and DIRECT Native-copy SHA readback PASS.
No fallback hides a missing Native copy in this retained-process assertion.
Two Android receipts:141.100s +88.128s,0skip/fail. Host full report PASS, browser
report PASS2replicas/verified SHA/CA trust and untrusted-CA refusal. Old unchanged-
fixture browser regression separately PASS12.387s. Test-APK builds PASS3m15s under
memory contention, then diagnostic build PASS; no new main APK or fresh JVM/Go/
full-Python claim. Original main code/hash unchanged from i.2 scoped JVM15 receipt.

Real failed/incomplete attempts are NOT counted as this PASS:
- SDK avdmanager lacks installed-package metadata for the already qualified
  emulator binary. A premature launch before AVD creation failed before any app
  existed; retained logs, created only NEW AVD text config using existing image.
- Two simultaneous TCG VMs exhausted usable memory/slow startup. Original
  ASC_JOIN_UI_API35 exited SIGSEGV(-11) BEFORE console-stop verification completed;
  console kill was not executed. Preserve original userdata/key images8files via
  offline copy; original signer intact. Primary crash-restart/readback still NOT
  TESTED here, not claimed clean shutdown/power-loss proof. New AVD remained live.
- First instrumentation shortMsg=Process crashed before JUnit start,0tests. Actual
  Launch/Binder diagnostic subsequently2PASS32.553s. No identity existed then.
- Setup resume initially rejected the known reserved local-controller row;
  corrected ONLY fixture precondition to require exactly its original Linux peer
  besides that reserved non-storage identity. No Registry/identity was deleted.
- Fresh native case DID enroll and persist local volume/proof but missed host
  READY deadline. Its completed cold-initialization JUnit receipt is UNKNOWN/
  INCOMPLETE, NOT PASS. Subsequent runs explicitly resumed SAME Node/context/
  Keystore/volume; no reinitialization/new Node to evade failure. The passing full
  run starts retained, not falsely relabelled fresh installation acceptance.
- Prior full retained attempt had successful browser/authorization and2Android
  receipts but host ended StopIteration: it mistook reconcile {busy:true} for
  completed proof. Fix ONLY wait predicate: actual nonbusy reconciliation AND
  verified2/available2 required before selecting Native download candidate. No
  byte/identity/auth assertions removed, no product limits/security weakened.

Private state/logs/supervisor/owner: /workspace/work/phase4-2j-native-catalog;
qualification/home preserves original Demo Controller/peer/CA/Registry/data and
qualification/runs keeps EVERY run separately. New AVD native context/proof/bytes
remain intact. tools/qualify_native_catalog.py --resume requires that same source/
APK/AVD; --resume-setup ONLY preidentity interruption (no app/context/proof and
only original peer Registry row), with existing app/Keystore NOT_PROVISIONED
assertion before provision. Lost/corrupt established identity is NEVER reset.

Docs ASC-USER-STATUS answers owner: web owner login/File Manager exists; native
file UI/multiuser login absent; LAN needs a local IP network but no Internet;
automatic hotspot/Wi-Fi Direct and Cloudflare remote are NOT IMPLEMENTED. No
Cloudflare/production/M51/real-phone/Termux operations performed.

Full4.2 NOT ACCEPTED. Next j.2 candidate/version+upgrade, primary crash readback,
remaining cold/fault gates, then j.3 final integrated full regression once. Phones/
ARM64/real LAN/Chrome Android/Doze/OEM/two physical domains/writableDR unqualified.
Rollback: main product source/APK/state formats unchanged; retain NEW test state/
objects, no old DB restore/uninstall/forced downgrade. Check tracked/index/untracked
secrets, normal feature push/fetch match before next checkpoint; receipt follows.
