# Owner checklist — Native Node internal candidate

Future owner-controlled ZTE/Bphone trial, NOT phone acceptance. Codex has used
only task-owned API30/API35 x86_64 emulators and Linux synthetic services. Never install
on M51/production/unknown devices or replace existing Termux data. Read current
PHASE4-2-ACCEPTANCE, ANDROID-NATIVE-OPERATIONS and ASC-USER-STATUS.

Final candidate5 has targeted actual API30 x86_64 proof. Historical API35 retained
APK4 proof is separate; final5/API35 transport5PASS, boot/PM READY; integrated
fresh35Node remains BLOCKED at network preflight/System UI ANR. Read
PHASE4-STATUS/HANDOFF for final-full/publication status before downloading.

The integrated j tests use the CURRENT branch's packaged Demo Controller, not
an independently qualified APK-candidate -> published Demo0.4.1 Controller path.
Do not infer that cross-version phone combination PASS. Keep existing Controller
state; a supported tested Controller upgrade/candidate is required for a trial.

## Before installation

Use only a candidate actually provided with its SHA-256 and signer report; a build
path is not a published download. The older Foundation APK has fewer functions.
Native Node TLS requires API30+; minSDK26 is a packaging minimum. ARM64/OEM/Doze/
physical LAN remain NOT TESTED. Stop if device guard refuses; never bypass it.

For an existing native app, verify the same original signer and higher versionCode,
stop Node, then use normal Android update. Do not uninstall, clear data or force a
downgrade. Keep private signer/state in operator custody; never upload them with
diagnostics. Termux/APK identities are independent: no key/database/marker copy.
The historical exact direct APK upgrade qualified is retained Native versionCode3
(SHA d1847ce8e73a7af44ad5b830875e4877143dd0b3c0486489de8613daceb2672a) to4.
Published Foundation2 ->4 directly is NOT TESTED; no general upgrade promise.
Final5 retained path tested: original4 ->unpublished5 builds ->final5, same UID/
context/Keystore/old bytes. Direct published4 ->FINAL5 artifact NOT TESTED. Final5
refuses exact APK4 downgrade and still reads original bytes. Never force -d or
restore an old database; owner phone upgrade itself remains a required pilot gate.

## Controlled trial once the candidate is available

1. Keep the existing Controller on its supported QuickStart/runtime. APK is a
   Storage Node, not a Controller. Prepare the same private Wi-Fi or owner-enabled
   hotspot with reachable IP addresses. Internet is not required by the protocol;
   a local IP network is. No automatic hotspot/discovery exists.
2. Open APK and explicitly consent. On a NEW install only, create application
   identity. Reuse existing identity; missing/corrupt key means STOP, never reset.
3. In Ghép enter the owner's Controller HTTPS endpoint, independently verified
   full public SHA-256 leaf pin and expected Cluster ID. Check TLS/cluster, confirm
   owner trust, then Chuẩn bị context và TLS native. Keep the displayed PUBLIC
   Node pin for owner registration. Obtain a fresh one-use code through owner CLI
   and Gửi mã ghép. If interrupted, Tiếp tục pending đã lưu with the same identity.
   ENROLLED does not mean approved storage or failure domain.
4. In Thiết lập explicitly allow only the APK-private Node volume, small quota/
   reserve and this phone's private LAN IP/port9443. The separate probe volume is
   a capability test, not a replica destination. Check actual writable/fsync:
   UNKNOWN/denied is not success. Do not point it at user/Termux data.
   If an existing Termux Node already uses9443, choose another unused port such as
   9444 for APK; do not kill/reconfigure another process to free its port.
5. Owner registers/approves Node endpoint/public pin, measured volume and truthful
   physical domain using existing tools (DEMO-QUICKSTART section4). No metadata/
   voter role. Two volumes on one phone are one domain; app cannot approve itself.
   Termux and APK Nodes on the SAME phone must also share ONE physical domain;
   distinct Node IDs/UIDs do not make them two independent replica destinations.
6. While Activity is visible, Chạy Storage Node. On API33+ grant notification
   permission and press Start again. Verify heartbeat/storage in owner Dashboard
   and foreground notification. Dừng Node stops only APK-owned runtime. OS/process
   death needs explicit restart; no24/7/OEM/Doze guarantee.
7. In Cụm choose Mở File Manager web with owner's Dashboard HTTPS LAN root URL.
   External browser must trust the independently verified public CA. Use a fresh
   separate Demo owner code, never code/token in URL. This is existing web File
   Manager, not native file upload or Core observer write API.
8. With TWO approved phones/physical domains online, upload a disposable file,
   require two VERIFIED replicas, download/compare SHA-256. Stop one Node and
   download via the other. Restart same Node: identical Node/Cluster/Volume/public
   pin and original bytes must remain. Emulator+Linux on one host does not prove
   physical independence. Do not use important data.
9. Disconnect router Internet while preserving Wi-Fi/IP reachability; record real
   results. Emulator NAT does not certify this phone test. No Cloudflare remote.
   Android may ask whether to keep using a network without Internet. Verify the
   correct private AP and use the ordinary user choice; do not disable network
   validation, change proxy/CA or bypass TLS. Wi-Fi enabled/DHCP alone is not proof
   the app has a usable default network; verify actual pinned Controller access.
10. Test notification Stop, foreground/background and Controller loss refusal.
    Never promote another Controller or activate a recovery writer. Optional Core
    observer has its own owner session and remains read-only.

## If anything fails

Stop Node, preserve keys/IDs/markers/state/bytes. Report version, Android/model,
public artifact/signing hashes and sanitized error/gate facts; no code/token/key/
database/full logcat. Android refuses version downgrade: use a forward-version
compatible fix, not old database restore over new data. Termux→APK/SAF/DR migration
is unsupported. Physical ARM64/Chrome Android CA trust/LAN/two phones/OEM/Doze and
upgrade custody require separate owner acceptance before a phone release claim.
