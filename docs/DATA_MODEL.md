# ASC DATA MODEL — Conceptual v1

No production schema exists. These logical entities and invariants must be represented in the initial migrations and wire contract.

## Entities
- `Cluster`: immutable cluster_id, configuration epoch, protocol/schema version.
- `Node`: immutable random node_id, public identity key, display_name, trust state, capabilities, last_seen_at, protected_mode flag.
- `Membership`: voter/non-voter set, configuration epoch, committed index.
- `Volume`: volume_id, node_id, adapter_type (internal, termux_sd, saf_bridge), filesystem identity (when available), available bytes, reserve bytes, health, mount status.
- `FileEntry`: file_id (stable), parent_id, display name, owner/ACL, current object/version pointer, tombstone state.
- `FileVersion`: version_id, object_id, size, hash, creation metadata, retention/deletion rules.
- `Object`: immutable object_id, sha256 digest, verified size, object lifecycle state.
- `Replica`: object_id, node_id, volume_id, local object path (never trusted from user request), verified_at, health, write_epoch.
- `Job`: job_id, idempotency_key, operation, state, retries, creation/expiry, authorized principal.
- `Event`: committed raft_index, term, event_type, schema_version, payload_digest, prev_hash when audit chaining enabled.
- `Snapshot`: cluster_id, committed_index, term, created_at, hash, metadata schema version.
- `Principal`, `Session`, `AccessGrant`: API identity/permissions and expirations.

## Invariants
1. Every committed `FileEntry.current_version` references an existing, verified `Object` (it may later be temporarily offline).
2. `Replica.verified_at` requires size + digest verification at the destination.
3. Presence in global catalog != contents currently reachable.
4. Replaying a committed event twice must not duplicate effects.
5. Data-plane operations are scoped to safe logical IDs; no arbitrary shell command/path from Controller.
6. Two independent copies must have distinct physical failure domains for the chosen replica policy.
7. Deletes are logical first. Garbage collection verifies reference counts, retention and sufficient remaining replicas before physical removal.
8. Node identities do not change when their IP address changes; lost keys require a controlled re-enrollment.
9. Epoch/term alone is not proof of commit; validated quorum authority is required.
10. A corrupted/lost SQLite local cache is rebuilt from an authenticated committed snapshot plus logs or local manifest, not declared canonical on its own.

## Actually implemented in v0.4
Controller SQLite `settings(key,value)`, `nodes(node_id,name,token_hash,profile,last_seen,joined_at)`, `join_codes(code_hash,expires_at,used)`.
Nodes store private `~/.asc/node.json` and atomic `~/.asc/topology_snapshot.json` (only registry topology). Controller stores `~/.asc/controller.json`, `registry.sqlite3`, `server.crt`, `server.key`.
No file catalog, data replicas, consensus log, access grants, migrations or backup persistence are implemented yet.

## Implemented Phase 1.1 — registry schema 2 / local config 1

The conceptual entities above are still future work. This migration is only the
single-writer development node registry, not a file or consensus schema.

- SQLite PRAGMA user_version: legacy v0.4=0, Phase 1.1=2. On controller-run,
  Registry.initialize validates cluster_id/known schema version (only 0 or 2) and uses BEGIN IMMEDIATE
  for idempotent CREATE/ALTER/version update in one transaction. Original settings,
  nodes and codes are retained; a cluster mismatch/newer schema aborts migration.
  Registry connection contexts commit/rollback then close SQLite handles explicitly,
  including authentication failures, to avoid accumulating descriptors on long runs.
  Controller-run requires an existing registry with the configured cluster_id before
  migration; a missing/empty/mismatched registry is not silently recreated.
- nodes retains every old column and adds state TEXT NOT NULL DEFAULT 'active',
  token_version INTEGER NOT NULL DEFAULT 1, revoked_at INTEGER NULL. Revoke writes
  a non-hash invalid marker, state=revoked and timestamp, increasing generation only
  once. Re-pair writes a fresh token hash and increments generation without changing ID.
- join_codes adds target_node_id TEXT NULL, enrollment_hash TEXT NULL, node_id TEXT NULL.
  The first field restricts grants to an existing node; the others bind a consumed
  grant to its retry operation/result. Codes remain SHA256 hashes. Expired rows older
  than 24 hours are cleaned when a new code is issued; newer used rows support retries.
- enrollments(enrollment_hash TEXT PRIMARY KEY,node_id TEXT NOT NULL) permanently
  routes hashed operation IDs to node IDs, including revoked/rotated operations.
  It holds no plaintext tokens or codes. It prevents a renewed initial grant from
  duplicating a successfully registered node after a lost reply or code cleanup.
- Node token hashes and code/operation hashes never appear in topology/detail output.
  Snapshot adds schema_version=2/protocol_version=1 plus public lifecycle fields.
  Revoked nodes remain in the registry; they are not deleted or eligible for active roles.

