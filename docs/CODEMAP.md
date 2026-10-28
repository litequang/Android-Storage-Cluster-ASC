# ASC CODEMAP — v0.10.0 development / Phase 3C Linux synthetic qualification

## Phase5 private access track
- asc/access/policy.py: version1 explicit private ingress/upstream pin/mode/size
  contract and fixed browser route exclusions; no runtime or authority source.
- tests/test_access_policy.py: public/DNS/wildcard/config/management/path and
  Core/recovery write refusals; private address never implies VPN/writer proof.
- PHASE5-PLAN/PROGRESS/ACCEPTANCE: owner defers phone acceptance to later combined
  campaign; no phone/production PASS, live VPN/Cloudflare/SSH or guard changes.

## Current API35 qualification handoff (2026-10-28)

- `qualification/phase4-api35-network-native.json` / `PHASE4-API35-QUALIFICATION`:
  actual default network +pinned Controller +cold/retained Native Node PASS on
  unchanged exact APK5/same retained SDK35. Two startup-ANR failures preserved;
  eth0/15 eventually became usable, no proxy/CA/validation override/ADB data relay.
  Main now provisioned: preserve/resume, never repeat fresh init. Fresh15 PASS
  209.708s/all6Main hashes equal; old interrupted15 UNKNOWN retained. SDK stopped,
  7images/32host files private backup/hash-equal, exitSIGSEGV not clean-powerloss.
  No physical phone/ARM64/LAN/Doze/Phase4 acceptance.
- `tools/qualify_native_catalog.py`: exact published4/5 or explicit current artifact,
  original SHA/signer/installed equality; API35 actual network +TLS/cluster/wrong-pin
  preconditions BEFORE Node init. Fresh process ownership before ADB. Existing
  Engine/Node/browser/fault assertions and time limits retained. API30 direct4->5
  and fresh-first5 proved separately in existing receipts, no whole branch merge.
- `tools/native_wifi_ingress.py`: optional PRIVATE task-owned QEMU Unix monitor
  ingress to fixed virtio-wifi/10.0.2.16:9443, host127 only, never runtime/browser
  management API. Exact process/start/AVD/port/monitor/socket guards, bounded reply/
  table verification/owned cleanup. Successful Node run uses normal eth0/15 redir;
  WiFi raw TCP probe is not TLS/Node qualification. `tests/test_native_wifi_ingress.py`
  six guards +three prior artifact guards PASS. No app/Core/package/identity change.
- Older `phase4-api35-cold-node-blocker.json` retains interrupted/failed evidence;
  fifteen old requested tests UNKNOWN, never added as passes. Read current receipt
  and progress before ADB. Original API30/other private SDK data/signer preserved.

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

- Phase 3C final qualification: PHASE3C-ACCEPTANCE.md; ACCEPTED for Linux x86_64 synthetic only. PHASE3C-PROGRESS records source 8b679bc, verified checkpoints and retained Windows provenance; no real-device or ordinary-runtime GC enable.

- 3C.5b `GCExecution._prove/_recheck` binds an ephemeral complete graph SHA across network proof and final CAS, including survivor pinned endpoints/approvals and every reference. New race tests change a survivor pin or introduce a pin during streaming; old evidence must fail closed with stale_gc_proof.

- `execution.proof_fingerprint` reuses the complete graph with effective profile protection, excluding unrelated self-reported heartbeat telemetry. Actual fresh/readable gates still use the original document; race tests require endpoint/protection/pin changes to deny and telemetry-only changes to remain non-authoritative.

- `asc.client.request_json` permits only fixed GC error labels for actionable retries, retaining unknown-text redaction. GC fault harness retries stale plan/proof with fresh exact confirmation/nonce on the same retirement/job, and accepts safe client-level lost-ACK recovery only after the actual drop marker is consumed.

- Final hardened Windows gate on 895e5bb: 203 Python OK (189 PASS / 14 platform skips), all legacy/replication/GC authorization faults PASS; Go/vet/module/build PASS. That Windows checkpoint left Linux physical qualification pending; the later Linux result below supersedes that historical status.

- Linux 3C.5: `failover.state._validate_catalog` reuses only successful structural
  Catalog validation for two exact immutable JSON byte strings (each <=2 MiB).
  Native-type checks reject Python tuple/key aliases; no mutable document or
  authority is cached. `test_runtime_validation` covers mutation, history and
  materialization mismatch, type aliases and uncached failures.
- `test_gc_faults.GCFixture` shares helpers without inheriting test cases;
  `gc_fixture` supplies private synthetic pause/crash hooks and stack diagnostics.
  `test_gc_linux_faults` exercises real TLS boundaries, partitions/takeover,
  delayed replies, process death/journal recovery, references and cluster replay.

- Final 3C.5e: frozen source/tests 8b679bc, fresh full **208 Python PASS / 0 SKIP**,
  all 39 legacy + 3 replication + 3 actual GC authorization + 8 Linux physical
  groups PASS. Fresh uncached Go 11 tests/vet/module/build PASS. Physical executor
  remains synthetic-only/default absent; Windows/Android outputs compile-only.

## Phase 3D continuation

PHASE3D-PLAN/PROGRESS/ACCEPTANCE own the external backup/DR contract and checkpoint
handoff on feature/phase3d-external-dr from Core acea2ae.3D.0 is architecture only;
no new runtime path yet. Existing backup is in-cluster and is not external DR.
ADR-055/056 require exact projection+all-version bytes, private separate store,
trusted manifest anchor and passive read-only recovery, no writer reconstruction.

-3D.1a asc/external/{format,local,engine}.py: strict full-runtime/all-version
  manifest, private no-follow POSIX local store, streaming SHA/fsync/readback,
  atomic no-replace per-object publication, durable resume/final complete check.
  tests/test_external.py owns actual filesystem safety/crash tests with explicit
  fake source authority; actual quorum/TLS acceptance remains separate.

-3D.1b external/http.py supplies runtime-only owner capture/read/check; failover
  RuntimeHandler delegates before generic routing. external/source.PinnedSource
  consumes exact nested capture and fresh scoped TLS streams/final quorum check.
  test_external_cluster uses original real3-voter/cohost fixture without inheriting
  old test cases; no GC capabilities or extra live data source.

-3D.2 external/verify.py: anchored point-in-time full-byte verification, explicit
  STALE/UNKNOWN/CORRUPT/INCOMPLETE, untrusted inventory and locked retention preview.
  external/cli.py: guarded Linux-development private owner bootstrap entrypoint;
  test_external_verify.py tests actual tampering/permissions/CLI, module helper
  reuse avoids duplicate testcase collection. PHASE3D-OPERATIONS owns commands.

