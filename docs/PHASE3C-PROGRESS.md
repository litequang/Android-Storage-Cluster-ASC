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
| 3C.1 | Replication extension/policy/reconcile; 70 targeted + 4 runtime tests PASS; publication pending |
| 3C.2–3C.5 | NOT STARTED |
| Full regression / acceptance | NOT RUN; Phase 3C NOT accepted |

## Next action / resume

Verify 3C.1 publication before implementing 3C.2 Drain/Rebalance. No physical delete.
Commands after existing activation:
`python -B -m unittest tests.test_replication tests.test_catalog tests.test_backup.BackupStateTests tests.test_nodes -q`
**70 PASS, 3.410s** (includes real pinned TLS placement fixture).
`python -B -m unittest tests.test_failover.RuntimeStateTests -q`: **4 PASS**.

3C.1 uses explicit replication schema 1 and 256 replay receipts, retains legacy
schemas/3A/3B and actual-term CAS. Increasing schedules independent COPY jobs;
reducing policy preserves current replica records/bytes. No quorum/invalid count
cannot commit. Full regression/GC fault acceptance NOT RUN; no Phase completion.
