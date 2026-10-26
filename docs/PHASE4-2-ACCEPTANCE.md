# Phase4.2 native foundation qualification

**Full Phase4.2 NOT ACCEPTED. Independent native FOUNDATION subset qualified on
actual API35 x86_64 emulator; fresh applicable Core regressions PASS below.**
The original a–e FOUNDATION results below are historical. Later g/h receipts
qualify actual native enrollment, owned Node, FGS and direct emulator NAT within
their scopes; i adds native Core observation. Final integrated j and physical
Android/Termux migration acceptance remain outstanding.
No real phone/production/M51 access, no Android Raft/GC/failover/writableDR.

## Actual qualification / scope

JDK17.0.21+9, Gradle8.11.1, AGP8.9.2, Kotlin2.2.20, SDK/target35/min26,
buildtools35.0.0, Chaquopy16.1/Python3.13. AOSP35 x86_64 actual boot/install/runtime,
software TCG (-accel off, no /dev/kvm), task-owned private ADB5038/loopback only.
Official source/version/checksum/TOFU limitations: ANDROID-TOOLCHAIN/toolchain-lock.
The final current-version native table uses the SAME published main APK, not a Kotlin mock Engine; the prior upgrade baseline is specified separately.

| Final Android gate | Result | Time |
|---|---|---|
|actual-controller-offline|1 PASS /0skip|11.861s|
|actual-controller-reconnect|1 PASS /0skip|11.298s|
|actual-default-network-ready|1 PASS /0skip|0.315s|
|foreign-uid-signer-permission-denied|1 PASS /0skip|0.254s|
|full-android-online|16 PASS /0skip|121.122s|

Final full16 includes real private Binder/consent/version/operation denial/golden
transaction compatibility, canonical Core Engine stream/commit/downloadSHA/verify/
fsync/restart, nonexportable KeyStoreAES/encrypted form/restart/key DELETION/no regen,
future/corrupt state hold, quota/reserve/actual unprivileged private0500EACCES restored
0700, marker/root/manifest/corrupt-object retention, SAF refusal, Vietnamese UI/
UNKNOWN/trust/background code clearing, real default-network readiness/loss/recovery
and controlled late UI callback discard during that real loss. Foreign1 has actual
different UID/signer/denied signature permission/explicit bind refusal. Public TLS
checks wrong pin/cluster and real stopped/restarted same registry+cert Controller;
zero enrollment mutation/Node credential issuance. No fake Node success or skips.

**Transport qualification is limited:** new upgrade AVD direct NAT10.0.2.2 returned
ConnectionRefusedError with INTERNET granted. That scenario is NOT PASSED and is
not replaced by a LAN claim. Final TLS/Controller gates explicitly select development
adb-reverse-loopback (guest127.0.0.1, real pinned Core TLS/cluster), no auto fallback,
HTTP downgrade, proxy modification or credential exposure. Only successfully owned
no-rebind mapping is cleaned. Actual WiFi/default-network loss UI gate is separate.
No proxy:8080 error observed. LAN on a physical Android device remains NOT TESTED.

Earlier15/16 runs correctly failed missing real default network and direct NAT;
setup failures, UI race correction and no-rebind reconnect harness fix are recorded
in PROGRESS. Final table is the last successful complete pipeline, not a blend of
failed runs. Native main APK SHA stayed unchanged through test-harness corrections.

## Exact prior native APK upgrade / process death

PRIVATE checkpoint4.2c0.1.0-foundation/versionCode1 SHA
7235444589ff0ae9fa3f56dfc4cc23bae910b46fdef27c290b021333959f6de9 -> current native
0.2.0-foundation/versionCode2 SHAab1b2da3797df93ea7fbc186866c187f8b04802f3b614fed4afcaa232fddf705.
Fresh AVD, installed base SHA checked, same debug signer, normal install-r only.
Five actual PASS gates: exact old binary seed; same-key upgrade preserving appUUID,
Keystore canary, exact encrypted UNSENT form/request, Volume ID/marker and committed
Core object SHA/COMMITTED verify; actual force-stop/start retaining all; Android
INSTALL_FAILED_VERSION_DOWNGRADE; retained state verification after refused downgrade.
No uninstall/clear/-d, old DB restoration, new Node/Cluster identity or Termux copying.
Old APK is private qualification input, not a released native baseline. No general
native rollback package/Keystore backup/restore or released Termux upgrade is claimed.