-3D.3 external/recovery.py: full anchored source validation before new passive
  READ_ONLY intent, streamed exact metadata/body staging, same-intent crash resume,
  final source+staged integrity and non-authoritative READY receipt. stage-verify
  uses existing shared lock and does not modify data. CLI stage/stage-verify routes;
  test_external_recovery covers real IO/IDs/no live configs/overwrite/floor/links.

-3D.4 external/destination.py declares provider-neutral logical Destination
  protocol with actual LocalDirectory CLI adapter; local engine remains POSIX,
  future cloud providers need equivalent conditional/private semantics.
  test_external_faults.py: actual three-voter/TLS/Controller+backup process death/
  ENOSPC/offline/corruption/pending/total-authority-loss matrix, nine groups.
  test_external_compatibility.py: exact baseline source schema roundtrip and
  unqualified platform refusal; recovery tests additionally kill real stage child.
  Strict native manifest/completion JSON and Backup ID checks prevent alias/relabel.

- Final3D.4b on frozen50df5d7:238 Python PASS0skip0fail1403.864s,54 targeted,
  all9 new +all original physical faults, Go11/vet/modules/builds PASS. Scoped
  external backup/verify/read-only staging accepted; Phase3D PARTIALLY COMPLETE,
  writable disaster recovery BLOCKED. Exact source/commands/limits in acceptance.

## Phase4 integration audit
PHASE4-PLAN/PROGRESS/ACCEPTANCE own Core-first allowlist/mode/QuickJoin foundation
and independent checkpoint handoff.4.0a documentation only; no module port yet.
Registry/server/CLI/client/identity/Catalog/StorageHTTP/manifest/Go identical across
refs; approved-root storage patch requires separate port+qualification. Preserve
external3D module/handler/tests and all old guards; ADR062 defines source vs state.


<!-- Reviewed Demo c9c2660 historical extension; current Phase4 status is in PHASE4-PROGRESS. -->
## Android Demo Alpha audit / separate track

Branch `feature/android-demo-alpha` from acea2ae. Audit/reuse boundaries, staged
checkpoint contract and upgrade design: DEMO-TRACK-PLAN.md; durable current handoff:
DEMO-TRACK-PROGRESS.md. No Demo implementation at DEMO.0. Reuse single-writer
Registry/CatalogService/StorageRuntime and existing guards; preserve all Core paths.

## Android Demo installer (DEMO.1)
- `asc/demo/installer.py`: read-only device/dependency preflight, private path checks, immutable source installation, separately verified launcher; no Core state adoption.
- `asc/demo/package.py`: deterministic public-source allowlist archive, per-file inventory/content SHA and release identity verification.
- `asc/demo/cli.py`, `scripts/demo-alpha.sh`: separate guarded Demo entry point; installer/preflight only at this checkpoint.
- `tests/test_demo_installer.py`: extracted package execution, deterministic checksums/tampering, dry-run/rerun/state retention, dependency/M51/unknown/unmarked/symlink refusal.
- `docs/DEMO-QUICKSTART.md`, `releases/`: owner installer preview and adjacent checksum.

## Android Demo LAN (DEMO.2)
- `asc/demo/state.py`: dedicated Demo marker format 1, exact read-only Core registry/manifest/cache compatibility, Raft/legacy/missing identity refusal, RFC1918/loopback-only IPv4 origin checks.
- `asc/demo/lan.py`: DemoCatalog two-domain measured upload gate, restricted Core HTTP handler, explicit-bind ControllerRuntime, isolated Core-HOME node process/StorageRuntime/heartbeats; owner Core ClusterClient transfer and bounded protection reporting.
- `asc/demo/cli.py`: init/join/storage-init/run-controller/run-node/pair/approve/nodes/files/replicas/upload/download; no policy reduction, whole-volume grants, Raft or GC commands.
- `tests/test_demo_lan.py`: actual subprocess CLI/controller/two synthetic phone nodes, TLS/SHA/fallback/Controller loss, domain/capacity/missing volume/guard/schema/attached-state refusal.

## Demo upgrade-safe source (DEMO.3a)
- `asc/demo/upgrade.py`: prefix/state binding, stopped lifecycle locks, complete private state+approved-volume inventory/copy/readback, exact release compatibility, immutable staging, journaled activation/code rollback, interrupted activation recovery, whitelist diagnostics. No automatic schema/data restore.
- `asc/demo/installer.py`: private code-prefix ancestor validation differs from private state root; installed source remains immutable.
- `asc/demo/cli.py`: backup/verify-backup/stage/upgrade-preflight/upgrade/rollback/recover-upgrade/diagnose; node re-exec resolves its verified installed source.
- `tests/test_demo_upgrade.py`: inherited LAN fault gates run via installed launchers, plus backup/external-volume/mutation/crash/upgrade/code-rollback/identity and diagnostics tests.
- `docs/DEMO-QUICKSTART.md`: final owner manual CLI workflow, archive README source, limitations and manual stopped cluster sequence.

Demo final qualification/package evidence is recorded in `docs/DEMO-TRACK-ACCEPTANCE.md`;
README / README-VI link the separate Demo plan/progress/owner workflow. Public package
contains source only, all Core Python retained; no Go sidecar/runtime/private data.
`docs/DEMO-ANDROID-PILOT.md` is the blank owner-only device acceptance checklist and
installer-preview prefix handoff; no phone result is prefilled by Cloud tests.

DEMO.3a.1: `asc/demo/locks.py` validates no links/regular/single-link/inode identity
before writing coordination files, opens with O_NOFOLLOW on Linux and reuses Core
OS lock primitives. All Demo lifecycle/source operations use private_lock; state
preflight checks internal engine/worker coordination files before Core constructors.
Final synthetic regression in test_demo_upgrade.py proves symlink/hardlink refusal
leaves outside empty test-owned bytes unchanged. Core runtime.py is unchanged.
Qualified Demo 0.3.0: releases/asc-demo-alpha-0.3.0.tar.gz + .sha256, 83 source/doc/
manifest members. Final acceptance/AGENTS/progress identify aaf7d16 implementation,
222 Python/11 Go evidence, publication receipt and owner-only Android pilot limits.

## DEMO.4a Dashboard backend
- `asc/demo/dashboard/tls.py`: explicit stopped setup/load/export/public_info for separate private CA + IP SAN browser HTTPS; original Core/node keys unchanged.
- `dashboard/auth.py`: bounded in-memory hashed one-use grants and owner sessions/CSRF; restart invalidates all browser credentials.
- `dashboard/views.py`: whitelisted Registry/Catalog node/volume/file/replica projections; measured freshness/nulls, owner domain counts, pending reservations and conservative shared-domain free-space aggregation.
- `dashboard/http.py`: exact same-origin browser routes, cookie/CSRF/Host/Origin/rates, one private bounded spool/transfer, actual byte/SHA counters, existing pinned ClusterClient upload/download/fallback. No node approval/policy/delete route.
- `dashboard/runtime.py`: optional second HTTPS listener in Controller process, same Catalog/service/lifecycle.
- `demo/lan.py`: explicit dashboard-enabled ControllerRuntime and pinned owner-only login-code route; `demo/cli.py`: dashboard-init/trust/code, run-controller --dashboard. `state.py` checks completed optional Dashboard format before writable Core open.
- `tests/test_demo_dashboard.py`: session unit bounds + real CA/SAN HTTPS/storage/auth/byte/domain/fallback/refusal tests. Current contract: DEMO4-PLAN; actual handoff: DEMO-TRACK-PROGRESS.

