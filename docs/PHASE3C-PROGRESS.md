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
| 3C.3a | Pure full graph + monotone transition guards; 69 targeted and 17 TLS/unit tests PASS; publication pending |
| 3C.3b–3C.5 | NOT STARTED |
| Full regression / acceptance | NOT RUN; Phase 3C NOT accepted |

## Next action / resume

Verify 3C.3a publication, then 3C.3b explicit audited terminal-job pointer release.
GC graph currently correctly holds retired bodies referenced by completed jobs
and old Catalog events. No physical unlink exists. Never discard retained events
or active jobs to fabricate eligibility. Terminal-job archival must preserve
identity/history/digest, upload retry and completion replay without raw object
pointers; monotone transitions must reject job resurrection or unaudited removal.

3C.3a checks (existing activation):
`python -B -m unittest tests.test_replication tests.test_failover.RuntimeStateTests tests.test_backup.BackupStateTests tests.test_nodes -q`
**69 PASS, 3.804s**.
`python -B -m unittest tests.test_replication_faults tests.test_replication -v`
**17 PASS, 24.849s**, actual three-voter/TLS copy and 1/2/3/1 policies with new
Runtime transition guards. Source unchanged afterward. Logs in /workspace/work/phase3c.

3C.2b broader initial run: 40 tests / 1 initial new-fixture ERROR (402.993s), all
39 legacy 3A/2B/3B gates PASS; repaired new fixture retest 13 PASS (16.600s).
Do not relabel that initial command PASS. Final full acceptance reruns all tests.
No Phase completion, phone/production/voter/3D/Dashboard permission.
