# Explicit native context — 4.2f.1

Additive provider foundation, **not a joined/runnable Native Node**. Continue f–j
from verified445bd31, keeping original branches and old packages unchanged.

`asc.node.context.NodeContext(private_parent, provider, app_id, build)` receives
trusted canonical Android Context/Build information explicitly. It never reads or
changes HOME/ASC_HOME, asks getpass, launches a subprocess/OpenSSL or initializes a
Registry/Controller. Only fixed `native-runtime-v1`(0700)/`native-node-v1` below app filesDir is used.
The existing Android filesDir0771 is never chmodded; initialization creates only
the new dedicated private parent. Core receives that fixed parent explicitly.
Binder cannot choose paths/providers/Build fields. Existing CLI guards/contracts
remain intact; subsequent enrollment/Agent integration must reuse Core selectively.

CredentialProvider.load returns exact authenticated plaintext, or None ONLY if
never created. Key loss/corruption throws. compare_exchange compares the COMPLETE
prior plaintext before atomic encrypted publication. Android delegates to the
existing ApplicationVault AES-GCM/Keystore with a fixed purpose and required-record
witness, detecting missing ciphertext. No generic record read/write in Binder.
Same app UID/signature, explicit consent, existing app UUID/canary and native fence
are required. No app key or identity is created by constructor/status/restart.

Core independently validates native Build: M51 in any identifying field dominates;
unknown/unrecognized phones refuse. DEBUG AOSP SDK product +ranchu/goldfish +SDK/
generic fingerprint is a separate SYNTHETIC scope; the actual AOSP image reports
manufacturer=unknown, which does not authorize unknown physical phones. No generic
override or environment flag exists. Neither native fence nor synthetic context
grants Node/GC/Raft authority. Model/OS spoofing by the trusted OS remains outside
this boundary. Hardware binding excludes upgradable OS SDK/fingerprint versions.

Context format1 has exactly format/app_id/context_id/revision/binding/device_binding/
pending/node/tls/storage. Binding records original root+parent dev/inode and path.
Public context.json binds app/context IDs/mode. **context_id is not Node/Cluster ID**.
f.1 requires pending/node/tls/storage all null; arbitrary/future records refuse.
Actual TLS/certificate/config/enrollment providers are subsequent checkpoints.

First initialization is explicit and exclusive: new0700 directory,0600 receipt,
descriptor-relative no-follow creation, file/directory fsync, sealed provider CAS.
It never opens filesystem `/`. Root/ancestor/owner/link/receipt identities are
rechecked around reads. Namespace changes cannot redirect receipt writes outside
the pinned approved directory. Operation ownership uses existing hardened Core OS
lock, no PID guesses. Missing/corrupt key/record/witness/root/receipt or partial
publication is held for operator review, never recreated. This trusts owning app
UID/OS; atomic disk+Keystore or physical power-loss recovery is not promised.

Plaintext legacy node/controller/pending/storage/Registry/runtime files and passive
RECOVERY_READ_ONLY/READY roots/ancestors cannot be adopted. Probe volumes and Termux
state stay separate. No listener/FGS/enrollment/storage approval/writer is created.

IPC1 adds native_context_init/native_context_status with no extra fields. They
return sanitized CONTEXT_READY/null Node+Cluster IDs/unconfigured TLS/enrollment/
storage/runtime_start_supported=false. Status refuses missing context. Existing
app1/alias1/draft1/probe1/Core schemas and explicit AIDL IDs remain unchanged.
Old APK lacks these operations. VersionCode3 is an internal development candidate;
normal Android downgrade/signature refusal still applies. Rollback needs a tested
same-signer nondecreasing-version compatibility build, never uninstall/data-clear
or stale database restore. See PROGRESS/ACCEPTANCE for actual gates and remaining f–j.
