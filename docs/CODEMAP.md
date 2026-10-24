# ASC CODEMAP — v0.10.0 Phase 3B Cloud simulation / preserved default boundaries

## Phase 2B — Windows development qualified

- `asc/failover/state.py`: runtime schema-2 envelope, authority-table allowlist,
  bounded validation, disposable in-memory SQL preparation and takeover fencing.
- `asc/failover/runtime.py`: Runtime.view/commit/ensure_ready/operation, durable
  verified private cache and RuntimeRegistry.connect; existing business SQL is
  prepared in memory and acknowledged only after Go commits. Original Phase 2A
  registry guards stay in place. No physical bytes/keys are in this projection.
- `asc/failover/service.py`: leader-only CatalogService worker, Recovery/Follower/
  Leader transitions, RuntimeHandler discovery/stale reads/Storage introspection.
  RuntimeHandler._json preserves exact MetadataSource snapshot/delta envelopes;
  runtime checkpoint labels must not alter their schema/digest. Failover tests
  import real pinned metadata before/after takeover and snapshot/restart.
  The repaired fake cohost restarts with retained Go state and waits for current
  quorum readiness before reapproval; Python-only failures remain separate cases.
- `asc/failover/discovery.py`: pinned endpoint allowlist, TTL and bounded retries;
  catalog.client, cli.agent_once, catalog.metadata.synchronize and storage.http
  opt in only through explicit `controllers` configuration.
- `asc/failover/cli.py`: explicit stopped development upgrade and separate opt-in
  run entrypoint. No automatic migration, installation or production execution.
- `consensus/fsm.go`: schema-2 commands require actual apply-term authority;
  `node.go`: local authenticated Python liveness watchdog and owner-ID check.
- Phase 2B state audit, final 101-test regression, 20/20 fault matrix and limits:
  PHASE2B-ACCEPTANCE.md. Qualification is Windows development only.
- `tests/test_failover.py`: actual three-Go/three-Python cohost processes, fake
  independent volumes, TLS, upload/copy/reconnect and recovery qualification.
  `consensus/runtime_fixture_test.go` supplies authenticated bounded partition
  controls only in a Go test executable; they are absent from `asc-raft` builds.
  `fsm_test.go: TestRuntimeAuthorityUsesActualCommittedTerm` checks stale/high
  term, downgrade and snapshot authority retention. Existing tests remain intact.
- Runtime schema validation supplies a constant disposable initial epoch through
  Registry.initialize/schema.migrate; default initialization/migrations retain
  their original call contract and never replace an existing persistent epoch.
- `failover.state.verify_attachment` reconstructs the initial full projection
  against the permanent upgrade receipt. A conflicting private registry fails
  closed; only the exact primary or an exact fresh metadata follower can attach.
- `storage.engine.commit(..., resume_verified=True)` is used only by distributed
  Storage HTTP after fresh scoped authority; both retained bodies must rehash to
  the same known job/session. Legacy commits keep their previous contract.
  `catalog.service._execute` requests this narrow recovery for NEEDS_REVIEW only
  in failover mode. No Engine replacement or object deletion is introduced.
- Runtime worker prioritizes pending jobs and bounds background reconcile to one
  physical verification per turn. `tests/test_failover.LostAckProxy` drops an
  actual successful TLS commit reply; it is test code, never a product endpoint.
  Replay checks inspect job-scoped sessions/manifests and immutable bytes on all
  volumes, plus the single original UPLOAD job; unrelated copies may continue.

Read AGENTS.md first. Default storage mode retains one Controller. The older
metadata-only mode below freezes physical/lifecycle/job/grant automation. Separate
Phase 2B runtime above adds Controller/storage coordination failover with its own
qualification in PHASE2B-ACCEPTANCE.md. No production/Android deployment. Historical
metadata acceptance remains in PHASE2A-ACCEPTANCE.md.

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
| Version / private state exclusion | asc/__init__.py; .gitignore; .gitattributes | 0.8.0 development; inspect tracked AND staged contents before publishing |

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

## Phase 3A extension ? Windows development accepted

- `asc/backup/state.py`: bounded backup schema 1 validation, committed-view
  manifest capture, version heads/pins and takeover lease invalidation.