New controller.json/node.json carry config_version=1. Versionless v0.4 configs are
read as legacy without implicit rewrite, preserving ID, token, pin and cluster.
New profile_version=1 adds labeled score/device/SD status while retaining old fields;
versionless wire profiles remain compatible. Unknown explicit versions are rejected
on wire; local configs with unsupported explicit versions must not be used.

Private local files (default ~/.asc, outside source/shared storage):
- controller.json, server.crt/server.key, registry.sqlite3 (and SQLite WAL/SHM).
- node.json: controller origin/pin, cluster/node ID, private token and optional generation.
- enrollment_pending.json: version 1, pinned destination, expected cluster, target,
  original profile and private request code/operation/token. Written before networking
  mutation. Restart retries it; completed node.json is never implicitly replaced.
- enrollment_abandoned-*.json and node_before_repair-*.json: explicit recovery copies,
  equally sensitive; never added to source distribution. Replacement initial codes
  preserve the operation/token; targeted re-pair may explicitly start a new operation.
- agent_state.json: credential_status (unknown until checked, active or repair-required)
  and checked_at. Active is a last observed result, not a live authorization guarantee.
- topology_snapshot.json: atomic private cached topology, not a verified Raft snapshot.
- controller.lock / agent.lock: OS-held advisory locks; files may persist after exit,
  existence alone is not proof of a running process. No PID identity is trusted for kill.
  Status returns null when lock state cannot be verified, rather than guessing running.

New secret files use exclusive creation; explicit re-pair, status and topology updates
use temporary 0600 files, fsync then atomic replacement. No automatic secret rotation
on reinstall, reconnect or authentication failure. Crash-corrupted private files require
manual recovery; full power-loss durability across Android filesystems is not claimed.

### Rollback compatibility
v0.4 Controller INSERTs assume the old column count and do not enforce revoked state.
Never point old Controller code at schema 2. Before migration stop all ASC processes,
copy the complete private state (including WAL/SHM) to a private timestamped directory,
keep v0.4 source unchanged and run new code from a separate versioned directory.
Rollback restores that pre-upgrade state per device; it loses later changes and may
reactivate credentials revoked since the snapshot. See README sections 7/9. Ordinary
v0.4 agents can continue heartbeating the upgraded Controller with their existing tokens.

## Implemented Phase 1.2A — registry 3 / manifest 1

Registry initialize accepts user_version 0, 2 or 3, validates cluster identity and migrates transactionally to 3. Existing lifecycle tables, IDs, hashes, timestamps and unused codes are retained. New storage_grants columns: grant_hash PK, node_id, volume_id, token_version, principal, operations JSON, expires_at. Only SHA-256 of the random owner bearer is persisted. Expired rows are pruned at mint; at most 1024 active grants. Profile version remains 1/legacy compatible; profile.storage has storage_version=1.

A separate private HOME/storage/manifest.sqlite3 uses WAL, synchronous FULL and explicit closed connection contexts. New/empty schema 0 initializes to 1 transactionally. Known schema 1 opens idempotently; future/unknown versions or a different node identity abort. This is the initial manifest migration contract, independent of registry version.

| Table | Fields / invariants |
|---|---|
| settings | node_id, immutable manifest owner |
| volumes | volume_id UUID PK, node_id, kind, approved absolute local root UNIQUE, observed medium identity, quota bytes, reserve bytes |
| uploads | session_id UUID PK, file_id UUID UNIQUE, principal, idempotency_key, logical_path, volume_id, size, sha256, version=1, state, created_at, updated_at; principal/key UNIQUE; live logical path per volume UNIQUE |
| files | file_id UUID PK, logical_path, volume_id, relative_path, size, sha256, version=1, state, created_at, updated_at, last_verified_at nullable; volume/logical path UNIQUE |

Absolute roots are node-local configuration, never global IDs or wire file paths. Physical names are staging/<session UUID>.part and objects/<file UUID>.blob. Logical names are labels only. Equal idempotency key + principal returns the same session only if all requested content/name/volume fields match. A different key at an occupied logical path conflicts; replacement/version increment is deferred.

Upload states: INITIATED -> WRITING -> READY -> COMMITTING -> COMMITTED. EOF/IO interruption becomes INTERRUPTED (resend full body); bad checksum becomes FAILED. EXPIRED releases an explicitly cleaned staging session. Ambiguous commit/revocation becomes NEEDS_REVIEW and reserves its data. Restart maps WRITING to INTERRUPTED; COMMITTING returns READY only when both staging and final size/hash match, requiring a fresh explicit authorized commit. It never silently publishes.

File states: COMMITTED, CORRUPT, MISSING, VOLUME_UNAVAILABLE, METADATA_CONFLICT. Startup rechecks manifest references and physical hash; unknown/missing verification has last_verified_at=null. Metadata conflicts never become filesystem paths. Inventory reports unreferenced objects, with bounded output, and never adopts/deletes them.

Schema-3 rollback requires the complete stopped-state pre-upgrade schema-2/0 backup and matching old source, not an edited PRAGMA. Preserve new manifest/volume contents separately: reverting source does not remove user objects. Restoring old state can lose later registry changes/reactivate old credentials; isolate the environment and review credentials. No automatic downgrade.

