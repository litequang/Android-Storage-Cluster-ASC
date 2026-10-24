# Phase 3C qualification - Linux continuation and retained Windows evidence


## Current Linux qualification (3C.5d targeted PASS; full regression pending; NOT ACCEPTED)

Start: owner-verified `8d5cd7d75ef0113e417b86940c0ad5d2ea2ccaa1`, fetched and
fast-forwarded on the same WIP branch with previous local handoff drafts preserved.
This session uses existing Python 3.13.5 / Go 1.27.3 Linux amd64 toolchain and fresh
synthetic temporary volumes only. No phone, production, normal-runtime GC enable,
proxy bypass or platform/freshness guard change.

New exact-byte structural-validation checks: 45 PASS / 10.566s. Linux sandbox,
authorization and actual Go/TLS GC suite: **28 PASS / 189.338s**, including real
unlink followed by a lost successful TLS ACK and idempotent same-job replay. This
is fresh Linux evidence, distinct from the Windows report below.

Expanded physical matrix first completed attempt: 2 tests / 1 PASS / 1 FAIL /
563.336s. Actual missing/corrupt last survivor, new snapshot/backup pin during final
pause, immutable versions/trash and snapshot/replay/restore case PASS. The second
case passed real quorum/term/delayed-reply gates, then FAILED because an attempt
was denied before the crash hook; Node crash was not observed. The corrected
harness must obtain fresh proof and still prove actual exit 91/journal/byte state.
The corrected boundary-only rerun is **1 PASS / 503.590s**, proving gates 01-05
including actual Node/cohost exits 91 before/after unlink, durable journal recovery
and real Go snapshot/all-process replay. Final reference-only target is **1 PASS / 313.247s**, gates 06-08.
Interrupted earlier diagnostics/competing runs contribute no
acceptance result. Complete fresh final Python/Go/build regression has not started.

Pure structural Catalog validation reuse keys two exact immutable canonical JSON
byte strings, validates native types and caches only success. It retains all
mutation/history/materialization rejection, runtime/extension validation and fresh
quorum/term/nonce/streamed-byte checks. No authorization, mutable document or
physical proof is cached. Destructive budgets remain 10s callback / 250ms local.

See PHASE3C-PROGRESS for exact targeted commands and current continuation. A future
reporting checkpoint must replace this partial status only after fresh full PASS.

### Linux targeted fault evidence (actual execution)

| Gate | Evidence |
|---|---|
| Network-authorized unlink/lost successful TLS ACK | 28-test sandbox/auth/real Go-TLS command PASS, 189.338s; original body absent only after actual successful execution/drop marker, same-job replay DONE |
| 01 Quorum lost before final callback | Actual all-voter partition, strong-read failure and actual Storage rejection, body retained, journal DELETING |
| 02 Term lost while paused | Majority elects/activates a higher actual term; old run is rejected before unlink |
| 03 Paused successful final reply | Actual committed nonce/term/index recorded, real >10s pause, gc_authority_budget_expired and unchanged body |
| 04 Node/cohost crash/journal restart | Actual exits 91 before/after unlink, consumed fault markers, durable DELETING across restart, same job DONE; replay reports unlinked_now=false and zero incremental bytes |
| 05 Whole-cluster GC replay | Successful actual Go snapshot; restart all Go/Python cohosts, exact DONE/plan/retirement/archive/receipt retention, journal DONE, upload replay cannot recreate target, survivor download exact |
| 06 Last readable copy | Physically missing/corrupt sole survivor denies actual network GC; retired target retained; real reconciliation/verification after synthetic-byte restoration |
| 07 All retained references | New real snapshot/backup pin during final pause denies unlink; versions, backup job and trash remain held |
| 08 Backup/version replay | Actual Go snapshot/all-process restart retains manifest/pins; old TRASH version restores via retained snapshot into new version with exact served bytes |

Gates 01-05: boundary-only target **1 PASS / 503.590s**. Gates 06-08:
reference-only target **1 PASS / 313.247s**. Commands are preserved in PROGRESS;
raw logs: linux-boundary-crash-retest.log and linux-reference-final-targeted.log.
These are separate successful commands; the earlier two-test failed attempt remains
recorded above. Every denial requires actual Storage response evidence; a client
timeout is insufficient. Every crash requires process exit 91 and the expected
journal/byte state. No fake callback, clock or success is used in these gates.

Structural validation and existing GC/replication/runtime target:
`python -B -m unittest tests.test_runtime_validation tests.test_gc_authorization tests.test_replication tests.test_failover.RuntimeStateTests -v`:
**45 PASS / 10.566s**. Tracked/index review: **136 paths, 0 findings**; all
**92 Python files parse** using Python-compatible UTF-8 BOM decoding; phase links
and whitespace PASS. Checkpoint publication precedes the final full run. No Phase
3C acceptance claim yet; full Python/Go/vet/module/build checks remain outstanding.

## Retained Windows evidence at 8d5cd7d (historical)

