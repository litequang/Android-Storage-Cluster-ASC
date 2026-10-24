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
| 3C.4b | Isolated local executor/journal; 67 safety regression + final local tests PASS; publication pending |
| 3C.4c–3C.5 | NOT STARTED |
| Full regression / acceptance | NOT RUN; Phase 3C NOT accepted |

## Next action / resume

Verify 3C.4b publication, then 3C.4c wire exact-object Controller/Storage authorization
and actual three-voter/TLS execution. Ordinary runtime/Agent has no executor or
context; no config/env/CLI enable exists. Local physical executor is Linux x86
fresh synthetic temp volumes only, with immutable restart binding and FULL journal.
Unit callbacks are simulated authorization, not yet proof of network quorum fencing.

`python -B -m unittest tests.test_gc_sandbox tests.test_storage tests.test_storage_cluster tests.test_distributed tests.test_replication -v`
**67 PASS, 49.807s** (actual local unlink plus existing Storage/TLS/distributed).
`python -B -m unittest tests.test_gc_sandbox tests.test_storage -v`: final local
PASS (see 3c4b-local-final.log), adds post-manifest/DONE lost-ACK and reappeared-body
holds. Source unchanged after tests. Logs under /workspace/work/phase3c.

Next: issued Controller fixture context + issued Node arena only; default absent
capabilities remain locked. Target-specific raw grant must never enter replicated
state/logs; persist only hash. Fresh nonce/current-term quorum reauthorization at
final unlink must reprove external-domain survivors/current graph. Takeover clears
permit; paused/expired/missing quorum/new pin/old run must deny. No cached/fallback
permit. Node journal makes actual unlink + lost ACK idempotent. API execute must
be explicit confirmed test-only, never automatic background GC. Final full/fault
acceptance and real physical-boundary timing limitations remain to document.
