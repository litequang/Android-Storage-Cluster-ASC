# Phase 3C progress / account-independent handoff

Updated: 2026-10-24 (Asia/Saigon).
Branch: `wip/phase2a-raft-qualification`.
Base: `b1b46e527826617748a8bc68795259060e12d705`.

## Verified session state

- GitHub fetched through inherited enforced unrestricted policy; remote WIP and
  starting HEAD equal the accepted Phase 3B base. Clean working tree; no 3C
  checkpoint found in existing available Git history. No main/reset/force operation.
- Read AGENTS and mandatory ordered docs, then Phase 3B plan/progress/acceptance,
  implementation roadmap and Phase 3A acceptance context.
- Existing Cloud activation: `/workspace/asc-cloud/activate.sh`; verified Python
  3.13.5 / Go 1.27.3 linux/amd64. No system installation or proxy changes.
- Phase 3B prior 152 PASS / 39 fault gates is historical, not current 3C validation.

## Checkpoints

| Checkpoint | Actual state |
|---|---|
| 3C.0 | PUSH VERIFIED `6a9deb58614bb51b351c3a9aed0cdee5e109180a`; docs/link/whitespace and tracked/staged review PASS |
| 3C.1 | PUSH VERIFIED `41fd522`; 70 targeted + 4 runtime tests PASS |
| 3C.2a | PUSH VERIFIED `c6a1012`; 73 targeted tests PASS (3.451s) |
| 3C.2b | PUSH VERIFIED `173faf8`; 13 targeted + all 39 legacy gates PASS; initial combined fixture error recorded |
| 3C.3a | PUSH VERIFIED `9a675c2`; 69 targeted + 17 TLS/unit PASS |
| 3C.3b | PUSH VERIFIED `445af5c`; 59 targeted + 20 TLS/unit PASS |
| 3C.4a | PUSH VERIFIED `b5cb2ed`; 91 targeted + 23 TLS/unit PASS |
| 3C.4b | PUSH VERIFIED `c909e1e70a4ce7a01674b6caaed1b3b4e6574a65` by Windows fetch on 2026-10-24; prior Cloud local executor/journal checks retained |
| 3C.4c | PUSH VERIFIED `74bb6a90f2e4e04751b3edb83d60ac00807ab06f`; 85 targeted OK (11 Linux-only skips) + actual Go/TLS GC fault test PASS |
| 3C.5a | PUSH VERIFIED `8d45b2637801a64ae5fa67cd3cb5a4c7295010f8`; 11 targeted consensus/runtime/device safety PASS (27.498s) |
| 3C.5b | PUSH VERIFIED `895e5bb26bf79ac36bbf85e22d82babfaac84b55`; 53 targeted PASS + actual Go/TLS PASS (345.308s) |
| 3C.5c | Windows final reporting: 203 OK (189 PASS / 14 platform skips), 1008.998s; final report commit identified by Git log |
| 3C.5 | PARTIAL: all Windows applicable checks PASS; Linux physical network fault qualification pending |
| Full regression / acceptance | Hardened source 895e5bb: 203 OK / 14 platform skips; Go/vet/module/build PASS. Phase 3C NOT ACCEPTED: Linux physical gates remain |

## Current Windows continuation

- Fetched origin and verified `c909e1e70a4ce7a01674b6caaed1b3b4e6574a65` as remote
  WIP HEAD and 3C.4b. Its earlier publication-pending label is corrected above.
- Original `E:/CODE/ASC-QuickStart` remains on 0550967 with uncommitted older 3B.1
  work. It was not reset, stashed, overwritten or pulled across those edits.
  Isolated detached worktree `.asc-worktrees/phase3c` starts exactly at c909e1e;
  publication destination is only `HEAD:refs/heads/wip/phase2a-raft-qualification`.
- Existing Python 3.14.7, private portable Go 1.27.3 and existing Git OpenSSL are
  used with process-local environment only. No WSL distro is installed. Physical
  executor remains Linux-only; do not bypass its Windows/Android lock for tests.
- 3C.4c implements Controller/Storage integration, same-job fresh permits, target
  generation/approval/endpoint binding, final full graph/external-domain SHA proof,
  nonce/current-term quorum receipt, exact completion and journal replay transport.
  Raw bearer is memory-only, no normal capability/enable path or automatic GC.