- `asc/failover/state.py`: optional backup extension carried through existing
  schema-2 export/install/validation and takeover. Original base SQL is unchanged.
- `asc/backup/service.py`: Backups._edit idempotent term-bound changes,
  snapshot/restore/delete/policy/retention, durable schedules/claims/checkpoints,
  physical checksum/domain verification and same-key restore upload recovery.
- `asc/backup/http.py`: owner-only `/catalog/v1/backup` routes through RuntimeHandler.
  `failover.Service` owns the scheduler and denies non-LIVE normal downloads.
- `tests/test_backup.py`: bounded-projection/retention/idempotency unit tests plus
  reused real three-voter/TLS Windows fixture, without duplicating Phase 2B tests.
- `asc/backup/catalog.py`: live namespace displays only latest LIVE heads after
  explicit enable; per-version lookup/history and public metadata remain intact.
- `asc/backup/cli.py`: explicit backup-* owner commands with required retry IDs;
  `catalog.cli.register` shares its existing protected-device/pinned client guard.
  Restore version reservations reject conflicting uploads; worker runs retention
  each minute using committed pins and advances due schedules atomically.
- Backup projection validation checks proof/cursor coverage, independent domain
  counts and restored target identity before accepting completion. Resume can
  verify an already completed target without requiring the original source again.
- `consensus/fsm_test.go:TestBackupProjectionKeepsActualTermFencingAndSnapshotBytes`
  checks stale backup deletion rejection and exact extension snapshot retention.
- Unit acceptance additionally rejects incomplete/duplicate-domain backup proof,
  stale checkpoint completion, invalid retention bounds and projection exhaustion;
  covers empty snapshots, batch restore replay and active-restore trash pins.
- Windows acceptance also drops a real successful restore commit ACK over pinned
  TLS, crashes the Controller, and checks one stable job/session/object/version
  after takeover. Snapshot/restart acceptance requires a real successful Go snapshot.
- Scheduler records/defer retries for an unverified head or exhausted map bound
  without starving existing backup/restore jobs. `asc/__init__.py`: 0.9.0 development.
- Base-commit packaging repair: `consensus/cmd/asc-raft/main.go` restores the
  documented thin init/run launcher using ReadConfig/Config.Initialize/Start/Close;
  `main_test.go` rejects malformed invocations. `.gitignore` now scopes Unix binary
  names to output locations so the command source directory is publishable.
- Retention additionally protects the latest historically VERIFIED version while
  a newer upload is incomplete; request IDs are hashed for bounded Go receipt keys.
  Fault acceptance corrupts every source and requires bounded FAILED with no proof.

- Final fresh gate: 122 Python tests OK (119 PASS / 3 POSIX skips), 12/12
  Phase 3A + 20/20 Phase 2B faults; Go/vet/build PASS. Exact reproduction,
  changed paths, bounded guarantees and rollback: PHASE3A-ACCEPTANCE.md.

## Phase 3B checkpoints

- `asc/nodes/scoring.py`: version-1 observation contract, bounded finite values,
  explicit UNKNOWN/provenance and published weights; `tests/test_nodes.py` tests
  malformed/boundary inputs. No score consumer or placement change in 3B.1a.
- 3B.1b `scoring.score`: pure freshness/normalization/weighted mean and confidence;
  ScoreEngineTests cover partial coverage, known zero, extremes and monotonicity.
- 3B.1c `nodes.view.observations/scores` and RuntimeHandler nodes/scores route:
  owner-only local/strong read-only score view; no live refresh or placement write.
- 3B.2 `nodes.history`: strict bounded hourly/daily aggregation, gap-aware windows;
  `nodes.service.Insights`: explicit enable, replay-safe CAS and post-refresh capture.
  `failover.state` preserves/validates extension across SQL preparation/takeover;
  RuntimeHandler history route serves owner local/strong views. Telemetry tests
  cover retention, missing/failure samples, malformed state and lost reply replay.
- 3B.3 `nodes.preferences.effective`: safe defaults/generation handling;
  `Insights.preference` + owner POST route: durable idempotent preferences, no
  movement/deletion. PreferenceTests cover modes, replay/conflict and generations.
