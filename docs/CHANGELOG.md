# CHANGELOG

## v0.9.0 — 2026-10-24 — Phase 3A Windows development accepted

- Explicit bounded backup schema 1 on the existing runtime schema 2: immutable
  version history/live heads, exact committed-index logical snapshot manifests,
  snapshot pins, logical TRASH/EXPIRED and conservative retention policies.
- Durable backup schedules, claims/proof checkpoints/retries and version-reserved
  restore jobs survive Controller changes. Restore reuses existing same-key upload,
  immutable Storage commit and independent byte proof, creating a new version.
- Verify enough distinct approved domains before backup completion; preserve
  suspect/last copies. Recheck active work after takeover and reject stale/minority
  authority with existing Go actual-term CAS and online Storage introspection.
- Add owner-only backup API/CLI, strict completion-proof validation, request replay
  and bounds. Retention protects the last historically verified version while a
  higher upload is incomplete; it never removes physical objects.
- Restore the documented Go init/run launcher missing in the supplied base checkout;
  scope executable ignore rules so the source directory is tracked. Existing Raft,
  Store/Engine, lifecycle and metadata envelopes retain their established boundaries.
- Fresh full Python: 122 tests OK, 119 PASS / 3 existing POSIX skips, 556.852s;
  12/12 Phase 3A and 20/20 Phase 2B fault gates PASS. Go 11 top-level tests,
  go vet, module verification and Windows/Android ARM64 builds PASS (Android
  compile only). Exact evidence/intermediate failures: PHASE3A-ACCEPTANCE.md.
  No Android/production or disconnected-backup qualification.

## v0.8.0 — 2026-10-24 — Phase 2B Windows development accepted

- Final full regression: 101 tests, 98 PASS / 3 existing POSIX skips,
  0 FAIL/ERROR, 1736.964 seconds. All 20 automatic-failover fault cases PASS.
  Go 9 top-level tests and Windows/Android ARM64 builds PASS; Android runtime
  remains unexecuted. Exact evidence and intermediate failures are retained in
  PHASE2B-ACCEPTANCE.md.

- Preserve exact metadata snapshot/delta schema and digest in runtime responses;
  add regression import checks and real pinned Agent sync across takeover/restart.
  Keep safe HTTP errors working before a malformed request has a parsed path.

- Audit unsafe single-Controller state before activation. Add opt-in schema-2
  runtime projection, disposable SQL preparation, term-bound CAS, committed
  takeover/lease/grant invalidation, private verified cache and leader-only worker.
- Add pinned multi-endpoint discovery with bounded retries, explicit stale reads,
  nonce-bound online Storage authority and Python liveness withdrawal at sidecar.
- Preserve default/Phase 2A behavior, original guarded private state, immutable
  Engine, historical PySyncObj 1 PASS / 5 FAIL and M51 restrictions. Acceptance
  is isolated Windows development; no phone or production deployment occurred.
- Reject unmerged private Controller authority using the initial upgrade receipt;
  support only freshly scoped revalidation of matching retained job bodies, keeping
  legacy NEEDS_REVIEW behavior. Prioritize queue recovery over bounded background
  physical audit. Add real TLS lost-ACK injection and negative attachment tests.

## v0.7.0 — 2026-10-23 — Phase 2A Windows metadata consensus accepted

- Add pinned official HashiCorp Raft/Bolt qualification and a development Go
  sidecar: durable integrity/quarantine policy, static voters,
  authenticated peer RPC, deterministic prepared-projection FSM/receipts,
  snapshots, quorum Barrier reads, local authenticated IPC and shutdown.
- Add opt-in `controller-run --consensus-config` with deterministic Catalog
  DECLARE/POLICY preparation, immutable intent-bound receipts, atomic projection/
  applied checkpoint/receipt transactions, stale follower reads and quorum Barrier
  strong reads. Exact metadata attachment and explicit empty-voter seed imports
  preserve existing history; raw node/admin secrets/jobs/grants are not replicated.
- Persist writer guards across restarts; deny old Catalog/registry/grant/job paths,
  old transfer authorization and single-writer fallback. Preserve existing RUNNING
  jobs/objects without activating physical transfers under a newly elected voter.
- Validate snapshots/log coverage and incomplete vote writes; require an external
  enrollment witness and refuse state-loss reset/re-init. Fix Android backend
  compilation with official bbolt v1.4.3; build Windows AMD64 and Android ARM64
  artifacts outside source. Android runtime, dynamic membership/rebuild and
  Controller/storage automatic failover remain disabled.
