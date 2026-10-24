# ASC DATA MODEL — Conceptual v1

## Phase 2B development schema — Windows qualified

Runtime document schema 2 wraps unchanged validated Catalog schema 1 with
cluster/epoch/control revision, activation node/term, allowlisted authority rows
(nodes/join_codes/enrollments/catalog_nodes/catalog_jobs/catalog_job_history/
transfer_grants) and the bounded inventory cursor. Node/code/grant values are
hashes; job lease IDs alone are not bearer authority. Legacy whole-volume grants
are not promoted. A separate private runtime.sqlite3 caches the complete committed
document/state with SHA and applied checkpoint; it cannot become a writer without
a fresh quorum barrier. Base registry 4, manifest 1 and metadata cache 1 remain
unchanged. Explicit stopped-state upgrade compares the exact metadata SHA and
preserves the original guarded registry and object volumes. No automatic downgrade
or voter reset exists. See PHASE2B-ACCEPTANCE.md before using development commands.

No additional migration table is needed for attachment provenance: the permanent
`runtime-upgrade-<source Catalog SHA>` receipt binds the original full runtime
document SHA. Reconstructing takeover from frozen private rows must match that
SHA for a configured initial owner, or the local state must be an empty-authority
metadata follower of that exact source. Conflicting histories fail closed.
Manifest schema remains 1. NEEDS_REVIEW can return to READY only for a freshly
authorized distributed job whose retained staging AND immutable final body both
match the original size/SHA/session scope; ordinary legacy resume stays denied.

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

## Historical Phase 2A investigation and Go persistence continuation

Go qualification persistence is separate from registry 4: synchronous official
raft-boltdb stores checksummed stable values/log extensions; an immutable sealed
binding anchor and required buckets/keys prevent accidental state recreation.
An incomplete vote-term/candidate pair is quarantined. FSM snapshots include the
prepared projection, its SHA-256, applied index/term and bounded permanent request
receipts. Receipt exhaustion rejects new requests rather than deleting history.
The opt-in attachment now adds auxiliary consensus schema 1 while retaining base
registry 4, manifest 1 and public cache 1. It never rewrites local object bytes.

- `settings.consensus_mode=metadata-v1` persists the mode; no missing-config
  fallback to the legacy writer is allowed.
- `consensus_checkpoint`: singleton/schema/cluster/epoch/applied_index/applied_term/
  document_sha256. `consensus_receipts`: request_id plus canonical receipt JSON.
  Catalog state/files/replicas/events, checkpoint and receipts share one FULL
  SQLite transaction. No local clock/network/randomness runs during installation.
- Prepared document schema 1 exports full Catalog files/replicas/history, excludes
  nodes/credentials/jobs/grants and validates canonical ordering, event digests,
  history/materialization consistency and bounds. DECLARE records metadata with
  no byte/replica claim; POLICY preserves no-op revision behavior. Replication
  evidence commands remain refused pending distributed fencing.
- Explicit seed attachment requires exact metadata equality. Import is available
  only into a fresh empty matching-cluster registry; independently initialized
  nonempty epochs cannot be merged. Export/import CLI never overwrites a seed.
- Raft snapshots and log tails can overlap or have gaps fully covered by a
  validated snapshot. Startup verifies the latest snapshot and every retained
  log; gaps beyond that snapshot quarantine. The outer `.enrolled` witness
  prevents reinitializing a known voter after loss of its entire state directory.
- Full prepared document limit: 2 MiB; receipts: 4096 without eviction. A new
  request after exhaustion fails explicitly. An identical intent/request ID
  reuses its committed result across preparation, timeout, snapshot and restart.

Rollback: stop all three development voters and Controllers, retain all current
state/witnesses/configs/objects, then restore complete pre-attachment registry
backups and matching v0.6 source in an isolated environment. This loses subsequent
consensus metadata. Do not drop triggers/mode/checkpoint or edit term/schema as a
rollback shortcut; do not resurrect an unfenced old cluster. No automatic quorum
rebuild, membership change or state-loss reset is provided.

The following paragraphs retain the original pre-Go design/status as history.

Runtime schemas stay registry 4, local manifest 1 and read-only metadata cache 1. No Raft database, schema-5 migration, new epoch or voter bootstrap state was created. See PHASE2A-ACCEPTANCE.md for engine rejection and the current-state classification.

