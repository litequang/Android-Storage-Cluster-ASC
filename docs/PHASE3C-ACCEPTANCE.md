# Phase 3C qualification - Windows continuation

Status: **NOT ACCEPTED**. Checkpoint 3C.4c is implemented and published with
Windows Controller/Storage authorization evidence. Final 3C.5 Linux physical
network fault qualification remains incomplete. No production/device readiness.
Date: 2026-10-24 (Asia/Saigon).
Branch: `wip/phase2a-raft-qualification`.
Verified starting checkpoint: `c909e1e70a4ce7a01674b6caaed1b3b4e6574a65` (3C.4b).
Published source under test: `74bb6a90f2e4e04751b3edb83d60ac00807ab06f` (3C.4c).

## Actual checks

All current results are new Codex-run Windows evidence, not reused Cloud/owner
PASS. Existing Python 3.14.7, portable Go 1.27.3 and Git OpenSSL only. Process-local
ASC_GO/PATH changes; no system installation, proxy/TLS bypass, phone or production.

| Command | Result |
|---|---|
| `python -B -m unittest tests.test_gc_authorization -q` | 12 PASS, 9.466s |
| `python -B -m unittest tests.test_gc_authorization tests.test_replication tests.test_gc_sandbox tests.test_storage tests.test_storage_cluster tests.test_distributed tests.test_failover.RuntimeStateTests -v` | 85 OK: 74 PASS / 11 existing Linux-only physical SKIP, 116.410s |
| `python -B -m unittest tests.test_gc_faults -v` | 1 actual three-voter/TLS test PASS, 306.174s |
| `python -B -m unittest discover -s tests -v` | First run has a reproduced Windows fixture failure; fresh rerun required after 3C.5a |
| `go mod verify` | All modules verified |
| `go vet ./...` | PASS |
| `go test -count=1 -v -timeout 240s ./...` | 11 top-level tests PASS; consensus 22.494s, launcher 1.013s |
| Windows AMD64 / Android ARM64 builds | PASS; CGO_ENABLED=0, Android compile-only |
| Python AST / tracked+staged secret review / whitespace | 90 Python files parse; 133 tracked/new working paths and 20 exact staged blobs reviewed, 0 secret/private artifact findings; whitespace PASS |

Raw local logs stay outside source in TEMP: asc-3c4c-targeted.log,
asc-phase3c-python-full.log and asc-phase3c-go-full.log. No raw keys, tokens,
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
