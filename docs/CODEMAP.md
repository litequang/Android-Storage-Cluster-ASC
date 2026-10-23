# ASC CODEMAP — v0.5.0 / Phase 1.2A

Read AGENTS.md first. Runtime is single-writer development, with opt-in node-local file storage. Distributed metadata, Raft, backups and production integration remain future work.

| Concern | Source / entry points | Tests |
|---|---|---|
| Device identity, protected M51/unknown-device guard, real telemetry and SD discovery | asc/probe.py: inspect, _detect_sd_locations, probe_sd_write; asc/cli.py: _must_not_protected | test_foundation, test_lifecycle.DeviceSafetyTests |
| Advisory coordination roles, excluding revoked/offline/protected nodes | asc/planner.py: recommend | foundation/lifecycle |
| Bounded v1 profiles/requests; nested storage_version=1 capability | asc/validation.py: profile, payload | lifecycle + storage_cluster |
| Registry schema 3, additive 0/2 migration, enrollment/re-pair/revoke | asc/store.py: Registry.initialize/connect/join/heartbeat/revoke/snapshot | RegistryLifecycleTests, including migration/file-handle release |
| Owner data delegation separate from node identity | asc/store.py: storage_grant/storage_authorize; asc/server.py admin/storage-grant + storage/authorize | schema-two migration, storage_cluster auth/rotation/expiry cases |
| Controller HTTPS, bounded workers and auth/join budgets | asc/server.py: Server, Handler, RateLimiter | LifecycleHTTPTests, LimiterTests |
| Pin before sending credentials, shared transport | asc/client.py: connect_pinned, request_json | real TLS lifecycle/foundation + storage_cluster wrong-pin case |
| Private identity/config, OpenSSL PATH diagnostics, exclusive creation | asc/identity.py: require_openssl, make_cert, save_private, replace_private | test_identity, ClientIdentityTests |
| Foreground locks | asc/runtime.py: foreground_lock, running | lifecycle + StorageEngine lifetime lock |
| Private node manifest schema 1 | asc/storage/manifest.py: Manifest/connect | test_storage restart, schema/identity rejection, immediate Windows SQLite release |
| Approved volumes, medium identity, root safety, actual probe/space, physical allocation | asc/storage/volumes.py: VolumeManager.register/discover/inspect; LocalVolume.check/open/allocated_files/remove_staging | test_storage junction/symlink/hardlink, replaced media, quota/unknown telemetry |
| Immutable objects, sessions, bounded streaming, integrity/recovery | asc/storage/engine.py: initiate/upload/commit/download/verify/recover/inventory/cleanup/capabilities | test_storage fault injection |
| Node HTTPS API /storage/v1, controller introspection and upload deadline | asc/storage/http.py: StorageServer, StorageHandler, UploadBody | test_storage_cluster + deadline test |
| Bounded owner transfer client | asc/storage/client.py: StorageClient.initiate/upload/commit/download/json | actual HTTPS and CLI roundtrips |
| Opt-in storage TLS/config/runtime | asc/storage/runtime.py: setup/load_config/StorageRuntime | storage_cluster runtime restart |
| Storage CLI | asc/storage/cli.py: register; commands storage-init/add-volume/status/cleanup/upload/download, controller-storage-grant | storage_cluster CLI and protected setup refusal |
| Lifecycle CLI and agent heartbeat/runtime integration | asc/cli.py: controller_*, _enroll, agent_once/run, local_status, main | lifecycle + storage_cluster actual heartbeat |
| Three simulated nodes ZTE V40, Bphone A40, Sony XZ3 | tests/test_storage_cluster.py: ClusterTests | separate temp private states/roots, pinned controller+agent HTTPS, no phone |
| Installer (unchanged) and launch scripts | install.sh, scripts/run-controller.sh, scripts/run-agent.sh | test_installer requires POSIX Bash; never installed on phones in this phase |
| Release / secrets exclusion | asc/__init__.py, .gitignore, .gitattributes | release 0.5.0; inspect tracked and staged contents before publish |

## Routing rules

- Upload: owner grant -> agent HTTP auth -> pinned controller introspection -> engine session -> generated staging -> exclusive object copy -> reauthorization -> manifest commit.
- Download: scoped read grant -> validated manifest/UUID -> full physical hash -> streaming response -> client SHA verification.
- Re-pair/revoke: controller Registry changes node generation/state; grants from the previous generation fail at introspection. Agent preserves identity.
- Restart/media errors: StorageRuntime -> StorageEngine.recover -> verify files; no automatic publication/deletion. inventory reports unreferenced objects.
- Missing OpenSSL: identity.require_openssl, README section 8, TROUBLESHOOTING. Missing executable is an error, never a TLS skip.
- Windows SQLite locks: both registry/manifest connection contexts close in finally; test_lifecycle/test_storage immediately rename/delete stopped fixture DBs.
- API/auth contracts: NODE_PROTOCOL. Schema/migration/rollback: DATA_MODEL + README section 11. Failure handling: TROUBLESHOOTING. Architecture choices: ADR-023 onward.
- Windows local simulation is the supported acceptance path. Android setup commands are deferred reference and retain protected/unknown-device refusal. No M51 access.

- Windows early TLS rejection: server.Handler._read_json bounded oversize discard; LifecycleHTTPTests.test_bad_schema_size_and_pin_never_send_join still requires 413 and unused enrollment code.

- Pre-migration status reports the actual unsupported/older schema and migration instruction instead of advertising schema 3 over a schema-2 database. Streaming client closes a connection when header setup fails.

- Volume probe distinguishes a measured read-only denial from unknown IO failure; test_read_only_probe_reports_measured_denial_and_advisory_backup covers the Backup advisory branch.

- Final Codex Windows acceptance: 61 tests OK (3 POSIX installer skips), actual three-node HTTPS PASS; full command/provenance/limits in docs/PHASE1-2A-ACCEPTANCE.md. No subsequent source/test changes.