- Preserve historical PySyncObj 1 PASS / 5 FAIL and the original qualification
  tool byte-for-byte in Git. New Go tests and actual Python/Go/TLS fault integration
  pass; full regression/publication results are in PHASE2A-ACCEPTANCE.md. No
  phone/M51/production access, main merge, force push or Phase 2B work.
- Final Codex checks: all 15 consensus scenarios PASS; 8 Go tests PASS (12 stable
  state subcases), 87.679 seconds; full Python 95 tests OK (3 POSIX installer
  skips), 92 PASS / 0 FAIL / 0 ERROR, 772.597 seconds. go vet, go mod verify,
  Windows/Android builds, AST/format checks PASS. Publication is on the existing
  WIP branch only; no production release/deployment or Android execution.
- Keep Go source/module files LF on Windows checkouts without changing global
  Git configuration; inspect all tracked/staged content before WIP publication.

## Historical WIP — 2026-10-23 — Phase 2A PySyncObj qualification rejected
- Keep runtime v0.6.0/base b645e539f737c461aaa112a51f6627ef0da80d92; v0.7.0 is not released and no Raft feature/schema/dependency is enabled.
- Add standalone tools/qualify_pysyncobj.py: explicit download/offline artifact, pinned official 0.3.17 SHA-256, temporary source/state only, no package installation/listener. Nonzero exit preserves rejected/inconclusive qualification.
- Reproduce second same-term vote after missing/corrupt upstream metadata; record ordinary restart success, synchronization-call gaps and default address-claim authentication failure. Six probes: 1 PASS / 5 FAIL, not a consensus acceptance result.
- Document engine alternatives and current Catalog write/authority classification, pending deterministic apply/read barrier/snapshot/fencing contracts and all fifteen unexecuted acceptance gates in PHASE2A-ACCEPTANCE.md. Stop before a homegrown engine per task section 3; integration choice remains pending.
- Fresh Codex Windows regression: 92 tests OK (skipped=3 POSIX installer), 89 PASS / 0 FAIL / 0 ERROR in 106.154 seconds. Existing asc/ and tests/ unchanged. No v0.7 commit/push, phone/production/M51 access or system installation.

## v0.6.0 — 2026-10-23 — Phase 1.2B Distributed Storage & Global Catalog
- Add registry schema 4 transactionally from 0/2/3, preserving lifecycle identities/tokens/codes/grants and unchanged local manifest 1/object bytes. Add global immutable versions, replica evidence, policy, persistent epoch/revision/digest-chained history and explicit node/domain/volume approvals.
- Add consistent bounded snapshots/deltas and atomic read-only metadata cache schema 1. Validate cluster/epoch/order/gaps/duplicates/digests/rollback and same-checkpoint materialization; compacted history resyncs safely. Offline caches remain lookup-only.
- Add measured quota/reserve/read-write/domain-aware placement for single/replicated_2/replicated_3. Separate desired/verified/available counts; unknown load/stability stays null; protected/stale/unreadable/full targets are excluded.
- Add durable UPLOAD/COPY jobs, idempotent session/object checkpoints, lease/run-token/generation fencing, backoff, timeout, explicit retry and owned background worker. No source/target data is deleted after failure or restart.
- Add expiring exact file/job/resource grants separate from node/admin credentials; preserve pinned HTTPS and legacy whole-volume compatibility. Controller independently hashes streamed served bytes before publishing a replica.
- Reuse Phase 1.2A Engine for bounded Controller-relayed copies and verified download fallback. Add scoped status/inventory, rotating persistent reconciliation cursors and bounded physical proof/report budgets. Keep unknown v0.5 files/orphans/suspect/last copies, with no automatic import or object GC.
- Add /catalog/v1 API and owner CLI for upload/download/catalog/replicas/policy/jobs/reconcile/node approval; Agent heartbeat imports approved metadata and records sync state. Metadata-only nodes need no fabricated storage endpoint.
- Fail closed on missing schema-4 catalog/epoch authority instead of recreating it; require reviewed backup restore.
- Fix replay fingerprint after policy changes, volume-level source eligibility and same-revision no-op timestamp consistency. Add bounded operation timeouts while retaining the original 12-second default for prior transport calls.
- Acceptance: Codex Windows full 92 tests OK (skipped=3 POSIX installer), 89 PASS / 0 FAIL / 0 ERROR; all distributed/TLS tests ran. Three actual pinned loopback Agent endpoints plus Controller cover independent simulated copies, metadata, outages/fallback, corruption, mid-stream loss, lost ACK, Controller restart, scope/revoke, quota and CLI.
- No Raft/election/automatic Controller failover, Dashboard/mobile/cloud/SAF, Android/physical power-cut or production readiness. No M51/real-phone/production data access or environment installation.