## Checks so far (new Codex-run Windows evidence)

- `python -B -m unittest tests.test_gc_authorization -q`: **12 PASS, 9.466s**.
- `python -B -m unittest tests.test_gc_authorization tests.test_replication tests.test_gc_sandbox tests.test_storage tests.test_storage_cluster tests.test_distributed tests.test_failover.RuntimeStateTests -v`:
  **85 tests OK: 74 PASS / 11 existing Linux-only physical SKIP, 116.410s**.
  Existing TLS/distributed/runtime checks ran; no test/gate was weakened.
- `python -B -m unittest tests.test_gc_faults -v`: **1 PASS, 306.174s**.
  Actual three-Go/three-Python pinned TLS: external-domain streamed SHA, exact
  nonce/intent receipt, wrong scope/volume/bearer and superseded run rejection,
  Windows physical denial with unchanged bytes, Leader loss/takeover and quorum
  loss denying old permits. Linux unlink/lost-TLS-ACK branch is added but unrun here.
- All 133 tracked/new working paths and contents reviewed: 0 private artifact/key/
  credential findings; all 90 Python files parse; whitespace review PASS. All 20
  staged blobs were reviewed with 0 findings before the verified 3C.4c push. No source behavior changed after
  these PASS results (only reporting and a module description updated).
- Intermediate failures: existing Windows nonexistent-arena path leaked
  FileNotFoundError (now fixed to the original closed CatalogError); new unit
  fixture initially referenced an unexposed helper/omitted required fake fields
  (fixed). First integration harness incorrectly used a second writer against
  the same sidecar and correctly hit CAS/probe holds. It now performs synthetic
  preparation on the actual cohost Runtime lock; protection gates remain intact.
- Prior Cloud 3C.4b 67 PASS / 49.807s and local journal evidence remain historical,
  not new Windows physical-deletion proof. No real phone/M51/production accessed.

## Next action / resume

The hardened source **895e5bb26bf79ac36bbf85e22d82babfaac84b55** is pushed and
independently remote-verified. Final Windows full: **203 OK, 189 PASS / 14 SKIP,
0 FAIL/ERROR, 1008.998s**. Go 11 uncached tests/vet/module verify and Windows/Linux/
Android builds PASS (Linux/Android compile-only). Details and exact commands:
[PHASE3C-ACCEPTANCE.md](PHASE3C-ACCEPTANCE.md).

Only 3C.5 physical qualification remains: use a supported Linux x86 synthetic temp
arena, execute all physical sandbox/network GC branches and paused final callback,
term/quorum loss before unlink, Node crash/journal restart, lost ACK and whole-cluster
snapshot/replay. Run full applicable regression afterward and publish/verify before
ACCEPTED. Windows has no installed Linux/WSL distro and physical execution remains
locked. Do not bypass/install a platform or operate real data to claim PASS.

No 3C.0-3C.4c reimplementation is needed. Ordinary startup issues no GC capability.
Preserve the original dirty root worktree; continue in `.asc-worktrees/phase3c` or
from latest verified remote WIP reporting commit. Rollback needs stopped/isolated
matching private state AND byte backups. Do not erase fences/journals/receipts,
edit terms/schema, reset voters, merge main, force push or deploy to phones/M51.

The following chronological notes preserve intermediate failures and source
provenance; the final result above supersedes their earlier RUNNING/pending labels.

3C.5 intermediate finding: the first full run on 74bb6a9 found the existing
metadata subprocess no-fallback assertion failing on Windows. Isolated reproduction
`python -B -m unittest tests.test_consensus -v`: 3 tests, 1 FAIL, 28.779s. Actual
stderr was DEVICE IDENTITY UNKNOWN, not the required attached-registry error.
The synthetic profile wrapper previously ran only on Linux. It now runs on every
host with unchanged product code, no-fallback assertion and explicit guard tests.
The first full run is not PASS; after this repair a fresh full rerun is mandatory.

3C.5a targeted repair check:
`python -B -m unittest tests.test_consensus tests.test_nodes.RuntimeSafetyTests tests.test_lifecycle.DeviceSafetyTests -v`:
**11 PASS, 27.498s**. Product M51/Android/unknown-device guards and all original
no-fallback assertions are unchanged. Go source has not changed after the fresh
11-test/vet/module verification/Windows+Android compile PASS recorded in acceptance.

