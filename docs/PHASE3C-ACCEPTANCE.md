# Phase 3C qualification - Windows continuation

Status: **NOT ACCEPTED**. Checkpoint 3C.4c is implemented and published with
Windows Controller/Storage authorization evidence. Final 3C.5 Linux physical
network fault qualification remains incomplete. No production/device readiness.
Date: 2026-10-24 (Asia/Saigon).
Branch: `wip/phase2a-raft-qualification`.
Verified starting checkpoint: `c909e1e70a4ce7a01674b6caaed1b3b4e6574a65` (3C.4b).
Published 3C.4c runtime source: `74bb6a90f2e4e04751b3edb83d60ac00807ab06f`.
Prior full-run source/test commit: `8d45b2637801a64ae5fa67cd3cb5a4c7295010f8`.
Latest 3C.5b proof-race hardening passes targeted checks; publication hash and
fresh complete regression are recorded in the following report.

## Actual checks

All current results are new Codex-run Windows evidence, not reused Cloud/owner
PASS. Existing Python 3.14.7, portable Go 1.27.3 and Git OpenSSL only. Process-local
ASC_GO/PATH changes; no system installation, proxy/TLS bypass, phone or production.

| Command | Result |
|---|---|
| `python -B -m unittest tests.test_gc_authorization -q` | 12 PASS, 9.466s |
| `python -B -m unittest tests.test_gc_authorization tests.test_replication tests.test_gc_sandbox tests.test_storage tests.test_storage_cluster tests.test_distributed tests.test_failover.RuntimeStateTests -v` | 85 OK: 74 PASS / 11 existing Linux-only physical SKIP, 116.410s |
| `python -B -m unittest tests.test_gc_faults -v` | 1 actual three-voter/TLS test PASS, 306.174s |
| `python -B -m unittest discover -s tests -v` | Prior 8d45b26 run: 199 OK, 185 PASS / 14 SKIP, 1010.082s. Latest hardening requires a new full run |
| `go mod verify` | All modules verified |
| `go vet ./...` | PASS |
| `go test -count=1 -v -timeout 240s ./...` | 11 top-level tests PASS; consensus 22.494s, launcher 1.013s |
| Windows AMD64 / Linux AMD64 / Android ARM64 builds | PASS; CGO_ENABLED=0, Linux/Android compile-only |
| Python AST / tracked+staged secret review / whitespace | 90 Python files parse; 133 tracked/new working paths and 20 exact staged blobs reviewed, 0 secret/private artifact findings; whitespace PASS |

Raw local logs stay outside source in TEMP: asc-3c4c-targeted.log,
asc-phase3c-python-full.log (first failed run), asc-phase3c-python-final.log
and asc-phase3c-go-full.log. No raw keys, tokens,
object bodies, runtime caches, bindings or journals are published.

## Executed GC evidence

- Real three-Go/three-Python cohosts use pinned loopback TLS and synthetic volumes.
  Ordinary COPY and independently streamed SHA precede logical source retirement.
  Explicit terminal-job archival plus ordinary 1024-event append/retention makes
  that exact retirement eligible; no history is manually deleted for the test.
- Current Controller issues a committed memory-only raw permit, persisting its
  hash/run/term/expiry/proofs. Hash also binds target generation, approval, domain
  and pinned endpoint. Real node introspection obtains new independent byte proof
  and an exact nonce/intent-bound actual-term committed receipt.
- Wrong volume, method/scope, bearer and superseded permits are refused. Windows
  Storage denies physical GC and keeps the original bytes. After actual Python/
  Go Leader loss, a new Controller denies the old permit; with only one voter,
  introspection cannot establish quorum authority.
- Unit checks additionally cover revoke/protection/reapproval, expiry/takeover,
  missing quorum, policy/term races during proof, lost/mismatched ACK, same-job
  renewal/replay, retained snapshot/backup/trash pins, missing/corrupt last survivor
  and delayed final authority replies. Unit receipts/ACKs are explicit fakes,
  separate from actual Go/TLS evidence.
- Existing Linux sandbox tests retain actual unlink, journal crash/restart,
  reappeared-object, link/root replacement and exact-known-absence checks. They
  are intentionally skipped on Windows, not claimed as freshly executed here.

## Remaining gates before ACCEPTED

No WSL distribution/Linux runtime is installed on this Windows machine. The
product executor intentionally refuses Windows/Android. Do not mock that guard or
install/change a system environment to obtain physical PASS.

Run the published new GC fault test on supported Linux x86 fresh temporary arenas:
its Linux branch attaches an issued Node capability before first data, performs
actual network-authorized unlink, drops a successful TLS ACK and requires same-job
fresh-permit journal replay. That branch is **unrun** in this session. Extend/execute
paused final-callback faults with term/quorum loss before unlink, Node crash/restart
and whole-cluster snapshot/replay of GC state. Prove version/snapshot/backup and last
copy safety at those physical boundaries. Run all full applicable regressions on
that source and publish exact evidence before declaring Phase 3C ACCEPTED.

