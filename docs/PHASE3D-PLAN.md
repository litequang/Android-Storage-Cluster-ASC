# Phase 3D — External Backup & Disaster Recovery contract

Branch: feature/phase3d-external-dr, from fetched/advertised Core WIP
acea2aead8cfd50f8a8fc2b31e24f8f9ccaeb84c. Demo c9c2660 remains separate/unchanged.
Read AGENTS and ordered mandatory documents, then IMPLEMENTATION_PLAN, 3A/3B
acceptance and 3C plan/progress/acceptance before work. No 3A–3C reimplementation.

## Scope / audit decisions

Existing backup.state/service preserve version lifecycle, snapshot pins and durable
logical restore jobs INSIDE the quorum-committed runtime schema2. MetadataSource
omits private jobs/lifecycle and is not enough for recovery. Runtime.ensure_ready
uses actual Go Leader/term + fresh quorum Barrier; raw cached/metadata snapshots
cannot establish authority. Catalog grants audit/read scopes already reach retained
versions via pinned Storage HTTPS; source_stream hashes bounded 64KiB chunks.
GC planner protects current versions/snapshots/trash/jobs/history; external files
will NEVER be used as new GC deletion evidence. No change to those invariants.

Export one exact validated runtime document with captured cluster/epoch/index/term/
SHA, control/Catalog revisions, all version descriptors, all optional 3A/3B/3C state,
node/volume historical IDs, job/pin/history/approval evidence. No live SQLite/WAL,
Raft log rewriting, secret config, raw token, private certificate/key is exported.
Projection has credential HASHES and private names/endpoints: ALL backup metadata
and bytes are sensitive; local adapter requires private operator-owned destination,
never public Git/cloud. Encryption/provider key management is deferred; no custom
crypto. Hashes provide integrity anchored in separately retained manifest SHA, not
Byzantine signatures, authenticity from an untrusted self-hash, or write authority.

Coverage is conservative: EVERY Catalog file/version at capture, including TRASH,
EXPIRED and versions referenced by snapshots/history/jobs. Preserve entire original
projection; copy one exact size/SHA body per global file ID from an approved current
readable replica. No assumptions about two nodes; try all approved candidates.
Unfinished upload with no readable committed replica makes backup INCOMPLETE;
metadata/jobs are preserved but private staging, uncatalogued/native/orphan bodies,
raw identity keys and uncommitted Raft proposals are explicitly OUT OF SCOPE. Pending
COPY/restore are captured as historical work, NEVER resumed by recovery staging.
No silent exclusion of inaccessible protected versions. Missing/corrupt/offline
sources are not deletion evidence. Source mutation after capture is not incorporated;
original immutable descriptors stay bound. Final authority check must succeed before
COMPLETE; retries use current legitimate authority, never captured old credentials.

## Format / transaction / storage safety

Versioned private local external store, separate from all declared source HOME and
volume roots (reject ancestor/descendant overlap, links, unsafe ownership/permissions,
source checkout). Same-host temporary directories simulate separation only, not
independent hardware/disaster protection. Operator must declare remote source
mounts if also visible locally; a Controller cannot discover remote host paths.
Provider interface separates capture/read/revalidate from durable destination IO.
Future USB/NAS/S3/cloud adapters need equivalent conditional publication, identity,
private access and credential/encryption contracts before enablement.

Each UUID bundle binds immutable capture manifest and exact metadata SHA, and
objects/<global-file-UUID>.blob. Work lives in working/<UUID>; complete bundles in
completed/<UUID>. Stream unique partials, file fsync + hash/readback, publish exact
object without overwrite; resume rehashes retained objects, never trusts progress
alone. Final complete receipt binds manifest SHA/coverage after full readback;
directory fsync and controlled publication. Existing COMPLETE never overwritten.
INCOMPLETE = transaction not published/all bytes unproved. CORRUPT = known invalid
manifest/metadata/body. UNKNOWN = inaccessible/untrustworthy IO, never healthy/zero.
VERIFIED is a timestamped observation, not a permanent property or latest-history
claim. Operator must separately retain trusted manifest SHA; unanchored listing is
inventory only. No automatic external deletion/retention executor in Phase3D.

## Recovery authority / hard blocker

