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
| 3C.4a | Default-locked plans/confirmation/quorum reservations; 91 targeted + 23 TLS/unit PASS; publication pending |
| 3C.4b–3C.5 | NOT STARTED |
| Full regression / acceptance | NOT RUN; Phase 3C NOT accepted |

## Next action / resume

Verify 3C.4a publication, then 3C.4b isolated local executor/journal with fault tests.
No physical unlink exists yet. Default Controller gc_test_context=None; only an
issued in-process synthetic temporary x86 context can confirm. No CLI/config/env
enable. GC prepare stores fresh external-domain proof and 60s immutable plan;
exact SHA confirmation reserves one target. Pending permits/proofs clear on takeover.

`python -B -m unittest tests.test_replication tests.test_catalog tests.test_backup.BackupStateTests tests.test_failover.RuntimeStateTests tests.test_nodes -q`
**91 PASS, 5.369s**.
`python -B -m unittest tests.test_replication_faults tests.test_replication -v`
**23 PASS, 18.783s** (real TLS policy/copy/archive/replay plus reservation units).
Initial 22-unit run: 1 ERROR from incorrect transition-helper module in new test;
corrected import and complete retests PASS. Product guards unchanged.

Next executor must require a distinct fresh synthetic temporary-volume capability,
never adopt an existing populated volume; serialize with Engine transfers; use
no-follow root/object identity and SHA; journal before unlink; reauthorize freshly
at the final boundary; recover known unlink/lost-ACK idempotently without accepting
unknown absence. Keep default runtime unreachable. Then wire exact-scope Storage/
Controller authorization and run real three-voter fault/regression gates before
claiming acceptance. Existing 3C.2b intermediate fixture error remains documented.