## DEMO.4b local browser frontend
- `asc/demo/dashboard/web/{index.html,style.css,app.js}`: same-origin Vietnamese responsive overview/nodes/volumes/files/replica dialog, one-use login, CSRF fetch, observed server byte counters, session-local nonsecret retry key, WebCrypto SHA verification before new download. All dynamic text uses DOM textContent; no CDN, browser Core token, service worker or offline writes.
- `asc/demo/package.py`: source allowlist includes exactly local HTML/CSS/JS Dashboard assets and manifest hashes; installed-tree verification still covers every asset.
- `dashboard/views.py`: retain approved volume IDs with UNKNOWN metrics when no fresh probe exists; aggregate protection counts UNKNOWN when the 256-file preview is truncated.
- `tests/test_demo_dashboard_browser.py` + `tests/browser/demo_dashboard.cjs`: actual packaged source + Chromium with isolated NSS public-CA trust, no TLS bypass; login/upload/physical two-node bytes/download SHA after real node stop, XSS/mobile/offline/session gates. Requires Node+Playwright/Chromium/certutil; missing prerequisites FAIL explicitly, never skip a security gate. Screenshots are private local test artifacts, not release contents.

## DEMO.4c compatible 0.4.0 source/package
- `asc/demo/__init__.py`: 0.4.0-alpha plus dashboard-lite capability; base STATE_FORMATS unchanged (demo1/registry4/manifest1/metadata1/config1/wire1).
- `tests/test_demo_release_upgrade.py`: exact checksum-pinned published 0.3.0 archive installs/populates two nodes; OLD installed launcher stages/upgrades current source; trusted Dashboard serves old bytes, new source writes a second file, then NEW complete backup/code-only rollback runs OLD immutable 0.3 code over actual new state. Verifies IDs/cluster/pins/certs/volume bytes, both file downloads, preserved/backed-up Dashboard private identity and unchanged schema.
- `docs/DEMO-QUICKSTART.md` and `DEMO-ANDROID-PILOT.md`: 0.4 package, manual owner public-CA trust/browser workflow, explicit stopped 0.3 upgrade/rollback and blank phone evidence. No old installer overwrite or Android acceptance claim.

DEMO.4c final qualification: frozen956bf8e source/tests/packaged guides;230 Python
PASS0skip incl all8 Linux GC physical gates,11 fresh Go/vet/modules/builds PASS,
22 targeted +3 exact-archive installer checks PASS. Qualified source-only0.4 archive
releases/asc-demo-alpha-0.4.0.tar.gz has92 regular files incl3 local web assets;
manifest/SHA and exact0.3 rollback proof in DEMO4-ACCEPTANCE. Source, package and
publication receipt in DEMO-TRACK-PROGRESS; Android/real CA-install UX NOT TESTED.

## DEMO.4d.1 approved-volume POSIX anchor
- `asc/storage/volumes.py:_PosixAccess`: direct approved-root O_NOFOLLOW descriptor + persisted dev/inode check, pinned marker/staging/objects and ancestor namespace pre/post rechecks; never open filesystem root. Fail closed without required descriptor primitives; Windows existing handle branch preserved.
- `LocalVolume.check/open/remove_staging/sync_directory/entries/disk_usage/allocated_files`: child no-follow descriptor IO, measured fd statvfs/scandir/fsync, single-link cleanup and optional expected probe identity. `VolumeManager.inspect`: only owned probe cleanup, success after all actual IO/cleanup, no collision deletion.
- `asc/storage/engine.py:_space/inventory`: use adapter descriptor-based capacity/inventory; other upload/commit/download/recovery/state/authorization unchanged.
- `tests/test_android_volumes.py`:13 Linux/Android-like root-open denial, actual file/SHA/fsync/probe cleanup/restart, real unprivileged directory EACCES, root/folder/marker/link swaps/traversal/hardlinks/collision/unsupported-primitives/failure metrics. Linux synthetic only. Plan/handoff: DEMO4D-PLAN / DEMO-TRACK-PROGRESS.

## DEMO.4d.2 root-denied runtime / owner probe
- `asc/demo/cli.py:storage-status`: reuse existing StorageEngine.capabilities on the enrolled node home under Demo operation + node agent ownership, validated installed prefix/state/schema. No initialization, config change, network route or identity recreation; running node refuses local inspection. Owner can confirm real read/write/fsync after upgrading before restarting that node.
- `tests/android_root_denial.py`: non-packaged child-only syscall fault wrapper; denies '/' and delegates all other actual OS IO, retaining real dir_fd capability metadata. Sets no product feature/permission bypass.
- `tests/test_demo_android_storage.py`: Controller/Dashboard+two actual enrolled pinned-TLS nodes under root denial, real probe/SHA/fsync/physical replicas, stopped-node fallback/restart/identity preservation and new stopped-node status/M51/unknown guard checks. Existing browser/API regressions remain intact.

DEMO.4d.2 additional ancestor race verifies a symlink back to the same approved
root inode still fails namespace binding, without touching the original bytes.
Current AndroidVolumeTests has14cases; historical4d.1 had13. Final combined36PASS
plus separately executed new ancestor1PASS; see progress for precise provenance.

## DEMO.4d.3 compatible0.4.1 release candidate
- `asc/demo/__init__.py`:0.4.1-alpha/android-volume-anchor capability, identical base formats. `package.py` includes dedicated public docs/DEMO-ZTE-0.4.1.md as93rd member; all Dashboard assets kept.
- `tests/test_demo_release_upgrade.py`: shared no-test fixture with two concrete exact published03/04 archive cases. Both exercise OLD installed backup/verify/stage/preflight/activate and NEW runtime under test-only root denial; existing04 browser CA and assets retained. New-state rollback checks old root-denial defect honestly, then baseline Linux old-code reads BOTH old+new files with all identities/credentials/media unchanged.
- `docs/DEMO-ZTE-0.4.1.md`: owner copyable existing-ZTE0.3 stop/backup/identity hashes/verified download/old-launcher activation/real status/trusted Dashboard/Bphone/replica/SHA/backup-before-rollback commands; no ZTE reinit or old-DB restore. General QuickStart/pilot updated, old archives unchanged. Qualification: DEMO4D-ACCEPTANCE, not historical0.4 report.