A prior 3C.4b Cloud local-callback PASS cannot establish new network/quorum fencing.
Windows full regression alone cannot substitute for these physical fault gates.
Static trusted/non-Byzantine Controllers and owner-approved failure domains remain
assumptions. No real-device, SD, SAF, physical power-cut or disaster-backup claim.

## Boundary and rollback

There is no normal GC enable command/config/env or background execution. Ordinary
Service creates no Controller capability; ordinary StorageRuntime has no issued
executor. Only an explicitly confirmed immutable reservation can be executed by
the isolated test harness. Every run rechecks all graph references and independently
hashes survivors outside the target device domain; final Storage authorization
commits a fresh nonce. No stale/cached/follower/legacy permit is accepted.

The 10-second callback round-trip bound and existing 250ms local post-proof budget
fail closed on slow work; they do not make Raft/network/filesystem atomic or recall
an already-authorized syscall. Permanent retirement/reservation and survivor pins
prevent later metadata from relying on the removed object. No schema migration,
Raft algorithm/membership change, Engine rewrite or phone installer is introduced.
Bounds retain the existing 2 MiB projection, 4096 Go receipts and bounded GC maps/
journals; exhaustion fails closed without evicting backup/history authority.

Rollback requires stopping/isolating all development processes and restoring
complete matching private state/configs/keys/Raft witnesses/manifests/journals AND
byte backups with matching source. Old metadata cannot recreate unlinked bytes.
Preserve newer state separately; never clear retirement/reservation/journal fences,
edit terms/schemas or reset a voter. Real devices remain locked.

## Publication and continuation

3C.4b publication-pending wording was corrected using fetched remote evidence.
3C.4c was pushed normally to WIP and independently matched by fetch and ls-remote:
`74bb6a90f2e4e04751b3edb83d60ac00807ab06f`. No main merge or force push.
The original older dirty worktree is preserved. Continuation uses isolated
`.asc-worktrees/phase3c` or a fresh checkout of the verified remote branch.
Final reporting commit will be identified by Git log/final response; it cannot
embed its own hash. First run is failed evidence; the 3C.5a test-only fixture repair requires a fresh full rerun.

## 3C.5a Windows fixture finding and repair

The first full run found an existing metadata subprocess fixture failure, not a
product fencing bypass. Isolated reproduction: 3 consensus tests, 1 FAIL, 28.779s;
no-config subprocess correctly hit the unknown-device guard before the test's
required consensus-configuration error. The fake profile wrapper previously ran
only on Linux. It now runs on every synthetic host with unchanged production
code and unchanged no-fallback/M51/Android assertions.

`python -B -m unittest tests.test_consensus tests.test_nodes.RuntimeSafetyTests tests.test_lifecycle.DeviceSafetyTests -v`:
**11 PASS, 27.498s**. The first full run cannot count as PASS. Fresh full regression
must run after this repair. Go source is unchanged since the successful uncached
Go/vet/module/build checks above; those need not be repeated for a fixture-only fix.

The first full run completed with exactly the known fixture failure above:
**199 tests, 184 PASS / 1 FAIL / 14 SKIP, 1038.894s**. Existing 12/12 Phase 3A,
20/20 Phase 2B, 7/7 Phase 3B and 3/3 Phase 3C replication gates passed, plus the
new Windows GC authorization matrix. This does not turn the overall failed run
into PASS. Skips: 3 existing POSIX installer + 11 Linux physical-executor tests.
The fresh complete rerun on published 8d45b26 is running with source/tests frozen;
only reporting documents may change afterward.

## Reproduction and changed paths

Windows checks use process-local existing tools:

```powershell
$env:ASC_GO = "$env:LOCALAPPDATA/ASC-DevTools/go1.27.3-verified/go/bin/go.exe"
$env:PATH = "C:/Program Files/Git/usr/bin;$env:PATH"
python -B -m unittest tests.test_gc_authorization tests.test_gc_faults -v
python -B -m unittest discover -s tests -v
Push-Location consensus
& $env:ASC_GO mod verify
& $env:ASC_GO vet ./...
& $env:ASC_GO test -count=1 -v -timeout 240s ./...
$env:CGO_ENABLED = '0'
& $env:ASC_GO build -trimpath -buildvcs=false -o "$env:TEMP/asc-phase3c-windows-amd64.exe" ./cmd/asc-raft
# Separate process-local GOOS/GOARCH cross-builds also passed: linux/amd64,
# android/arm64. Their TEMP outputs are compile-only and were never executed.
Pop-Location
```

