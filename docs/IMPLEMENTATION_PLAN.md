# ASC IMPLEMENTATION & ACCEPTANCE PLAN

## Current acceptance order — 2026-10-23
- Baselines: v0.4.1 b74bb594a5bff9ad0926255effed1fd41bbc1647; v0.5.0 f70b095b8f2ec507baaea5a4bdb3d03667209f94.
- Phase 1.2B v0.6.0 is explicitly authorized: Global Catalog, metadata replication, placement, durable copy jobs/reconciliation, local checks and non-force main publication after applicable PASS.
- Codex final Windows gate: 92 tests OK (skipped=3 POSIX installer), 89 PASS / 0 FAIL / 0 ERROR; no previous owner PASS reused. See PHASE1-2B-ACCEPTANCE.md.
- Source remains one development project; end-to-end v1.0 still needs vetted Raft/fencing/recovery, application UX/Quick Join/Installer and hardware acceptance, one separate phase at a time.
- No M51/real-phone/production private-state access, installer execution or system installation/change. Windows simulated nodes precede Android trials.

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
- Phase 1.2B was subsequently authorized and is documented below.

### Phase 1.2B — Distributed Storage & Global Catalog v0.6.0
- Implemented registry-4 Global Catalog with one mutation boundary, physically verified independent copies, measured-domain placement, persistent leased/retried jobs and safe download fallback.
- Added consistent snapshots/ordered history, atomic read-only node caches and bounded reconciliation with persistent inventory cursors. Uncatalogued/suspect/last copies are preserved; no GC or silent import.
- Real pinned HTTPS ZTE V40/Bphone A40/Sony XZ3 simulation covers replicas, metadata, outage/fallback, corruption repair, Controller crash, lost ACK, replay/scope/revoke, quota/protected modes and compatibility.
- Gate PASS on Windows: full 92 tests OK with only 3 POSIX installer skips. Production/Android/SD/power-cut and hardware failure independence remain unverified.
- Phase 2 readiness: clean command/event boundaries and fault-tested vertical slice exist. Must first define deterministic prepared commands, replicated job/authority boundaries, fencing/epochs, membership and recovery under a vetted Raft implementation. Do not infer consensus from these copies/caches.

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

## Historical Phase 2A investigation — before Go continuation

Completed investigation: mandatory document/source review, actual Catalog-write/authority classification, five candidate assessment, reproducible six-gate PySyncObj probe, and fresh v0.6 Windows regression (92 tests OK, 3 POSIX skips). See PHASE2A-ACCEPTANCE.md and ADR-037/038.

Unmodified PySyncObj 0.3.17 fails missing/corrupt vote-state recovery and other sampled persistence/identity gates. No evaluated candidate is yet qualified for the available Windows Python/target Termux architecture. Next choice is an authorized native toolchain/etcd-raft sidecar qualification, or a reviewed pinned PySyncObj fork with durable persistence and authenticated transport. No system tools/dependencies were installed, no consensus algorithm was invented and no runtime migration/version change was made.

Remaining Phase 2A gates: engine/platform acceptance; deterministic commands and atomic applied-index/receipt persistence; comprehensive Catalog bypass protection; quorum strong reads; safe bootstrap/static membership, snapshot/catch-up/restart; per-voter RPC identity; all 15 requested deterministic election/partition/fault cases plus full regressions. Physical-write failover stays disabled until distributed fencing is proved. Commit/publish v0.7 only after those gates pass; Phase 2B and phone trials remain blocked.

## Phase 2A v0.7.0 — Go metadata consensus continuation

Owner authorized Go development tooling and selected HashiCorp first. The new
`consensus/` module and `asc/consensus/` adapter implement static three-voter
metadata consensus, persistent state/quarantine, per-voter mTLS, loopback IPC,
deterministic projection CAS/receipts, atomic Python applied checkpoints,
snapshots/replay, quorum Barrier reads and persistent denial of legacy writers.
No new project, homegrown Raft or PySyncObj fork was created.

Qualification and actual Python/Go/TLS integration PASS all fifteen gates and
extra state-loss/crash/identity/replay/snapshot cases. Phase 2A is accepted for
Windows metadata consensus: 8 Go tests PASS and final Python full suite 95 OK
(3 existing POSIX installer skips, 92 PASS, no FAIL/ERROR). Publication status
lives in PHASE2A-ACCEPTANCE.md and the completion report. Commit/push uses only
the existing WIP branch after secret/staged review, without main merge or force push.

The accepted scope may only be metadata consensus. Registry approvals, private
jobs/grants and physical storage automation are frozen rather than promoted by
metadata election. Android ARM64 cross-build proves feasibility only; no phone,
physical power-cut, Doze/SD, dynamic membership, disaster rebuild or production
acceptance is inferred.

## Phase 2B v0.8.0 — Windows development complete

Controller failover is implemented on the existing WIP branch. The readiness
audit and design for unsafe authority groups are in PHASE2B-ACCEPTANCE.md.
All 20 fault scenarios PASS with separate temporary processes/volumes; the final
full regression is 101 tests OK (98 PASS, 3 POSIX skips), with 9 Go tests and both
Windows/Android ARM64 builds PASS. Original engines and Phase 2A evidence remain
intact. No real-phone/Android runtime or production acceptance is inferred.