DEMO.4d.3b final Linux qualification: frozen dae8e7a source/tests/packaged guides,
246 Python PASS0skip/all8 physical faults,11 fresh Go/vet/modules/builds,38 targeted
and3 exact-archive installer checks PASS.0.4.1 public source-only archive93 regular
files incl dedicated existing-ZTE guide; SHA/source/full evidence in DEMO4D-ACCEPTANCE,
normal publication receipt/next owner-only pilot in DEMO-TRACK-PROGRESS. Shared Core
changes limited to volumes.py and engine.py on Demo branch; Core WIP unchanged.

## Phase4.0b.1 reviewed port actual state
Allowlisted asc/demo modules/assets/installer/upgrade/launcher and test fixtures
now reuse existing common Core services. Shared storage volumes.py/engine.py match
reviewed Demo c9c2660; external3D modules/handler/Go and original Core tests unchanged.
95 targeted integration cases PASS; exact provenance and artifact checks in Phase4
progress. No QuickJoin implementation yet; historical source status above retained.

## Phase4.0b.2a Quick Join foundation
- asc/demo/pairing.py: DemoCatalog-only owner session facade, existing pinned admin/pair and read-only Registry evidence; hash-only bounded RAM tracking, no new database.
- asc/demo/quickjoin.py: guided local subprocess adapter to Core enrollment, pin/cluster/mode checks, redacted states and same durable retry operation; no auto-approval.
- asc/cli.py:_enroll: optional expected-cluster-id guard, existing pending format unchanged. asc/demo/state.py rejects recovery staging before init/inspection.
- tests/test_quick_join.py:9 actual TLS/CLI/one-use/concurrency/ACK/restart/security/identity/device cases. Historical release tests use exact published04.1 fixture; old assertions retained.
- docs/PHASE4-QUICK-JOIN.md: source-candidate CLI/API contract and operator limits; UI/candidate final qualification pending.

## Phase4.0b.2b owner UI
Existing Dashboard web/index.html/app.js/style.css adds Ghép điện thoại tab;
same request/session facade. One-use code only DOM/RAM, generation guards discard
old async replies; offline/logout/pagehide clears it. No node approval action.
tests/browser/quick_join.cjs +test_quick_join_browser.py: trusted actual Chromium
owner create ->real CLI registration, pending approval,390px layout, no persistent
codes/secret URLs, offline clearing and delayed successful POST after logout.

## Phase4.0c.1 exact compatibility candidate
- tests/test_phase4_upgrade.py: standalone exact04.1 ->persisted candidate byte equality/upgrade; lost actual TLS ACK pending both directions, new-state code-only rollback, IDs/CA/volume/token and old/new SHA preservation. Existing historical03/04->04.1 tests stay exact.
- asc/demo/package.py: adds only public Phase4 guide and candidate README warning, keeps format1; candidates/ contains deterministic source-only0.4.2-dev and SHA, no release/tag/phone claim.
- PHASE4-PLAN/PROGRESS/ACCEPTANCE: audit, source freeze/qualification status, next app foundation and authority/migration blockers. Do not edit source/tests/packaged guides/candidate during final full.

## Phase 4.0 final Linux qualification
Frozen4d1758d source/candidate:287 Python PASS0skip/fail, all old/Core3D faults;
11 Go/vet/modules/builds PASS. PHASE4-ACCEPTANCE owns exact evidence/limits;
PHASE4-PROGRESS owns receipt/next steps; PHASE4-QUICK-JOIN owns qualified upgrade/
rollback use. No post-full source/test/package-guide drift. Candidate only,
Android and writable DR remain NOT ACCEPTED.

## Phase4.1a local bridge / quorum observer contracts
- asc/bridge/contract.py: strict version1 framed JSON/operation/scopes; no arbitrary paths/shell/PID/init/approval/GC.
- tests/test_bridge_contract.py: malformed/duplicate/type alias/unknown/dangerous operations and secret-safe error boundary.
- tests/test_phase4_upgrade.py: historical exact04.1->published Phase4.0 fixture pinned, old assertions unchanged;4.1 needs separate exact old-candidate upgrade test.
- PHASE4-1-PLAN/PROGRESS/ACCEPTANCE own task. LOCAL-ENGINE-BRIDGE/THREAT-MODEL, CORE-QUORUM-DASHBOARD, ANDROID-APP-CONTRACT own IPC/actors/lifecycle/observer/future Android limits.

## Phase4.1b.1 private IPC implementation
- asc/bridge/private.py: private no-link owner file checks, exclusive config publication and bounded FULL request journal; not an engine DB.
- asc/bridge/service.py: explicit provision/load, app scopes +actual Linux SO_PEERCRED UDS, eight bounded handlers, fixed mode/root, journal retry/secret-code hash and historical receipts.
- asc/bridge/engine.py: existing state/installation inode binding, read-only approved volume adapter metrics and pinned Controller reachability, existing Quick Join subprocess via private stdin/ASC_HOME before imports; no identity init/approval/write probe.
- asc/bridge/cli.py: explicit provision/run/status/hidden-code client; no shell/path/PID operations. Lifecycle unsupported until b.2.
- tests/test_bridge.py: actual UDS/TLS/engine lost replies/restart/pending/no approval, scopes/peer credentials/frame limits, secret-safe receipts, root/guard/foreign socket/bounds.

## Phase4.1b.2 controlled lifecycle
- bridge/lifecycle.py OwnedNode: retained supervisor thread owns fixed guarded Node Popen, explicit start/stop/historical receipts; never external PID/Controller/Core launch.
- bridge/child.py: Linux parent-death fence in single-threaded launcher before exec, original device/state/runtime guards retained.
- bridge/service.py Runtime: exact private socket crash receipt recovery under exclusive OS lock, no foreign/live unlink. bridge/private.py atomic owned receipt publication.
- bridge/cli.py register/execute_demo and demo/cli.py: verified installed launcher commands with root/prefix binding; local app scopes distinct from owner/node credentials.
- tests/test_bridge_lifecycle.py:4 actual TLS/bytes/start/stop/parent SIGKILL/socket recovery/installed source/enrollment-commit crash tests. Linux parent-thread regression caught and fixed.