On a separately available supported Linux x86 development environment with existing
Python/Go/OpenSSL, first run
`python -B -m unittest tests.test_gc_sandbox tests.test_gc_faults -v` on the verified
remote source, then the full applicable suite/Go commands. Preserve the real product
platform/device locks; only the synthetic test launcher issues capabilities.
Additional paused-boundary/crash/replay gates listed above are still required.
Do not operate real volumes or install/run Android agents to satisfy these checks.

| Changed paths | Responsibility |
|---|---|
| asc/replication/execution.py, gc.py, http.py | Exact GC contracts, permit issuance, fresh graph/survivor/quorum authorization, explicit owner execute/completion |
| asc/client.py | Fixed safe GC error-label whitelist for explicit fresh retries; unknown server text remains redacted |
| asc/failover/runtime.py, service.py | Separate GC introspection dispatch and owned authorizer; ordinary context remains absent |
| asc/storage/http.py; replication/sandbox.py, arena.py | Exact-volume issued executor route, final fresh authority, delayed reply bound and closed missing-arena error |
| tests/test_gc_authorization.py, test_gc_faults.py, gc_fixture.py | Unit and actual Go/TLS/isolated-capability harness; Windows physical lock, unrun Linux lost-ACK branch |
| tests/test_consensus.py | Synthetic Windows no-fallback fixture repair, original assertions/guards preserved |
| CODEMAP, ARCHITECTURE, DECISIONS, NODE_PROTOCOL, DATA_MODEL, SECURITY, TROUBLESHOOTING, CHANGELOG | Source routes, authority/wire/hash-only state boundaries, timing/rollback risks and fixture diagnosis |
| PHASE3C-PLAN, PHASE3C-PROGRESS, PHASE3C-ACCEPTANCE | Published checkpoint verification, exact evidence and incomplete Linux qualification handoff |

No Go algorithm/module, original Storage Engine, manifest schema, voter membership,
installer or real-device configuration was changed. Original dirty checkout stays
untouched; all continuation edits are in the isolated worktree/verified WIP commits.

## 3C.5b proof-approval race hardening

Second full run on 8d45b26: **199 tests OK, 185 PASS / 14 SKIP, 1010.082s**.
This qualifies that precise revision only. Additional focused safety review then
reproduced a survivor endpoint/pin change during checksum proof being accepted
under unchanged node/volume/generation IDs. No actual physical deletion occurred;
the probe used the synthetic unit fixture while real-device GC stayed locked.

The new transient proof fingerprint binds every reference/policy/approval/identity,
survivor endpoint and effective protection before/after IO and final CAS. It
canonicalizes only unrelated self-reported telemetry; actual pinned freshness/
readability and streamed SHA still use the unmodified current document. Existing
GC plan/confirmation digests and persistence schemas are unchanged. New tests
require endpoint/new-reference/protection races to deny and telemetry-only updates
to remain non-authoritative.

A first strict whole-profile implementation hit an ordinary heartbeat (actual
Go/TLS test 1 ERROR, 151.186s). The telemetry/protection distinction is now explicit,
not a relaxed reference/authority gate. Latest focused GC/replication/runtime suite:
**41 PASS, 15.278s**. Go/TLS and a new full run on the hardened source are required
before publication/qualification is complete. Prior 199 PASS is not relabeled as
proof for this later source. Linux physical gates remain unrun and block ACCEPTED.

The next Go/TLS attempt correctly refused a stale exact confirmation (1 ERROR,
41.403s). Known GC error labels now remain actionable through the client's fixed
whitelist; arbitrary text remains redacted. The isolated harness explicitly retries
only recognized stale plan/proof/CAS outcomes with fresh confirmation SHA/byte proof/
nonce and the same retirement/job. It does not accept a denied attempt as execution.
Linux lost-ACK proof requires the real successful-drop marker to be consumed and
original bytes absent, even if existing Discovery already recovers the lost ACK.

Latest GC/replication/runtime/foundation/device target: **53 PASS, 16.995s**;
`python -B -m unittest tests.test_gc_authorization tests.test_replication tests.test_failover.RuntimeStateTests tests.test_foundation tests.test_lifecycle.DeviceSafetyTests -q`.
No source from the earlier passing full run is silently substituted as qualification
for this later hardening. The actual TLS rerun and final full result follow below.

3C.5b final targeted actual TLS rerun: **1 PASS, 345.308s**. Together with the
53-test target, this verifies current graph/approval fencing and bounded fresh
retry on real Go/TLS under the Windows physical lock. Final full regression is
still required after this source publication. No new Go source/module change;
prior fresh Go/vet/module/build results remain applicable to the unchanged Go tree.
