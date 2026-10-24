# Phase 3A — Backup, Versioning & Safe Restore acceptance

Status: **ACCEPTED — Windows development only**, v0.9.0. All applicable checks PASS.
Date: 2026-10-24. Base: 5c6f212041e3b54976231a10cfe699cb831655a0.
Branch: wip/phase2a-raft-qualification. Initial working tree clean; fetched origin
and verified HEAD...origin counts 0/0. No reset, local deletion or history rewrite.

## Scope and evidence rules

All results below are Codex-run Windows checks from this task, not reused owner
PASS. No real-phone/M51/production state, Android installer, Dashboard or Phase 3B.
The implementation extends the existing v0.8 runtime, immutable Engine, Catalog,
HashiCorp Raft Go CAS/failover and TLS fixture. No engine/module rewrite or physical
object GC. Backup schema 1 is explicitly enabled inside runtime schema 2.

## Final Codex-run checks

| Check / exact command | Actual result |
|---|---|
| `python -B -m unittest discover -s tests -v` | **122 tests OK: 119 PASS / 3 existing POSIX installer SKIP, 0 FAIL/ERROR, 556.852 seconds** |
| Final Phase 3A matrix within full regression | **12/12 PASS**, including every-source corruption and five failed retries without fabricated proof |
| Existing Phase 2B matrix within full regression | **20/20 PASS**; all prior consensus, Catalog, Storage, TLS/lifecycle checks also ran |
| `python -B -m unittest tests.test_backup.BackupStateTests tests.test_failover.RuntimeStateTests -v` | **24 PASS**, 0.659 seconds; 20 backup unit + 4 existing runtime tests |
| `go mod verify` | **all modules verified** |
| `go vet ./...` | **PASS**, exit 0 |
| `go test -v -timeout 240s ./...` | **11 top-level tests PASS**: 10 consensus (21.413 seconds, plus 12 stable-state subcases), 1 launcher (already passed; cached in full Go run) |
| Windows AMD64 `go build -trimpath -buildvcs=false` | **PASS**, CGO_ENABLED=0, private TEMP artifact |
| Android ARM64 cross-build with same flags | **PASS**, compile only; never executed on Android |
| Python AST and `git diff --check` | **PASS**; no syntax/whitespace failures |

Only the three existing POSIX installer cases skip on Windows. No TLS, storage,
consensus, backup or failover test was skipped or weakened. All full regression
results are fresh Codex execution, not reused owner evidence. Raw full-run log:
`$env:TEMP/asc-phase3a-python-full.log` (local development artifact, excluded from
publication). Source/tests were frozen throughout this final full run; only
reporting documentation changed afterward.

## Boundaries and rollback

Logical snapshots preserve immutable descriptors at an exact committed source
index/term and control/Catalog revisions. VERIFIED means historical streamed SHA
and independent approved-domain proof. Live reachability can subsequently change.
Restores create a new explicit version using durable same-key uploads; old versions
and suspect objects remain. Retention is logical and does not free physical space.
This is in-cluster version/snapshot protection, not a disconnected disaster backup.
Windows separate roots simulate physical domains. No Android, SD, physical power-
cut or production readiness is claimed.

Bounds: 256 file versions, 64 snapshots, 256 backup jobs, 32 schedules, 256 policies,
512 backup request receipts, 2 MiB whole runtime projection, 4096 permanent Go
receipts. Limits reject/defer new work without unsafe eviction. No garbage collector
or automatic quorum rebuild. Static trusted, non-Byzantine Controllers only.

Before enabling, stop/upgrade all development Controllers and retain complete
private state/configs/keys/DB/WAL/Raft state/external witnesses/volumes and matching
source. Old source rejects the extension. Rollback stops/isolates every voter and
restores complete pre-enable private backups plus v0.8 source, retaining newer
state/objects separately. Never edit schemas/terms, remove extension/guards or
reinitialize a lost voter. Restoring old state loses subsequent metadata and may
reactivate old credentials; review trust state before reconnecting.

## Toolchain and intermediate findings

