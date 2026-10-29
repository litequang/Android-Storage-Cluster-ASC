# Native Core enrollment — g.2b

This is an app-owned client of the existing Core Registry, not a second Registry,
Catalog, Storage Engine or enrollment authority. NativeNodeContext delegates to
asc.node.enrollment.NativeEnrollment using the shared asc.enrollment contract and
existing pinned asc.client transport. Android enrollment is separate from the old
encrypted DRAFT_NOT_SENT form. No draft is silently adopted or transmitted.

## Preconditions and trust

Own UID AND matching signature, existing explicit local consent and original
M51/unknown-device fences apply before vault/Engine access. Explicitly provision
application identity, initialize native context and prepare TLS first. API30+ is
required for qualified anonymous-memory TLS; API26–29 TLS remains NOT QUALIFIED.
Build/device/RAM profile comes from trusted native OS providers, never IPC fields,
global HOME/getpass/Termux/OpenSSL executable or a device override. Scores do not
grant voter/Leader, storage or failure-domain authority.

Owner independently confirms numeric private HTTPS endpoint, full leaf SHA-256 pin
and expected Cluster ID. UI check_controller checks the exact same public binding;
user trust confirmation is additionally required before quick_join. Changing
network/Activity background invalidates UI verification and clears code. No
redirect, public/wildcard endpoint or HTTP fallback. A certificate alone does not
authorize enrollment: Controller requires a valid one-use owner code. Core runtime
must explicitly advertise supported single-writer schema/protocol/retry feature;
no automatic switch to Core quorum, recovery staging or another Controller.

## Private IPC / durable operation

Existing request transaction1/version1 is unchanged. Fixed methods:

| Operation | Permitted fields beyond request ID | Result |
| --- | --- | --- |
| native_context_init | none | Valid existing context or explicit new app-only context |
| native_tls_prepare | none | Existing/provisioned TLS public pin; no key |
| quick_join | endpoint, pin, clusterId, name, code, trustConfirmed=true | Core join, safe receipt or unconfirmed/pending |
| native_context_status | none | Redacted private context status/public bindings |
| resume_join | none | SAME saved operation/token; no endpoint or replacement identity |
| replace_join_code | code, trustConfirmed=true | ONLY pending code changes; original operation/token retained |

No arbitrary path/profile/command/provider/repair/Node-ID argument is accepted.
All mutations are serialized in the service and protected by the existing
context ownership lock + encrypted provider CAS. Initial pinned info check precedes
CSPRNG credential creation. Pending publication precedes POST; accepted node and
pending removal are a single encrypted CAS. A real successful201 ACK can be lost;
resume replays the exact original enrollment_id/token, giving one server Node.
Missing/corrupt record, witness, app key or context never reinitializes identity.
A new code is an explicit owner grant for an existing pending operation, not repair
of revoked accepted credentials. Enrolled retry returns a historical local receipt
without issuing a fresh join or claiming the current token is valid.

Public fields include application/context IDs, controller/pin/expected cluster,
accepted Node/Cluster IDs and pending application request UUID. No code,
enrollment_id/token, certificate private key or arbitrary exception/server text
crosses IPC/log/UI storage. PENDING_RECEIPT is not enrollment success.
ENROLLED_PENDING_APPROVAL means only a validated historical Core join receipt;
controller_confirmation=HISTORICAL_JOIN_RECEIPT, approval=null, runtime_start=false,
writer=false. There is no listener, Agent, FGS or replica claim at this checkpoint.

Failures expose only fixed labels: invalid_or_expired_code, rate_limited,
controller_unverified, cluster_mismatch, unsupported_runtime, binding_mismatch,
resume_required, tls_identity_required, no_pending_enrollment,
enrollment_unconfirmed or native_context_locked. Pin/transport failures are
intentionally grouped as unverified; no raw TLS/HTTP/provider details are reflected.
On unconfirmed result, read pending status before retry. Preserve state/keys.

## Qualification and repeatable harness

Use only a verified task-owned Linux-hosted emulator, original private signer and
retained app data. Build with the pinned existing Gradle/Chaquopy toolchain; audit
APK as version3/0.3.0-native-context before installation. This remains an internal
source checkpoint, not a new public Android release or in-place candidate version.