## Phase4.1c.1 Core observer
- asc/observability/core.py: existing validated prepared registry/Catalog/Views read-only public projection, policy counts/jobs/backup history/UNKNOWN; observe uses only Runtime.view +status, never ensure_ready/commit.
- observability/http.py +3-line failover/service.py delegation: owner GET /cluster/v1/observability, POST denial before readiness side effects, exact own response envelope.
- observability/client.py Observer: fixed pinned identities/epoch/static3/floor, bounded GET collector/no legacy fallback, stale availability downgrade. RecoveryObserver: existing full-byte verified passive stage only.
- observability/native.py (4.2i.1): fixed owner-session consumer of existing HTTPS gateway; RAM-only cookie/CSRF, exact mode/cluster/epoch/floor, no Node credentials or writer operations. Tests: test_native_observer.py; contract: ANDROID-CORE-OBSERVER.md. Android wiring: i.2 below.
- NativeCoreObserver.kt/ObserverPolicy.kt +EngineService transaction4 (4.2i.2): bounded private owner observation IPC and existing Python client, no Node/schema mutation. MainActivity Cụm page displays actual sanitized Core view; NativeObserverTest.kt +tools/qualify_native_observer.py exercise actual gateway/three-voter partition/heal on owned emulator. ObserverPolicyTest.kt covers fixed modes/bindings/operation denial.
- NativeCatalogTest.kt +tools/qualify_native_catalog.py (4.2j.1): existing native Binder/Engine joins a separate actual marked Demo Controller; existing owner Dashboard/Chromium uploads two logical-domain replicas (APK+Linux peer), native outage/fallback, current-Controller authorization refusal and retained-process exact bytes. No Core-to-Demo state adoption or second Catalog. Existing browser fixture gains optional required-native-node/retained-file selection; original default assertions remain. ASC-USER-STATUS.md distinguishes web/native/LAN/Cloudflare gaps.
- tests/test_observability.py: separate no-test helper +actual TLS API/partition/takeover classes, no duplicate fixture test inheritance; source/secret/read-only/policy3/verified backup/passive corruption gates.

## Phase4.1c.2 shared read-only browser gateway
- observability/gateway.py: explicit Linux-only private gateway/CA/source config, loopback HTTPS by default, no engine lifecycle; unique session cookie per root.
- demo/dashboard/http.py: explicit mode routing before Demo mutation paths, authenticated Core GET-only state/detail; existing Sessions/CSRF/security headers reused.
- dashboard/tls.py generate_identity: shared no-overwrite TLS creation, existing Demo default preserved.
- dashboard/web assets: same mobile-first UI, Core controllers/quorum/jobs/backup and policy counts; no Core writes/download/Quick Join.
- tests/test_observer_gateway.py +browser/core_observer.cjs: actual trusted Chromium/Core3-voter transport partition/heal, policy3, server-side denial and passive verified stage.

## Phase4.1d source candidate / compatibility qualification
- tests/test_phase41_upgrade.py: exact published0.4.2-dev ->exact rebuilt0.4.3-dev, original pending BOTH directions, identity/volume/CA/credentials, new-state bytes/download after code rollback; installed bridge/private control preserved and old API refuses.
- demo/package.py: public bridge/Core/app/operator guides and capabilities in deterministic124-file source-only candidate; private material excluded, prior archives unchanged.
- observability/client.py RecoveryObserver expected_epoch: gateway explicit epoch binding checked against anchored staged manifest; mismatch UNKNOWN, never activation.
- candidates/0.4.3-dev +SHA: source-only Linux qualification input, not APK/Android release. PHASE4-1-OPERATIONS owns compatible upgrade/use/rollback.

## Phase4.1 final qualification
Frozen0a3ea839217156b69209a073f5d836ee1db4452b:311 fresh Python/all legacy+new faults PASS0skip/fail;11
uncached Go/vet/module verification/builds PASS. Acceptance owns exact source/
archive/commands/evidence and limits; progress owns handoff/receipts. Reporting
docs only after full, no source/test/packaged guide/archive drift. Linux synthetic
bridge/Core read-only only; Android/native migration/writable DR remain unqualified.

## Phase4.2a isolated native toolchain/project
- android/ settings/build/app Gradle Kotlin project: pinned AGP8.9.2/Kotlin2.2.20/API35, own application ID, no Core state/runtime adoption.
- Contract.kt: version1 refusal/UNKNOWN contract; MainActivity: explicit FOUNDATION/unsupported Engine only.
- ContractTest/LaunchTest: JVM version/UNKNOWN checks and actual Android launch gate (no emulator result implied).
- PHASE4-2-PLAN/PROGRESS/ACCEPTANCE own serial checkpoints, toolchain evidence and native runtime blockers.

## Phase4.2b.1 private native Binder
- android/app/src/main/aidl ILocalEngine: typed bounded versioned fixed operations, no paths/PID/shell.
- RequestPolicy.kt: canonical UUID/private HTTPS/full pin/Cluster ID/name/code/trust validation, own UID+signature policy.
- EngineService.kt: exported=false/signature permission and per-call UID/signature, consent, honest FOUNDATION/UNKNOWN/unsupported runtime, no automatic identity/lifecycle.
- MainActivity: explicit local consent and private binding/status; no browser/backend/Termux state.
- RequestPolicyTest/BinderTest: JVM denial/validation and actual Android consent/version/runtime refusal gates; no mock online success.

## Phase4.2b.2 embedded canonical Core library
- Gradle syncAscSources/Chaquopy: allowlisted public Core .py to generated APK assets, pinned Python3.13/16.1, no source fork or state copy.
- EmbeddedEngine.kt/native_engine.py: actual library info +internal fresh synthetic I/O/commit/restart proof, no Node runtime API.
- EmbeddedEngineTest/test_native_engine_adapter.py: real Android +Linux I/O/root/link refusal, preserved core guards and private Context canonical approval.
- ANDROID-ENGINE-INTEGRATION owns current native runtime blocker and future explicit-context provider boundary.

## Phase4.2c app Keystore/private capability volume
- ApplicationVault.kt: explicit app UUID/AES-GCM AndroidKeyStore alias1/canary, atomic private encrypted DRAFT_NOT_SENT, loss/schema/cipher hold/no regeneration.
- StorageFoundation.kt: PrivateProbeStorage delegates same Core JNI, UnqualifiedSafStorage refuses unproven provider semantics.
- native_engine approve_probe/_approved/probe/volume_status: fixed app-private capability scope, root/app/schema/original volume binding, no constructor after missing manifest; Core quota/free/readback/fsync/own cleanup +read-only DB status.
- EngineService: typed explicit app provision/draft/probe/approval operations, UID/signature/consent first, no cluster storage/failure-domain approval.
- VaultStorageTest +extended native adapter tests: actual Android Keystore/permission/budget/identity/schema/corrupt bytes/root/SAF and Linux private I/O.
- ANDROID-NATIVE-STATE owns format/backup/rollback/provider boundaries.

