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
|3D.2|PUSH/REMOTE VERIFIED554c992f9f234c2f1dd44efa2c1e70f70cd19e8e;37 targeted PASS|
|3D.3|PUSH/REMOTE VERIFIED531d91ec7805c14297fa8a70679daaa9330c134e;23 targeted PASS|
|3D.4a|READY:54 targeted PASS0skip0fail66.001s; all9 actual network/process fault groups; source freeze/push gate follows|
|3D.4b|NEXT after4a remote proof: fresh full238 Python; acceptance/report only after completion|

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

## 3D.3 passive disaster recovery staging

2 pushed/remote matched554c992 before3. Added external/recovery.py plus stage/
stage-verify CLI. Require separately trusted manifest SHA, expected cluster and
operator minimum-known-index plus separate explicitly private empty recovery root.
Full backup verified before any destination mutation; no nonempty active root
adoption (even an extra lock is not written on refusal). Durable READ_ONLY intent,
exact metadata/manifest and streamed/fsynced portable objects preserve historical
IDs/version/pins/jobs/hashes; full readback/source reverify before READY. Retry
requires exact original intent/floor, rehashes retained objects and never rewrites
completed data. Shared-lock stage-verify is read-only. No live config/DB/Raft log/
volume marker/credential/key restoration/worker/server; writer_authority=false.
Missing identity/authority metadata, changed intent, stale/newer floor, corrupt
source/stage, symlink or source/store overlap fails. Stage is NOT a writable cluster.

`python -B -m unittest tests.test_external tests.test_external_verify
 tests.test_external_recovery -v`: **23PASS0SKIP0FAIL0.460s** incl6 new actual IO
stage/resume/identity/CLI cases. Interrupted after first object retains its inode,
retries finish two exact bodies, foreign intent/nonempty active state remains
unchanged; modified staged authority cannot verify. Full/new actual network fault
matrix and fresh full regression still pending3D.4; no full DR/Android claim.
Next after normal push/remote equality:3D.4 faults/final safety/Go/full regression.

## 3D.4a fault qualification / frozen source handoff

3D.3 normal push/remote matched531d91e before4. Added actual3-voter/TLS fault
matrix (9 groups), exact baseline source compatibility check, actual recovery
process exit91/resume and strict native JSON/Backup ID guards. Destination Protocol
and LocalDirectory adapter now own logical CLI provider boundary; other providers
must independently qualify equivalent private immutable conditional publication,
resume/readback, anchoring and no-delete contracts (not pretend POSIX descriptors).
Local directory inventory streams/caps4096 names; completed-ID mismatch and bool/
float JSON aliases cannot pass exact canonical checks. CLI fixed error whitelist
and generic argparse errors never echo private paths/unrecognized secret arguments.
Private recovery marker ignore rules supplement full tracked/index content audit.

Final frozen target command: `python -B -m unittest tests.test_external
 tests.test_external_verify tests.test_external_recovery tests.test_external_compatibility
 tests.test_external_cluster tests.test_external_faults tests.test_backup.BackupStateTests
 tests.test_failover.RuntimeStateTests -v`: **54PASS0SKIP0FAIL66.001s**.
All9 actual network/process groups PASS. This includes30 unique new3D tests plus
20 existing backup units/4 runtime units; full discovery expects238 (208 unchanged
Core +30 new).16 new Python files AST PASS; all original assertions/tests retained.
Earlier unique target28PASS106.535s and53PASS125.361s preceded final stricter
completion/ID/native checks; only final54 is frozen target evidence.

Fault groups:1 exact runtime/all3A–3C extensions, retained versions/snapshot/TRASH;
2 real source upload during backup => exact earlier point/newer known floor STALE;
3 actual all-voter partition before final callback denies COMPLETE then same-ID
resume after heal;4 actual Controller+voter crash/new higher term resume/isolated
former Leader denies capture/check/actual upload (no ghost file after healing);
5 actual backup child exit91 after durable object and normal CLI resume retains
inode/one object perID;6 explicit ENOSPC at actual streamed .part fsync (injected,
NOT a measured physically full disk), incomplete then same-ID resume;7 real offline
cohost/corrupt source with third healthy SHA fallback, corrupt/last/pinned bytes
retained;8 actual pending upload with no bodies => INCOMPLETE;9 total live authority
loss => exact offline read-only staging, no writer/credentials, historical complete
replay only. Separate actual recovery-process exit91 +normal CLI same-intent resume
also PASS, beyond exception-only unit interruption. No product fault/GC flags.

First matrix FAILED1test108.635s: after quorum healing a source was still
unreadable before intended Controller crash, so no actual crash occurred. Fixture
now waits for original measured replica readiness, bounds safe same-ID retry of
early rejected attempts, and REQUIRES actual crash-hook execution +both child
process handles gone +higher actual term. No early denial is counted as crash.
Restart control partition is applied only after the stopped test sidecar restarts.
Corrected9-gate matrix1PASS48.793s, final54 PASS above. No test/guard/budget weakened.

Fresh uncached Go11PASS, vet/modules andLinuxAMD64 build PASS; WindowsAMD64/
AndroidARM64 cross-build PASS only (not runtime). Logs/results private under
/workspace/work/phase3d/go-*; source/module tree unchanged from Core baseline.
Exact old Core acea2ae source archive actually validates/SQL-memory round-trips new
captured/staged schema without migration; no live old writer/DB restore is tested
or claimed. Base registry4/manifest1/runtime2/3A–3C formats unchanged. Code rollback
retains NEW state/bytes/external stores, old source ignores passive archives.

NEXT only after source checkpoint normal push/remote match: activate existing
/workspace/asc-cloud/activate.sh; run /workspace/work/phase3d/run-full.py or fresh
`python -B -m unittest discover -s tests -v` on frozen source. Full must finish with
238 uniquePASS0skip0fail/all original physical gates before scoped acceptance.
If interrupted, rerun incomplete full (do NOT reuse old3C/Demo full results).
No source/test changes during full; reporting docs only afterward. Writer recovery
still BLOCKED, Android/Windows runtime/independent media/power-cut NOT TESTED.
