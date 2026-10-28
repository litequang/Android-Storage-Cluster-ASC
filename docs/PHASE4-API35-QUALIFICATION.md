# API35 qualification supplement — 2026-10-28

This is a TASK-OWNED emulator, never phones/M51/production. The original cold35
sandbox resumed without wipe/restore/identity reset. Seven raw images/config files
were hash-verified in an offline PRIVATE backup first; no key/state was copied
into another running Node. Original private signer and all other AVDs preserved.

Official Google AOSP35/default/x86_64 repository still revision2, ZIP782404023bytes,
SHA1 2d857d170c0d1b827149565da34b3383e5306f7f. Emulator37.2.12, no /dev/kvm,
2048MiB/1vCPU TCG, no concurrent Core full/Gradle/other guest. Same retained
ASC_NATIVE_CATALOG_API35, serial emulator-5560, private ADB5038. Fresh /proc UID,
exe/start/AVD/datadir/port check BEFORE ADB; historical PIDs must never be signaled.

Boot completed and real Package Manager responded twice in138.886s. This is NOT
app/Node acceptance. Published APK5/aec65c2c and original-signer testAPK installed
normally (-r, no -d/uninstall/clear). Initial private harness misread API35 appId
as old userId, failed before JUnit; no PASS claimed. Corrected harness uses standard
`cmd package list packages -U`, checks each fixed diagnostic command exit status.
Normal5->5 install preserves UID; main identity has0records, NOT a retained-Node
upgrade proof. The first4->5 step proves only normal package/appId continuity.

Actual same-signer instrumentation on APK5: NativeListenerRestartTest(2) and
NativeSocketTest(3),5PASS210.286s,0skip. Real rebind/concurrent bind denial, pinned
binary SHA/wrong pin, idle handshake deadline and nonreading-peer WRITE cancellation.
Each test provisions ONLY its own disposable private namespace, leaving the main
identity unprovisioned. No second Storage Engine, fabricated Node, trust/SELinux/
permission bypass or change to operation budgets.

[Receipt](../qualification/phase4-api35-transport5.json). Raw logs/backups/ownership
records private /workspace/work/phase4-api35-resume. No full392/Go rerun because
source/artifacts unchanged; previous proof scopes remain separate.

Replay only after proving task-owned emulator/actualSDK35/original signer:

```sh
adb -P 5038 -s emulator-5560 shell am instrument -w -r   -e class org.asc.foundation.NativeListenerRestartTest,org.asc.foundation.NativeSocketTest   org.asc.foundation.test/org.asc.foundation.UpgradeQualificationRunner
```

Next: existing NativeCatalogTest/host driver for real enrollment/Storage/FGS/
bytes/process death and Controller-loss behavior on SAME userdata. No re-init if
Main identity/pending already exists; retain original context and resume. SDK NAT
and two logical domains on one host are not physical phone LAN/domains. Notification
permission/network changes, if needed, are explicit synthetic test-fixture actions,
not a production configuration or proof Doze/OEM/24x7 works. Full Phase4 remains
NOT ACCEPTED until the required platform/owner-device gates actually pass.

## Cold integrated Node preflight — BLOCKED, not a Node failure

Continuation from8ffd5ef, same original AVD/userdata/APK5/signer. Main application
identity, native context and Catalog proof were explicitly absent before testing;
no Controller fixture, enrollment or Node volume was created by this attempt.

The first private preflight disabled Wi-Fi expecting the old radio0/.15 fixture.
This image had no connected alternative; route lookup failed. Wi-Fi was restored
to its original enabled setting. A graceful SDK shutdown and second hash-verified
offline backup preserved all seven images/config files AFTER the passing transport
run; none was restored. Same AVD then booted with the documented per-emulator
`-feature -WiFiPacketStream` legacy SDK network mode. Boot/Package Manager READY
twice in267.105s. No proxy/CA, host policy, route-table, root or SELinux change.
This fixture change is NOT an application fix or proof of the old failure's cause.