Proposed future consensus persistence must bind cluster/node identity, engine/schema version, membership, term/vote, indexed log, commit/applied checkpoint and validated snapshot metadata. Lost/corrupt state must stop participation rather than initialize defaults. Existing Catalog epoch/revision alone is not sufficient Raft authority.

A future apply transaction must atomically store Catalog changes/event, applied index/term and permanent replay-safe request receipt (ID, payload digest, result). Prepared command IDs/timestamps/placement must not be regenerated during replay. A snapshot needs the applied checkpoint, membership and receipt set alongside consistent materialization/checksums; schema-1 public exports omit these. Preserve logs until safe snapshot installation/compaction is implemented and tested. These are pending contracts, not a schema currently accepted by source.

## Phase 3A extension persistence

The optional `backup` member of runtime schema 2 has its own `schema:1` and strict
bounded maps: files (256 tombstones), snapshots (64 manifests), jobs (256),
schedules (32), policies (256), requests (512 intent/result receipts). Overall
runtime 2 MiB and Go permanent 4096-receipt limits still apply; exhaustion rejects
new work rather than evicting authority. MemoryRegistry carries this JSON in its
private disposable settings only; the persistent authority is the Go document.

Snapshot manifest binds cluster/epoch, source applied index/term, control revision,
Catalog revision/digest, captured creation time and immutable file descriptors.
Manifest SHA excludes later verification/expiry state. Job proofs record streamed
size/SHA, approved distinct domains and verification time. Backup/restore jobs have
lease/run IDs and durable cursors; takeover resets active proof progress and leases.
Restore reserves max Catalog/pending-restore version+1; its stable existing UPLOAD
key is restore-<job UUID>. Old/new objects and their manifests are never overwritten.

LIVE is implicit. TRASH and EXPIRED tombstones affect namespace/download eligibility;
metadata version history remains. Retained snapshots and active restore jobs pin
versions. keep_last plus minimum age expires only older unpinned versions; trash
expires after its grace period. Scheduled retention is logical, physical GC absent.

Rollback: before enable upgrade all stopped development Controllers and retain full
private state/witnesses/volumes and matching v0.8 source. Once enabled, old runtime
validators refuse the extension. Stop/isolate all voters and restore complete
pre-enable private backups plus matching source; preserve post-enable state and
objects separately. Do not remove the extension, lower schemas or edit Raft state.
The latest historically verified version is also retained while a higher version
is still incomplete. Older-version age/count retention counts verified versions.

## Phase 3B insights schema 1 (explicit opt-in)

Optional runtime `insights`: schema=1, history (<=16 node records), requests
(<=128 permanent owner intent/result receipts). Per node: approved credential
generation, last_sample_at, <=24 hourly buckets and <=30 daily buckets. Each
bucket contains raw sums/counts for capacity_ratio/reachable/memory_mb/thermal_c,
with at most one fresh probe sample per node per calendar hour. No raw profiles,
addresses, secrets or unbounded samples enter this extension. Base registry 4,
Engine manifest 1, public metadata cache 1 and Phase 3A backup schema are unchanged.

24h/7d/30d means UTC calendar buckets including the partial current bucket; gaps
are null with zero observed samples, never fabricated outage/uptime. Reliability
is observed successful probes / observed probes in the reported window. Score
reliability remains fresh for 3600 seconds (hourly sampling); other score inputs
retain 120-second freshness. Prior-generation history is retained/tagged and not
used for new-generation scores. Whole-runtime 2 MiB / Go 4096 permanent receipts
remain limits: sustained long-running deployments can exhaust receipts before
30 days. Retention describes available history, not a promise of 30-day runtime
capacity. No authority receipt is evicted to collect telemetry.

Rollback requires complete stopped/isolated pre-enable backups and matching source;
retain newer runtime/history/backup/object state separately. Old validators refuse
the extension; never remove it by hand or change schemas/terms to downgrade.

3B.3 adds optional bounded `insights.preferences` (<=64 node records), each exactly
mode/generation/updated_at. Existing insights without preferences remain valid.
All Controllers must upgrade before the first preference write. Old code rejects
unknown extension fields. Restrictive modes survive credential-generation changes;
stale Preferred becomes Auto until owner explicitly sets it for the new identity.
No node identity, Catalog replica/version/backup or raw token is overwritten.
