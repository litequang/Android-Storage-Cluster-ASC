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
- 3B.5b / v0.10.0: Linux Cloud simulation accepted. Fresh full Python 152 tests
  OK (152 PASS / 0 SKIP), 369.626s, all 39 fault gates PASS. Uncached Go
  11 tests/vet/module verify and Linux/Windows/Android builds PASS. Retain actual
  product platform/device guards; reject null node mutation replay IDs. Exact
  evidence/remaining platform limits: PHASE3B-ACCEPTANCE.md.

## Phase 3C — Linux synthetic qualification accepted

- 3C.1: explicit bounded replication extension, owner replay-safe policy count
  transitions 1/2/3 and reconciliation using existing independent COPY/proof jobs.
  Shortages remain explicit; lowering policy preserves every replica and byte.
- 3C.2a: durable Drain/Rebalance intents, stable independent COPY jobs and explicit
  no-target reports; retain source records/bytes until separate proof/retirement.
- 3C.2b: current-term fresh survivor checksum/domain proofs before logical source
  retirement; preserve bytes/history/jobs and permanently fence retired object IDs.
  Ready moves advance through the existing Leader worker without physical GC.
- 3C.3a: read-only full-reference GC plan, explicit held/reclaimable estimates and
  checkpoint/graph/plan SHA; prevent retirement/receipt/history fence erasure across
  Runtime commits. Native/unknown data stays held; no physical GC execution.
- 3C.3b: explicit audited COMPLETED-job pointer release; retain identity/history,
  upload/completion replay and immutable digests, reject unaudited removal or job
  resurrection. History and backup pointers continue to block physical GC.
- 3C.4a: durable fresh-proof GC plans, exact SHA confirmation and current-term
  quorum reservation with default absent synthetic-only capability; no physical
  executor. Preserve immutable reservations/plans and reset permits on takeover.
- 3C.4b: isolated fresh Linux temporary-volume executor, exact-body checksum/identity
  and final callback gate, durable bounded journal and crash/lost-ACK restart
  recovery. No network activation yet; ordinary Agent/real devices remain locked.

- 3C.4c development: connect confirmed synthetic GC jobs to exact-object, fresh-proof, actual-term quorum introspection and explicit owner execution; preserve hash-only permits, takeover fencing and journal replay. Default Agent/real-device physical GC remains locked. Windows targeted qualification: 85 tests OK (74 PASS / 11 Linux-only physical skips), plus actual three-voter/TLS GC authorization fault test PASS. Linux physical network execution and final Phase 3C acceptance remain pending.

- 3C.5a regression fixture repair: Windows synthetic metadata subprocess now uses the same explicit fake profile as Cloud, so missing consensus config tests the actual no-fallback guard rather than an unrelated unknown-device refusal. Product device guards are unchanged.

- 3C.5b safety review: fence survivor endpoint/reference changes during GC proof with an exact ephemeral graph SHA before final CAS; stale evidence is refused without changing schema or device locks.

- Preserve a fixed safe GC error-label whitelist for explicit fresh-plan/proof retries; unknown error content stays redacted. Fault simulation now exercises legitimate stale-plan retry and client-level lost-ACK recovery without weakening confirmation or byte assertions.

- 3C.5c Windows reporting: hardened source 895e5bb passes full 203 Python tests (189 PASS / 14 platform skips), all prior/new applicable Windows faults, Go 11 uncached tests/vet/module verify and builds. Phase 3C remains NOT ACCEPTED until separately executed Linux physical network GC faults pass; no real-device activation.

- Linux 3C.5 continuation from 8d5cd7d: bound reuse of successful structural Catalog
  validation to two exact immutable JSON byte strings; preserve native types,
  mutation/history checks and all current authority/physical-proof gates. Add
  synthetic-only paused TLS/crash/journal/replay/reference fault qualification;
  runtime GC/device locks and destructive freshness budgets remain unchanged.

