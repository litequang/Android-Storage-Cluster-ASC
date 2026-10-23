# ASC CODEMAP — v0.7.0 Phase 2A development / v0.6 default storage boundary

Read AGENTS.md first. Default storage mode retains one Controller. Opt-in
metadata consensus uses the Go sidecar described below; it freezes all physical
write/lifecycle/job/grant automation. No automatic Controller/storage failover or
production deployment. Acceptance status: PHASE2A-ACCEPTANCE.md continuation.

| Responsibility | Source / entry points | Dependencies / tests |
|---|---|---|
| Device probe, M51/unknown Android refusal, SD discovery | asc/probe.py; cli._must_not_protected | foundation + lifecycle DeviceSafetyTests |
| Advisory coordination roles, bounded profile/request validation | asc/planner.py; asc/validation.py | lifecycle/foundation; no authority from scores |
| Registry migration 0/2/3 -> 4, lifecycle/re-pair/revoke | asc/store.py: Registry.initialize/connect/join/heartbeat/authenticate_node/revoke | test_lifecycle + test_catalog migration/rollback; preserves old tokens/codes |
| Pinned HTTPS transport, configurable bounded timeout | asc/client.py: connect_pinned/request_json | identity/foundation/lifecycle TLS + distributed scope tests |
| TLS/OpenSSL/private config and runtime locks | asc/identity.py; asc/runtime.py | test_identity, lifecycle locks; no automatic dependency installation |
| Controller lifecycle/HTTPS dispatch and rate budgets | asc/server.py: Server, Handler, serve | /api/v1 plus catalog/http delegation; bounded 32 workers |
| Private local manifest schema 1 (unchanged) | asc/storage/manifest.py | test_storage restart/Windows connection release |
| Approved volumes, identity/no-follow/junction/hardlink safety | asc/storage/volumes.py: VolumeManager.register/inspect, LocalVolume | test_storage; inspect optionally scopes one volume |
| Existing immutable storage engine + added read-only inventory/status interfaces | asc/storage/engine.py: initiate/upload/commit/download/recover unchanged; placement_status/reconciliation_inventory/inventory | test_storage + test_distributed; no object overwrite/GC |
| Node storage API and exact job scope constraints | asc/storage/http.py: StorageHandler._authorize/_route | /storage/v1, pinned Controller introspection; v0.5 whole-volume compatibility; scoped grants never omit constraints successfully |
| Node storage transport/runtime/CLI | asc/storage/client.py, runtime.py, cli.py | original storage commands, actual TLS restart; optional bounded client timeout |
| Catalog canonical data and initial schema | asc/catalog/common.py, schema.py | SHA-256 canonical JSON; registry.initialize installs tables transactionally |
| Sole file/replica/policy write path and event history | asc/catalog/state.py: Catalog.mutate/_event, schedule/file/files | SQLite BEGIN IMMEDIATE; ordered epoch/revision/digest; test_catalog |
| Physical-domain and measured-capacity placement | asc/catalog/placement.py: eligible/readable/candidates | Controller-probed capacities + explicit domain approval; excludes protected/stale/unknown/full volumes |
| Durable jobs, stable checkpoints/backoff/leases | asc/catalog/queue.py: claim/checkpoint/source/recover/failed_attempt/retry | private registry tables; foreground worker lock; test_catalog + crash tests |
| Minimum expiring transfer authority | asc/catalog/grants.py: mint/authorize | Registry.storage_authorize fallback for separate hashed job/read/inspect grants; node generation + lease/resource constraints |
| Controller orchestration, physical proof and repairs | asc/catalog/service.py: CatalogService.register/refresh/upload_plan/run_one/_execute/_proof/reconcile | existing StorageClient/Engine, queue/state; Controller independently hashes streamed served bytes before verification |
| Bounded transfer and verification streams | asc/catalog/transport.py: source_stream, RelayReader | 64 KiB, configured rate, deadline; no full-body RAM buffer |
| Consistent snapshots, deltas and node read-only cache | asc/catalog/metadata.py: MetadataSource, MetadataReplica, synchronize | separate cache schema 1, atomic imports, digest/order/epoch checks and safe snapshot resync |
| Global API | asc/catalog/http.py: handle | /catalog/v1; admin writes, explicitly approved current nodes read/ack metadata only |
| Cluster client and user commands | asc/catalog/client.py: ClusterClient.upload/download; catalog/cli.py: register | owner admin only to Controller; scoped node grants; fallback uses new seekable output |
| Controller/Agent integration | asc/cli.py: controller_run, agent_once/run, main | owned background worker, optional metadata sync; metadata rejection does not masquerade as node repair |
| Catalog invariants and migration fixtures | tests/test_catalog.py | registry-3 preservation, rollback failure, materialized snapshot consistency, domains/quotas, cache and lease tests |
| Distributed acceptance | tests/test_distributed.py: DistributedTests | reuses helpers from test_storage_cluster without duplicate tests; real four-endpoint HTTPS, three isolated temp nodes |
| Previous regression and installers | tests/test_foundation.py, test_identity.py, test_lifecycle.py, test_storage.py, test_storage_cluster.py, test_installer.py | full suite includes all; three POSIX installer tests skip on Windows |
| Version / private state exclusion | asc/__init__.py; .gitignore; .gitattributes | 0.7.0; inspect tracked AND staged contents before publishing |

## Lookup routes

