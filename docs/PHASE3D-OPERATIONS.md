# External backup operator guide — Linux synthetic development

Read PHASE3D-PLAN/ACCEPTANCE first. No phone/M51/production, no Dashboard or
network exposure. Product runtime still Windows-development gated; Linux tests use
existing synthetic launcher only, not a new production launch bypass. This CLI is
Linux desktop only and refuses Termux/Android/getprop hosts. It never starts services.

## Preparation / backup

Use matching Phase3D source on every stopped development Controller, preserve
complete current private state/witnesses/volumes and matching source; no schema
migration. Existing configured healthy development cluster must already have
legitimate current Leader/quorum and owner-approved pinned Storage endpoints.
A separate private owner bootstrap JSON (or existing matching cluster-client.json)
contains exactly cluster_id and controllers, with each preapproved Controller
origin/pin and its owner token. Use existing private provisioning; never pass raw
secrets in flags, paste them into logs, or put config/backups in Git/public storage.
Private files must be0600 and parent0700, current operator owned; no automatic chmod
of an existing directory. No config/key generation or credentials restore here.

Example commands on SYNTHETIC data only. Replace paths with existing private
operator-owned source roots and an approved new external directory. Declare ALL
source Controller/Agent HOME and local/mounted volume roots; declare remote source
mounts if locally visible. Adapter rejects lexical/canonical overlap both ways.
Physical independence cannot be proved by paths; same-host folders are simulation.
No arbitrary directory adoption, formatting or permission escalation.

```sh
# Existing toolchain only; source environment activation if already provisioned.
# Run from the verified Phase3D source checkout.
ASC_EXTERNAL=/absolute/private/external-copy
ASC_OWNER_CONFIG=/absolute/private/operator/cluster-client.json
ASC_SOURCE_HOME=/absolute/private/synthetic-cluster
# A backup mount/directory must already have been approved by the operator.
mkdir -m 700 "$ASC_EXTERNAL"
python -B -m asc.external.cli init --store "$ASC_EXTERNAL" --source-root "$ASC_SOURCE_HOME"
python -B -m asc.external.cli create --store "$ASC_EXTERNAL" \
  --source-root "$ASC_SOURCE_HOME" --owner-config "$ASC_OWNER_CONFIG"
```

Repeat --source-root for every additional non-overlapping source/mount root. Create
returns backup_id, manifest_sha256, captured index, COMPLETE and actual bytes/count.
Privately retain ID/SHA/cluster/captured index OUTSIDE this store through a separately
trusted channel. Listing a digest supplied by an untrusted store is not a trust anchor.
Missing pending upload/retained bytes leaves INCOMPLETE, never silent partial coverage.

```sh
python -B -m asc.external.cli list --store "$ASC_EXTERNAL"
python -B -m asc.external.cli resume --store "$ASC_EXTERNAL" \
  --backup-id "$ASC_BACKUP_ID" --source-root "$ASC_SOURCE_HOME" \
  --owner-config "$ASC_OWNER_CONFIG"
python -B -m asc.external.cli verify --store "$ASC_EXTERNAL" \
  --backup-id "$ASC_BACKUP_ID" --expected-sha256 "$ASC_TRUSTED_MANIFEST_SHA" \
  --cluster-id "$ASC_EXPECTED_CLUSTER" --minimum-index "$ASC_MINIMUM_KNOWN_INDEX"
python -B -m asc.external.cli retention-preview --store "$ASC_EXTERNAL"
```

Set the ASC_* witness variables from separately retained trusted values. Minimum
known index is the latest operator-known REQUIRED recovery floor, NOT an index read
from an untrusted manifest. Zero means no newer history witness; it cannot prove
latest history or zero RPO. Verify reports STALE below floor even with valid hashes;
UNKNOWN for inaccessible/untrusted IO; CORRUPT for missing/incorrect required content;
INCOMPLETE for unpublished work. VERIFIED is a point-in-time observation only.
List COMPLETE_UNVERIFIED does not hash/trust all bytes. Retention never deletes.
Create has a new UUID each invocation; after lost reply/interruption LIST and RESUME
the original ID instead of blindly creating more captures. Initialization interrupted
before durable metadata+manifest requires review/new capture, preserve old evidence.

## Recovery staging

Only a NEW isolated empty private root is permitted, separate from external store
and all active state/volumes. Entire anchored backup verified BEFORE destination
mutation, then source/staged full-byte recheck before READY. Existing intent may
resume only the exact backup/anchor/cluster/index-floor; a changed intent fails.

```sh
ASC_RECOVERY=/absolute/private/new-isolated-recovery
mkdir -m 700 "$ASC_RECOVERY"
python -B -m asc.external.cli stage --store "$ASC_EXTERNAL" \
  --backup-id "$ASC_BACKUP_ID" --expected-sha256 "$ASC_TRUSTED_MANIFEST_SHA" \
  --destination "$ASC_RECOVERY" --source-root "$ASC_SOURCE_HOME" \
  --cluster-id "$ASC_EXPECTED_CLUSTER" --minimum-index "$ASC_MINIMUM_KNOWN_INDEX"
python -B -m asc.external.cli stage-verify --destination "$ASC_RECOVERY" \
  --expected-sha256 "$ASC_TRUSTED_MANIFEST_SHA"
```

Success is VERIFIED_RECOVERY_STAGING, writer_authority=false and
credentials_restored=false. RECOVERY_READ_ONLY.json is the immutable intent;
READY.json is a completed integrity receipt. metadata.json is the EXACT captured
runtime projection with original Cluster/Node/Volume/File/version IDs, history,
pins, trust hashes and job evidence; objects/<global-file-ID>.blob are portable
verified bytes. Historical physical locations are not new live manifests. Re-read
metadata privately to map original logical path/version to global file ID; never
interpret a label as an extraction path. All versions have separate global IDs.

No automatic Controller/Storage/worker start, Raft epoch/quorum/Leader, SQLite/log
import, volume marker recreation or old credential resurrection. Do not point any
ASC runtime at this staging root. No full writable disaster recovery claim;
upstream recovery/old-cluster fencing/identity re-enrollment is a separate BLOCKER.
Never use an old backup to overwrite newer state. Lost latest external witness
means freshness/zero data loss cannot be proved even when every byte verifies.

## Upgrade / rollback / scope

Source-only additive module/API; base runtime2/registry4/manifest1 and3A–3C state
unchanged. Stop/upgrade all development Controllers coherently after complete
private backups. Old source ignores new external stores/staging. Code rollback
stops services, preserves NEW current state/bytes/backups and selects matching old
source; NEVER restore a stale DB over newer history or erase retirement fences.
No deletion/retention cleanup command exists. Preserve corrupt/unknown evidence.

Local adapter requires qualified POSIX dir_fd/no-follow/flock/hardlinks and
file/directory fsync. USB/NAS semantics, encryption/key escrow, Windows/Android
runtime, hardware power cuts, real independent media and writable recovery are
unqualified. Authenticated local data archive is not a Raft snapshot or key backup.
