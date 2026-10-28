# Native Node operations — internal debug only

Current candidate builds internal versionCode5 / 0.4.1-native-node-candidate with real
scoped emulator Node/FGS/direct NAT, Catalog replicas and separate Core observation.
See current PHASE4-2-ACCEPTANCE/PROGRESS for exact candidate/hash/test scope. The
Cụm page adds Mở File Manager web: enter the owner's existing Demo Dashboard root
HTTPS LAN URL (for example https://192.168.1.20:8444). This opens an external
browser; trust the independently verified public CA and use a fresh Demo owner
login code. No code/token in URL, no certificate-warning bypass. Gateway Core
login remains separate/read-only. Native file picker, multiuser accounts,
automatic hotspot/Wi-Fi Direct and Cloudflare remain unimplemented.

Shared network-only Dashboard PWA/install guidance: PHASE4-WEB-APP. Final5 has
actual API30 transport/restart/nonreading-peer/retained catalog qualification;
historical API35 APK4 proof does not qualify final5 on35. Final5 now has API35
transport5PASS and boot/PM READY, but integrated cold35Node is BLOCKED at network
preflight/System UI ANR. PHASE4-API35-QUALIFICATION owns the exact scope. Published
artifacts/full software results: PHASE4-STATUS/HANDOFF, not the historical text below.

Direct exact published4/7c4ba649 ->FINAL5/aec65c2c now qualified on API30 x86_64:
17targeted Android executions, normal-r update, original UID/Keystore/IDs/volume/
pin/old bytes, actual retained5 replicas/browser/fallback/Controller loss/process
death and old4 readback after new5 writes. Fixed artifact selection/host guards3
also PASS. Receipt qualification/phase4-direct-published45-final.json. No interim
main5, uninstall/clear/-d, DB restore or cloned Node. This is a tested SDK upgrade
path, not a new APK release or phone acceptance. Keep original private signer in
owner custody. If update fails, stop/preserve state and use a compatible forward
update with higher versionCode/same signer; no forced downgrade or old DB restore.
Private SDK images/host archive preserve this task only, not a phone backup/export.

Fresh published5 FIRST identity now also qualified on independent blank API30:
NetworkReadiness1 +cold/retained NativeCatalog2 PASS, no prior4/interim APK/state
clone. See phase4-fresh-final5-api30.json. Same native Engine/enrollment/TLS/FGS and
existing Controller/File Manager, not another implementation. Normal new install
of exact5 is a separately tested SDK path; owner ARM64/phone acceptance required.

The original foundation artifact/version and unsupported-operation text below
is HISTORICAL, not the current Node capability. Do not replace Termux state or
infer physical-phone/full Phase4.2 acceptance. Candidate upgrade uses the original
private signer and normal install-r; never uninstall/clear/-d or restore an old
database to evade refusal. An older versionCode is refused by Android: keep the
current data and stage a forward-version compatible fix, not a forced downgrade.

Application `org.asc.foundation`, versionCode2 / `0.2.0-foundation`, minSDK26,
targetSDK35. This is an independent native FOUNDATION, not a replacement for a
Termux Controller/Storage Node or a production release. Existing Demo Dashboard
and Core remain unchanged. No native joined Node, replica upload/download, active
Core observer, FGS, notification or background uptime is implemented here.

## Development build

Use JDK17/Gradle8.11.1/SDK35 and the exact checksums in ANDROID-TOOLCHAIN and
android/toolchain-lock.json. Set ASC_ANDROID_BUILD_PYTHON to a qualified Python3.13
executable, ANDROID_HOME/ANDROID_SDK_ROOT and private GRADLE_USER_HOME; keep inherited
network proxy/CA. No system tools or production configuration changes required.

```sh
android/gradlew --no-daemon -p android :app:assembleDebug :app:testDebugUnitTest \
  :app:assembleDebugAndroidTest :app:lintDebug
sha256sum android-artifacts/asc-native-foundation-0.2.0-debug.apk
(cd android-artifacts && sha256sum -c asc-native-foundation-0.2.0-debug.apk.sha256)
```

Public internal APK is debug-signed, contains canonical Python Core plus ARM64 and
x86_64 runtime assets. Only x86_64 API35 emulator runtime was exercised. ARM64
packaging is not a physical-phone PASS. No instrumentation/foreign test APKs,
private signer, SDK/AVD/private state or Controller fixture are published.

## Owned emulator qualification

Create a new API35 AOSP x86_64 AVD in an isolated development directory. With no
KVM use `-accel off -gpu swiftshader_indirect -no-window -no-snapshot`; startup is
slow. Use an explicit private ADB server and task-owned numeric loopback serial,
never phone discovery. Confirm ro.kernel.qemu=1, hardware=ranchu/goldfish and
sys.boot_completed=1. Install main/test APKs using that explicit endpoint only.
The optional untrusted fixture MUST use a distinct private signer; its real test
asserts a different signature/UID and denied signature permission before bind.
Create that test key/password file in a private development folder outside source,
using keytool password-file options (never a password in argv/logs). Set
ASC_ANDROID_UNTRUSTED_STORE and ASC_ANDROID_UNTRUSTED_PASSWORD_FILE to those private
paths, then build :untrusted:assembleDebug and :untrusted:assembleDebugAndroidTest.
No variables means the default debug signer: the distinct-signer gate will correctly
FAIL if it matches the main signer; this is not acceptance evidence.
Install app/build/outputs/apk/debug/app-debug.apk and app/build/outputs/apk/androidTest/
debug/app-debug-androidTest.apk, plus untrusted/build/outputs/apk/debug/untrusted-debug.apk
and untrusted/build/outputs/apk/androidTest/debug/untrusted-debug-androidTest.apk, each
with `$ANDROID_SDK_ROOT/platform-tools/adb -P 5038 -s 127.0.0.1:5555 install -r PATH`
from android/. Never install these synthetic fixtures on phones.

```sh
python tools/qualify_android_emulator.py runtime \
  --adb "$ANDROID_SDK_ROOT/platform-tools/adb" --port 5038 \
  --serial 127.0.0.1:5555 --foreign --output /workspace/private-new-runtime-proof
```

The default NAT transport is intentional: on the new upgrade AVD, direct10.0.2.2
failed with ConnectionRefusedError despite granted INTERNET and real guest network.
It remains NOT PASSED, not silently retried/fallen back. To isolate actual TLS/Core
protocol on this Cloud host, the qualified final foundation run explicitly added
`--host-transport adb-reverse-loopback`: a no-rebind owned-port development mapping,
127.0.0.1 inside the guest, unchanged full certificate pin and Cluster ID. Cleanup
removes only the successfully owned mapping. This is NOT native LAN qualification,
no HTTP/TLS bypass or proxy change; no proxy:8080 error was observed. Native actual
LAN/Node join is still BLOCKED/NOT ACCEPTED. Boot or WiFi-enabled alone never counts
as network ready: the harness connects only this AOSP emulator's virtual AndroidWifi
and the native precondition observes actual default network before any online gate.

Output must be a NEW private directory outside source; contains a synthetic TLS
Controller key/registry and raw test logs. Never commit it. The tool uses actual
Core TLS/registry, stops/restarts the same Controller and checks zero enrollment
mutation. Native tests temporarily disable BOTH WiFi and cellular on the owned
emulator and restore them in finally. Never run these tests against a phone.

Upgrade mode requires a FRESH AVD with no target app, exact trusted baseline and
current APK SHA256, same signer, and current test APK. It seeds actual old-version
Keystore/private draft/volume/committed bytes, upgrades normally, verifies exact
identity/marker/ciphertext/data, force-stops/restarts the app, then requires Android
to refuse a lower-version APK and rechecks retained state. No uninstall, data clear,
adb -d, fabricated migration or stale database restore is used. Only for a harness
failure BEFORE seed, --resume-unseeded may continue the same owned fresh AVD after
matching the installed base APK SHA and proving all three seed namespaces absent;
otherwise it refuses. Test-only UpgradeQualificationRunner delegates ordinary JUnit
without a phase, and executes only fixed seed/verify phases when explicitly passed.

## UI / trust / state

Consent is local app authorization, separate from owner session/Node identity.
Explicit provisioning creates only an application UUID and nonexportable AES key.
Private capability probing has its own synthetic Core actor/volume and cannot be
adopted as an enrolled cluster volume. Device guard denies M51/unknown models;
known test models remain NOT ACCEPTED. Emulator debug allowance is diagnostics
only; no Core guard, Node startup or authority bypass.

Enter a private LAN HTTPS endpoint, full public TLS certificate fingerprint and
expected Cluster ID obtained through a trusted owner channel. Confirm bindings,
then validate over the real existing pinned Core transport. Only public GET/info
is sent. No code/token/credentials leave this check. An encrypted join form remains
DRAFT_NOT_SENT; native enrollment/resume/network identity are BLOCKED. No QR trust,
auto-approval, second Catalog or filesystem/process control is supplied.

UNKNOWN stays UNKNOWN. Process/bind success and free bytes do not prove writable
storage, quorum, approved failure domains, replication or writer authority. The
probe does actual Core read/write/SHA/fsync, scoped own-probe cleanup and reports
point-in-time evidence. Network/background transitions clear visible codes and
invalidate trust; late async UI responses are discarded.

## Safe upgrade / rollback / diagnostics

Native state format1 and Core probe manifest1 are unchanged. The verified baseline
is this branch's PRIVATE checkpoint4.2c versionCode1 build, not a previously released
Termux package or APK. No released APK downgrade/Termux migration is claimed.

Android requires same application ID/signing key and nondecreasing versionCode.
Keep the debug signing key privately with its operator; a different Codex account
normally generates a DIFFERENT key and cannot update this APK in place. Do not put
that key/password in GitHub or solve signature mismatch by uninstalling/clearing.
No production signing/rotation/automatic update service is provided.

To stop, leave the UI; bound foundation Service has no owned Node/FGS and is not
sticky. Do not kill Termux or other processes. A lower-version install is refused.
No general native code rollback artifact/schema migrator or Keystore export/restore
has been qualified. A future rollback requires an explicitly tested same-signer
nondecreasing-version compatibility build preserving current state; do not restore
an old DB over new data. Backup excludes private CE/DE state in both cloud and D2D;
copying folders cannot back up a nonexportable Keystore key. Lost key locks identity,
never regenerates Node/Cluster or adopts Termux state.

Collect only version, public package/signing digest, device policy, generic error
code and aggregate gate counts. Do not share logcat/full app-private folders,
join code/draft, keys, certificates' private material, tokens or registry databases.
See PHASE4-2-ACCEPTANCE for precise evidence and remaining implementation blockers.

Continuation4.2f.1 development source uses versionCode3/0.3.0-native-context, same
private signer; no new public APK until qualified artifact publication. Prior
0.2.0 published APK remains unchanged. Context operations are private Binder/
provider foundation only; native Node/enrollment/TLS/FGS are not delivered by them.
Read ANDROID-NATIVE-CONTEXT and current progress before any continuation.

4.2f.2 source adds native_tls_prepare/typed sealed TLS; read ANDROID-NATIVE-TLS.
API35 x86_64 guest loopback proof is distinct from direct LAN/phones. TLS on26–29
NOT QUALIFIED. Version3 build remains PRIVATE qualification input, not a release
or Native Node. Keep original signer/UID/state; no uninstall/clear/-d. First native
TLS preparation does not start a listener or approve storage; g–j remain separate.

## Native enrollment g.2b
See ANDROID-NATIVE-ENROLLMENT for explicit context/TLS preparation, pin/cluster/
owner trust, join/pending status/resume and replacement-code operations. No Node
start or storage approval yet. Keep original signer/state/keys; never adopt the
Termux directory. Android qualification uses only owned emulator, explicit dev
loopback and real Core; direct LAN and phone/Agent/FGS remain outstanding. Private
retained fixture/proof must not be deleted to rerun seed. No public APK was changed.

## Internal native transport h.2a
No user start command/listener/Foreground Service was added. Native node_start
still refuses. Socket tests are synthetic guest loopback, not file/replica/LAN
acceptance. Source private APK remains version3, original signer; new116 modules
audited. Keep enrolled state and original signer on normal install-r; no public
release. ANDROID-NATIVE-TRANSPORT specifies API/ownership/deadline and next gates.

## Native Node foreground MVP (API35 emulator qualified, not phone release)
After enrollment and explicit private Node-volume approval, start Node while the
Activity is visible. On33+ grant notifications, then press Start again; no Node is
started on permission denial. The real Node session uses connectedDevice FGS,
shows ASC Storage Node notification and Dừng Node action. Activity can close;
notification Stop closes only the app-owned listener/Engine and removes service.
Service is START_NOT_STICKY: process/OS death needs explicit user restart using
existing state, not new identity or boot auto-start. No24/7/OEM/Doze guarantee.

Android requires FOREGROUND_SERVICE, FOREGROUND_SERVICE_CONNECTED_DEVICE and a
connectedDevice prerequisite (normal CHANGE_NETWORK_STATE declaration for actual
network interaction); POST_NOTIFICATIONS enables visible Stop UX. No proxy/CA/
system network setting changes, broad storage, root or new crypto provider. See
https://developer.android.com/develop/background-work/services/fgs/service-types#connected-device
Package inventory command adds --foreground-node; old archives/default audit
remain unchanged. Main artifact remains private version3, not a public release.

## Moving a known Controller address without resetting the app
Stop the Node. On Ghép enter the new HTTPS address, SAME expected PIN/Cluster ID,
verify TLS/cluster and confirm owner trust; press Đổi địa chỉ Controller — giữ Node
ID, then start Node. A changed certificate/cluster needs a separate reviewed
procedure; this operation does not adopt it or grant writer authority.
Preparing TLS again on a valid context reuses identity and displays the selectable
PUBLIC Node certificate SHA-256 PIN for owner approval. No private key is displayed.
Owner still approves storage/volume/physical domain with existing Core tools.

NativeNodeDirectTest/tools/qualify_native_direct.py is Linux/task-owned emulator
qualification ONLY. Requires already installed/enrolled/configured app+test APK,
notification permission, owner receipt and private synthetic fixture JSON with
origin=https://127.0.0.1:PORT, pin, cluster_id, node_id, owner_token. Never commit
the fixture. Example command (paths refer to private task development workspace):

```sh
python tools/qualify_native_direct.py --adb /path/to/sdk/platform-tools/adb \
  --adb-port 5038 --serial emulator-5556 --emulator-owner /private/emulator-owner.json \
  --fixture /private/native-mvp-network-fixture.json --out /private/new-direct-run
```

Driver removes/restores only its Controller reverse mapping, uses loopback-only
standard SDK NAT for host-to-guest TLS and10.0.2.2 for Node-to-Controller. ADB carries
control/receipts, no file bytes. Real SHA verify/download +JUnit completion required;
adb exit0 alone is NOT PASS.180s emulator startup allowance, original transfer/TLS
deadlines unchanged. No installs/resets/key generation or physical device support.
This is emulator NAT, not physical phone LAN or two independent storage domains.