Fresh JVM/lint: --rerun-tasks BUILD PASS40s/40executed tasks,10JVM PASS0skip; lint0errors21warnings (17VN-only strings,3pinned dependency notices,1durable consent commit). Gradle9 remains unqualified. Exact upgraded state also verified PASS after all Android faults.

## Artifact / security

`android-artifacts/asc-native-foundation-0.2.0-debug.apk`, org.asc.foundation,
versionCode2, min26/target35, internal DEBUG only, ARM64+x86_64 packaged.
SHA256: `ab1b2da3797df93ea7fbc186866c187f8b04802f3b614fed4afcaa232fddf705`.
Signer certificate SHA256: `bba77b68e43ecfe885705442d2224977208bf77a397c216393c26fc151a6bc30`.
Permissions: own signature LOCAL_ENGINE, INTERNET, ACCESS_NETWORK_STATE only.
No broad storage/camera/boot/FGS/notification permission. export=false Service plus
per-call UID+signature and explicit consent. M51/unknown unit fence10 JVM suite,
no real device access. No runtime/Core guard removed. No secret in browser storage.

Inventory/pattern audit:109 canonical Core modules, byte-identical generated public
source inputs and matching packaged module set; nested Chaquopy archives/DEX checked,
no private key/state/credential pattern or test-only class found. apksigner and exact
SHA sidecar PASS. Not comprehensive binary SAST, publisher signatures or hardware
attestation. SDK/private keys/cache/AVD/test APKs/foreign fixture are not published.
Debug signer remains PRIVATE: another account's new debug key cannot update this
APK. Do not uninstall/clear state to bypass signature/version refusal.

## Remaining implementation and runtime gates

| Gate | Status / next evidence |
|---|---|
|Canonical Engine library actual Android I/O|PASS; not a joined Node|
|Native Core enrollment/resume and Storage Agent|NOT IMPLEMENTED; remaining4.2g/h; no CLI/HOME/subprocess bypass|
|Native TLS identity/certificate provider|4.2f.2 targeted PASS API35 guest loopback; does not qualify a Native Node|
|Encrypted unsent form|PASS; NOT Core pending enrollment/token/Node identity|
|Owned Node/Controller lifecycle, FGS/notification/stop|BLOCKED; no idle fake service/background uptime claim|
|Native authenticated Core observer/node list/replicas/quorum|UNCONFIGURED/UNKNOWN; existing Linux adapter retained|
|Native LAN10.0.2.2 on new Cloud AVD|NOT PASSED: ConnectionRefusedError; dev tunnel proof is separate|
|Hardware/biometric permanent-key invalidation|NOT TESTED; key deletion/loss was exercised|
|SAF/revoked provider/SD/USB|NOT SUPPORTED; private EACCES is not SAF revocation|
|QR scanning/automatic trust|NOT IMPLEMENTED; manual owner binding only|
|Android mid-write power loss/Doze/OEM long-running Node|NOT TESTED|
|Termux→APK/key/volume migration; production signer/rotation/native rollback|NOT IMPLEMENTED/NOT ACCEPTED|
|Android11 ARM64 ZTE/Bphone/Sony/other phones|NOT TESTED; ARM64 package/build only|
|API26–34,36+ runtime; Windows runtime|NOT TESTED; minSDK declaration/cross-build does not prove runtime|
|Android Raft/GC/failover/recovery writer|FORBIDDEN; Core3D staging remains read-only|

## Fresh final regression — actual final run

Frozen source/tests/packaged guides/project/APK:
`c7dabb041ee06ed27de7077f1ceb7c51f59288a1` (native source67fdd0c).
Fresh full actually ran2026-10-25 19:20:48UTC→19:51:06UTC:
`python -B -m unittest discover -s tests -v -f` **317PASS/0FAIL/0ERROR/0SKIP**,
1817.803s test time.243 frozen file hashes unchanged during run and rechecked after
Go/audit. Reporting docs/receipts only afterward. No historical311 result reused.