- Global upload: ClusterClient -> Catalog API owner auth -> measured placement -> durable UPLOAD job -> scoped Agent session/commit -> Controller physical byte proof -> Catalog.mutate COMPLETE -> schedule COPY jobs.
- Copy: owned worker -> lease/checkpoint -> pinned source read + target streaming upload -> existing Engine commit -> independent Controller SHA readback -> one catalog transaction. Lost acknowledgement reuses the same job/key/session/object.
- Repair: bounded rotating inventory cursor + at most 8 physical verifications/run -> preserve unknown/suspect data -> mark discrepancies -> queue missing copies. Reports capped at 256 diagnostic entries/category. Failed targets need explicit retry rather than new clones on the same domain.
- Metadata: authenticated Source snapshot/deltas -> cache atomic validation -> node ack. Offline CLI reads last verified cache with stale/read_only markers; no global mutation or election.
- API shapes: NODE_PROTOCOL. Schema/backup/rollback: DATA_MODEL. Trust and limitations: SECURITY. Error recovery: TROUBLESHOOTING. Architecture/Phase 2 boundary: ARCHITECTURE and ADR-029 onward.
- Prior Windows gate: PHASE1-2A-ACCEPTANCE.md (61 tests, 3 POSIX skips). New results and fault matrix: PHASE1-2B-ACCEPTANCE.md; prior PASS is not reused for changed source.

- Catalog schema.validate_existing blocks known-schema-4 missing tables/epoch instead of recreating authority; test_known_schema_four_never_recreates_missing_epoch_authority preserves data/version and requires backup recovery.

## Phase 2A Go continuation — metadata-only integration

Continuation on `wip/phase2a-raft-qualification`: `consensus/go.mod`, `go.sum`
pin HashiCorp Raft v1.8.0 and raft-boltdb/v2 v2.4.2. `consensus/store.go`
owns explicit offline initialization, immutable identity binding, checksummed
stable/log records, incomplete-vote quarantine and preflight before backend open.
Observed live stable/log corruption or storage errors latch quarantine; the
transport/IPC refuse participation and the store refuses writes until restart
with a complete valid restored state. Missing stable keys never use the engine's
fresh-store `not found` default path.
`consensus/qualification_test.go` exercises real upstream voting and damaged
temporary state. Integration is opt-in; Windows metadata-only acceptance passes
95 Python tests (3 POSIX skips), 8 Go tests and all 15 required fault scenarios.
Historical PySyncObj evidence below remains unchanged.

- `consensus/transport.go`: bounded mTLS HTTP Raft RPC transport; exact pinned
  certificate -> configured voter ID/address checks before engine dispatch;
  `transport_test.go` covers known-peer spoofing and unknown/no certificate.
- `consensus/fsm.go`: bounded deterministic prepared-projection CAS, permanent
  request receipts, applied index/term and checksummed Raft snapshots;
  `fsm_test.go` covers CAS, semantic replay, conflicting IDs, snapshot and limits.
- `consensus/cluster_test.go`: three real loopback mTLS voters with durable
  temporary stores, fixed partition/delay/restart/compaction fault schedule.
  Election timers remain upstream randomized wall-clock timers.
- `consensus/node.go`: private config validation, static-membership binding,
  fail-closed startup, authenticated loopback IPC, quorum Barrier reads,
  health/leader discovery and shutdown; `cmd/asc-raft/main.go` is the explicit
  `init|run --config PRIVATE_FILE` development entrypoint. Android runtime is
  deliberately refused; Android ARM64 cross-compilation proves build feasibility only.
- `asc/consensus/client.py`: bounded authenticated loopback IPC; `projection.py`:
  deterministic prepared Catalog document/event validation; `adapter.py`:
  explicit seed import/attachment, atomic projection/checkpoint/receipt apply,
  last-verified stale reads during Go replay and crash hooks;
  `service.py`: metadata-only API (DECLARE/POLICY, strong or stale reads);
  `cli.py`: explicit stopped-state export/import, refusing overwrite/history loss.
- `Registry.connect` supplies the default-deny apply function and write/DDL
  authorizer; attachment installs persistent guards on all authority tables.
  Only the adapter apply connection writes distributed projections. Legacy
  `Catalog.mutate`, JobQueue construction and storage authorization are denied.
  `controller-run --consensus-config` uses the loopback metadata facade, without
  lifecycle refresh/storage worker. Attached state cannot fall back silently.
- `tests/test_consensus.py`: real Go subprocesses + Python/TLS API; existing
  v0.6 metadata/private-job preservation, replay, crash boundaries, unprojected
  snapshot/restart, quorum loss/recovery, authenticated IPC and bypass checks.
- Reproduction/config/bootstrap/rollback: [GO-SIDECAR.md](GO-SIDECAR.md).

- tools/qualify_pysyncobj.py: artifact / unpack_package / qualify / main. Standalone upstream qualification tool; hash-pinned PySyncObj 0.3.17 modules run in TemporaryDirectory. No ASC import, package install, listener or consensus engine integration. Exit 1 reports rejected gates, not suite PASS.
- Historical initial investigation had no engine integration. The Go modules
  above now supply the opt-in metadata mode; the original report remains retained.
- Default-mode mutation routing: service.upload_plan -> state.Catalog.mutate CREATE; http.handle -> POLICY; service._execute -> COMPLETE; service._bad_replica -> REPLICA_STATE; service.reconcile -> REVERIFY. These remain single-writer and are all denied after consensus attachment. Distributed writes use Adapter.submit -> quorum FSM CAS -> Adapter.sync transaction.
- Existing metadata.MetadataSource/MetadataReplica are Catalog export/cache, not Raft snapshot/install. queue/grants/registry are not consensus state.
- Historical investigation and current 15-gate evidence: [PHASE2A-ACCEPTANCE.md](PHASE2A-ACCEPTANCE.md). ADR-037/038 retain PySyncObj rejection; ADR-039 selects Go. Historical v0.6 regression: 92 tests OK, 3 POSIX skips; PySyncObj probe: 1 PASS / 5 FAIL. New source requires fresh full regression.