The current Windows machine initially lacked Go at the documented path. Owner
explicitly authorized official portable Go, without system installation/global
PATH changes. Go 1.27.3 windows-amd64.zip from https://go.dev/dl/ was checked against
SHA-256 f26081f438319757f8a1b46d7d0b2c5ec7583d4038e485e0aa725cfde7885fff.
The fully extracted private executable used for final checks is
$env:LOCALAPPDATA/ASC-DevTools/go1.27.3-verified/go/bin/go.exe. OpenSSL uses existing
C:/Program Files/Git/usr/bin through process-local PATH only. Python is 3.14.7.
An early Go attempt before slow PowerShell extraction completed reported missing
standard packages; fresh fully verified extraction fixed tooling without source
or module changes. Pinned modules verify successfully.

A real clean-checkout blocker was found: base commit omitted the documented
consensus/cmd/asc-raft launcher because unanchored asc-raft ignored its source
directory. The new thin launcher delegates to existing ReadConfig/Initialize/
Start/Close, refuses Android execution and malformed invocations. A scoped ignore
rule prevents recurrence. Go library/Storage Engine were not rewritten.

Intermediate real Phase 3A target: 19 tests PASS in 173.976 seconds, including all
11 then-present fault gates. Subsequent targeted 24 tests PASS in 0.659 seconds
(20 backup unit tests + 4 existing runtime tests), adding incomplete-upload
retention and maximum request-ID regressions. The final full run additionally
passed the all-corrupt-sources failure gate; exact results are above.

Go full checks: `go mod verify`, `go vet ./...`, `go test -v -timeout 240s ./...`
PASS. Consensus package: 10 top-level tests, 21.413 seconds including 12 stable-
state subcases; launcher package: 1 top-level test PASS. Go source unchanged since.
Windows AMD64 build PASS and Android ARM64 cross-build PASS (CGO_ENABLED=0,
-trimpath -buildvcs=false, output under private TEMP). Android was never executed.

## Executed Phase 3A fault gates (final full-run matrix)

All 12 gates below PASS in the full-run log. They use actual three Go voters,
three Python Controller/Storage cohosts, pinned loopback TLS, independent temporary
manifests/volume roots and real object bodies. The two generic suppressed-request
messages during injected disconnects are expected transport failures, not a test
skip or a success signal.

| Gate | Result / evidence |
|---|---|
| 01 Explicit enable | Existing runtime gains validated backup extension after quorum commit |
| 02 Committed snapshot | Exact source index/revisions, canonical manifest SHA and served-byte proofs on two approved domains |
| 03 Accidental delete | History retained; head in trash; normal deleted-version download denied |
| 04 Version restore/retry | Old bytes become a new immutable version; same request returns same job |
| 05 Lost ACK + crash | Real target commit succeeds but TLS ACK drops; Controller killed; takeover resumes one job/session/object/version |
| 06 Scheduled backup failover | Captured schedule/job/manifest retained and completed after Python Leader crash/watchdog withdrawal |
| 07 Stale Leader | Returned former Leader cannot commit direct logical delete |
| 08 Quorum loss | Every isolated Controller rejects delete; recoverable bytes survive healing |
| 09 Snapshot/restart | At least one actual Go snapshot succeeds; all Go/Python processes restart with identical retained manifest |
| 10 One corrupt source | Actual object checksum corruption rejected; healthy independent source restores exact bytes; corrupt evidence retained |
| 11 Retention | Snapshot-pinned versions/manifests retained; physical_deletions=0 |
| 12 Every source corrupt | Actual bodies on every retained source damaged; five bounded attempts end FAILED with no proof; all evidence retained |

Unit checks additionally cover lost prepared-commit reply, conflicting request IDs,
maximum ID length, exact snapshot checkpoint, snapshot corruption/future schema,
SQL projection roundtrip, malformed policy, current/last-verified protection,
trash/active restore pins, reserved versions, batch replay, due-schedule deferral,
empty snapshots, proof/domain coverage, stale leases and fail-closed bounds.

## Reproduction (Windows, existing tools only)

