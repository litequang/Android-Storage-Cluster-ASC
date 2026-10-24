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
| 3C.2a | Durable copy planning/Drain; 73 targeted tests PASS (3.451s); publication pending |
| 3C.2b–3C.5 | NOT STARTED |
| Full regression / acceptance | NOT RUN; Phase 3C NOT accepted |

## Next action / resume

Verify 3C.2a publication, then 3C.2b fresh physical survivor proofs and logical
retirement only. No source record/byte is removed by current move planning.
Command: `python -B -m unittest tests.test_replication tests.test_catalog tests.test_backup.BackupStateTests tests.test_nodes -q`
**73 PASS, 3.451s**. Copy intents survive SQL roundtrip/takeover and retries; blocked
Drain keeps existing readable bytes. All Controllers must upgrade before new fields.

Next retirement must stream/hash remaining independent copies, preserve backup
copy floor, recheck current policy/approvals/active jobs/term and fence retired IDs
against reintroduction. Physical reclaim stays a separate reference-graph/GC gate.
No Phase acceptance; no phone/production/voter/3D/Dashboard work.