- 3B.4 `catalog.placement.candidates`: eligibility/capacity/domain first, enabled
  preference + confidence-adjusted score ranking; legacy ordering without enable.
  `nodes.history` preserves per-bucket generation during re-pair and allows new
  measurements without attributing earlier failures to the new credential.
  SmartPlacementTests/TLSTests cover actual byte uploads/copies, drained nodes,
  independent policy domains, reservations, deterministic ordering and hard gates.
- Linux fixture portability: `test_distributed` CLI simulated profile explicitly
  allows installation; actual CLI M51/unknown-device guard remains unchanged.
- 3B.5a `nodes.reduction.preview`: pure checkpoint-bound policy/domain/pin/job/proof
  checks with no IO/apply/deletion; RuntimeHandler owner local/strong GET route.
  ReductionPreviewTests prove nonmutation and conservative stale/pin/domain holds.
  `nodes.cli.register`: shared pinned owner client for enable/scores/history/
  preferences/reduction preview, required mutation replay IDs; no apply command.
- 3B.5b `tests/test_node_faults.py`: seven real three-voter/three-Controller/TLS
  gates for owner reads/enable replay, smart placement, history, snapshot holds,
  watchdog failover, minority rejection and actual Go snapshot/all-process replay.
  Shared `test_failover.launch_python` supplies a test-only module-local platform/
  synthetic profile wrapper on Linux; real entrypoint still refuses Linux/Android.
  RuntimeSafetyTests prove the product guard and required non-null mutation IDs.
  `asc/__init__.py`: 0.10.0 development; acceptance remains platform-scoped.
- 3B.5c `test_consensus` metadata-only subprocess fixture also uses a module-local
  synthetic platform/profile launcher on Linux. The fallback assertion now checks
  the exact missing-consensus diagnostic, ensuring hardware refusal cannot falsely
  satisfy the no-legacy-writer gate; product/platform guard remains unchanged.
- 3B.5d `test_storage_cluster` owner upload/download CLI fixture supplies an
  explicitly permitted synthetic profile on Linux. Existing protected setup
  refusal, byte equality, pinning and non-overwrite assertions are unchanged.

Phase 3B final qualification and exact reproduction: PHASE3B-ACCEPTANCE.md.
All published checkpoint and continuation status: PHASE3B-PROGRESS.md.

## Phase 3C checkpoints

- 3C.1 `replication.state/service/http`: optional bounded schema-1 extension,
  replay-safe owner policy 1/2/3 and explicit reconciliation through existing
  Catalog/COPY jobs. `failover.state` preserves extension; runtime Service owns
  Replication; Catalog HTTP delegates only after owner/quorum gate. No unlink.
  `tests/test_replication.DynamicPolicyTests`: count transitions, deduplication,
  shortages, failed quorum and 3A/3B/3C roundtrip/takeover preservation.
- 3C.2a `Replication.plan_moves/move/drain/required`: durable bounded migration
  plans using existing stable COPY jobs, 3B target preferences/capacity and independent
  domains; retained snapshot copy targets raise the safety floor. Source is retained;
  shortage reports blocked replicas. MovePlanningTests cover replay/shortage/roundtrip.
- 3C.2b `replication.proofs`: actual served-byte verification and fresh distinct-
  domain/current-generation recheck; `Replication.complete_move/tick`: finish one
  durable move after COPY completion, commit source-reference retirement and event,
  retain original bytes and full retirement/proof record. Runtime worker advances
  moves. Validator permanently fences retired physical identities from new Catalog
  records/active jobs. RetirementTests and ReplicationClusterTests cover this path.
- 3C.3a `replication.planner.references/graph/plan`: pure full authoritative
  reference index and checkpoint/graph/plan SHA, separate eligible/held logical
  bytes, explicit reference reasons/examples; unknown/native count UNKNOWN/held.
  `replication.state.transition` runs in every Runtime.commit to preserve retirement/
  request/move fences and retained event history. GCPlannerTests cover all reference
  classes and ordinary 1024-event aging without manual history eviction.