| Retained actual Linux synthetic fault group | PASS |
|---|---:|
|Phase3A backup/version/restore|12|
|Phase2B takeover/fencing|20|
|Phase3B|7|
|Phase3C|3|
|Linux actual physical GC|8|
|GC network authorization|3|
|Phase3D external backup/recovery staging|9|

All required banner IDs checked for exact count/sequence, not just exit0. Existing
Core faults/regressions were retained. First full attempt failed after76tests due
a Dashboard fixture readiness race; c7dabb0 waits only CA-verified TLS handshake
before original FIRST HTTP401/key-preservation assertions. No cookie/HTTP response
retried into success. Targeted6PASS29.498s +strict restart3PASS20.901s +actual browser
1PASS9.671s before fix push/remote and a completely fresh full317 run.

Go final fresh2026-10-25 23:50UTC: `go test -count=1 -v -timeout 240s ./...`
**11PASS**, `go vet ./...` PASS, `go mod verify` PASS. `CGO_ENABLED=0 go build
-trimpath -buildvcs=false` Linuxamd64/Windowsamd64/Androidarm64 PASS. Windows/Android
are CROSS-BUILDS, not runtime. Core asc/, consensus/, old release/candidate archives
and packaged Phase4.1 guides remain byte-identical to accepted Phase4.1 baseline.

Fresh post-full APK nested/module/test-class/signature/SHA audit PASS,0 findings
under stated bounded review. Published artifact was independently fetched into a
separate bare repository: exact APK SHA and all243 frozen source hashes matched;
all5 protected Core/Demo/Phase4.0/4.1 branch heads unchanged. Final documentation
publication verification follows this report commit; no source or APK drift allowed.
Old candidate0.4.3 SHA96260f1709f6a9db6cb98869fbef8fc2313feaf68a4f12da354665ad04693c04
also independently matched, not rewritten. Full reports: `qualification/phase4-2-
foundation.json` and `qualification/phase4-2-source-sha256.json`.

Full Phase4.2 remains **NOT ACCEPTED**: shared-Core native enrollment/Node TLS/agent/
owned FGS/observer providers and direct LAN are outstanding. This closes independent
foundation regression/package qualification only. Continue remaining4.2 work before
native Node acceptance; no Phase4.3/production readiness or Termux migration claim.
See ANDROID-NATIVE-IPC/STATE/OPERATIONS/PILOT and PHASE4-2-PROGRESS.

## Continuation4.2f.1 — scoped context gate, NOT full Phase acceptance
Explicit native context and actual Keystore sealed provider now qualify separately:
24 targeted Python/11JVM/15Android(PASS45.226s,0skip), actual context process-death
restart and retained prior-native-APK state proof PASS. Gradle build/lint/package
audit PASS. Original public artifact unchanged; new private version3 checkpoint
is NOT a release. Public bounded evidence: qualification/phase4-2f1-context.json;
exact source/commands/failures/limits in PROGRESS and ANDROID-NATIVE-CONTEXT.
All old table entries about missing enrollment/TLS/Agent/FGS/observer/direct LAN
remain outstanding. f.1 creates NO Node/Cluster identity. Full Phase4.2 NOT ACCEPTED,
new-source full Python/Go/fault regression is deferred until final runtime gates.

## 4.2f.2 fresh targeted acceptance — TLS provider only
Workspace/source/signer/AVD recovered, all12 dirty source files preserved; normal
docs-only161e833 fast-forward without reset/overwrite. Full Phase4.2 NOT ACCEPTED.

Fresh34 Linux/11JVM/20Android(106.286s)+foreign1 PASS0skip/fail; actual BC/JCA/JSSE
handshake with canonical Core pinning, wrong pin/default-system-trust denial,
key mismatch, Bionic sealed memory/FD cleanup, Keystore/corrupt+missing state,
context/Binder/Engine regression. Actual process-death TLS fingerprint/exact
ciphertext/app/context identity and retained old native upgrade-state proof PASS.
No new app identity/VolumeID, no uninstall/clear/forced downgrade or old DB restore.