- 3C.5e final Linux qualification on frozen source 8b679bc: **208 Python PASS,
  0 SKIP/FAIL/ERROR, 1336.964s**; all 39 prior faults, 3 replication, 3 actual
  GC authorization and 8 Linux physical groups PASS. Fresh Go 11 uncached tests,
  vet/module verification and Linux/Windows/Android builds PASS; cross-builds are
  compile-only. Ordinary/runtime/real-device GC remains locked, with no production,
  Android, hardware power-cut, Phase 3D or Dashboard qualification/deployment.
  Source version remains 0.10.0 development; no release tag or installer change.

## Phase 3D.1a — external local archive engine (development)

- Add separate versioned private POSIX external store/all-version manifest and
  bounded streaming SHA/fsync/readback transaction, durable same-ID object resume,
  immutable complete bundles and source final authority interface. No live source
  schema/Engine/GC/membership change; actual quorum/TLS integration follows1b.
- Actual filesystem target35PASS0skip incl11 new external cases; full qualification
  pending. No Windows/Android/production/writable DR claim; see PHASE3D documents.

-3D.1b: owner/quorum-gated exact external capture, retained-version read plans and
  final authority check; PinnedSource reuses scoped TLS/hash streams. Real3-voter
  target12PASS0skip incl exact old/new bytes/lifecycle/owner/pinning. Full fault
  acceptance still pending; no writer recovery/Android authorization.

-3D.2: add anchored offline full-byte/metadata verification with measured coverage,
  stale index floor and UNKNOWN semantics; inventory/retention-only preview and
  private guarded Linux CLI.37 unique targeted PASS0skip; full acceptance pending.

-3D.3: isolated read-only recovery staging and stage-verify, full anchor/schema/
  byte checks before and after copy, exact IDs/history/intent-preserving resume,
  newer-history floor and nonempty active-state refusal.23 targeted PASS0skip.
  Writer/credential/quorum recovery deliberately unavailable, full faults pending.

-3D.4a: provider logical interface, strict manifest/completion native JSON/ID
  validation, bounded filesystem inventory and nonreflecting CLI errors; actual
  nine-group Raft/TLS/process/IO fault matrix plus exact baseline schema and real
  recovery-child crash/resume. Final54 targeted/Go11/vet/modules/builds PASS; full
  fresh238 regression pending. No Android/Windows runtime/full writer DR claim.

-3D.4b final fresh Linux qualification on50df5d7:238 Python PASS0SKIP0FAIL,
  1403.864s;54 targeted/all9 new fault groups and all retained Core faults PASS.
  Go11/vet/modules/Linux build PASS; Windows/Android compile-only. External
  backup/anchored verify/isolated read-only staging accepted for Linux synthetic;
  Phase3D PARTIALLY COMPLETE, full writable DR NOT ACCEPTED/BLOCKED.


<!-- Reviewed Demo c9c2660 historical extension; current Phase4 status is in PHASE4-PROGRESS. -->
## Android Demo Alpha — separate track (not source-ready yet)

- DEMO.0: audit/reuse plan and upgrade contract on feature/android-demo-alpha from
  acea2ae, with account-independent progress. No runtime code/device/GC unlock;
  preserve Core branch, source, tests and historical qualification.

### Demo Track DEMO.1 — installer preview
Separate guarded Android preflight, immutable source-only package with per-file and
archive SHA-256, read-only dry-run and state-preserving rerun. Stable launcher verifies
before import and disables bytecode. Linux synthetic qualification only; no LAN
cluster/runtime/upgrade readiness yet. Existing Core installer/guards unchanged.

### Demo Track DEMO.2 — restricted single-writer LAN CLI
Dedicated marked state and exact read-only schema checks; separate Controller/node
homes permit Controller phone storage. Explicit private IPv4 TLS binds, Core durable
enrollment and owner domain approval, measured two-copy upload, SHA verification,
replica reporting and download fallback reuse existing engines. Controller loss
fails closed; missing volume/domain/capacity/pin/unknown schema/attached state and
M51/unknown runtime guards tested on Linux synthetic. No Android runtime qualification,
upgrade readiness, Raft, reduction, GC or Dashboard claim.