- 3C.3b `replication.archive` + `Replication.archive_jobs`: explicit terminal-job
  physical-pointer release with immutable identity/record digest/completion digest;
  retained job history remains. Queue GET/list/completion and upload replay support
  archived receipts. Transition checks require exact proven COMPLETED archive and
  forbid mutation/resurrection; JobArchiveTests + real TLS archive/replay gate.
- 3C.4a `replication.gc.GarbageCollection.prepare/confirm`: fresh independent proof,
  durable 60s plan/digest and exact confirmation, irreversible bounded reservation.
  `replication.arena`: in-process temporary x86 fixture capability, default absent,
  real Android/ARM/non-temporary roots refused. No unlink implementation yet.
  State validates/fences plans/jobs and invalidates pending permits on takeover;
  GCReservationTests cover default lock/confirmation/expiry/new pin/no-quorum.
- 3C.4b `replication.sandbox.Executor`: Linux x86 temporary-volume-only exact-body
  unlink under existing Engine transfer/mutex ownership and no-follow descriptors;
  current root/object-dir/file identity, SHA and final fresh authorization callback.
  `replication.journal`: private FULL SQLite immutable-identity PREPARED/DELETING/
  DONE journal with quarantine/bounds and restart/idempotent known-absence handling.
  `arena.fixture_node_capability` mints before first data; restart must match retained
  binding. Ordinary runtime has no executor; SandboxTests exercise actual fake-byte
  unlink/crash/ACK/restart/link/root/corruption/default-lock boundaries.

- 3C.4c `replication.execution.GCExecution`: contract/permit_hash, issue, authorize,
  execute; ephemeral generation/approval/endpoint-bound exact-object permits,
  streamed external-domain survivor proof, full graph recheck, fresh actual-term
  nonce receipt and exact completion. Never hold Runtime lock across network proof.
- `RuntimeRegistry.storage_authorize` dispatches GC separately; Service installs
  the authorizer but issues no capability. `replication.http` adds explicit owner
  gc-execute; no background GC. `StorageHandler` requires an issued exact-volume
  Executor and a fresh nonce at the final boundary, with no legacy fallback.
  Sandbox rejects callbacks over 10s before the existing 250ms local unlink budget.
- `tests/test_gc_authorization.py`: exact scopes/nonces, hash-only permits,
  generation/endpoint/revoke/protection, pins/last copies/corruption, policy/term/
  quorum changes, completion/lost ACK and delayed reply. Missing arena paths fail
  closed on Windows too; no nonexistent directory is created/adopted.
- `tests/test_gc_faults.py` / `tests/gc_fixture.py`: actual three-Go/TLS cohosts,
  separate owner-authenticated fixture preparation sharing the real Runtime lock;
  fixture routes/capabilities never enter product handlers/configs. Linux attaches
  only fresh-arena executors and drops a real successful GC TLS ACK before retry;
  Windows asserts physical denial. Prior tests and ordinary history aging remain.

- 3C.5a `tests/test_consensus.py` synthetic metadata launcher supplies its explicitly permitted fake profile on Windows as well as Linux. No-config subprocess must reach the unchanged attached-registry no-fallback guard; all original assertions and separate M51/Android guard tests remain.

- Phase 3C qualification/remaining physical gates: PHASE3C-ACCEPTANCE.md; current status NOT ACCEPTED. PHASE3C-PROGRESS records independently verified checkpoint hashes and Windows fixture repair provenance.

- 3C.5b `GCExecution._prove/_recheck` binds an ephemeral complete graph SHA across network proof and final CAS, including survivor pinned endpoints/approvals and every reference. New race tests change a survivor pin or introduce a pin during streaming; old evidence must fail closed with stale_gc_proof.

- `execution.proof_fingerprint` reuses the complete graph with effective profile protection, excluding unrelated self-reported heartbeat telemetry. Actual fresh/readable gates still use the original document; race tests require endpoint/protection/pin changes to deny and telemetry-only changes to remain non-authoritative.

- `asc.client.request_json` permits only fixed GC error labels for actionable retries, retaining unknown-text redaction. GC fault harness retries stale plan/proof with fresh exact confirmation/nonce on the same retirement/job, and accepts safe client-level lost-ACK recovery only after the actual drop marker is consumed.