## Phase4.2d native UI/public TLS binding
- MainActivity: four Vietnamese native pages, actual device/private capability sources, explicit UNKNOWN/no observer, consent/trust/code-clearing/generation guards; encrypted unsent draft, no Node or fake cluster state.
- native_engine.inspect_controller/EmbeddedEngine: existing Core pinned GET only, expected cluster/mode/schema, no code/token/POST.
- ControllerBindingTest/NativeUiTest +test_native_controller_binding: actual Android+Linux TLS wrong-pin/cluster/outage/reconnect/no-enrollment and live UI/background secret clearing.
- Manifest INTERNET/ACCESS_NETWORK_STATE only normal network permissions, no broad storage/camera/boot/FGS. Native0.2.0-foundation versionCode2, own state unchanged.

## Phase4.2e emulator/security/upgrade qualification
- NativeDeviceGate: M51 dominates fields, unknown denied before private state; debug AOSP emulator diagnostics only, known test model !=runtime acceptance.
- MainActivity NetworkCallback: actual default-network loss invalidates public binding, clears code and drops late UI generation.
- Explicit AIDL0/1 IDs +Binder golden Parcel test preserve native IPC1 ABI.
- NativeLifecycleTest: actual owned-emulator WiFi+cellular fault/restoration. UpgradeQualificationRunner TEST APK ONLY: exact old APK state/Keystore/marker/bytes ->new APK/process death/platform downgrade refusal.
- android/untrusted: different signer/UID/denied permission +actual bind refusal fixture, never shipped as main app. Backup XML excludes all CE/DE cloud+D2D state, no key/folder migration.
- tools/qualify_android_emulator.py: explicit owned loopback AVD verification, actual Core TLS outage/reconnect, exact-APK upgrade fault gates, private output only.
- ANDROID-NATIVE-IPC/OPERATIONS/PILOT: versioned Binder, developer/owner qualification and honest unsupported Native Node/migration boundaries.

- NetworkReadinessTest: actual default-network precondition; NativeLifecycle waits observed onAvailable before a real loss fault. ControllerBindingTest failure diagnostic emits only public primitive error category. Direct NAT ConnectionRefused remains NOT PASSED; explicit dev-only adb-reverse-loopback qualifies TLS/protocol, never LAN. Tool removes only owned no-rebind mapping, no automatic transport fallback.

Phase4.2 regression fixture: DashboardAPITests.start waits a CA-verified Dashboard TLS handshake separately from Core API readiness; sends no HTTP/cookie before original first-response401/session/key assertions. No runtime/Core change.

Phase4.2 final qualification data: qualification/phase4-2-foundation.json owns bounded
actual counts/scopes/artifact/protected-publication facts; phase4-2-source-sha256.json
pins243 public source/test/tools/guides/archive/APK inputs to c7dabb0. Reports only,
no runtime/config/authority or secrets. Full native Phase4.2 remains NOT ACCEPTED.

## Phase4.2f.1 explicit native context
- asc/node/context.py: explicit private home/device binding/strict format1, pinned
  descriptor receipt, credential-provider CAS and OS operation ownership. No Node
  identity/TLS/enrollment/Agent yet.
- NativeNodeContext/ApplicationVault: fixed Keystore-encrypted context+witness,
  trusted JNI only; EngineService adds consent/device-gated context init/status.
- test_native_context/NativeContextTest and fixed runner context phases own Linux
  filesystem and actual Android credential/restart gates. ANDROID-NATIVE-CONTEXT
  defines format/threat/compatibility; f–j remain unfinished.

## Phase4.2f.2 native TLS identity/providers
- asc/node/tls.py: explicit sealed anonymous-memory loader, verified seals/CLOEXEC/
  readback/FD cleanup; public Bionic ABI only when Python wrapper absent. Linux
  CPython and explicit Android native loaders never fall back after denial.
- NodeContext tls_provider/prepare_tls/tls_context: typed sealed TLS component,
  one durable cert/key, key-match validation/restart/downgrade refusal; no Node.
- NativeTLSIdentity.kt: pinned BC/JCA EC/X.509 generation. NativeTLSLoader.kt:
  standard Android JSSE/KeyFactory/Signature/in-memory KeyStore/KeyManagerFactory;
  no proc reopen/plaintext key store, explicit API30+ guard.
- NativeNodeContext +EngineService/RequestPolicy: private native_tls_prepare/public
  pin only; explicit Binder IDs/consent/device/UID unchanged.
- test_native_tls/NativeTLSTest and fixed TLS runner phases qualify actual TLS/
  sealing/credential/process faults alongside retained context/Binder/Engine gates.
- ANDROID-NATIVE-TLS owns provider format/threat/API/platform/next-agent boundaries.

## Phase4.2g.1 shared Core enrollment client contract
asc/enrollment.py extracts new_pending/accepted_identity from existing CLI only:
unchanged format1/payload/CSPRNG op+token/cluster+target+token ACK checks. CLI
continues original device/HOME/locks/persistence/repair/discovery. No native join
wiring yet. test_enrollment_contract plus all original lifecycle/QuickJoin gates
preserve lostACK/code replacement/one-use/identity behavior. Native g.2 next.

## Phase4.2g.2a sealed native enrollment adapter (Linux qualification)
- asc/node/enrollment.py: NativeEnrollment reuses shared Core pending/ACK contract
  and pinned request_json under NodeContext ownership lock. Private CAS persists
  original operation before POST, atomically publishes node + clears pending.
  Strict typed fields, explicit code replacement, historical receipt only; no
  CLI/HOME/repair/startup/storage or physical-domain approval.
- asc/node/context.py: validates typed pending/node slots and returns redacted
  enrollment/UNKNOWN approval status. Existing context1/null slots unchanged.
- tests/test_native_enrollment.py: actual Core Registry/TLS/lost successful ACK,
  offline/reconnect, private publication failure, reply mismatch, retry identity,
  expiry/replacement, pin/cluster/mode/protected-device and corrupt-state gates.
  Memory CAS fixture is Linux only, NOT Android Keystore/IPC evidence.

## Phase4.2g.2b native Core enrollment bindings
- asc/node/enrollment.py:public_request: fixed private dispatch + safe public
  failures/pending receipt; no raw exception, code/token or new authority.
- NativeNodeContext.join/resume/replaceCode: trusted native Build/RAM profile,
  existing embedded Core +Keystore context provider; no CLI/HOME/repair fallback.
- EngineService/RequestPolicy: existing ownUID+signature/consent gates on
  quick_join/resume_join/replace_join_code, fixed fields and transaction1 retained.
- MainActivity: explicit context/TLS preparation, verified binding +owner trust,
  actual join/pending status/resume/code replacement, secret clearing and truthful
  historical receipt/UNKNOWN approval; old encrypted unsent draft stays separate.
- NativeEnrollmentTest/BinderEnrollmentTest +fixed runner join phases: actual
  Android Keystore/TLS/Core/pending/process proof; test-only private fixture outside
  main APK. NativeUiTest/RequestPolicyTest retain old assertions +new trust/fields.
