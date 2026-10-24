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
| 3C.4c | IMPLEMENTED / targeted Windows PASS; publication commit identified by Git log/next checkpoint |
| 3C.5 | NOT STARTED |
| Full regression / acceptance | NOT RUN; Phase 3C NOT accepted |

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
  credential findings; all 90 Python files parse; whitespace review PASS. Exact
  staged blobs are reviewed again before commit. No source behavior changed after
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

Publish 3C.4c after final staged review and verify remote WIP HEAD before 3C.5. Final 3C.5 must run full Python/Go checks and
Linux synthetic physical-boundary faults (paused final callback, quorum/term change,
real unlink/lost ACK/restart) before ACCEPTED. Windows skipped physical tests are a
concrete remaining qualification limit, not evidence that GC is safe on Windows.
No test capability is created by normal Controller or Agent startup. Preserve the
original dirty worktree and all history; no reset/force/main or device deployment.

Rollback requires stopped/isolated matching private state AND byte backups. Never
restore an older Catalog over physically GC-mutated volumes or erase reservations,
retirements, journals, terms or receipts. Synthetic volumes only; real devices locked.
