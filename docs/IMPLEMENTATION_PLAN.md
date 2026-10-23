# ASC IMPLEMENTATION & ACCEPTANCE PLAN

## Current acceptance order — 2026-10-23
- Phase 1.1: owner-reported Windows 40 tests OK (3 POSIX installer skips); published baseline b74bb594a5bff9ad0926255effed1fd41bbc1647.
- Phase 1.2A is explicitly authorized: local storage foundation, versioned API/schema, targeted then full local suite, three-node Windows HTTPS fault simulation, documentation and non-force publish after applicable PASS.
- See PHASE1-2A-ACCEPTANCE.md for Codex-run results and remaining gates. No owner PASS is reused for changed source/tests.
- End-to-end v1.0 still requires distributed metadata, vetted Raft/fencing, replication/backup/recovery, Dashboard Web/PWA, Quick Join and Installer acceptance, one phase at a time.
- No Android installation trial before the Windows v1.0 end-to-end gate. No M51, production data/private state, real-phone installer or environment installation/change in this task.

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
  These describe the 1.1 boundary; Phase 1.2A adds local storage below. Phase 1 as a whole is not complete.

### Phase 1.2A — Storage Foundation v0.5.0
- Implemented approved local volumes/medium identity, private local manifest schema 1, bounded streaming and immutable commit/download/integrity/recovery/controlled staging expiry.
- Added distinct owner data grants, registry schema 3 additive migration, pinned Agent API and versioned capability heartbeat; Controller remains single-writer.
- Windows three-node real HTTPS acceptance and fault matrix are in PHASE1-2A-ACCEPTANCE.md. Termux/SAF/Doze/power-cut behavior remains unverified; no distributed durability claim.
- Future Phase 1.2B requires its own explicit request, global metadata/fencing API/schema and migration contracts, recovery/partition acceptance. It is not implemented in this turn.

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

Phase 1.2A local gate: Codex Windows final 61 tests OK (skipped=3 POSIX installer), 58 PASS, 0 FAIL/ERROR. Three-node HTTPS simulation passed. See PHASE1-2A-ACCEPTANCE.md; Android/SAF/power-cut and distributed acceptance remain open.