Explicit native JSSE avoids the recovered Android proc-fd EACCES while retaining
actual memfd/sealing/readback checks. No plaintext disk/raw syscall/policy change
or failed-operation fallback. TLS key is software in RAM, Keystore-encrypted at
rest, not hardware nonexportable TLS signing. Native TLS26–29 NOT QUALIFIED.

Strict build/6new dependency hashes/old pins retained/bounded APK audit PASS;
original signer,112 canonical modules,unchanged3permissions. Private version3 APK
SHA88435153fda9493bf13bd75a2d4e6a0cd3bc6c833e179e275b5f0faa511f2aa3, no public
artifact/release. Lint0errors22warnings includes retained unused BC EST trust-all
helper warning; app uses no such helper and actual default trust rejects untrusted
peer. Review scope in ANDROID-NATIVE-TLS; not comprehensive binary SAST.

Evidence/progress/API/state/security docs updated. Remaining g enrollment, h native
socket adapter/Agent/FGS, i read-only observer, j direct LAN/end-to-end/fresh full
regression remain separate. This does not close those mandatory Native Node gates.

## g.2a targeted source receipt — Linux only
Native sealed-context enrollment adapter:9 new actual Core Registry/TLS fault
tests +61 related context/TLS/CLI/lifecycle/QuickJoin regression PASS0skip.
This is not Android native enrollment acceptance: test-only memory CAS does not
prove Keystore persistence or Binder/UI network use. No APK rebuilt/published.
Full Phase4.2 remains NOT ACCEPTED; g.2b actual Android join/resume qualification,
h Agent/FGS, i observer and j direct network/fresh full gates remain outstanding.

## g.2b source qualification — API35 owned emulator, explicit dev loopback
Fresh Linux33/JVM12/Android28 targeted PASS0skip; actual foreign caller denial1
and5 fixed process/TLS/old-upgrade proof phases PASS. Real Core Registry/Keystore/
pinned TLS enrollment:4 Nodes,0 automatic storage approvals,2 actual successful
ACK losses +same-operation resume. Node/app/context/TLS/volume/draft/committed bytes
retained; original signer and UID preserved by normal install-r. Public bounded
receipt qualification/phase4-2g2b-enrollment.json; exact commands/scope in current
progress and ANDROID-NATIVE-ENROLLMENT. No new public APK/release. Private source
APK version3 SHA59541e41afe010a9ca7c6041c96d16549b727666d4430fedafdf717d88bb62bd.
Positive enrollment uses the actual native provider/Core on Android; real Binder
pin-failure/consent/allowlist and UI trust gates qualified. Positive full UI/Binder
join still g.2c; Agent/FGS/observer/direct LAN/phone acceptance not claimed. Full
Phase4.2 NOT ACCEPTED, writer DR BLOCKED. Full Python/Go/fault gates still deferred
to final changed-runtime qualification; historical counts not reused as fresh.

## g.2c real UI callback / Binder / Core proof (limited)
Three fixed actual API35 x86_64 phases PASS across force-stop/cold restarts:
MainActivity View callbacks ->production private Binder ->embedded Core ->real
pinned Controller. One real successful ACK lost, twoPOSTs, one accepted Node,
zero storage approvals; app/context/TLS/operation/token/Node/cipher identities
preserved. No direct adapter substitute for UI send/resume. Main APK unchanged
SHA59541e41.../original signer, new testAPK Gradle build PASS. JVM12 reused unchanged
from g.2b, not fresh counts. See qualification/phase4-2g2c-native-ui.json.
Initial new-AVD SIGABRT before UI gates and fixture readiness failures retained in
progress; same userdata recovered without wipe/identity reset. Launcher Quickstep
ANR observed: programmatic real UI/Binder proof is NOT physical-touch usability
acceptance. Interactive UX NOT QUALIFIED, direct LAN NOT PASSED, phones/ARM64
runtime NOT TESTED, Agent/FGS/observer absent. Full4.2 NOT ACCEPTED, writableDR
BLOCKED. This is no new public Android release/in-place upgrade claim.

