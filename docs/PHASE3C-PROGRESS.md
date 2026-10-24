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
| 3C.3b | Audited terminal-job pointer release/replay; 59 targeted + 20 TLS/unit PASS; publication pending |
| 3C.4–3C.5 | NOT STARTED |
| Full regression / acceptance | NOT RUN; Phase 3C NOT accepted |

## Next action / resume

Verify 3C.3b publication, then 3C.4a guarded confirmation/reservation protocol
(default locked; no physical unlink yet). Explicit terminal-job archives preserve
identity/hash/history and upload/completion replay, remove no events, never archive
active/retryable/backup jobs. A retired body remains held by every retained pointer.

`python -B -m unittest tests.test_replication tests.test_catalog tests.test_backup.BackupStateTests tests.test_failover.RuntimeStateTests -v`
**59 PASS, 1.378s**. Initial new archive fixture cached the old projection across
fake commit (2 FAIL/1 ERROR); refresh its test reference, no production/test
assertions weakened. Corrected whole target PASS.
`python -B -m unittest tests.test_replication_faults tests.test_replication -v`
**20 PASS, 14.861s**; actual TLS copy/1-2-3-1/archive/upload+completion replay gates.
Source unchanged after tests. Logs /workspace/work/phase3c/3c3b-*.log.

Next GC must have: default absent in-process isolated test capability; no CLI/env/
config enable for real devices; owner plan-SHA confirmation; irreversible bounded
quorum reservation and exact-object nonce-bound final authorization; private durable
node journal, no-follow/root/size/SHA checks and idempotent lost-ACK/crash handling.
Do not delete any object with live graph pins. Final full safety regression pending.