```powershell
$ascGo = "$env:LOCALAPPDATA\ASC-DevTools\go1.27.3-verified\go\bin\go.exe"
$env:ASC_GO = $ascGo
$env:PATH = "C:\Program Files\Git\usr\bin;$env:PATH"
python -B -m unittest tests.test_backup.BackupStateTests tests.test_failover.RuntimeStateTests -v
python -B -m unittest tests.test_backup -v
python -B -m unittest discover -s tests -v
Push-Location consensus
& $ascGo mod verify
& $ascGo vet ./...
& $ascGo test -v -timeout 240s ./...
$env:CGO_ENABLED = '0'
& $ascGo build -trimpath -buildvcs=false -o "$env:TEMP\asc-phase3a-windows-amd64.exe" ./cmd/asc-raft
$env:GOOS = 'android'
$env:GOARCH = 'arm64'
& $ascGo build -trimpath -buildvcs=false -o "$env:TEMP\asc-phase3a-android-arm64" ./cmd/asc-raft
Remove-Item Env:GOOS,Env:GOARCH,Env:CGO_ENABLED
Pop-Location
```

These are process-local environment values. Android output is compile-only.
Private test logs/artifacts stay under TEMP; no keys/configs/objects are published.

## Changed source and documentation routing

| Paths | Purpose |
|---|---|
| asc/backup/{state,service,catalog,http,cli,__init__}.py | Bounded schema/manifest/pins, jobs/scheduler/checksums/restore, live namespace and owner API/CLI |
| asc/failover/{state,service}.py | Preserve extension through existing projection/takeover; own worker and current authority |
| asc/catalog/{http,cli}.py | Delegate explicit backup routes/commands with existing authentication and guards |
| asc/__init__.py | v0.9.0 development label |
| consensus/cmd/asc-raft/{main,main_test}.go; .gitignore | Restore missing documented launcher and prevent source-directory ignore regression |
| consensus/fsm_test.go | Actual-term stale backup delete and exact snapshot-byte regression |
| tests/test_backup.py | Semantic unit checks and real Windows fault matrix |
| README.md; README-VI.md | Current owner commands, scope and upgrade guidance |
| docs/CODEMAP.md; ARCHITECTURE.md; DECISIONS.md | Responsibilities, runtime boundaries and ADR-045..047 |
| docs/NODE_PROTOCOL.md; DATA_MODEL.md | Versioned API/persistence, compatibility, bounds and rollback |
| docs/SECURITY.md; TROUBLESHOOTING.md; CHANGELOG.md | Trust/retention risks, resolved packaging failure and behavior history |
| docs/PHASE3A-ACCEPTANCE.md | This exact evidence and limits |

Existing Engine, local manifest, Catalog business SQL, consensus engine/store/
transport modules, all pre-existing test assertions and installer remain intact. No applicable
Python test result is reused; final full run includes every prior test. Go source
has not changed since successful full Go tests/vet/build, so those were not repeated.


Node metadata cache schema 1 retains its existing all-version envelope and is not
current backup/trash authority. Use quorum-gated owner backup routes for lifecycle
state. Previously issued short-lived read grants/streams retain the existing
expiry semantics; trash does not provide secure erasure.

Publication requires a full tracked/staged path and blob-content review, then a
normal push to the authorized WIP branch. The final response supplies the actual
commit hash and independently verified remote ref. No main merge, force push,
production release or deployment is part of this acceptance.


## Final publication review

- Reviewed all **100 tracked paths and contents**, plus all **27 staged paths and
  exact index blobs**. Private artifact paths, private keys, known credential
  formats, credential URLs/JWTs and long credential literals: **0 findings**.
- All **62 Python files parse**, staged whitespace check PASS, and no unstaged
  source changes remain. Vietnamese documentation UTF-8 roundtrip was checked;
  a documentation-only PowerShell pipeline encoding issue was corrected before
  publication. Source/tests were not changed after the full PASS.
- Initial and pre-publication remote refresh retained base history, with no
  reset/discard/force operation. Only the explicit WIP ref is authorized for push.
- No remaining implementation/test blocker. Android/physical power-cut/disaster
  backup and production acceptance remain outside this Windows qualification.
