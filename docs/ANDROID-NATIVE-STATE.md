# Native application Keystore/storage foundation1

Application identity !=Node/Cluster identity. Explicit app_provision requires own
UID/signature and UI consent. Native application.json format1 contains public app
UUID/key_version1; native alias asc.application.aes.v1.<namespace SHA> holds a
nonexportable256-bit AndroidKeyStore AES key. Standard AES/GCM/NoPadding/random
provider IV/128-bit tag; AAD binds app UUID/version/purpose. Canary verifies the
current key. AtomicFile+fd.sync publishes private state; no custom cipher/key export.
No automatic creation on bind/restart/status. Existing/partial/future schema, lost
key or corrupt canary =>IDENTITY_LOCKED; provision refuses, preserves files and
never creates Node/Cluster IDs. Software emulator key is not hardware/TEE proof.
Actual key deletion/loss tested; biometric/permanent hardware invalidation not yet
exercised (error handling fails closed). Backups disabled; uninstall/data-clear can
lose Keystore+data. Do not promise private-folder restore of nonexportable keys.

join-draft.json is authenticated encrypted app-owned form data, not Core pending
operation/token. It retains one canonical request ID/public bindings/name/code;
same exact draft idempotent, changed draft conflicts without overwrite. Public
summary omits code, says DRAFT_NOT_SENT/network_enrolled=false. Existing enrollment
provider is still unqualified; never silently convert draft to Node identity.
No browser storage/keys, raw secret logs, shared password or Termux key imports.

## Core private capability probe / provider boundary

StorageFoundation delegates PrivateProbeStorage to the SAME embedded Core volume
adapter/Manifest/Engine. Explicit approvePrivateProbe(version,requestId,quota,reserve)
requires app identity+consent. Fixed Context canonical private-probe-v1 only; no IPC
path/provider/Node identity. Synthetic internal actor app-probe-<applicationUUID>
is NOT a network Node ID, never reported as one or usable to enroll/authorize data.
It is an APP_PRIVATE_PROBE_ONLY namespace; cannot adopt it as a live Node volume
without a separate implemented/tested identity/provider migration. No user-file
storage/Catalog/backend is added. Node/Cluster IDs remain UNKNOWN/null.

Native probe-approved.json format1 binds appUUID,volumeUUID,quota/reserve,rootdev/
inode. Core manifest1 +original .asc-volume marker retained, never rewritten to
recover missing data. Root/manifest/marker/schema/config mismatch refuses BEFORE
an Engine constructor can recreate authority. Existing Root/settings repeat only
with exact binding; missing manifest/future format does not reinitialize. Only
NEW canonical Context root is approved; existing swapped namespace fails closed.

Explicit probe uses existing Core quota accounting/measured free reserve before
existing bounded staging write/readback SHA/fsync/identity-bound own-probe cleanup.
No physical user object GC. Core immutable bytes/corruption behavior stays intact.
Readonly volumes reads original manifest mode=ro +LocalVolume identity/real statvfs;
writable/fsync remain null until actual probe, never inferred from free space or
process. Probe report is point-in-time, not physical power-loss durability or
cluster-approved storage. Actual EACCES gives readable/false writable/null fsync;
unmeasured failures UNKNOWN, not0. No user-folder writes/chmod777/root/SD formatting.

UnqualifiedSafStorage implements same capability seam: NOT SUPPORTED, durability/
identity/writability UNKNOWN and approve refuses. No SAF URI->POSIX path mapping,
persisted permissions or false fsync. No external/broad storage permission requested.
SAF revoke/removal/real SD tests remain NOT TESTED pending a real provider.

## Upgrade / rollback limits

Native formats are separate from immutable Core/Demo formats/candidates. Same-key
install-r must preserve app UID/private state/alias/context inode and pending form;
actual4.2e same-signer versionCode1->2 qualification PASS (exact private checkpoint APK, retained key/cipher/marker/committed bytes/process death). Never uninstall/clear app data or use adb -d to
manufacture compatibility. Unknown schemas refuse; no native schema migrator yet.
Keep NEW state/bytes before code changes. Android signature/version rollback rules
are mandatory; do not restore stale DB or promise extracting Keystore keys into
Termux/OpenSSL. Core4.0/4.1 code rollback remains independently qualified/unchanged.

