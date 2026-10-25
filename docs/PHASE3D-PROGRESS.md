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
|3D.1a|Local format/streaming transaction READY:35 targeted PASS0skip0fail0.402s; push gate follows|
|3D.1b|NEXT: actual pinned owner/quorum source and end-to-end TLS fixture|
|3D.2|NOT STARTED|
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
