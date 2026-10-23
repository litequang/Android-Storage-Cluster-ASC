# Phase 1.2B acceptance — v0.6.0

Base: f70b095b8f2ec507baaea5a4bdb3d03667209f94. Codex worked in the existing Windows repository only. All Controller/node/private states, certificates and data bodies are isolated TemporaryDirectory fixtures. No M51, Android/phone, production database/private state, server/installer deployment or system environment installation/change occurred.

## Executed results — 2026-10-23

- Final full Windows suite: **92 tests, OK (skipped=3)**, 106.317 seconds: **89 PASS, 0 FAIL, 0 ERROR**.
- Exactly three original test_installer POSIX Bash cases skipped. No Catalog, distributed storage, TLS/pinning or migration test skipped.
- Final focused Engine + Catalog run after restoring/reviewing the accepted Engine core: 31 tests OK. Catalog/legacy authorization targeted checks also passed before the full run.
- Earlier faults were investigated: disconnect injection now waits for receiver WRITING; legacy compatibility test issues a scoped credential before simulating an old Controller. A local temporary-patch cleanup accidentally removed engine.py; it was restored from the exact accepted base and only the intended inventory/status additions reapplied. The final full run covers the restored code.
- Final missing-schema-4-epoch guard targeted run: 16 Catalog tests OK; an existing schema never silently recreates lost authority.
- Python AST validation and final git diff/secret review are recorded before publication. The project has no separate configured lint/typecheck/build pipeline.
- Existing OpenSSL from C:\Program Files\Git\usr\bin was exposed only in the test process PATH. No installation or system/global PATH modification.
- The previous v0.5 61-test PASS and owner v0.4.1 40-test PASS are historical; neither was reused for this changed source.

The actual final runner was Python -B with this driver:
```python
import os, sys, unittest
os.environ['PATH'] = r'C:\Program Files\Git\usr\bin' + os.pathsep + os.environ['PATH']
sys.dont_write_bytecode = True
r = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover('tests'))
sys.exit(not r.wasSuccessful())
```

Equivalent owner reproduction in PowerShell:
```powershell
Set-Location E:\CODE\ASC-QuickStart
$env:PATH = "C:\Program Files\Git\usr\bin;$env:PATH"
python -B -m unittest tests.test_catalog -v
python -B -m unittest tests.test_distributed -v
python -B -m unittest discover -s tests -v
```
Use the PATH line only when that existing installation is present. Missing OpenSSL is ERROR, never a TLS skip.

## Three-node physical-data and metadata matrix

| Requirement | Evidence |
|---|---|
| Controller and ZTE V40/Bphone A40/Sony XZ3 | Four actual pinned loopback HTTPS endpoints, separate identities/roots/manifests and explicit device-domain approvals |
| Automatic placement and two real file bodies | independent-copy test + owned background-worker test; each final object independently matches source SHA-256 |
| Full Catalog on all three nodes | actual snapshot/delta HTTPS imports/acks; read-only cache contains both replica references |
| Primary endpoint disappears after valid plan | actual endpoint is stopped; first candidate fails, verified second candidate downloads complete bytes |
| Node offline/online metadata catch-up | node runtime stops, policy/history advances, runtime returns and incremental/snapshot sync catches up |
| Controller offline | cached metadata remains queryable with stale/read_only markers and unknown current availability; no global writes/promotion |
| Corrupt or unavailable medium | corrupt physical file is retained/replaced; removed volume is not counted readable and repair uses spare node/domain |
| Controller restart after target commit | injected crash at exact checkpoint, Controller/worker reconstructed with same private DB/pin; same job/session/local ID succeeds, file count does not increase |
| Retry/duplicate/replay | stable upload/job fingerprints, active-job uniqueness, source generation/lease fencing and no duplicate target object on retry |
| Mid-stream connection loss | actual partial transfer after target WRITING, client connection closes, session INTERRUPTED; same ID retries with no partial VERIFIED publication |
| Target offline after commit before confirmation | real target runtime stops after commit; bytes remain, job RETRY, restart/proof records one replica |
| Lost owner ACK | matching local manifest principal/key/session is discovered; Controller still physically reads/hash-verifies before publication |
| Metadata-only node | no fabricated endpoint, receives full catalog, never selected for body storage |
| Fake ACK/unauthorized writes | arbitrary proof field rejected; nonexistent target IDs never yield a replica; normal node tokens cannot mutate Catalog |
| Expiry/revoke/wrong file/scope | expired hashes and generation/revoked identities fail; exact job target restrictions enforced; no-scope job authority denied |
| Quota/protected/unknown metrics | no eligible plan or explicit degraded counts; no fake healthy/zero/replica result |
| Catalog/local manifest disagreement | mismatch detected, suspect bytes retained, no verified replica count from metadata alone |
| Invalid snapshot/delta | gap/order/digest/rollback/wrong-cluster/same-checkpoint conflict rejected atomically; compacted history safely resyncs |
| Legacy migration and rollback failure | schema 3 identity/token/grant + manifest/body preserved; injected DDL failure rolls back version/table; existing 0/2 lifecycle tests remain |
| CLI | real catalog upload/download and local read-only cache commands exercise actual HTTPS/source output |

Tests: tests/test_catalog.py (16 invariants), tests/test_distributed.py (15 distributed cases), plus the full existing 61-test regression suite. Test fixtures are reused without duplicating discovery of old cases.

## What this proves and does not prove

The accepted vertical slice stores a file on at least two independently simulated nodes, verifies source/target SHA-256 from actual served bytes, replicates the catalog and retrieves bytes with a storage endpoint down. The three directories are on one Windows development machine: they simulate failure domains and do not prove physical phone or disaster independence.

Faults are deterministic checkpoints/stream disconnects and scoped temporary data mutations. There was no OS power-cut, actual SD removal, Android Doze, Termux installer or phone test. No Raft, election, automatic Controller failover, peer-direct/resumable transport, Dashboard/mobile/cloud/SAF, object GC or production readiness is claimed.

Controller is still required for file authority. Metadata caches are lookup-only; checksums/ordered logs are integrity evidence, not consensus or storage-byte proof. Standalone v0.5 files/orphans remain preserved and reported, without automatic catalog import.

Default one transfer, 4 MiB/s relay/readback, 300-second RUNNING lease/five failed attempts; reconciliation rotates 16 manifest pages and verifies at most eight replicas/run with bounded diagnostics. History compaction (1024 revisions), Catalog limits (256 immutable versions/16 approved nodes/2048 jobs) and explicit retry are documented. Large-file limits/rates must fit multi-pass verification within the reviewed timeout.

Phase 2 can build on the command/event/cache/queue boundaries and fault fixtures. It still requires deterministic prepared commands, vetted Raft integration, real writer fencing, membership/epoch recovery and partition/quorum acceptance. No Phase 2 code was started.

No source/tests changed after the final 92-test full run. Subsequent changes record documentation and publishing only. Pre-stage review inspected 60 tracked/candidate files: no sensitive runtime paths, matching private-key/GitHub/AWS credential patterns, missing tracked files or UTF-8 corruption found; Python AST and git diff --check passed. Fetched origin/main matched the accepted base. Staged blobs are audited again before commit.

Final staged review: 60 tracked blobs inspected, 37 changed files; no sensitive runtime paths, matching private-key/GitHub/AWS or literal credential patterns detected. All Python ASTs parsed, staged git diff --check passed and no unstaged source remained. GitHub main was fetched without divergence from the accepted base.
