# ASC IMPLEMENTATION & ACCEPTANCE PLAN

## Current acceptance order — owner update, 2026-10-23
- Phase 1.1 Windows is accepted: the owner reports 40 tests OK (skipped=3 POSIX installer).
  This task only updates workflow/docs and publishes v0.4.1; it does not start Phase 1.2A.
- Codex now runs local targeted tests after source changes and the full applicable suite
  before Phase completion, fixing failures or reporting concrete blockers without weakening
  tests. Reuse the owner PASS when source/tests are unchanged, with clear provenance.
  Production servers, real-phone installers, real data and production private state remain forbidden.
- After owner-confirmed Phase 1.1 PASS, develop v1.0 incrementally with explicit versioned
  API/schema/migration/rollback contracts: Storage Engine, distributed metadata and vetted
  Raft, backup/recovery, Dashboard Web/PWA, Quick Join and Installer. Do not implement
  all modules at once, replace the project, or claim unproven safety/HA.
- Multi-node Windows simulation and end-to-end v1.0 acceptance precede real Android
  installation trials. Existing phone commands/checklists are deferred reference only.
- The owner has supplied the required PASS and authorized main publication of v0.4.1;
  review tracked/staged source and preserve remote history. M51 production remains
  source-only and outside every development/test/deployment action.

## Phase 0 — this package
Hardware audit is integrated into automatic on-device profiling instead of requiring user to manually inventory every phone. Working quickstart v0.4 enrolls nodes in a *single-writer LAN development registry*. Its hardware scores are recommendations, not proof of reliability. Actual SD capabilities, sleep behavior and voter eligibility still require observation before enabling durable file storage or Raft.

## Phase 1 — Core vertical slice (single-writer DEVELOPMENT MODE only) — in progress, v0.4 bootstrap available
- Agent identity, registry, durable local manifest, health report; HTTP API behind LAN credentials, strict role/auth; start with one simulated Windows node.
- Controller catalog schema + log/snapshot *interface* using SQLite transactions; avoid exposing multiwriter or automatic failover in Phase 1.
- Pair a second simulated Windows node with one-time enrollment and documented key lifecycle; real phone trials remain deferred until v1.0 Windows end-to-end acceptance.
- Test idempotent registration/restarts, compromised token, missing volume and revoked node.
- Gate: v1 API/contracts and migrations stable before Raft integration.

### Phase 1.1 — secure node lifecycle (0.4.1 Windows accepted)
- Added bounded one-use enrollment, per-IP/global rate budgets, authenticated admin
  list/detail/rename/revoke and targeted token rotation/re-pair preserving node ID.
- Added retry-safe private pending operations, schema 2 additive migration, permanent
  hashed operation routing, revoked-token state and fail-closed unknown-device guard.
- Added foreground duplicate-run locks, dependency reporting without package mutation,
  explicit versioned-source upgrade and pre-upgrade-state rollback instructions.
- Lifecycle suite: owner Windows run is 40 tests OK (skipped=3 POSIX installer cases).
  The publication task changes docs only and reuses that PASS. Linux/Termux installer
  acceptance remains unverified; ZTE/Bphone trials follow the v1.0 Windows end-to-end gate.
- Durable local file manifest, catalog, file jobs, consensus and storage remain absent;
  Phase 1 as a whole is not complete.

## Phase 2 — Consensus and metadata replication
- Select and document a maintained Raft library implementation confirmed on target Termux.
- 3 voting nodes with quorum; non-voter metadata replicas and checkpoint freshness markers.
- Test leader loss, network partition 1/2, stale log candidate, power cycling, membership update, rollback/replay, no false commits and stale-leader fencing.
- Gate: failure injection pass. Otherwise remain read-only/single-writer test mode.

## Phase 3 — Storage/data protection
- Internal storage adapter; separate SD and optional Android SAF bridge.
- Staging/immutable object ids, SHA256, chunks, retries, versioning, replica placement and safe GC.
- Recovery: delete mistake, node loss, card removal, lost metadata snapshot, file corruption.
- Gate: reproducible verified restore of representative 1GB+ file and important metadata backups.

## Phase 4 — User-facing application
- ASC Drive PWA mobile/desktop: files/search/volumes/node view/jobs/restore/health.
- Quick Join installer: true enrollment (not CSV registration), signed config, idempotent install/reinstall, safe rollback.
- WebDAV/desktop sync/android photo background/iOS native only as follow-on capabilities once storage integrity works.

## Phase 5 — Remote access and production readiness
- LAN local discovery independent of cloud.
- Tailscale private connectivity, leader-aware gateway(s) on compatible devices; HTTPS edge optional after threat review.
- M51 production-protected export-only first; load-throttled backups of consistent MariaDB/web artifacts after explicit approval.
- 72h test with phone sleep, Wi-Fi dropout, power loss, failover, monitoring of temperatures. Confirm no hosting impact.

## NO premature promises
- Not always-on despite Doze/ROM limitations until verified on devices.
- No 'any one node can write safely' when original 3-voter quorum absent.
- No durable data safety until independent copies and tested restore exist.
- No marketing capacity as real usable capacity without measuring files and replication factor.