First full completed: **199 tests, 184 PASS / 1 FAIL / 14 SKIP, 1038.894s**.
Only failure was the reproduced/fixed Windows metadata fixture assertion. All
12/12 3A, 20/20 2B, 7/7 3B, 3/3 existing 3C replication gates and new Windows GC
authorization faults passed within that failed overall run. Fourteen skips are
3 POSIX installer + 11 Linux physical-executor cases. No TLS/consensus gate skipped.
Fresh full source/test commit is **8d45b2637801a64ae5fa67cd3cb5a4c7295010f8**;
raw log TEMP/asc-phase3c-python-final.log. No source/test edits during this final run.

3C.5b review finding: the second full run on 8d45b26 passed **199 tests,
185 PASS / 14 SKIP, 1010.082s**, but a separate synthetic race probe then proved
survivor endpoint reapproval during streaming could reuse old byte evidence.
The new proof_fingerprint binds all references, policies, approvals, identities,
endpoints and effective protection across IO and final CAS. It does not change
persistence/wire schemas. Two race tests require denial for endpoint changes and
new pins during streaming. A further regression distinguishes unrelated heartbeat
telemetry from protected state; actual freshness/readability still uses the real
current document. Original planner/confirmation digests are unchanged.

Initial strict whole-profile binding correctly denied an ordinary heartbeat in
the actual TLS test (1 ERROR, 151.186s); unrelated self-reported telemetry is now
canonicalized only in the transient proof binding. No safety gate/assertion was
removed. Latest focused command:
`python -B -m unittest tests.test_gc_authorization tests.test_replication tests.test_failover.RuntimeStateTests -q`:
**41 PASS, 15.278s**. Actual Go/TLS rerun is pending; latest full regression must
be repeated after publication of this source change. Phase 3C remains NOT ACCEPTED.

The subsequent actual TLS run correctly rejected a stale exact confirmation
(1 ERROR, 41.403s) under concurrent heartbeat. The owner client now preserves only
fixed safe GC error labels (unknown text stays redacted). The new fault harness
bounds explicit retries: reprepare/reconfirm a new SHA for stale plans, obtain
new byte proofs/nonces for stale proof, and keep the same retirement/job identity.
Negative wrong-scope/old-token assertions remain immediate failures. Linux lost-ACK
checks require the actual successful-drop marker and missing original body, allowing
safe Discovery-level recovery to return success instead of demanding an exception.

Latest focused command additionally includes foundation and device guards:
`python -B -m unittest tests.test_gc_authorization tests.test_replication tests.test_failover.RuntimeStateTests tests.test_foundation tests.test_lifecycle.DeviceSafetyTests -q`:
**53 PASS, 16.995s**. This includes 16 GC unit tests and fixed-error redaction.

3C.5b final actual TLS rerun: `python -B -m unittest tests.test_gc_faults -v`,
**1 PASS, 345.308s**. Exact scope/nonce, superseded permits, Windows physical
lock/unchanged bytes, actual Leader loss and quorum loss all PASS after fresh-plan/
proof retry. This hardening is ready for publication; then run fresh full Python
on its published hash. Go code is unchanged since successful uncached Go checks.
The nested worktree alone is locally excluded through .git/info/exclude (existing
entries preserved); original 0550967 worktree still has its same older local edits.

Final hardened full run source/test hash:
`895e5bb26bf79ac36bbf85e22d82babfaac84b55`, independently pushed/fetched/ls-remote
verified before starting the run. Log: TEMP/asc-phase3c-python-hardened-final.log.
No source/test edits after that published checkpoint; only reporting docs change.

Final hardened gate completed: **203 OK (189 PASS / 14 SKIP), 1008.998s** on
895e5bb. All 39 legacy 3A/2B/3B fault gates + 3 existing replication gates and all
three new GC authorization groups PASS in that final log. No tests/source changed
afterward. Reporting publication follows tracked/staged review; its own hash is
available through Git log/final response. Phase 3C remains NOT ACCEPTED for the
concrete remaining Linux physical gates, not because Windows regression failed.