### Demo Track DEMO.3a — stopped upgrade, backup and identity preservation
Version 0.3.0-alpha adds prefix/state binding, complete verified private backup
including external approved volumes/empty directories, exact-format compatibility,
immutable staging, journaled source activation/code rollback and explicit interrupted
activation recovery. Stable IDs/keys/pins/bytes retained; no schema/data restore or
background updater. Diagnostic output uses a status whitelist. Installed-source
tests caught/fixed prefix ancestry and node re-exec issues; compatibility permits
Core's existing catalog inventory cursor while rejecting consensus/advanced state.
Final source-ready status waits for fresh full qualification and checksum package.

### Demo Track DEMO.3a.1 — refuse linked coordination files before writes
Final review reproduced a symlinked lifecycle lock changing an outside empty
synthetic file before backup refusal. New Demo-only no-follow/regular/single-link/
inode validation precedes any lock marker write; internal Core lock preflight and
symlink/hardlink regression added. Core unchanged. Initial 221-case full PASS is
retained as provenance; a fresh hardened full run is required. Installer preview
retired from recommended installs; final candidate includes blank Android pilot.

### Demo Track DEMO.3b — 0.3.0 source-ready, Linux synthetic only
Final hardened fresh full 222 Python PASS/0 skips, 14 targeted PASS, all eight Linux
physical gates and unchanged-source 11 uncached Go/vet/modules/builds PASS. Qualified
83-member source-only QuickStart archive + SHA, owner README/pilot and full handoff
published on separate Demo branch. No Android/runtime/real SD/production acceptance,
APK, GC/Raft enablement, Phase 3D or Dashboard. Core source/tests and WIP preserved.

### DEMO.4a — optional trusted-HTTPS owner-session backend
Separate browser CA/IP SAN preserving Core/node TLS, one-use owner login/session/CSRF,
read-only node/volume/file/replica views with UNKNOWN/domain safeguards, bounded
private upload/download spool through existing Catalog/client/SHA/fallback. CLI-only
node approval, no second Catalog/schema migration, policy/delete/GC/public access.
35 targeted tests PASS on Linux synthetic; frontend/new package/Android not accepted.

## DEMO.4b — Dashboard Lite frontend (2026-10-25)
Vietnamese mobile-first overview, node/approved-volume details, file upload and SHA-verified browser download, per-replica status and honest degraded/UNKNOWN states. Core jobs/idempotency and fallback reused. Local packaged assets, no CDN/token-in-JS/delete/approval controls. Actual Chromium trusted-CA integration passes with two synthetic phone processes, first node stopped before download, XSS literal filename and mobile/offline gates. Android runtime remains NOT TESTED; 0.4.0 package awaits 4c qualification.

## DEMO.4c — 0.4.0-alpha compatible QuickStart candidate (2026-10-25)
Release capability dashboard-lite; unchanged base formats. QuickStart now covers separate trusted HTTPS browser listener, owner one-use login and stopped 0.3.0 upgrade/code rollback. Exact published0.3 package upgrade/new-state rollback test passes with preserved identities, browser CA and old/new bytes; final full regression/public artifact qualification is recorded separately in DEMO4-ACCEPTANCE. Android/runtime/CA-install UX remains NOT TESTED.

## DEMO.4c — 0.4.0 Linux source-ready qualification (2026-10-25)
Final fresh230 Python PASS0skip incl all8 physical fault gates;11 uncached Go tests,
vet/modules/Linux build/Android cross-build PASS.22 targeted and3 exact-archive
installer checks PASS. Source-only92-file QuickStart includes Dashboard assets,
manual public-CA trust/owner login,0.3 upgrade and code-only rollback instructions.
Unchanged base formats/Core guards/branch; final public SHA and receipt recorded
in DEMO4-ACCEPTANCE/DEMO-TRACK-PROGRESS. Android runtime remains NOT TESTED.

