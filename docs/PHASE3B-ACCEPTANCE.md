# Phase 3B acceptance — pending final gate

Status: NOT ACCEPTED YET. Linux Cloud isolated development simulation only.
Date: 2026-10-24 (Asia/Saigon). Version: 0.10.0 development.
Base: 0550967f57f145ff75179c20500e4aafe9c5cb31 (Phase 3A Windows accepted).
Branch: wip/phase2a-raft-qualification. See PLAN/PROGRESS for published checkpoints.

## Executed targeted evidence

All results here are new Codex-run Cloud checks, not reused Windows evidence.
Existing tools: Python 3.13.5, Go 1.27.3 linux/amd64, activated through
`source /workspace/asc-cloud/activate.sh`. No system install/PATH/proxy changes.

- 3B.1a: 3 contract tests PASS. 3B.1b: 7 contract/engine tests PASS.
- 3B.1c: 13 score/runtime tests PASS.
- 3B.2: 38 node/runtime/backup unit tests PASS.
- 3B.3: 41 targeted tests PASS.
- 3B.4: `python -B -m unittest tests.test_nodes tests.test_catalog tests.test_distributed -v`:
  54 PASS, 59.175s. Actual synthetic TLS upload/copy/download avoids Drain and
  preserves independent physical-domain policy and double-copy reservations.
- 3B.5a: 37 targeted preview/CLI/placement/history/backup/runtime tests PASS.
- 3B.5b: `python -B -m unittest tests.test_node_faults -v`: 1 matrix test,
  **7/7 gates PASS, 73.429s** (logs in workspace work/ only).
- Existing Go module verification/vet/11 top-level tests PASS; Linux AMD64,
  Windows AMD64 and Android ARM64 builds PASS. Final post-checkpoint checks pending.

## Executed new fault gates

1. Explicit enable/replay; node bearer denied owner scores; follower local stale
   score read succeeds without becoming a writer.
2. Preferred/Drain place actual exact bytes on two independent approved domains.
3. Real pinned probe observations persist bounded history; gaps and continuous
   uptime stay UNKNOWN.
4. Retained Phase 3A snapshot prevents reduction; no apply route, no physical deletion.
5. Python Leader crash/watchdog takeover retains preferences; former Leader rejects writes.
6. Every minority Controller rejects preference mutation during all-voter partition.
7. Actual Go snapshots and restart of all Go/Python processes preserve generation-tagged
   history, preferences, intent receipts, Phase 3A manifest and retrievable file bytes.

## Intermediate findings and actual fixes

- Contract fixture initially omitted seed_self name: 2 new test errors fixed in fixture.
- First distributed Cloud target: 52 tests, 1 error. CLI fixture supplied only
  protected=false; Linux correctly required installation_allowed. Fixture now
  explicitly permits its synthetic hardware; product guard/assertions unchanged.
- First new fault run: 1 startup failure in 11.360s. Existing real entrypoint is
  Windows-only; shared test launcher now mocks only its module-local OS selector
  and inspect result for synthetic cohosts. Product Linux refusal is explicitly
  tested and unchanged. No consensus/TLS test is skipped or weakened.
- Re-pair integration uncovered stopped history collection at generation changes;
  per-bucket generation tags now retain old evidence and collect new evidence
  separately. Scores use only the current approved generation.
- Required request_id=null is rejected before state access, preserving replay safety.

## Boundaries and rollback

No phone/M51/production access, membership/quorum changes, automatic Drain movement,
physical GC, Phase 3C/3D or Dashboard. Windows/Android builds are compile-only; no
new real-device/physical-power-loss/Windows execution result is implied by Cloud.
Scores are advisory, probe success is not continuous uptime/durability, runtime
RAM is agent self-report, and uncollected thermal sensors stay UNKNOWN. 24h/7d/30d
are bounded UTC calendar aggregates with partial current bucket and explicit gaps.

Conservative reduction preview never authorizes deletion: current independent
policy domains must remain; retained pins/trash/expired versions/unfinished jobs
hold proposals. Unknown/suspect/stale proof cannot count toward safety. Every
candidate would require fresh byte verification under a separately qualified
future protocol. apply_supported=false, physical_deletions=0 always.

Limits: 16 history records, per node <=24 hourly/30 daily generation-tagged bucket
records, <=64 preferences, <=128 node mutation receipts; inherited whole-runtime
2 MiB, Go 4096 permanent receipts and Phase 3A bounds unchanged. Frequent re-pair
reduces available bucket coverage. Hourly sampling does not guarantee 30 days of
uninterrupted runtime capacity: all existing operations share lifetime receipt
limits, fail closed and never evict authority to fit telemetry.

Upgrade every stopped development Controller to matching source before enable/
new preference writes. Preserve complete private config/key/DB/WAL/Raft/witness/
volume backups and matching source. Rollback stops/isolates all voters, restores
complete pre-enable backups plus matching source, and retains newer state/objects
separately. Never edit extension/schema/term/membership or reinitialize lost state.

## Final full regression and publication

PENDING. Phase 3B must not be declared complete until full Python (including
existing Phase 3A/2B and new faults), Go test/vet/module/build and final tracked/
staged secret/whitespace review pass and source/report commits are on GitHub.

## Final regression intermediate fixture repair — 3B.5c

First full Cloud run found one metadata-only subprocess fixture assuming Windows
in actual_python_controller_write_crash_restart_and_no_legacy_fallback. Its
synthetic launcher now uses the same module-local platform/profile technique;
no product code changed. The no-fallback assertion is strengthened to require
`consensus configuration required`, so an unrelated hardware refusal cannot count
as successful fencing. Existing protected/Android guard assertions remain intact.
Targeted `python -B -m unittest tests.test_consensus -v`: **3 PASS, 22.837s**.
`python -B -m unittest tests.test_nodes.RuntimeSafetyTests -v`: **2 PASS**.
This intermediate full run is not acceptance; a new complete run is required.
