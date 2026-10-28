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