## DEMO.4d.1 — Android-compatible approved-volume anchor (2026-10-25)
Reproduced old write_denied when only filesystem-root read-open is denied. POSIX adapter now opens only approved root, binds medium/marker/descriptors and checks ancestor/folder replacements before/after no-follow child IO. Capacity/inventory/fsync/cleanup use pinned descriptors. Probe success is reported only after actual write/read/SHA/fsync/owned cleanup; collision/changed/linked files preserved. Windows handle adapter/base formats/IDs unchanged; shared storage files changed on Demo branch only.61 targeted storage/security/sandbox/TLS tests PASS0skip17.030s; no Android/runtime or0.4.1 release claim yet.

## DEMO.4d.2 — actual root-denied Demo runtime / local volume status
Test-only root denial now exercises real Controller+Dashboard/two-node TLS runtime with measured probes, two independent synthetic replicas, SHA/fallback/offline/restart. `ascdemo storage-status` reuses stopped-node Engine probe with existing device/state/ownership guards; no initialization or network API added. Normal Dashboard/Chromium regression is rerun. Linux synthetic only;0.4.1 release/full qualification follows4d.3.

## DEMO.4d.3 —0.4.1 compatibility/package candidate
0.4.1-alpha adds Android volume anchor capability, unchanged schemas/identities and all Dashboard0.4 assets. Exact published0.3/0.4 direct-upgrade tests run backup/verify/stage/preflight/upgrade/new runtime under root-open denial; preserve credentials/pins/media/browser CA and old/new files. Code-only rollback uses NEW backup, honestly restores old Android defect; baseline Linux checks preserved files. Dedicated existing-ZTE copyable guide is packaged. Final fresh full/Go/fault/public SHA gates remain in DEMO4D-ACCEPTANCE; Android not qualified.

## DEMO.4d.3b —0.4.1 Linux synthetic accepted (2026-10-25)
Fresh246 Python PASS0skip/all8 Linux physical gates;11 uncached Go/vet/modules/
Linux+Android cross-build PASS,38 targeted +3 exact-archive installer PASS.93-member
source-only QuickStart0.4.1 keeps Dashboard and fixes approved-volume access without
opening '/', preserves formats/IDs/media; exact03/04 direct upgrades and new-state
code rollback proved with real TLS/bytes. Dedicated existing-ZTE copyable guide
included. Old packages unchanged; SHA/publication receipt in progress/acceptance.
Android0.4.1 NOT TESTED; downgrade still returns original Android defect. No Core
WIP push/Raft/GC/failover/production activation or phone access.

## Phase4.0b.1 — selective integration (not Android accepted)
Port reviewed Demo0.4.1 source/assets/installer/upgrade/tests/historical public
archives plus approved-root Android volume patch into Core3D feature baseline.
Keep Core3D external backup/recovery/guards, no merge/schema/state change.95
combined targeted PASS0skip0fail incl actual browser, exact historical upgrade,
all9 external faults and local GC/storage checks. Full new integration pending.

## Phase4.0b.2a — source candidate0.4.2-dev
Owner-authenticated session-bound pairing API reuses existing Core one-use grants.
Guided local quick-join validates pin/cluster/mode, preserves pending/identity,
refuses recovery staging and never approves storage.31 targeted Linux synthetic
PASS; UI and exact candidate upgrade/full qualification pending. Historical04.1
archive fixtures/assertions preserved. No public Android release/acceptance.

## Phase4.0b.2b — Quick Join owner page
Vietnamese mobile Dashboard reuses existing HTTPS owner session/backend, shows
full lifecycle pin/cluster and separate registration/storage permission. No
browser node credentials or auto-approval. Codes clear on use/non-waiting state,
offline/logout/pagehide; stale async results cannot repaint them. Test-only delayed
response preserves real Chromium certificate validation; no TLS-error bypass.