A new isolated empty recovery destination may receive exact validated metadata and
bytes plus a durable READ_ONLY marker, with original IDs/history and portable file
mapping. It is NOT a live ASC HOME/volume/registry/Raft config and has no tokens,
private keys, new epoch, quorum, Leader, automatic worker or network entrypoint.
Require trusted expected manifest SHA, expected cluster ID and operator's minimum
known committed index; reject older backup when a newer floor is known. Loss of
latest witness means RPO/newest history cannot be proved. Staging cannot overwrite
active/nonempty roots. Recovery may resume only its exact durable original intent.

**Writer recovery BLOCKED:** no qualified upstream Raft disaster membership recovery,
old-cluster fencing or identity-key restoration/re-enrollment protocol exists in
ASC. Do not implement homemade epoch/quorum/log repair. Phase3D can qualify external
backup/verification/VERIFIED RECOVERY STAGING only; FULL WRITABLE DISASTER RECOVERY
NOT ACCEPTED. Operator-controlled writer recovery needs a separate reviewed task.

## Checkpoints / publication gate

| Step | Required implementation and tests |
|---|---|
|3D.0|Audit/ADR/risk/contract/plan/progress/acceptance; document validation + existing backup units|
|3D.1|Bounded format/local private destination; immutable metadata + streaming bodies; fresh pinned owner/runtime source; resume/idempotency/no overwrite/final authority; actual IO targeted tests|
|3D.2|Anchored metadata/body/coverage verification, missing/corrupt/unknown/stale reports; list/verify CLI; conservative retention dry-run only|
|3D.3|Fresh isolated verified read-only staging; identity/history/byte preservation, interrupted same-intent resume; no executable authority/config/DB restoration|
|3D.4|Actual multi-voter/TLS/sandbox fault matrix; full fresh Python + targeted + Go/vet/modules/applicable builds; security audit; accurate partial-scope acceptance|

Split a/b when useful. After EACH: targeted PASS, relevant contracts/CODEMAP and
progress, tracked/index secrets+whitespace review, normal push ONLY this feature
branch, compare remote HEAD before next. No reset/force/main/Core/Demo mutation.
Record previous commit hashes in next checkpoint (self-hash cannot be embedded).
On interruption read this plan/progress/acceptance and continue exact completed
checkpoint; never reuse old full PASS as validation of new source.

## Risk controls / acceptance limits

- False COMPLETE: immutable manifest-to-projection/bytes bijection and independent
  full readback SHA before publication; no source ACK as substitute.
- Controller/quorum/stale Leader: current strong gate for capture/grants/final check;
  no cached authority or old backup promotion. IO already authorized may finish;
  it cannot grant writer or COMPLETE without final check.
- IO interruption/ENOSPC: retain source and partial transaction, no success; fsync
  journal boundaries; retry same IDs, preserve ambiguous/corrupt bytes for review.
- Path/link/root replacement: descriptor/no-follow, regular single-link files,
  pinned root identities, private trusted OS account. No arbitrary extraction paths.
- Retention: report only, UNKNOWN held, never delete final/last verified backup.
- Lost authority/credentials: IDs historical only, no silent token reuse; writer
  blocker explicit. Stale snapshot cannot replace newer active state.
- Source GC/lifecycle race: frozen coverage may become unavailable => INCOMPLETE;
  no pin release/deletion/source mutation by external engine and no GC credit.
- RPO: captured timestamp/index vs operator's known newer checkpoint, not a schedule
  or zero-loss promise. RTO: measured copy/verify/stage elapsed time only, no hardware
  performance/recovery SLA. Real power cuts, independent disks/NAS, Android, Windows
  execution, encryption/key escrow and writable DR require separate qualification.

## Upgrade / rollback

Additive source-only module/API; no base registry4/manifest1/runtime2/3A–3C schema
migration or enable flag. Stop development processes, keep complete current private
state/witnesses/bytes and matching source before upgrade. Code rollback keeps all
new external stores/staging separately; old code ignores them. Never restore an old
DB over current state, erase backup/retirement fences, edit Raft logs/terms, or
restart old unfenced clusters. No device/system/production operation in this task.

## Final scoped outcome

3D.0/1a/1b/2/3/4a complete/pushed; final fresh238 Python0skip/0fail/all original
physical and9 new fault groups PASS on frozen50df5d7;54 targeted/Go11/vet/modules/
builds PASS. See acceptance/progress for exact counts/times/commands and final
normal publication receipt. External backup/verify/read-only recovery staging is
accepted for Linux synthetic. Phase3D PARTIALLY COMPLETE; full writable disaster
recovery remains blocked by authority/fencing/identity recovery qualification.
No device/Windows runtime/real-media/production claim or safety unlock.