- tools/qualify_native_enrollment.py: explicit task-owned Linux emulator/signer/UID
  validation, synthetic Core/actual successful201 ACK-loss +retained state gates.
  Explicit ADB dev loopback ONLY; not direct LAN/phone qualification. Contract:
  ANDROID-NATIVE-ENROLLMENT. No listener/Agent/FGS or storage approval added.

## Phase4.2g.2c positive native UI/Binder/Core proof
- NativeJoinUiQualification +fixed ui-join-* runner phases: real MainActivity
  View callbacks/private production Binder/Core/pinned HTTPS, successful201 ACK
  loss, actual process force-stop/restart and preserved app/context/TLS/op/token/
  Node identity. Separate fresh task-owned AVD, no old fixture/assertion changes.
- tools/qualify_native_join_ui.py: live owned AVD/signer validation, private exact
  Controller/TLS fixture, pre-enrollment setup-only resume, explicit dev tunnel.
  Retains state; never uninstall/clear. Main APK/source unchanged. NOT direct LAN
  or physical-touch/phone usability proof; observed launcher ANR recorded.

## Phase4.2h.1 shared explicit Agent heartbeat contract
- asc/agent.py:heartbeat(config,profile,send=None): unchanged Core pinned request/
  Discovery routing +cluster match, without HOME/hardware discovery/FS/lifecycle.
  Trusted optional transport callback, never IPC. Not storage/Leader authority.
- asc/cli.py:agent_once retains inspect/M51 storage fence/real capabilities,
  credential rejection/private cache/metadata-sync behavior; delegates network
  exchange to shared heartbeat, preserving existing transport injection seam.
- tests/test_agent_contract.py: actual Core Registry/TLS/UNKNOWN profile, wrong
  pin, cluster mismatch, revoked token and offline/reconnect, no identity repair.
  Existing lifecycle/storage/distributed/discovery regressions remain unchanged.

## Phase4.2h.2a native JSSE socket facade
- asc/node/socket.py: NativeSocket/_Input bounded binary read1/readinto/sendall,
  fixed errors/timeout/file modes, explicit socket ownership; no HTTP/Engine.
- NativeTLSListener/NativeTLSConnection: SDK/device/private-bind/TLS1.2+ gates,
  bounded32 owned sockets and absolute read/WRITE deadline/close cancellation.
  No fd adoption, plaintext tunnel, external CLI or product startup/IPC.
- test_native_socket +NativeTLSListenerPolicyTest/NativeSocketTest: Linux facade
  contracts versus real API35 JSSE/pin/all-byte SHA/read and blocked-write deadline
  proof, kept distinct. ANDROID-NATIVE-TRANSPORT owns contract/limits/next Handler
  integration; no binary echo-as-Storage-Node acceptance.

## Phase4.2h.2b.1a existing-only metadata gate (scoped PASS)
- tests/test_phase41_upgrade.py: exact published0.4.3 rebuilt from qualified
  0a3ea839 source and byte/SHA checked; additional CurrentSourceUpgradeTests runs
  the SAME full upgrade/pending/identity/bytes/rollback assertions against the
  unpublished current-source package, with independent source/inventory checks.
- asc/storage/manifest.py: existing_identity +Manifest existing_only/expected_file:
  POSIX private regular owner/single-link/inode checks, SQLite mode=rw, exact
  version/Node/schema/integrity validation WITHOUT DDL/identity repair. Canonical
  existing DDL reused in RAM for structural comparison (whitespace normalized).
- asc/storage/engine.py: optional existing_only/manifest_identity prevents missing
  home/DB creation and chmod before lifecycle ownership; old default unchanged.
- test_existing_storage/ExistingStorageTest: actual missing/replacement/schema/
  identity failures plus exact previous h.2a Android Engine bytes/marker/Volume ID.
  Not yet approved native network-volume config or Handler/Agent/FGS.

## Native Node MVP session (h.2b, Android qualification pending)
- asc/node/storage.py: explicit fixed app-private Node volume configuration, same
  canonical Engine/probe, held partial setup and existing-only reopen.
- asc/node/runtime.py: owned TLS/StorageHandler/heartbeat session and stop/status;
  no second backend/Catalog or Raft/GC/approval.
- asc/server.py, asc/storage/http.py: optional unbound constructor for native TLS
  dispatch; old bound-server defaults unchanged. asc/node/socket.py timeout getter.
- NativeNodeSession.kt/NativeNodeContext.kt/EngineService.kt: same private Binder,
  Keystore context and JSSE factory; typed configure/start plus status/stop.
- MainActivity.kt: minimal Node quota/host/port/start/stop controls; foreground UI
  session only, no FGS yet. tests/test_native_runtime.py:4 actual Linux TLS/I/O/
  heartbeat/restart/missing-state/interrupted-setup/Controller-loss gates.

- NativeNodeMVPTest.kt: focused actual API35 Binder/JSSE/owner grant/bytes/hash/
  heartbeat/stop-start plus independent fresh-process retained identity/readback.
  Uses private task fixture, never packaged owner credentials; no direct LAN claim.

## h.3 owned foreground Node
- EngineService.kt: promote ONLY actual explicitly started Node session as Android
  connectedDevice FGS; notification Stop, own runtime health cleanup, no boot/auto
  restart/initialization. MainActivity.kt requests notification permission on33+.
- NativeNodeForegroundTest.kt: actual OS foreground/notification, all UI/test
  bindings removed, real SHA download while background, PendingIntent Stop and
  real closed port. tools/audit_native_apk.py --foreground-node explicitly expects
  the4 documented service/notification permissions; old3-permission default kept.

## h.4 actual direct NAT Node
- NativeEnrollment.change_controller/public_request: explicit new address, SAME
  certificate PIN/Cluster ID/Node credentials/storage; verified existing info+CAS,
  rejects pending/unqualified runtime. Not leader/writer/recovery authority.
- NativeNodeContext/RequestPolicy/EngineService/MainActivity: stopped-Node-only
  address setting with existing trust UI; public Node TLS PIN is selectable for
  owner approval. No new enrollment/state/schema or private-key export.
- NativeNodeDirectTest.kt +tools/qualify_native_direct.py: owned AVD, reverse
  removed, actual direct heartbeat +host upload/verify/download over loopback-only
  standard SDK NAT; ADB control only. Cold Binder/identity and direct TLS probes.

## j.2 candidate and existing File Manager entry
- DashboardLink.kt: bounded root HTTPS numeric private-IP URL validation; external
  browser navigation only. No credentials, WebView, bridge or trust override.
- MainActivity.kt: Cụm -> Mở File Manager web reuses existing Demo Dashboard;
  runtime labels reflect measured Node status and preserve UNKNOWN approvals.