## Phase4.0c.1 — compatibility candidate freeze
Exact published04.1 ->source candidate0.4.2-dev upgrade and compatible code-only
rollback over NEW state, pending enrollment both directions PASS with real TLS/
bytes.13 targeted +1 exact artifact PASS;11 fresh Go/vet/modules/builds PASS.
No formats/schema change.106-file synthetic source candidate/SHA under candidates;
no public Android release. Full287 Python and original faults still pending.

## Phase 4.0 — Linux synthetic foundation accepted
Selective Core-first Demo reuse and Quick Join owner UI/local durable adapter
qualified on frozen4d1758d:287 fresh Python PASS0skip/fail/all Core3A–3D faults,
11 fresh Go/vet/modules/builds PASS. Exact published04.1 candidate upgrade and
NEW-state code-only rollback/pending resume qualified. Source candidate0.4.2-dev
only; no public Android release, APK/Core quorum UI/state migration or writable DR.
See PHASE4-ACCEPTANCE for full evidence and initial interrupted run disclosure.

## Phase4.1a — architecture and bounded IPC contract
Separate feature from verified Phase4.0; strict versioned local app IPC contract,
threat model/Core read-only observer/native app boundaries. No active bridge yet.
Historical exact Phase4.0 archive regression stays pinned; new source0.4.3-dev,
unchanged base formats/old packages, not Android release. Qualification pending.

## Phase4.1b.1 — authenticated local engine facade
Private same-UID UDS/app scopes, bounded FULL retries and read-only state/approved
volume status reuse existing services. Actual Quick Join via existing pinned
worker, lost ACK/restart/identity and pending-owner-approval reporting; no auto init,
new Catalog/Engine/approval/lifecycle or browser/Android access. Qualification in
Phase4.1 progress; base formats and old candidate archives unchanged.

## Phase4.1b.2 — controlled Node lifecycle and crash resume
Only owned configured Demo Node lifecycle, retained supervisor/PDEATHSIG fence,
exact known socket crash recovery and verified installed launcher bridge commands.
Actual lost enrollment response +bridge SIGKILL retains same Core operation/Node.
19 targeted PASS0skip/fail; no Android acceptance, Controller/Raft start or PID kill.

## Phase4.1c.1 — read-only Core and passive recovery observation
Owner GET-only sanitized Core endpoint, actual Barrier/identity/term evidence,
policy1/2/3 counts/jobs/historical verified backup and explicit UNKNOWN. Pinned
three-controller collector and full-byte passive-stage view, always no writer.
28 targeted PASS0skip/fail including actual partition/loss/heal/TLS and retained
Core external/metadata/GC gates. HTTPS shared Dashboard UI still c.2 pending.

## Phase4.1c.2 — shared Core read-only HTTPS/browser gateway
Reuses owner sessions, TLS generator/security handler and responsive Demo assets
with explicit mode isolation and unique cookie scope. Core policy3/Controller/
quorum/jobs/historical backup views; no storage/runtime/authority mutation. Real
Chromium transport-partition/reconnect and existing Demo browser regression gates.

## Phase4.1d — exact compatibility candidate / app contract qualification
Source-only0.4.3-dev adds public operator/bridge/Core/native contracts, unchanged
base formats, immutable original packages and separate private control exclusions.
Exact0.4.2 upgrade/new-state code rollback test includes installed bridge/identity
preservation and pending both directions. Recovery observer binds expected epoch,
wrong epoch remains UNKNOWN. Android runtime/APK/migration and writable DR blocked.

## Phase4.1 — Linux synthetic foundation accepted
Frozen0a3ea839217156b69209a073f5d836ee1db4452b,311 fresh Python PASS0skip/fail incl all original faults,
11 uncached Go/vet/modules/builds PASS. Authenticated local bridge/owned lifecycle,
existing durable Quick Join and shared read-only Core Dashboard qualified; exact
0.4.2->0.4.3 source candidate upgrade/NEW-state code rollback. Candidate only,
Android/native/migration not tested, writable disaster recovery still BLOCKED.