## Implemented Phase 1.2B — registry 4 / local manifest 1 / metadata cache 1

Registry.initialize accepts 0, 2, 3 or 4 and validates the existing cluster identity before additive transactional migration. Node IDs, raw-token hashes, codes, enrollment history, TLS/config files and owner storage grants are preserved. Migration never opens/rewrites Agent manifests or object bodies. Failure rolls back new tables/version; future/unknown versions are rejected. Global cluster_id remains in registry settings; catalog_state holds a persistent random epoch, monotone revision and digest head. Epoch is not a Raft term.

| Table | Purpose / important fields |
|---|---|
| catalog_state | singleton, epoch, revision, head_digest |
| catalog_nodes | explicit node_id, private origin/pin, device_id failure domain, metadata/storage permission, approved generation/volumes, controller-probed capabilities/timestamp/error, last metadata ack |
| catalog_files | global file_id, logical_path, explicit version, size, sha256, current policy, created/updated/revision, immutable upload_key + upload_policy fingerprint; path/version UNIQUE |
| catalog_replicas | replica_id, global file_id, node_id, volume_id, local_file_id, state, created/updated/verified time; local physical reference UNIQUE |
| catalog_events | ordered revision, epoch, previous_digest, digest, canonical public file/replica payload, time |
| catalog_jobs | job_id/key, global file/replica, UPLOAD/COPY, state, source replica, target node/volume/local object/session, generated local logical path, attempts/backoff, run token/lease/generations, fixed error/times |
| catalog_job_history | private ordered state/error/time transitions; API returns latest 200 |
| transfer_grants | SHA-256 token hash only, node/volume/generation, job/side/run token or exact local file, expiration |

Global file_id identifies one immutable logical version; different explicit versions at the same path get distinct IDs. Local_file_id is a separate UUID from the Agent manifest. A new key cannot overwrite an occupied path/version. Replaying the original upload key/content/policy resolves its same file even after a later explicit policy change. Replica local paths are generated _asc-global/<global ID>/<replica ID>; host roots/absolute file paths never enter the metadata replica.

Replica states VERIFIED/MISSING/CORRUPT/UNAVAILABLE/METADATA_CONFLICT are evidence states, not replica-count guesses. Only physical verification can add/reverify a replica. Repeating an unchanged failure does not mutate timestamps behind an unchanged revision. Controller reports desired count from policy, verified distinct approved device domains from evidence, and available count from recent reachable/readable active identities. Keep last verification timestamp visible; offline or revoked authority does not prove bytes were deleted.

Jobs are PENDING/RUNNING/COMPLETED/RETRY/FAILED. Claim/checkpoint is durable before transferring body bytes. A unique active file/target-node index and stable job key/principal/session/local path prevent retry duplicates. RUNNING jobs have lease/run-token fencing and generation checks. Restart under the exclusive OS worker lock converts unfinished RUNNING jobs to RETRY, retaining checkpoints. Backoff is min(300,2^attempts) seconds, default five failed attempts; explicit owner retry resets the retry cycle on the same job. No failure transition deletes bytes or metadata. Uncompleted owner uploads remain pending until resumed/completed/reconciled; expired grants do not erase their reservation.

File/policy/replica materialization and public change event commit atomically. Private node approval/probe, job bookkeeping, metadata ack and inventory cursors are not replicated file events. settings.catalog_inventory_cursor stores fair per-volume offsets and pair rotation across restart. Completed/suspect replicas remain recorded; reducing policy does not perform GC.

Node private catalog-metadata.sqlite3 is cache schema 1: replica_state (cluster/epoch/revision/head/controller revision/last sync), replica_files (canonical public aggregates), replica_events (recent imported digests). Snapshot/delta imports are atomic with explicit closed SQLite handles. read_only=True uses SQLite mode=ro and validates cluster/schema; there is no authoritative mutation entrypoint. Snapshots exclude identity/token/grant/job/private-control tables. File names and digests still contain private user metadata and require approved access.

Standalone v0.5 committed files remain intact in local manifest 1 and are reported as uncatalogued. They are not silently promoted into global replicas. Automatic import/deletion is deferred; global uploads managed in this phase use generated job namespaces.

Rollback requires matching source plus complete stopped-state pre-upgrade private backups (registry/DB/WAL/config/keys) and retained volumes. v0.5 Controller refuses schema 4. Never lower PRAGMA by hand or erase objects to downgrade. Preserve v0.6 metadata/manifests/objects separately; restoring older identities can reactivate old secrets and loses later registry/catalog changes. Cache checkpoints ahead of a restored Controller are intentionally rejected; epoch/recovery planning is operator-controlled, not automatic failover.

An already-initialized schema-4 registry must contain its Catalog tables and epoch/checkpoint. Missing authority is a restore blocker; initialize never silently recreates an epoch over existing Catalog data.
