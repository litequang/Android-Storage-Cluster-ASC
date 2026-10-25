# Phase4.2 native foundation qualification

**Full Phase4.2 NOT ACCEPTED. Independent native FOUNDATION subset qualified on
actual API35 x86_64 emulator; final fresh Core regressions pending below.**
No joined native Node, native Quick Join, FGS or Termux migration is accepted.
No real phone/production/M51 access, no Android Raft/GC/failover/writableDR.

## Actual qualification / scope

JDK17.0.21+9, Gradle8.11.1, AGP8.9.2, Kotlin2.2.20, SDK/target35/min26,
buildtools35.0.0, Chaquopy16.1/Python3.13. AOSP35 x86_64 actual boot/install/runtime,
software TCG (-accel off, no /dev/kvm), task-owned private ADB5038/loopback only.
Official source/version/checksum/TOFU limitations: ANDROID-TOOLCHAIN/toolchain-lock.
All native results below use the SAME published main APK, not a Kotlin mock Engine.

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

## Fresh final regression

PENDING at source-freeze checkpoint. Full applicable Python317 discovered unique
cases, uncached Go11/vet/module verification/applicable builds, final security/
package/remote proof must finish before claiming even final foundation regression
qualification. Old Phase4.1 full311 is NOT reused as a fresh4.2 result.

Full Phase4.2 remains NOT ACCEPTED even if independent regressions PASS. Continue
remaining native Core provider/enrollment/lifecycle/observer work before native Node
acceptance; no Phase4.3/production readiness claim. See ANDROID-NATIVE-IPC/STATE/
OPERATIONS/PILOT and PHASE4-2-PROGRESS for reproducible boundaries and safe handoff.
