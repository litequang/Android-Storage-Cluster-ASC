# Future ZTE/Bphone native pilot checklist

NOT physical-device acceptance. Codex has not accessed any phone. Never install on
Samsung M51/production or unknown devices; do not change Termux/Boot/system state.
This foundation does NOT replace ASC Demo 0.4.1 or enroll a working native Node.
Leave existing Termux Controller, identities, volume and data untouched.

Owner-only future controlled trial on a separate ZTE9045/V40 or BphoneA40:

1. Read PHASE4-2-ACCEPTANCE and ANDROID-NATIVE-OPERATIONS. Verify the published APK
   SHA256 and public signing digest before installation. Do not uninstall an older
   native app to bypass signature/version failure. Preserve the private signer.
2. Install only the internal debug artifact in a disposable test context. SDK26 is
   the build minimum; only API35 x86_64 emulator runtime is qualified. Android11
   ARM64 runtime, OEM Keystore, background policies and actual storage remain untested.
3. Open ASC Foundation, review FOUNDATION/device policy/UNKNOWN values, explicitly
   consent. Provision independent application identity only. This does not create
   Node ID/Cluster ID or import Termux state. Missing/lost key must lock, not reset.
4. Approve only its app-private capability probe with conservative quota/reserve.
   Verify actual SHA readback/fsync report and unchanged Volume ID after reopening.
   Do not point it at existing ASC volumes or user files; no SAF/SD/USB support.
5. Obtain the Demo Controller's LAN HTTPS endpoint, full public certificate pin and
   expected Cluster ID through a trusted owner channel. Confirm/check the public
   binding. Wrong pin/cluster and offline Controller must fail. No credentials are
   sent; encrypted join form remains NOT SENT and cannot complete native enrollment.
6. Reopen/background/restart app, verify application identity and private probe
   remain stable. Network changes must invalidate trust/clear displayed code.
   Cluster/replica/quorum remain UNKNOWN without an authenticated observer provider.
7. Stop trial without deleting data/keys or touching Termux. Report only sanitized
   version/device-policy/error/gate facts, never code/token/private state/logcat.

Actual native enrollment, Node TLS/agent lifecycle, controlled foreground service/
notification/stop and real file replication require further implementation and
emulator acceptance BEFORE phone Node trials. Hardware-key invalidation, permission
revocation on a real provider, Doze/network transitions/OEM process death, upgrade
signer custody and ARM64 tests are separate gates. No Termux→APK migration, APK
rollback restoration, writable disaster recovery or production readiness is promised.