Optional4.2f.1 context format/witness/CAS is specified in ANDROID-NATIVE-CONTEXT.
It uses a NEW dedicated native-runtime-v1(0700)/native-node-v1 parent/home; Android
filesDir0771 is not chmodded or treated as approved private Node state. Existing
app1/draft1/probe1/alias/Core schema unchanged. Network identity slots remain null;
context UUID never stands in for Node/Cluster. Partial/missing state is held.

Current4.2f.2 extends ONLY typed optional TLS slot in context1, specified in
ANDROID-NATIVE-TLS. Existing app/alias/draft/probe/Core IDs and formats remain.
EC software key/cert are encrypted in existing Keystore-wrapped record, never
plaintext disk; old f.1 rejects non-null TLS rather than adopts it. Missing/corrupt
record/witness/key holds, no replacement. Node/pending/storage remain null.

## g.2a typed enrollment (Linux adapter only)
The prior null-only node/pending restriction is superseded ONLY by the strict
components in asc/node/enrollment.py. Both require existing TLS/context/app
identity. Pending stores original Core retry-safe operation privately before POST;
accepted node + pending removal is one CAS. Restart never recreates credentials.
Public node_id/cluster_id appear only after a validated Core receipt; enrollment
is PENDING_RECEIPT or ENROLLED_PENDING_APPROVAL. controller_confirmation explicitly
says HISTORICAL_JOIN_RECEIPT; approval booleans remain null, runtime/writer false.
Revocation is not repaired by repeating join; explicit future repair contract is
required. Changed endpoint/pin/cluster or concurrent request refuses. A replacement
code can change only pending code, keeping the operation/token. Old unsent draft
is separate, never automatically adopted. Missing/corrupt state or publication
failure holds the original operation; there is no reset/delete-state remedy.
No native Binder/Keystore enrollment acceptance yet; g.2b must exercise the actual
Android provider. Old f.2 code rejects populated slots: code-only downgrade after
join is unsupported, preserve NEW state rather than restoring old databases.

## g.2b native provider wiring
NativeNodeContext now invokes the same Core adapter with Android Keystore provider
and trusted Build/RAM profile. Public status additionally returns saved public
controller/pin/expected cluster, allowing operator review without revealing code/
operation/token. Encrypted legacy draft is independent and never sent implicitly.
Native UI requires explicit preparation +fresh pin/cluster verification and owner
trust before first send, clears transient code and can resume the exact sealed
pending without importing form data. Replacement changes only pending code.
App/process restart does not initialize or repair Node identity. Error labels and
actual tests are specified in ANDROID-NATIVE-ENROLLMENT/current acceptance.

## MVP Node volume slot (h.2b source; Android runtime NOT YET TESTED)
Context1.storage now accepts null or a typed format1 PREPARING/READY record. Fixed
node-storage-v1/{engine,data} under the existing native context; never adopts probe
volumes or Termux. Explicit local quota approval persists PREPARING before creating
anything. Interrupted setup remains held, without resetting identity or cleanup.
READY retains Node ID/quota/reserve, root dev/inode, manifest dev/inode, Volume ID
and medium. Reopen uses canonical existing-only Engine and exact marker/identity.
This is local storage consent, NOT Controller storage/failure-domain approval.
Old readers rejecting nonnull storage must refuse the context; no downgrade or
Termux migration is claimed. Preserve app state/Keystore, never restore an old DB
over new bytes. Before configuring the primary test app, retain its old receipt;
legitimate storage/revision mutation changes ciphertext, not app/Node/TLS identity.

### Explicit address change
An enrolled Node's controller URI may change only through the explicit stopped-
session operation with verified SAME PIN/Cluster ID. CAS changes URI/revision,
not Node/token/TLS/storage/Volume identity. No schema or pending migration, no
re-enrollment or authority claim; credentials become live only after heartbeat.

### i.2 observation session has no persistent state
Optional Core gateway owner cookie/CSRF exists only in NativeCoreObserver RAM.
No new files, schema, Keystore alias, Node-context field, token export or identity
adoption. Existing app key is validated without provision. Process/service restart
requires NEW explicit owner login; Node/pending/volume/committed bytes unchanged.
Native observer mode/cluster is separate from the active single-writer Node; an
observation never performs a state/authority migration. See ANDROID-CORE-OBSERVER.