The explicit tool tools/qualify_native_enrollment.py checks live local emulator
PID/UID/cmdline receipt plus guest qemu/hardware/AVD/boot properties, then compares
installed/main/test signer before normal install-r. It preserves UID/app data,
creates an independent synthetic TLS Core Controller, tests actual private
Keystore/provider/native bindings and existing TLS/Binder/Engine/UI gates. It
requires the separately retained foreign-caller fixture. Provide explicit SDK,
private ADB port/serial/AVD, task-owned emulator-owner JSON, original public signer
SHA and a NEW private output directory OUTSIDE the checkout. See --help for flags.
No tool touches phones, root, proxy/CA, Termux or production.

Networking uses explicitly created ADB reverse-loopback mappings only; it refuses
to overwrite existing mappings and removes only mappings it created. This is NOT
10.0.2.2/direct LAN qualification. Process proof phases join-pending-seed -> actual
force-stop/cold Activity -> join-pending-resume -> force-stop/cold Activity ->
join-receipt-verify retain app/context/TLS IDs and exact operation/token hashes.
All original TLS/upgrade receipts remain independent and are reverified. No
uninstall/clear/downgrade/reset or database restore. The first proof intentionally
refuses an existing proof folder/fixture instead of replacing retained evidence.
For resumption, retain the private Controller/output and proof; do not delete it
just to rerun seed. Fixed verification can run without a live Controller once
receipt is committed, since it explicitly proves historical identity only.

Only public-report.json is suitable for a bounded report after checking contents.
Private fixture/Registry/keys/logs stay outside Git; test-only fixture codes are
passed on stdin into a task-owned private file, never command arguments/APK.
Actual counts and limits belong to PHASE4-2-PROGRESS/ACCEPTANCE, not this contract.

## Compatibility / next work

App1/context1/Keystore alias/probe1/Core schemas and original Node/TLS/volume IDs
remain unchanged. Populated optional pending/node fields are refused by older
f.2 code: no code downgrade after join is supported. Keep NEW state and original
signer; never restore an older DB over new bytes or regenerate identity. No
Termux-to-APK import/migration, re-pair, quorum runtime or writer recovery exists.

h must adapt native TLS sockets to the existing StorageHandler/Engine, implement
explicit owned storage configuration and Agent/foreground lifecycle, actual
Controller-authorized transfers/heartbeat/probe and restart gates. i adds only
verified read-only observer data; j must resolve direct NAT/LAN and run fresh full
Python/Go/Core faults, APK upgrade and package/security qualification. Native
phone/ARM64 runtime, Doze/OEM behavior, physical replicas and full Phase4.2 remain
unaccepted until actually tested. Writable disaster recovery stays BLOCKED.

## g.2c positive UI path
NativeJoinUiQualification executes actual MainActivity View callbacks through
production private Binder and embedded Core to a real pinned TLS Controller.
Fixed ui-join-seed/resume/verify phases run across actual force-stop/cold restarts.
No direct NativeEnrollment call substitutes for the UI send/resume path.
Separate NEW task-owned ASC_JOIN_* AVD keeps the original upgrade AVD/fixtures
intact; source main APK/signer unchanged. tools/qualify_native_join_ui.py checks
live local owner process and guest identity, original signer, fresh app prerequisite
and zero automatic storage approval. --resume-setup is ONLY for an interrupted
pre-enrollment setup: exact private Registry/cluster/cert/pin/code, zero server
Nodes/catalog approvals and NO prior UI phase logs. Actual UI seed additionally
requires vault NOT_PROVISIONED; existing app/Node identity is never reset/adopted.
It cannot re-seed an already-created UI proof or silently replace credentials.

After am start -W, wait for actual platform filesDir created by the asynchronous
private Binder status before writing the synthetic private fixture. No manual
privileged directory, identity creation or guard bypass. Test fixture/code is
passed on stdin only; keep private output, even after setup failure. A failed
post-enrollment phase requires reviewed resume/verification of retained proof,
not clearing the app or rerunning seed.

Scope is programmatic real View event callbacks/Binder/network, NOT physical
touch or phone usability. This TCG emulator had an initial SIGABRT before the
UI gates and an observed Quickstep launcher ANR during the scenario. Actual
three fixed phases later PASS with same userdata after controlled restart;
no wipe/uninstall/clear. Interactive UX is NOT QUALIFIED by those results.
Exact receipt/proof and all limits are in current progress/acceptance.
