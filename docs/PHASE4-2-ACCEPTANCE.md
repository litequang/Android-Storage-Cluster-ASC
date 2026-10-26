# Phase4.2 native foundation qualification

**Full Phase4.2 NOT ACCEPTED. Independent native FOUNDATION subset qualified on
actual API35 x86_64 emulator; fresh applicable Core regressions PASS below.**
No joined native Node, native Quick Join, FGS or Termux migration is accepted.
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
|Native Core enrollment/resume and node TLS/agent|BLOCKED: explicit native context/credential provider not implemented; CLI HOME/getpass/subprocess/OpenSSL path cannot be bypassed|
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
