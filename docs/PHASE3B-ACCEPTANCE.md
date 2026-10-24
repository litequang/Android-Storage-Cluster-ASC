# Phase 3B acceptance — Linux Cloud development simulation

Status: ACCEPTED for Linux Cloud isolated development simulation; all applicable
checks below PASS. Windows runtime and real Android/production requalification
remain outside this Cloud result.
Date: 2026-10-24 (Asia/Saigon). Version: 0.10.0 development.
Base: 0550967f57f145ff75179c20500e4aafe9c5cb31 (Phase 3A Windows accepted).
Branch: wip/phase2a-raft-qualification. See PLAN/PROGRESS for published checkpoints.

## Executed targeted evidence

All results here are new Codex-run Cloud checks, not reused Windows evidence.
Existing tools: Python 3.13.5, Go 1.27.3 linux/amd64, activated through
`source /workspace/asc-cloud/activate.sh`. No system installation, global PATH or proxy changes.

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
- Existing and post-checkpoint Go verification/vet/11 top-level tests PASS; Linux
  AMD64, Windows AMD64 and Android ARM64 builds PASS. Exact final evidence below.

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

## Final regression intermediate fixture repair — 3B.5c

First full Cloud run found one metadata-only subprocess fixture assuming Windows
in actual_python_controller_write_crash_restart_and_no_legacy_fallback. Its
synthetic launcher now uses the same module-local platform/profile technique;
no product code changed. The no-fallback assertion is strengthened to require
`consensus configuration required`, so an unrelated hardware refusal cannot count
as successful fencing. Existing protected/Android guard assertions remain intact.
Targeted `python -B -m unittest tests.test_consensus -v`: **3 PASS, 22.837s**.
`python -B -m unittest tests.test_nodes.RuntimeSafetyTests -v`: **2 PASS**.
This intermediate failure required a fresh full rerun; final successful evidence is below.

## Complete first full-run findings — 3B.5d

The first run completed **152 tests in 371.462s: 1 failure + 1 error**, not PASS.
The failure was the metadata launcher fixed in 3B.5c. The error was the legacy
Storage CLI fixture using the actual unrecognized Linux host profile. Its two
owner upload/download calls now supply an explicitly permitted synthetic profile;
M51/protected setup refusal, byte equality and non-overwrite assertions remain.
Targeted Storage CLI + all consensus + runtime safety: **6 PASS, 25.228s**.

A rerun started after 3B.5c was stopped before completion when the full first-run
summary revealed the Storage CLI error. It contributes no acceptance result.
A fresh full run on published 3B.5d followed (result below). No test is skipped/weakened and
no real platform/device guard is changed to address these fixture assumptions.

## Final full regression and publication

Source commit under test: `d1cd0e4a439db9836d1b44eacb20d1affa8eeb08`. No source/test changes during final full
regression; only reporting docs change afterward. All commands used existing
activation: `source /workspace/asc-cloud/activate.sh`.

| Exact command / check | Actual result |
|---|---|
| `python -B -m unittest discover -s tests -v` | **152 tests OK: 152 PASS / 0 SKIP, 0 FAIL/ERROR, 369.626s** |
| Phase 3A retained fault matrix within full run | **12/12 PASS** |
| Phase 2B retained fault matrix within full run | **20/20 PASS** |
| New Phase 3B fault matrix within full run | **7/7 PASS** |
| `go mod verify` | all modules verified |
| `go vet ./...` | PASS, exit 0 |
| `go test -count=1 -v -timeout 240s ./...` | **11 top-level tests PASS**, fresh uncached: consensus 18.100s, launcher 0.003s |
| `CGO_ENABLED=0 go build -trimpath -buildvcs=false -o PRIVATE_OUTPUT ./cmd/asc-raft` | Linux AMD64 PASS |
| Same build with `GOOS=windows GOARCH=amd64` | Windows AMD64 PASS, compile only |
| Same build with `GOOS=android GOARCH=arm64` | Android ARM64 PASS, compile only |
| Python AST / tracked+staged content / whitespace | PASS, final publication review below |

No prior Windows PASS was reused as current evidence. Linux runs the existing
POSIX installer fixtures too; no TLS/storage/consensus/fault gate is skipped or
weakened. Go source/module files are unchanged from the accepted base; final
post-checkpoint verification/builds succeeded and uncached tests ran again.

Raw logs are private scratch artifacts under `/workspace/work/`:
phase3b-python-final.log, phase3b-go-uncached.log, 3b5-faults-retest.log and targeted
checkpoint logs. Build binaries and synthetic keys/state stay outside source.
Summary and reproduction commands are durable in GitHub; raw temporary logs are
not required for another session to continue.

All checkpoint source commits are pushed/verified individually on the exact WIP
branch. Final reporting commit and verified remote hash appear in the final task
report and Git log (a commit cannot embed its own hash). No main merge, force push,
release/deployment, phone/private production access or physical GC occurred.

## Source and documentation routing / final review

- `asc/nodes/`: strict observation/score contract, checkpoint views, bounded history,
  quorum-committed preferences, pure reduction preview and pinned owner CLI.
- `asc/catalog/{placement,http,cli}.py` and `asc/failover/{state,service}.py`:
  hard-gated allocation/API, optional extension roundtrip and leader refresh capture.
- `asc/__init__.py`: 0.10.0. Existing Engine/manifests and Go engine/modules unchanged.
- `tests/test_nodes.py`, `test_node_faults.py`: contract/safety/history/placement/preview
  tests and seven actual fault gates. Prior fixture-only portability adjustments
  preserve/strengthen prior assertions and product guards.
- AGENTS, README/README-VI, CODEMAP, roadmap, architecture/ADR, API/schema/security/
  troubleshooting/changelog and Phase 3B plan/progress/acceptance carry the handoff.

Final review: 71 Python source/test files parse; all 113 tracked paths and working/
index blob contents reviewed for private artifacts/key/token/credential patterns,
with 0 findings. Staged diff/whitespace review PASS; final commit changes documents
only. Source/tests stay exactly at the fully tested source commit above.
