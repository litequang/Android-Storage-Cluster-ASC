# Phase 3B plan and continuation contract

Date: 2026-10-24. Repository: litequang/Android-Storage-Cluster-ASC.
Only development/push branch: `wip/phase2a-raft-qualification`.
Accepted base: `0550967f57f145ff75179c20500e4aafe9c5cb31` (Phase 3A v0.9.0).
Read AGENTS.md and its ordered documents, then PHASE3A-ACCEPTANCE.md and this
plan/progress before continuing. Fetch GitHub every session; preserve local work,
use fast-forward only, never main/reset/force push. Stop immediately on a
proxy:8080 error; preserve inherited network settings and TLS verification.

## GitHub gate after EVERY checkpoint

Run targeted tests, fix real failures, update CODEMAP and relevant architecture/
API/schema/security/troubleshooting/changelog, record exact results and next steps
in PROGRESS, review all tracked and staged paths/blobs for private state/secrets,
commit, normal push to the exact WIP ref, compare `git ls-remote` with local HEAD.
Do not start the next checkpoint until remote verification succeeds. A blocked
push may use a supported draft PR targeting WIP; it remains unsynchronized until
its commit appears on GitHub. Never claim remote success from local commit alone.
Commit hashes are recorded by the following checkpoint or final report (a commit
cannot embed its own hash). Fetch and log are the authoritative recovery record.

## Ordered checkpoints and reviewable outcomes

| Checkpoint | Deliverable / targeted evidence |
|---|---|
| 3B.0 | This plan, durable progress and corrected roadmap; docs/link/whitespace review; first push before source changes |
| 3B.1a | Versioned Node Score contract, strict bounded finite inputs, UNKNOWN and provenance semantics; malformed/boundary contract tests |
| 3B.1b | Pure deterministic 0–100 score, separate observed reliability and confidence, freshness/UNKNOWN behavior; monotonicity/extremes/unknown tests |
| 3B.1c | Owner-only read-only score API, exact source checkpoint labels; auth/nonmutation/follower tests; no placement changes yet |
| 3B.2 | Bounded replicated telemetry history: 24h hourly and 7d/30d daily summaries, explicit coverage/gaps/provenance; restart/takeover/stale/bounds tests |
| 3B.3 | Owner-only replay-safe Auto, Preferred, Avoid New Storage, Drain, Protected preferences; generation-aware persistence; no movement/deletion from Drain |
| 3B.4 | Rank only hard-eligible destinations after approval/generation/protected/freshness, independent physical domain, policy and double-copy capacity/reservation checks; preferences/score tie-breaks and actual upload/copy tests |
| 3B.5 | Replica reduction preview only: retained versions/snapshots/backup/active jobs/domain policy and current evidence; no apply endpoint or physical byte deletion; nonmutation/negative tests |
| Final gate | Fresh full Python regression including Phase 3A/2B faults, Go tests/vet/module verify/build and related new fault tests; exact results in PHASE3B-ACCEPTANCE.md |

Large checkpoints may be split into suffixes; each subcheckpoint has the same
GitHub gate. No Phase 3C/3D, Dashboard or deployment in this task.

## Design constraints to preserve

Scores are advisory observations, never authentication, Raft authority, membership
or quorum input. Explicit approved node/domain/volume and independent byte proof
remain mandatory. Manufacturer specifications and old readiness_score are never
measured telemetry. Missing, invalid, stale or future observations are UNKNOWN,
never fabricated zero or maximum health. Report score, observed reliability and
confidence separately, with component contributions, timestamps and provenance.

The initial scoring contract will use measured capacity, pinned probe reachability,
observed probe reliability, and explicitly available runtime sensor/resource data.
Document formula/weights/freshness before engine implementation. Unknown components
reduce confidence; no unmeasured Android sensor is invented. Probe success ratio
is not continuous uptime, disk durability or backup proof.

Use the existing bounded runtime prepared-document CAS/actual-term fencing for
optional versioned node-insights state; no live DB/Engine/schema rewrite. Explicit
all-Controller upgrade/enable for new persisted extensions. Bound history with
hour/day aggregates, sampling coalescing and 30-day retention, preserving UNKNOWN
gaps; never evict private authority/backup history to fit telemetry. Whole runtime
2 MiB and Go permanent receipt 4096 limits remain fail-closed constraints.

Preferences cannot override safety. Auto default; Preferred ranks safe targets;
Avoid New Storage and Drain exclude new target allocation but retain reads and
existing bytes; Drain does not schedule automatic moves; Protected excludes new
storage and remains readable only under existing authentication/eligibility rules.
Hardware-protected devices remain blocked regardless of preference.

Smart placement keeps policy minimum independent approved physical domains and
existing pending double-copy capacity reservations. Stable deterministic ordering
and explanations must not equate a high score with independent storage proof.
Replica reduction only returns a checkpoint-bound proposal with reasons/holds;
retained snapshots/history/backups and in-flight work are preserved. No final
object deletion API, manifest deletion or destructive grant is introduced.

## Qualification and rollback

Local fake-node/temp-volume/loopback TLS tests only; no phone/M51/production
inspection or system tool installation. Record installed tool availability and
concrete blockers; never silently skip consensus/TLS tests or reuse Windows PASS
as a new Cloud result. Existing Phase 3A Windows acceptance remains historical.
Rollback follows stopped/isolated complete private pre-enable backups plus matching
source, preserving all newer state/objects. No schema editing, extension removal,
voter reinitialization or restoration over active state.
