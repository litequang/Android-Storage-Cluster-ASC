# Phase 3D progress — account-independent continuation

Branch feature/phase3d-external-dr from verified Core acea2aead8cfd50f8a8fc2b31e24f8f9ccaeb84c.
Demo branch c9c2660b5aad9fe347cb0b216f0d691144f74caa unchanged. Initial tree clean;
fetch/advertised refs verified, feature branch absent and created without reset.
Mandatory docs read in order, followed by requested implementation/3A–3C evidence.
Cloud skill/network policy enforced unrestricted; inherited proxy/trust unchanged.
Existing activation /workspace/asc-cloud/activate.sh supplies Python3.13.5/Go1.27.3.

| Checkpoint | State |
|---|---|
|3D.0|PUSH/REMOTE VERIFIED08d36d041f009a9417bc300157d9cb0526130818;20 backup units PASS|
|3D.1a|PUSH/REMOTE VERIFIED86d11056a00fbbb4d52a809a4cbf236a8c21b4f5;35 targeted PASS|
|3D.1b|PUSH/REMOTE VERIFIEDe62d06a0b8ed68538305b6a09007fae0450ddabf;12 targeted PASS|
|3D.2|READY:37 targeted PASS0skip0fail0.467s; anchored verify/inventory/retention/CLI; push gate follows|
|3D.3|NOT STARTED|
|3D.4|NOT STARTED|

Next: publish/remote-verify3D.0 after document/backup unit validation, then implement
format/private adapter/streaming engine and fresh pinned owner source. Each checkpoint
must targeted PASS +docs/CODEMAP +tracked/index secrets audit +normal feature push
+remote equality before next. Read AGENTS/PHASE3D-PLAN/this/ACCEPTANCE to resume.

Contract: full runtime projection +EVERY Catalog version's bytes, independent private
store, trusted out-of-band manifest digest, no source deletion/GC credit, read-only
isolated recovery staging. Missing/uncommitted bytes => INCOMPLETE; no secret keys/
raw tokens exported. Historical jobs never become active recovery authority.
Writer recovery is BLOCKED pending upstream library recovery/old-cluster fencing/
identity credential recovery qualification. Do not claim full writable DR acceptance.
No phones/M51/production/Core/Demo edits, no GC/Raft/membership unlock/new Leader.

3D.0 actual: `python -B -m unittest tests.test_backup.BackupStateTests -v`:20PASS,
0skip/0fail0.252s. Plan/ADR links/fences and git diff --check PASS. No source
changes; source audit only. Normal feature push/remote proof recorded next checkpoint.

## 3D.1a local archive engine

asc/external/format.py validates immutable manifest1 against exact runtime2 bytes,
all Catalog versions and exact captured checkpoint; local.py owns a private POSIX
store with pinned descriptors/no-follow/single-link/ownership checks +exclusive
flock; engine.py streams64KiB, SHA/fsync/readback, per-file atomic no-replace link,
exact partial-link crash recovery, final source revalidation and directory publication.
Resume rehashes every existing object; corrupt published data is retained/refused.
Completed bundle replay never fetches/replaces source bytes. No external CLI/API yet.
Local filesystem requires dir_fd/flock/hardlink/directory-fsync; other providers/
Windows fail closed, no unsafe fallback. Raw metadata is sensitive despite absence
of raw secrets. No source/pin/job/schema/GC/authority mutation introduced.

`python -B -m unittest tests.test_external tests.test_backup.BackupStateTests
 tests.test_failover.RuntimeStateTests -v`: **35PASS0SKIP0FAIL0.402s**.11 new actual
private-filesystem tests: exact versions/stream/SHA/replay, source interruption,
final authority loss, source mismatch/pending unavailable bytes, corrupt retained
object, source/destination overlap, real unsafe permissions/links, root replacement,
snapshot/future format, fsync ENOSPC injection, lock/missing marker and post-link
crash replay. Authority is an explicit UNIT FAKE here; actual Raft/TLS remains1b/4.
Initial test failed because restrictive umask made its intended0755 root0700;
fixture now sets0755 explicitly, proving actual permission rejection. No product
safety relaxation. Next only after normal push/remote equality:3D.1b source/API/TLS.

## 3D.1b actual pinned owner/runtime source

1a normal pushed/remote matched86d1105 before source integration. Added owner-only
runtime POST external/capture/read/check. Capture nested exact strong schema2 view;
read validates immutable version descriptor and same cluster/epoch, obtains only
current approved exact-object audit/read grants, including retained lifecycle
versions. Node/anonymous/wrong pin denied. Final check requires fresh actual Leader/
quorum; old snapshot is never permission. No destination/restore/writer API.
PinnedSource uses existing scoped Storage TLS/source_stream and bounded64KiB SHA;
Engine retries unpublished partials across candidates after offline/corrupt reads,
never overwrites published objects or changes Catalog data/replica evidence.
Current transfer grant bookkeeping is existing quorum-fenced preparation; no new
schema/authority algorithm/membership/GC path. Default single-writer/Demo unchanged.

Actual `python -B -m unittest tests.test_external tests.test_external_cluster -v`:
**12PASS0SKIP0FAIL12.663s**. Actual three Go voters/three Python-TLS cohosts, two
versions/two independent approved simulated domains, retained snapshot+TRASH,
exact manifest-to-runtime SHA, copied old+new bytes, no node/admin raw secret in
metadata, node credential denied owner capture, wrong pin and forged content denied.
Unit authority fakes remain labelled; this separate integration actually uses Go
Barrier/CAS/storage online nonce authorization. Original Linux runtime guard stays
unchanged; existing private synthetic launcher supplies its test-only profile.
Next after normal push/remote match:3D.2 anchored verification/list/retention/CLI.

## 3D.2 verification / retention / operator entrypoint

1b pushed/remote matched e62d06a before2. Added verify.py: trusted manifest SHA,
strict metadata/manifest/complete coverage, all object SHA/readback and byte/count,
point-in-time verified_at, known-index STALE even when integrity passes. Missing/
corrupt content CORRUPT; unsafe/inaccessible/busy/replaced IO UNKNOWN, never0.
Inventory is explicitly COMPLETE_UNVERIFIED without trusted anchor/full hash.
retention_preview returns no candidates/delete implementation, holds every backup
including UNKNOWN/last valid. No GC credit. CLI init/create/resume/list/verify/
retention-preview is local Linux development only, rejects getprop/Android/Termux,
reads bounded private existing owner bootstrap (normal JSON, duplicate keys denied),
uses existing pinned owner discovery, and prints no exception/path/token text.
New PHASE3D-OPERATIONS explains exact commands/coverage/witnesses/upgrade/rollback.

`python -B -m unittest tests.test_external tests.test_external_verify
 tests.test_backup.BackupStateTests -v`: **37PASS0SKIP0FAIL0.467s** incl6 new
verification/CLI cases and11 filesystem +20 old backup units. Tampered manifest
with recomputed self-receipt still rejected against independent trusted digest;
metadata mismatch, missing/corrupt/extra object, real permission denial, unanchored
inventory, newer-history floor, INCOMPLETE and nondeleting last-backup retention.
Initial collected48 included an imported duplicate TestCase; changed import to
module-only helper reuse, final37 are unique. No product/test assertion weakened.
Next after push/remote:3D.3 actual isolated read-only staging/resume/integrity.
