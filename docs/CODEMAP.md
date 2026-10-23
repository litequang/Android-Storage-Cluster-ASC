# ASC CODEMAP — v0.6.0 / Phase 1.2B

Read AGENTS.md first. Current runtime: one Controller writes Global Catalog; approved Agents store immutable local objects and verified read-only metadata caches. No Raft, election, automatic Controller failover or production deployment.

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
| Version / private state exclusion | asc/__init__.py; .gitignore; .gitattributes | 0.6.0; inspect tracked AND staged contents before publishing |

## Lookup routes

- Global upload: ClusterClient -> Catalog API owner auth -> measured placement -> durable UPLOAD job -> scoped Agent session/commit -> Controller physical byte proof -> Catalog.mutate COMPLETE -> schedule COPY jobs.
- Copy: owned worker -> lease/checkpoint -> pinned source read + target streaming upload -> existing Engine commit -> independent Controller SHA readback -> one catalog transaction. Lost acknowledgement reuses the same job/key/session/object.
- Repair: bounded rotating inventory cursor + at most 8 physical verifications/run -> preserve unknown/suspect data -> mark discrepancies -> queue missing copies. Reports capped at 256 diagnostic entries/category. Failed targets need explicit retry rather than new clones on the same domain.
- Metadata: authenticated Source snapshot/deltas -> cache atomic validation -> node ack. Offline CLI reads last verified cache with stale/read_only markers; no global mutation or election.
- API shapes: NODE_PROTOCOL. Schema/backup/rollback: DATA_MODEL. Trust and limitations: SECURITY. Error recovery: TROUBLESHOOTING. Architecture/Phase 2 boundary: ARCHITECTURE and ADR-029 onward.
- Prior Windows gate: PHASE1-2A-ACCEPTANCE.md (61 tests, 3 POSIX skips). New results and fault matrix: PHASE1-2B-ACCEPTANCE.md; prior PASS is not reused for changed source.

- Catalog schema.validate_existing blocks known-schema-4 missing tables/epoch instead of recreating authority; test_known_schema_four_never_recreates_missing_epoch_authority preserves data/version and requires backup recovery.