## v0.5.0 — 2026-10-23 — Phase 1.2A Storage Foundation
- Added opt-in approved local volumes, stable marker/root identity, Android internal/Termux-SD candidate discovery and a filesystem adapter seam for future SAF. Reject traversal, symlinks/reparse junctions and hardlinked bodies; missing telemetry stays null.
- Added private node manifest schema 1, independent from registry; immutable UUID object paths, streaming session/staging/upload/size+SHA checks/exclusive final copy/commit/download/list/verify. Interrupted writes restart full-body only; ambiguous copies are preserved, not implicitly published.
- Added real quota/free-space reserve, pending double-copy reservations and retained/orphan allocation accounting; bounded chunks/rate/concurrency, upload deadline, non-destructive restart inventory and explicit dry-run/apply staging expiry.
- Migrated registry 0/2 -> 3 additively for hashed short-lived owner grants bound to node generation; separate user data authority from node heartbeat identity. New /storage/v1 API uses separate pinned Agent HTTPS and pinned Controller introspection on every operation and before commit.
- Integrated opt-in storage runtime/capability heartbeat and CLI setup/status/add-volume/cleanup/owner upload/download. Lifecycle/pinning/re-pair/revoke/protected-device behavior remains covered.
- Acceptance: Codex Windows final 61 tests OK (skipped=3 POSIX installer), 58 PASS / 0 FAIL / 0 ERROR; three-node HTTPS simulation passed.
- Added isolated three-node ZTE V40/Bphone A40/Sony XZ3 real loopback HTTPS simulation plus fault injection, Windows junction/SQLite release and old-schema migration regression. Execution results: see PHASE1-2A-ACCEPTANCE.md.
- Windows regression found during v0.5.0 full suite: bounded discard of small oversized JSON bodies preserves the HTTP 413 rejection instead of racing TLS close/WinError 10053. The same size limit and no-parsing behavior remain enforced.
- Local status reports pending schema-2 migration accurately; streaming owner client closes failed header-setup connections.
- Capability probe reports explicit access-denied/read-only as writable=false instead of unknown, preserving null for unmeasured fsync; Backup is an advisory readable archival-source label only.
- No M51/phone/production access, environment installation, Raft, distributed catalog/durability, backups, PWA or automatic election. Android/SD/power-loss and POSIX installer acceptance remain unverified on this Windows run.


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

## Phase 3B checkpoints (development, not yet accepted)

- 3B.1a/b: versioned strict observation contract and deterministic 0–100 advisory
  score with component explanations, separate probe reliability and confidence.
  UNKNOWN/stale/future inputs never become fabricated measured zeros. No API,
  placement or voter membership changes at this checkpoint.
- 3B.2: explicitly enabled bounded node history with hourly sampling, UTC calendar
  24h/7d/30d views and observed-probe reliability. Preserve history and Phase 3A
  backup state through preparation/takeover; no physical or consensus policy change.
- 3B.3: owner Auto/Preferred/Avoid New Storage/Drain/Protected preferences with
  replay/generation semantics; no automatic movement or physical deletion.
- 3B.4: enabled allocation preferences and confidence-adjusted score ranking after
  original hard capacity/approval/domain gates. Preserve independent replica policy,
  reserved double-copy capacity and reads from drained nodes. Reject future probes.
  Retain per-generation telemetry across re-pair while collecting new samples.
- 3B.5a: checkpoint-bound replica reduction dry-run with explicit retention/job/
  domain/proof holds and zero physical deletion. Add owner node-insights CLI using
  the existing protected-device guard and pinned client; no apply command.
- 3B.5b / v0.10.0 development: real seven-gate node-insights fault matrix passes
  on Linux Cloud using synthetic cohosts. Retain actual product platform/device
  guards; reject null node mutation replay IDs. Full regression/acceptance pending.
