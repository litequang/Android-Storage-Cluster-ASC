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
actual upgrade qualification in4.2e. Never uninstall/clear app data or use adb -d to
manufacture compatibility. Unknown schemas refuse; no native schema migrator yet.
Keep NEW state/bytes before code changes. Android signature/version rollback rules
are mandatory; do not restore stale DB or promise extracting Keystore keys into
Termux/OpenSSL. Core4.0/4.1 code rollback remains independently qualified/unchanged.