Android Settings reported no connected Wi-Fi. A real scan found the SDK's
`AndroidWifi` AP. A normal connection request obtained DHCP10.0.2.16/24, gateway
10.0.2.2, then Android disconnected locally (reason3) and recorded
`NETWORK_SELECTION_DISABLED_NO_INTERNET_PERMANENT`. Later interfaces/routes showed
no usable IPv4 connection. Public-nonce TCP probes did not establish host/guest
transport; no successful TLS/LAN claim follows. A shell route lookup alone is
not an application-level TLS proof. No ADB reverse/forward was used as a data path.

Opening ordinary Wi-Fi Settings to inspect the user choice for a network without
Internet encountered **System UI isn't responding**. Only the normal Wait button
was selected; no force-close, validation disable or connectivity privilege was
used. A subsequent UI dump did not produce usable XML. Private crash logs also
contain Bluetooth SIGABRT during this boot; this is infrastructure evidence, not
an ASC fault gate or proof of an ASC defect. KVM remains unavailable. A read-only
stack request as the actual app UID was denied (`root is required`); no escalation.

Do not keep reinitializing a Node or replacing its credentials to diagnose this.
Before any future fresh Catalog run on a freshly verified owned emulator, establish
an actual default network using ordinary SDK/Android settings, then run the existing
read-only precondition:

```sh
adb -P 5038 -s emulator-5560 shell am instrument -w -r \
  -e class org.asc.foundation.NetworkReadinessTest \
  org.asc.foundation.test/org.asc.foundation.UpgradeQualificationRunner
```

Require actual `OK (1 test)`, then pinned Controller connectivity; boot_completed,
Wi-Fi enabled, a DHCP receipt or an empty/zero-exit diagnostic are insufficient.
If Android asks to use the approved private network without Internet, inspect the
normal user choice. Do not disable validation, alter proxy/CA or assume PWA can
change connectivity. The hardware-phone no-Internet/LAN test remains owner-only.
Once ready, use existing `tools/qualify_native_catalog.py` on SAME retained data;
fresh initialization only if Main is still NOT_PROVISIONED, otherwise preserve and
resume the original enrollment. No repeat of accepted Core/Native implementation.

## Additional isolated instrumentation — UNKNOWN, no completed suite

Exact same APK5 and testAPK requested NativeTLSTest(5), NativeContextTest(3),
VaultStorageTest(6), EmbeddedEngineTest(1). Host watchdog expired600.104s without
final JUnit. Private TestRunner log shows the first method
`platformDefaultTrustRejectsUntrustedSelfSignedPeer` finished after290.455s; the
next `missingTlsCredentialOrWrappingKeyNeverRegeneratesIdentity` started. There is
no aggregate `OK (15 tests)` or failure/skip total. Requested15 are NOT15PASS,
NOT15FAIL and NOT15SKIP; no extra passing count is claimed. Do not infer a TLS
deadlock/root cause or fix certificate generation based on this incomplete run.
Original per-test assertions/timeouts were unchanged; no repeated attempt.

After watchdog: freshly verified exact emulator and package UID, stopped ONLY the
owned instrumentation app; explicit echo-checked guard confirms Main identity,
native context and Catalog proof still absent. Newly added SDK AP0 forgotten,
original Wi-Fi enabled/no saved networks restored. Requested normal SDK shutdown;
observed Linux waitstatus11/SIGSEGV, so no clean-shutdown/powerloss proof. Seven
final image/config files preserved offline/hash-equal PRIVATE, never restored.
Other AVDs, signer and all public bytes unchanged. **Guest now STOPPED; historical
PIDs must not be used.** Private records under/workspace/work/phase4-api35-resume,
final backup/receipt `closing-preservation.json`. Public sanitized
[blocker receipt](../qualification/phase4-api35-cold-node-blocker.json).

All314 frozen inputs still match full392 source. Prior Go/full/fault proof remains
limited to unchanged code; no new full run. This is a docs-only handoff, NOT a
completed Node checkpoint or Phase4 acceptance. Next adequate/responsive owned
Android environment, actual network readiness, then unfinished Android gates and
Native Catalog E2E. No source reset, new identity, broader privileges, Phase5 or DR
writer activation to get around an infrastructure/qualification blocker.
