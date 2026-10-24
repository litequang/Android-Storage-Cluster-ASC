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
| 3C.2b | 13 targeted PASS; all 39 legacy fault gates PASS; initial combined fixture error preserved; publication pending |
| 3C.3–3C.5 | NOT STARTED |
| Full regression / acceptance | NOT RUN; Phase 3C NOT accepted |

## Next action / resume

Publish/verify 3C.2b, then implement 3C.3 GC reference graph and monotone transition
guards. Fresh copy/domain proofs and logical retirement are implemented; original
bytes/events/completed jobs remain. Retired identities cannot reenter current
Catalog or active jobs. No physical unlink or garbage collection exists yet.

Targeted retest:
`python -B -m unittest tests.test_replication_faults tests.test_replication -v`
**13 PASS, 16.600s**; includes actual three-Go/three-Python/TLS copy-before-retire
and policy 1/2/3/1 gates. Product source unchanged after retest.

Broader safety run:
`python -B -m unittest tests.test_replication_faults tests.test_replication tests.test_backup tests.test_failover tests.test_node_faults -v`
**40 tests, 402.993s; 39 PASS / 1 ERROR** in the initial new fixture (empty move list
because target probes were not ready). All existing **12/12 3A + 20/20 2B + 7/7 3B**
fault gates PASS in that run. New fixture now waits for actual successful probes;
its fresh retest above PASS. Combined initial command remains reported ERROR,
never relabeled PASS. Final full acceptance still must rerun every applicable test.

Logs: `/workspace/work/phase3c/3c2b-regression.log`, `3c2b-retest.log`,
`3c2b-unit.log`. Existing activation `/workspace/asc-cloud/activate.sh`.
Next graph must scan every authoritative version/snapshot/trash/job/grant/history
pointer; no history eviction to force eligibility. Add permanent transition fences
before physical apply. No Phase acceptance or real-device permission.