## h.1 shared Agent transport — Linux source checkpoint
Fresh57 targeted Linux PASS0skip/fail: new actual TLS heartbeat/auth/outage5 plus
original lifecycle/storage-cluster/distributed/discovery-related regression.
Existing assertions unchanged; source/wire/CLI behavior preserved, no schema.
This is transport reuse, NOT native listener/Agent/Foreground Service acceptance.
No new APK/native tests/release; previously qualified Android artifact is frozen
at g source. Full4.2 NOT ACCEPTED, writableDR BLOCKED; h.2/native owned lifecycle,
i observer and j direct LAN/fresh full gates remain.

## h.2a native transport scope — API35 guest loopback
Fresh Linux23/JVM13/Android3 socket +15 retained TLS/context/Engine/Keystore tests
PASS0skip; actual foreign caller denial1 and2 retained enrolled-identity fixed
verifications PASS. Binary1MiB/all256 values through real JSSE/JNI/Core pinned
client; actual idle read and blocked-write deadline/close/worker exit proved.
Not physical-file/replica or Storage Node acceptance. No new dependency/permission/
public release. Private version3 APK SHA89a2c9a29a6b41e1d198519eb67e4b87aed91b2e32f3f0282914f367c1da54b4
original signer/UID/enrolled Node/cipher preserved. Public scoped receipt
qualification/phase4-2h2a-socket.json, details in ANDROID-NATIVE-TRANSPORT/progress.
Native Handler/Engine integration/approved network volume/Agent/FGS/observer/LAN
still incomplete. Phones/ARM64/OEM/Doze not runtime-tested, interactive UX not
qualified. Full4.2 NOT ACCEPTED; full Python/Go/fault/new-candidate gates not yet
rerun for remaining runtime; writableDR BLOCKED.

## h.2b.1a existing-metadata prerequisite — scoped PASS
Fresh full368 Python PASS0skip/failure/error1991.896s on source923c5558, all230
frozen source/test/native/package inputs unchanged. Actual original physical-GC,
quorum/backup/observer/browser faults and both exact historical/current-source
upgrade scenarios passed. Earlier interrupted/failed runs retained, not acceptance.
Targeted10 PASS44.775s; actual API35 existing-only3 +original regression18 +foreign
caller1 and enrolled identity retention PASS. Go11/vet/verify/Linux+Windows+Android
builds PASS (Windows/Android cross-build only); JVM13 unchanged retained, not fresh.
Strict build/APK inventory/original signer preserved; no new public artifact.

Opt-in private POSIX Manifest/Engine mode refuses missing metadata and identity/
structure mismatch without creating/repairing a DB. Format1/default callers kept.
Not an fd-pinned SQLite VFS for untrusted shared metadata. Native approved Node
volume/Handler/Agent/FGS/direct LAN still incomplete; full4.2 NOT ACCEPTED.
Next work follows owner MVP priority with targeted tests, preserving existing
TLS/pinning/identity/data guards; fresh integrated final gates remain required.

## h.2b Native Node MVP — limited actual API35 PASS
Source9001f152 +NativeNodeMVPTest: actual private Binder/JSSE/canonical Engine/
Controller-authorized256KiB transfer/hash/fsync/verify/restart PASS30.023s, then
separate force-stopped fresh-process Keystore/Node/TLS/Volume/old SHA download
PASS13.499s,0skip/fail. Original signer/UID/old state retained by normal install-r;
no identity reset. Native43+original storage4 targeted Linux and JVM13/build PASS
as recorded. No new full regression reused as current source acceptance.

This is a real emulator Native Storage Node session, not merely an Engine library.
It is one explicit owner-delegated object; no Global Catalog replicated_2/protection
claim or automatic storage/domain approval. Guest loopback +dev ADB reverse !=LAN.
FGS/background/notification, observer, direct network, phones/ARM64/OEM/Doze and
full Phase4.2 remain NOT ACCEPTED/NOT TESTED. No new public APK; private unchanged
version3 SHA2d843e1be727782105f092396a2620a5ba7c2ef76daa11477c3eb4fd46ee8d60.