- DashboardLinkTest.kt / NativeUiTest.kt: navigation policy and actual UI refusal.
- NativeUpgradeDataTest.kt: retained app/context identity and actual canonical
  Engine read/hash of an original v3 object after normal v4 APK upgrade and
  Android's lower-version refusal. No fixture identities packaged in main APK.


## j.3 retained original VM recovery qualification
- NativeCrashRecoveryTest.kt: requires pre-crash h.2b proof; real Keystore decrypt,
  same application/Node/Cluster/TLS/token/Volume and canonical local Engine byte
  hash. No seeding, credential reset, network grant or copied Termux state.


### Explicit API30/API35 synthetic qualification
tools/qualify_native_catalog.py --android-api {30,35} validates matching owned AVD
name/serial/actual ro.build.version.sdk. Default35 unchanged;30 uses5562. No phone
serial, identity reset, startup-budget or I/O assertion relaxation.


## Phase4 network-only Dashboard PWA

- docs/PHASE4-WEB-APP.md: Controller/CA/login/PWA/LAN/no-offline-write and safe
  upgrade/rollback operator guide; Linux install proof is not ChromeAndroid proof.
- NativeCandidateUpgradeTest.kt: separate exact APK4->5 retained app/context and
  committed bytes test, repeated after actual downgrade refusal. Keeps historical
  NativeUpgradeDataTest literal APK4 contract unchanged.
- NativeListenerRestartTest.kt: actual Android accepted TCP close/rebind and
  concurrent-listener rejection. NativeTLSListener privately owns accepted raw
  transport below server-mode JSSE for bounded cancellation of blocked TLS writes;
  Core receives TLS streams only. NativeSocketTest retains real binary/wrong-pin/
  nonreading read/write deadline assertions.
- tests/test_backup.py: original12fault matrix now requires actual SHA readback
  on two distinct domains of the restored head before scheduled-backup cohost
  loss. Restore's initial upload and async policy COPY are separate; no Core
  behavior, original failure assertions or acceptance deadlines changed.
- tests/test_gc_linux_faults.py: original five crash/replay gates require fresh
  successful actual Storage probes after healing/restart before crash injection.
  Same45s startup budget, five execution attempts,10s/250ms authority budgets,
  actual exit91/unlink/journal/whole-cluster assertions. Sanitized denial labels
  identify an unreached crash point; denied requests never count as a crash.
- asc/demo/dashboard/assets.py: one fixed public HTTP/package asset allowlist.
- dashboard/web/manifest.webmanifest,service-worker.js,icon-{192,512}.png: standalone
  browser metadata/network-only navigation, never caches API/file/owner data.
- dashboard/http.py: fixed MIME routes +manifest-src/worker-src self; existing
  no-store/auth/CSRF/mode guards retained. package.py reuses the exact allowlist.
- web/app.js: browser install event/prompt UX, no Node/native lifecycle control.
- tests/test_demo_dashboard +browser: real trusted TLS/PWA criteria/active SW/empty
  CacheStorage before and after full file/logout/offline workflow; old assertions kept.


### Phase4 closure diagnostics / artifact ownership
- qualification/phase4-closure-gc-investigation.json records full4/failed trials,
  unchanged GC budgets and next failed-target-first work; no Core fix claimed.
- qualification/phase4-web-native5-internal-snapshot.json plus distinct APK5/source
  artifacts preserve matching scoped Android/PWA proofs and exact-source audits.
  Debug review only, full regression BLOCKED; never use artifact availability as
  runtime/full-phase acceptance. PHASE4-STATUS/HANDOFF own current operator state.


### Core projection decode reuse (Phase4 closure)
- asc/failover/state.py:decode_validated/_validated_runtime_bytes retain only the
  structural validation result for two immutable <=2MiB byte inputs, returning a
  newly decoded document. Mutable validate/prepare_registry contracts unchanged.
- asc/failover/runtime.py:_cached/view use that decode path but still read/check
  the durable hash and fresh Go envelope, cluster/epoch/index/term/canonical bytes.
  ensure_ready, actual quorum receipts and all GC freshness/physical checks stay.
- tests/test_runtime_decode.py adds mutation isolation, malformed/bounded cache,
  fresh quorum loss, envelope rollback/hash/identity, canonical wire and durable
  corruption gates. Existing test_runtime_validation and original fault cases
  remain byte-identical. Current qualification is in PHASE4-2-PROGRESS.


### Published043 snapshot compatibility qualification
- tests/test_phase4_snapshot_upgrade.py pins exact e69(native-node) and c831(PWA)
  archives to b423(core-decode), real installed CLI/TLS bytes/pending/backup/new-
  state code rollback. Reuses original fixture helpers without changing any old
  test or product source; both old/new043 bridge APIs must still work.
- qualification/phase4-direct043-upgrade.json records2additional Linux synthetic
  tests, not a replacement/full394 claim; current source full392 remains frozen.


### API35 supplemental runtime evidence
- docs/PHASE4-API35-QUALIFICATION.md / qualification/phase4-api35-transport5.json:
  fresh ownership, offline preservation, boot and actual APK5 JSSE5test scope;
  Node/identity/process lifecycle acceptance remains separate. No new runtime.


Published4 baseline receipt: qualification/phase4-published4-cold-baseline.json,
existing NetworkReadinessTest1 +NativeCatalogTest2 on exact original APK4/blank
API30. Real existing Engine/Node/host Catalog, no new implementation. Cold+retained
workflow PASS, direct final5 upgrade remains separate/NOT TESTED until actual run.

Direct published APK4->final5 LOCAL-state receipt:
qualification/phase4-direct-published45-local.json (11 actual Android tests, API30).
Uses original NativeUpgradeDataTest/NativeCandidateUpgradeTest/UI/Binder/Engine;
no product or APK delta. Networked retained5 qualification remains separate.


Current exact direct published4->FINAL5 qualification:
`qualification/phase4-direct-published45-final.json` binds17Android executions,
3host selection guards, actual original4-first state/update/retained5 Node/old4
bytes after new5 writes. Existing canonical Engine/Catalog/tests reused. Raw state
private/offline, SDK STOPPED. Core/app/APKs unchanged; Native STATE/OPERATIONS/PILOT
and STATUS/HANDOFF own limited API30 SDK upgrade contract; API35 still blocked.

Fresh first-install published5 qualification:
qualification/phase4-fresh-final5-api30.json, NetworkReadiness1 +NativeCatalog2 on
new blank API30 (first main APK5 before identity), actual bytes/enrollment/TLS/FGS/
replicas/browser/fallback/Controller loss/process death. No new product code. Both
exact fresh/upgrade paths now observed; API35/physical limits retained.7SDK images/
32private host files verified offline; cache cleanup only public installer ZIPs.
