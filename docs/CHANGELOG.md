# CHANGELOG

## v0.4.1 — 2026-10-23 — Phase 1.1 Windows accepted / workflow and main publication
- Owner confirms Windows unittest result: 40 tests, OK (skipped=3). The three installer
  cases require Linux/Termux. TLS, pinning and SQLite migration tests were not skipped.
- This publication update changes documentation/workflow only, retaining source/tests
  and reusing the owner's PASS as explicitly requested; no redundant Codex rerun.
- AGENTS now permits proactive local test/typecheck/lint/build: targeted checks after
  source changes, full applicable suite before Phase completion, repair failures or
  report real blockers. Never skip/delete/weaken tests merely to obtain PASS.
- Aligned README, CODEMAP, historical prompts and acceptance/security guidance with
  the new rules. Isolated test fixtures are permitted; production servers, real-phone
  installers, real data changes and M51/private production state remain forbidden.
- Added `.gitattributes` to keep shell scripts LF on checkout despite Windows autocrlf;
  source/test contents are unchanged.
- Owner authorizes source review, commit and non-force main publication. Audit tracked
  and staged paths/blob contents, preserve remote history, and verify the pushed commit.
  Actual commit/push outcome is reported separately; no new GitHub Actions or deployment.
- Phase 1.1 is accepted as a Windows single-writer registry foundation. Linux/Termux
  installer validation and real-device/end-to-end v1.0 acceptance remain deferred.
  Phase 1.2A is ready for a separate task and is not started here.

## v0.4.1 fixes — 2026-10-23 — Windows retest / Git preparation pending acceptance
- Fixed missing-OpenSSL diagnostics: explicit PATH lookup, resolved executable argv,
  actionable Windows instructions and generic subprocess-failure messages. No TLS skip,
  certificate pinning change, insecure fallback or automatic dependency installation.
- Fixed Windows migration-fixture WinError 32: connection context alone did not close
  SQLite. Added explicit connection/cursor closure and regressions for rollback and
  immediate rename/delete while references remain alive. Runtime Registry.connect
  already closes in finally; migration/API/schema/token semantics are unchanged.
- Added dependency diagnostic tests and reliable TLS class setup cleanup. Real HTTPS
  and wrong-pin tests remain required. Owner previously reported 30 tests / 3 errors /
  3 skipped; Codex has not run the updated suite.
- Added .gitignore for private ASC state/recovery copies, TLS/SSH keys, environment
  secrets, runtime databases/journals, logs, temp files and archives; documented staged
  review and the fact ignore rules cannot scrub tracked files or arbitrary secret values.
- Initialized previously absent local Git metadata on main and configured origin to
  litequang/Android-Storage-Cluster-ASC. Read-only remote lookup advertised no branch/tag
  at preparation time; recheck before publishing. No commit, push, force, history rewrite
  or GitHub Actions was created. Per-command workspace trust handles sandbox ownership.
- Updated workflow: fix/accept Phase 1.1 on Windows first; future v1.0 components are
  phased with API/migration contracts and multi-node Windows simulation before phones.
  No new v1.0 module or Android/production operation was performed.

## v0.4.1 — 2026-10-23 — Phase 1.1 secure node lifecycle
- Added authenticated Controller CLI/API list/detail/rename/revoke and targeted
  re-pair/token rotation preserving node ID, joined_at and administrator name.
- Added idempotent revoke, rejected-old-token behavior and agent repair-required state;
  agent stops on rejected credentials, retaining identity and cached topology.
- Added client-persisted private enrollment operations, transactional retry-safe grants
  and permanent hashed operation routing. Lost responses and explicit replacement
  initial codes cannot create another node for the same operation. Legacy enrollment
  remains one-use without retry guarantees.
- Added additive transactional registry migration from v0.4 user_version 0 to schema 2,
  lifecycle fields, targeted grants and enrollments table. Existing IDs/token hashes
  remain intact; API stays /api/v1 and versionless v0.4 profiles/configs remain readable.
- Added schema/body/profile/text bounds, generic secret-safe errors/logs, per-IP/global
  join/auth-failure limits, bounded TLS workers/timeouts and bounded client responses.
- Closed per-operation SQLite handles explicitly and cleaned the uniquely created SD
  probe file on partial write/fsync failures where cleanup is possible.
- Added profile_version 1, explicit score basis and honest SD detected/writable-tested/
  unknown states. Missing runtime RAM/storage remains null. Unknown Android identity
  now blocks install/runtime and SD writes; strengthened secondary M51 identification.
  Deduplicated SD app-folder aliases so one visible card is not reported twice.
- Ignored invalid legacy self-reported scores for role ordering instead of allowing
  malformed v0.4 profile values to break topology reads; no permissions derive from scores.
- Added foreground OS locks/status with Ctrl+C stop; no daemon/boot/service changes.
  Installer reports missing dependencies without installing/upgrading packages, preserves
  installed source/identity and refuses a different release pending explicit upgrade.
- Added owner-run lifecycle/security/migration/retry regression cases and Vietnamese
  ZTE/Bphone/XZ3 guide including two-device acceptance, versioned-source upgrade and
  pre-migration-state rollback. Old Controller must not run directly on schema 2;
  rollback may restore revoked credentials and loses post-backup registry changes.
- Codex did not run tests, typecheck, lint, build, server or installer. Hardware and
  acceptance results are pending. No M51/production access, Raft, file NAS, backup,
  automatic failover, Internet exposure or production-readiness claim.
- Added POSIX installer regression cases using a fake HOME/getprop/pkg environment:
  repeated install preserves identity/source, unknown/M51 refuses before install, and
  missing dependencies only produce instructions. These cases skip on Windows.
  Reinstall of an already enrolled node also preserves state while its agent is running.

## v0.4.0 — 2026-10-23
- Added runnable Python (standard library) single-writer local HTTPS registry Controller.
- Added node auto hardware profile, manufacturer baseline role hint and protected M51 detection.
- Added optional bounded microSD write/read/remove probe (app-specific directory only).
- Added cluster-wide advisory role planning (no voting / failover authority).
- Added one-time expiring join codes, individual node tokens, heartbeat, registry queries, local topology snapshot.
- Added safe Termux installer that will not overwrite existing ASC installation or mutate M51 hosting.
- Added unit/integration tests, CODEMAP and permanent Codex documentation maintenance policy.
- Explicit scope exclusion: no real Raft, file storage, user dashboard, auto failover, internet gateway or backup yet.