## h.3 Foreground Node — actual API35 limited PASS
One actual test PASS58.326s0skip/fail: OS foreground flag +notification, all UI/test
bindings removed, old file downloaded with pinned Controller grant and SHA while
background; actual notification Stop then no notification/foreground AND closed
TLS port. Same canonical actor/Engine/context. Original signer/state kept, normal
install-r. JVM13/build/inventory PASS, no fresh full Python/Go claim for new runtime.
Private APK55bec3d9a9a9590ef6b35d70c37e164eed76ed4b2d56021175e96bc9fb44a4d5,
not public release. FGS connectedDevice for real Node network session; no automatic
restart/boot/identity/approval. No physical phone/ARM64/Doze/OEM/direct LAN/two
replica acceptance; full Phase4.2 NOT ACCEPTED, writableDR blocked.

## h.4 Native Node direct networking — emulator NAT PASS
Targeted Native46 Linux PASS0skip14.632s/JVM13/build PASS; direct TLS/cluster probe
9.935s and cold Binder address setting14.730s PASS. Final-APK actual host upload/
Node commit+verify/download256KiB exact SHA over standard SDK NAT PASS84.213s;
Node heartbeat/authorization direct10.0.2.2, ADB reverse removed, ADB control only.
Same enrolled Node/token/TLS/volume/data retained; no rejoin/permission/dependency/
parallel backend. Setup-timeout failed attempt retained; no fake/partial PASS.

Scope is owned API35 x86_64 emulator NAT, one owner-delegated local object; NOT
physical phone LAN/ARM64/Doze/OEM or two independent protected replicas/fallback.
Core observer/native UI and final integrated gates still pending; full4.2 NOT
ACCEPTED. No fresh full Python/Go claim or new public APK/release.

## i.1 Native Core observer client — scoped Linux PASS
12 targeted tests PASS0skip/fail40.877s: new canonical Python owner-session client
through existing TLS gateway, actual three-voter stale Leader/partition/quorum loss/
Controller death/reconnect, pinned mode/identity/checkpoint/session denial and
full-byte passive recovery integrity. Existing gateway security/mutation-denial
and no-writer projection regressions retained. No Node/Core schema/identity/storage
change, no new backend or source authority. Owner sessions RAM-only, not Node tokens.

Android Binder/UI not yet wired or qualified by i.1; no new APK/full Python/Go
acceptance claimed. Next i.2 adds that actual Android integration. Full4.2 remains
NOT ACCEPTED; writable disaster recovery BLOCKED.

## i.2 Native read-only Core observer — API35 targeted PASS
Actual owner UI ->private Binder transaction4 ->canonical Python observer ->existing
Core gateway over DIRECT private host HTTPS. Real3-voter Core file/3logical domains,
wrong-pin refusal, actual owner login,3/3replica display, real partition/quorum loss/
UNKNOWN Leader+availability, heal/strong read, logout and unchanged existing app/
Node-context payload (decrypted comparison, not ciphertext bytes): **1 Android PASS90.332s**,
driver113.234s. This app is only
an observer of that Core cluster; no Android voter or state migration is implied.

Additional12 actual Android regression PASS136.452s: existing UI/Binder/golden ID/
Core Engine I/O+fsync+SHA/restart/old volume+manifest+bytes, original Native Node
old-file download/identity and real default-network loss/recovery including observer
secret/trust/healthy-view clearing. JVM15 PASS/build PASS, original signer/UIDs/
state preserved via normal install-r. Bounded package audit119modules/7unchanged
permissions/no findings PASS; current private APK d1847ce8e73a7af44ad5b830875e4877143dd0b3c0486489de8613daceb2672a.

Initial harness ACK-file race failed79.910s; fixed only atomic test-control
publication, complete rerun above passed with original assertions/main APK. Logs
and exact failure retained; not counted as PASS. Session RAM-only, no Node/schema/
credential migration or writer capability. Linux12 client gates from i.1 unchanged;
no new full Python/Go claim or public APK/release. Full4.2 remains NOT ACCEPTED
pending integrated j/candidate+upgrade/final gates; physical phones/ARM64/real LAN/
Doze/OEM/two hardware domains unqualified; writable DR BLOCKED.