Status: **NOT ACCEPTED**. Checkpoint 3C.4c is implemented and published with
Windows Controller/Storage authorization evidence. Final 3C.5 Linux physical
network fault qualification remains incomplete. No production/device readiness.
Date: 2026-10-24 (Asia/Saigon).
Branch: `wip/phase2a-raft-qualification`.
Verified starting checkpoint: `c909e1e70a4ce7a01674b6caaed1b3b4e6574a65` (3C.4b).
Published 3C.4c runtime source: `74bb6a90f2e4e04751b3edb83d60ac00807ab06f`.
Prior full-run source/test commit: `8d45b2637801a64ae5fa67cd3cb5a4c7295010f8`.
Final hardened source/test commit: `895e5bb26bf79ac36bbf85e22d82babfaac84b55`
(3C.5b). Targeted and full Windows checks PASS on that published hash. Linux physical
qualification remains incomplete; Phase 3C is NOT ACCEPTED.

## Actual checks

All current results are new Codex-run Windows evidence, not reused Cloud/owner
PASS. Existing Python 3.14.7, portable Go 1.27.3 and Git OpenSSL only. Process-local
ASC_GO/PATH changes; no system installation, proxy/TLS bypass, phone or production.

| Command / final source | Actual result |
|---|---|
| `python -B -m unittest tests.test_gc_authorization tests.test_replication tests.test_failover.RuntimeStateTests tests.test_foundation tests.test_lifecycle.DeviceSafetyTests -q` | **53 PASS, 16.995s**; hardened source |
| `python -B -m unittest tests.test_gc_faults -v` | **1 actual three-voter/TLS test PASS, 345.308s**; hardened source |
| `python -B -m unittest discover -s tests -v` on **895e5bb** | **203 OK: 189 PASS / 14 platform SKIP, 0 FAIL/ERROR, 1008.998s** |
| `go mod verify` | All modules verified |
| `go vet ./...` | PASS |
| `go test -count=1 -v -timeout 240s ./...` | **11 top-level tests PASS**; consensus 22.494s, launcher 1.013s |
| Windows AMD64 / Linux AMD64 / Android ARM64 builds | PASS; CGO_ENABLED=0, Linux/Android compile-only |
| Python AST / tracked+staged secret review / whitespace | 90 Python files parse; 134 tracked paths and exact staged blobs reviewed with 0 findings; whitespace PASS |

Final full source/tests remained frozen at 895e5bb. Only reporting docs changed
afterward. Fourteen skips are **3 existing POSIX installer + 11 existing Linux-only
physical sandbox tests**. No TLS, consensus, backup, distributed or Windows GC
authorization test was skipped/weakened. The new GC matrix runs its Windows lock
branch; its Linux physical unlink/lost-ACK branch remains separately unrun.

Final full log contains all **12/12 3A + 20/20 2B + 7/7 3B + 3/3 existing 3C
replication fault gates PASS**, plus all three new GC authorization milestone
groups. These are Windows synthetic development results, not physical-GC acceptance.

Raw local logs stay outside source in TEMP: asc-3c4c-targeted.log,
asc-phase3c-python-full.log (first failed run), asc-phase3c-python-final.log
(prior 199-test PASS), asc-phase3c-python-hardened-final.log and
asc-phase3c-go-full.log. No raw keys, tokens,
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

3C.5b publication independently verified local/fetch/advertised remote equality:
`895e5bb26bf79ac36bbf85e22d82babfaac84b55`. Fresh final full run starts exactly
there, with source/tests frozen. Current Go tree is byte-identical to the previously
checked Go tree; Windows/Linux/Android builds are unchanged source and only Windows
Go tests are executed here. No Linux/Android executable is run on a device.

## Final Windows gate and account-independent handoff

Final full source/test hash: **895e5bb26bf79ac36bbf85e22d82babfaac84b55**.
`python -B -m unittest discover -s tests -v`: **203 tests OK, 189 PASS / 14 SKIP,
0 FAIL/ERROR, 1008.998s**. All prior/new applicable Windows checks PASS. No source
or tests changed during/after this final successful run. Go tree remains identical
to the fresh tested/vetted/module-verified/built tree (checked against c909e1e).
No Go rerun was needed for later Python-only changes; Python full regression still
builds and runs actual current Go fixtures. No owner-supplied PASS was reused.

Resume from the latest verified WIP reporting commit, with runtime/test source
895e5bb. Do not redo checkpoints 3C.0-3C.4c. Finish only the remaining 3C.5 Linux
synthetic network physical-boundary, pause/term/quorum, crash/journal, lost-ACK and
snapshot/replay gates described above, then full applicable regressions. No WSL
installation/platform bypass is authorized by this handoff. **NOT ACCEPTED** remains
the Phase 3C status until these remaining gates actually PASS.

3C.4c, 3C.5a and 3C.5b were individually pushed/remote-verified. Final reporting
commit changes documents only, follows full tracked/index secret review, and is
identified by Git log/final response after independent fetch/ls-remote equality.
Original root local changes remain preserved; use the isolated worktree or a fresh
remote checkout. No main merge, force push, phone/M51/production access or Android
execution occurred. Rollback still requires matching private state AND byte backups.
