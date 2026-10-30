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

3B.4 history buckets additionally tag credential generation (older buckets infer
the record generation until the next capture). Re-pair keeps old buckets and adds
new-generation samples separately, even within the same UTC hour/day. The same
24/30 record bounds apply across generations; frequent re-pair can reduce window
coverage, reported through gaps. History exposes generations; score filters to the
current approved generation. No authority/backup/history outside telemetry is pruned.

## Phase 3C replication schema 1 (explicit enable)

Optional `replication` member: schema=1 and requests map (<=256 permanent intent/
result receipts). All Controllers upgrade first; older validators reject unknown
extension. Existing base schemas and 3A/3B members remain unchanged. Policy count
1/2/3 maps to single/replicated_2/replicated_3. Policy and scheduled jobs commit
in one prepared runtime document; receipt conflicts fail closed. No automatic
receipt/history eviction. Complete stopped pre-enable state/volume backups plus
matching source are required for rollback; physical GC is still absent in 3C.1.

3C.2a optional replication.moves map (<=128): move ID -> file_id/source_replica_id,
job_id (nullable if enough other domains already exist), COPY_PENDING/READY,
created_at/updated_at. Same-source planning reuses durable intent; takeover retains
intent while existing COPY leases/grants receive their established invalidation.

3C.2b move terminal state RETIRED plus optional replication.retired (<=256 records).
Key is original replica ID; record retains exact original replica, immutable file
identity/size/SHA/version/path, required_domains, fresh proof records, retirement
term/time. Proofs bind replica/node/volume/local IDs, approved physical domain and
credential generation, size/SHA and observation time. Catalog removal/event and
retirement record share the quorum-committed document. Old events and completed
job pointers are retained and continue to hold future physical GC.

A retired physical identity cannot appear in current Catalog replicas or active/
retryable job sources/targets, even under another replica ID. This fence survives
snapshot/replay/takeover and cannot be removed to roll back metadata independently
of bytes. Whole-runtime and authority receipt bounds remain fail-closed.

3C.3b optional replication.archived_jobs <=512 permanent records: job_id/file_id,
kind/state=COMPLETED, created_at/updated_at/archived_at, original_sha256 and
completion_sha256. The latter binds original session/local-file IDs by digest
without retaining a usable physical pointer. State history rows remain unchanged.
No archived ID may reappear in catalog_jobs; immutable archive receipts and exact
prior completed-row hash are checked at every Runtime transition. Archive is
explicit and may still reclaim zero bytes because retained events/snapshots/jobs
hold them. Lifetime limits never silently evict archived identity or authority.

3C.4a optional replication.gc_plans <=64 and gc_jobs <=128. Plans bind target retired
ID, graph/plan SHA, source term/control/index, 60s time bounds, required domains and
fresh proof records. Immutable plan rows are preserved by every Runtime writer.
Jobs bind immutable confirmation/target/plan/graph/term plus RESERVED/RUNNING/DONE,
permit term/hash/run/expiry, proofs, attempts/error/times. No raw grant is persisted.
RESERVED has no permit/proof; RUNNING permits must match the current authority term
and bounded 120s lifetime; DONE is immutable. Takeover resets unfinished execution
to RESERVED with no permission; reservations/confirmation/audit identity remain.
Lifetime/2 MiB/Go receipt bounds fail closed without erasing reference history.

3C.4b test-only private files under Engine HOME: gc-test-volume-<volume UUID>.json
binds schema 1, node/volume/root/medium and root-subdirectory identities plus arena ID.
A first binding refuses any existing upload/file/body; a marker alone never activates
ordinary runtime. gc-journal-<volume UUID>.sqlite3 schema 1 binds the arena SHA and
<=256 immutable job/object identities with digest and PREPARED/DELETING/DONE phase.
No grant token is stored. Unknown schema/binding/hash/link fails closed. Base local
manifest schema stays 1; after confirmed unlink its exact file row is removed,
completed upload receipt remains. Restart cannot republish the deleted body; old
Controller upload completion is served from the permanent archived receipt instead.
Rollback after deletion requires matching retained byte backups, not metadata alone.

3C.4c uses existing gc_jobs fields without a schema migration. permit_hash is SHA-256 over a canonical binding of bearer SHA plus target node, volume, credential/approved generation, device domain and endpoint/pin. Only the raw bearer in memory is sent to the pinned exact target. A new execution replaces run/hash/proofs/120s expiry and increments attempts on the same immutable job. RUNNING last_error=execution_unconfirmed remains until exact authenticated completion; takeover resets unfinished permits as before. DONE retains its immutable outcome and survivor references. The existing node journal identity excludes ephemeral permit/run fields, permitting the same exact object to recover after renewal/takeover without a second unlink. No raw token is added to request receipts or logs.

Linux 3C.5 structural-validation reuse is memory-only: two successfully validated
exact immutable canonical Catalog byte strings, each <=2 MiB. Native JSON type
checks avoid representation aliases; caller dictionaries and failed inputs are
not cached. No persisted schema, receipt, manifest, journal or authority change.

## Phase 3D external local format1

Separate operator-private store.json {format:1,store_id UUID,kind}, working/ and
completed/ directories. Each UUID bundle: canonical manifest.json, exact canonical
runtime2 metadata.json, objects/<global-file-UUID>.blob, then complete.json binding
manifest SHA/objects/bytes. Manifest binds capture cluster/epoch/index/term/authority,
control/Catalog revisions/digest, metadata SHA and ALL version descriptors, with
writer_recovery_supported=false/secrets_included=false. This excludes raw keys/
tokens, not sensitive hash/name/profile/endpoint metadata. Never publish backups.
Per-object <global-ID>.part is transaction-owned temporary data; retry can replace
only that exact private partial. Atomic hardlink publication refuses overwrite;
known exact two-link .part/.blob crash is proved by inode+SHA before partial unlink.
No completed object or source byte is deleted/replaced. Manifest/metadata/status
must validate; init interruption before durable capture may remain INCOMPLETE for
operator review. Base schemas and old code compatibility remain unchanged.

External VERIFY is returned evidence (verified_at/checked_at/integrity/coverage/
known-index floor), not a permanent mutable archive state. Stale integrity-valid
backup reports STALE; inaccessible values UNKNOWN/null. No schema/receipt change
or last-verified retention deletion authority. Manifest SHA must be retained
separately; a rehashed corrupt store cannot replace the trusted anchor.

Recovery format1: RECOVERY_READ_ONLY.json binds backup UUID/trusted manifest SHA/
cluster/source index/operator minimum index with writer_authority=false and
credentials_restored=false. Exact original metadata.json/manifest.json and
objects/<global-ID>.blob preserve original historical relationships, not physical
medium adoption. READY.json binds intent SHA/manifest SHA/object count/bytes after
complete independent readback. No registry/manifest/Raft DB/config/key is created.
Interrupted same-intent resume never resets IDs/known-history floor or overwrites
a completed object; corrupt/foreign state held. No base schema migration.


<!-- Reviewed Demo c9c2660 historical extension; current Phase4 status is in PHASE4-PROGRESS. -->
## Demo source package format 1 (DEMO.1)
`release.json` records format=1, version, capabilities, exact state_formats, a mapping
of relative public source paths to SHA-256, and release_id=SHA256(canonical sorted
compact JSON of every field except release_id). No links/special/unlisted/missing
files are accepted. Prefix install.json format=1 selects releases/<release_id>;
source and launcher are exclusive-create/verify-on-rerun. No private identity/schema
is created or migrated by install. Preview capability is installer only.

## Demo private state format 1 (DEMO.2)
<state>/demo.json contains exactly format, track=android-demo-alpha,
mode=single-writer-demo, role=controller|node, stable installation_id, state_formats
(demo1/registry4/manifest1/metadata1/config1/wire1), explicit host and port.
Controller identity/certs/registry live in controller/, enrolled identity/certs/
manifest/cache in node/. Core schemas are reused unchanged. An unmarked existing
root, unknown version, consensus/extension state, missing registry/node identity or
mismatched node/cluster is refused before Core constructors can create/migrate it.
Internal file data is the dedicated node/data root; explicitly approved SD adapters
still require the existing Termux app-folder and UUID/medium checks. Repeated setup
with identical parameters verifies rather than replaces identities/volume markers.

## Demo backup/activation format 1 (DEMO.3a)
Prefix state-binding.json records format, absolute private root, installation UUID.
It never includes Controller/node credentials. install.json remains format/release_id.
upgrade-journal.json records format, status PREPARED|COMPLETED|RECOVERED_OLD_CODE,
action, installation UUID, old/new release IDs, private backup path and backup digest.
PREPARED denies runtime even after the new pointer was persisted.
Private backup-complete.json records format=1, installation UUID, exact formats,
selected release ID, source label/root map, entries (directories plus file size/SHA)
and SHA256(canonical body excluding backup_sha256). state/ contains all stopped
private state/bodies; external volumes use volume-<UUID>/, preserving empty directories.
Only known OS coordination lock files are excluded. Completion follows source
stability and copied readback verification; failed copies stay incomplete. Backup
is private and is never part of a public package. No schema restore/migrator exists.

Demo coordination files keep Core's empty-or-one-space convention and OS locks; no
state/schema migration in DEMO.3a.1. Existing linked/nonregular/multi-link or unexpected
coordination files are refused/preserved before writes; never auto-delete a lock.

## Optional Dashboard state 1 (DEMO.4a)
Base Demo/registry/manifest/cache/wire formats unchanged. Private dashboard/ holds
CA key/public certificate, separate leaf key/cert, empty bounded ephemeral spool/
and dashboard.json exactly format=1, host (existing Controller IP), distinct port,
max_upload_bytes<=32 MiB. No key/cert regeneration over existing/partial state.
Completed optional config is checked before new writable Core open; partial state
without config is retained, never adopted into a running Dashboard. Old 0.3.0 can
ignore optional directory in CLI-only mode; complete stopped backups include it.
Login grant hashes/expiry, session hashes/CSRF/expiry and transfer ticket/status/
actual bytes live only in bounded RAM, never a second persistent Catalog. Restart
invalidates them; durable upload key/job/session/object authority remains in Core.

### Demo 0.3 -> 0.4 compatibility
0.4.0 adds dashboard-lite release capability, with identical base STATE_FORMATS and no Catalog/Registry/Manifest/config migration. Optional Controller dashboard/dashboard.json format1 and own CA/leaf/spool are separate from Core identity and included by existing complete-state inventory backup. Exact published0.3 launchers accept compatible0.4 manifests; old0.3 CLI code ignores optional Dashboard directory on rollback, preserving both files written by0.4 and browser identity. No Termux/APK, Raft or unknown-schema migration is implied. Runtime browser sessions/tickets remain volatile, no second database.

### DEMO.4d storage compatibility (no migration)
Volume record/marker/schema unchanged: persisted root/medium st_dev:st_ino and node/volume IDs remain exact. New POSIX anchor snapshots/descriptors/file identities are operation-local only; no identity regeneration, new schema, database rewrite or medium cloning. Existing immutable objects/uploads/jobs remain unchanged. Exact old-code upgrade/rollback must be separately qualified for0.4.1; rollback can restore Android root-open bug even though schemas are compatible.

### Demo0.4.1 exact published-package compatibility
Adds release capability android-volume-anchor but retains all base formats and0.4 optional Dashboard state1. Exact0.3/0.4 installed launchers accept compatible0.4.1 manifest; no schema migration. Tests explicitly backup/verify/stage/preflight/upgrade with root open denied, retain core and existing04 browser identities and data, write new file, make NEW backup then select old code over new state. Old Android root-open defect is retained on downgrade and is not called functional Android rollback. Old/new bytes still read under baseline Linux proving schema compatibility; no database restore or medium/state rewrite.

## Phase4.0 compatibility
No schema/format increment. Optional expected Cluster ID CLI validation reuses
existing pending expected_cluster_id; operation, enrollment token and retry
payload remain legacy-compatible. Quick Join session tickets are transient maps
of owner hash, code hash, cluster, expiry and UUID, never a second Catalog.
Registry join_codes/enrollments/nodes/catalog_nodes remain authoritative.
RECOVERY_READ_ONLY markers forbid Demo init/adoption. Candidate code-only rollback
requires fresh full private backup and compatibility preflight; final exact04.1
candidate upgrade/rollback qualification is still pending.

## Phase4.1 bridge control1 (separate private root)
bridge.json binds fixed initialized state installation UUID/dev-inode, one app UUID,
local-app bearer SHA/scopes and optional installed prefix. client.json has the raw
private app credential only. requests.sqlite3 schema1: request_id/app_id/public
intent hash/code SHA/RECEIVED or DONE/sanitized historical result,<=256 permanent
rows. This is not a Catalog/Storage/Node identity database. Engine pending schema,
base Demo/Core/registry/manifest/cache formats unchanged; no auto init/migration.

Phase4.1b.2 adds only optional private control/socket.json format1 (app UUID,
device,inode), never engine identity. Same request journal stores sanitized owned
Node lifecycle receipts; replay historical, not process authority. Old candidate/
base schema/credentials/pending/volume markers unchanged. No PID file controls.

## Phase4.2 native foundation1 (separate app UID)
Explicit application.json format1 app UUID/key version and AndroidKeyStore AES
alias; canary/draft standard AES-GCM IV+ciphertext+Aad(app/version/purpose), no raw
key export. Draft is DRAFT_NOT_SENT, NOT Core enrollment. Probe-approved format1
binds application/volume/quota/reserve/rootdev/inode; original Core manifest1 used
only in isolated APP_PRIVATE_PROBE_ONLY namespace, not cluster Node identity.
Missing/unknown/corrupt state held, no auto regeneration/schema migration.
No Core/Demo formats/archive changes; ANDROID-NATIVE-STATE defines exact limits.

## Native state compatibility evidence
Application/probe/Core manifest remain format1; no schema migration. Android cloud and D2D CE/DE backups explicitly exclude private state. Same-signer native versionCode1 checkpoint ->2 qualification preserves existing appUUID, Keystore canary, exact encrypted unsent draft, private Volume ID/marker and committed Core bytes. Test-only upgrade receipt never ships in main APK. Lower version installation must refuse; no general native rollback/key export/Termux state adoption is supported.

## Native explicit context1 (optional, 4.2f.1)
Fixed native-node-v1/context.json public receipt plus ApplicationVault fixed
node-context.json AES-GCM/purpose/app binding and node-context-required.json
witness. Sealed record: format1/app_id/context_id/revision/binding/device_binding/
pending/node/tls/storage; four runtime slots must remain null at f.1. Persisted
parent/root inode and original path prevent replacement adoption. Missing witness/
record/key/root holds, never regeneration. Existing app/draft/probe/Core schemas
unchanged; context_id is NOT network Node/Cluster identity. See native context doc.

## Native TLS component1 (4.2f.2)
Optional sealed context1 tls slot is now exactly format1/certificate/private_key/
pin (PEM strings and lowercase SHA256). Revision advances once on explicit first
prepare; complete record uses existing app-purpose AES-GCM/CAS/witness. Public
receipt/app ID/Keystore alias/probe/Registry/manifest formats unchanged. Node/
Cluster/pending/storage remain absent/null. Existing TLS validates/reuses, damaged
state is held. Exact old f.1 code refuses this non-null slot rather than reinit.
No plaintext key/PKCS12/database restore or Termux migration; native TLS doc owns
compatibility and retained upgrade/process receipts.

### Native context1 optional enrollment components (4.2g.2a)
The predeclared pending/node slots are now strictly typed by asc/node/enrollment.py.
Pending contains ONLY canonical application request_id and the existing Core
private pending1 operation (controller/pin/expected cluster, original CSPRNG
enrollment_id + enrollment_token, code/name/profile). Repair targets remain null.
Accepted node contains ONLY Core config1 controller/pin/node_id/token/token_version/
cluster_id. Both cannot coexist; either requires an existing valid TLS identity.
They share the Keystore-provider atomic CAS record; neither plaintext node.json
nor enrollment_pending.json is created. Revision increases at each publication.
All prior app/context/draft/probe/volume/Registry schema identifiers are unchanged.
Old f.2 code refuses non-null pending/node; do NOT downgrade after enrollment by
restoring stale records or dropping identity. Keep new state and use compatible
code only. No Termux/Core-state adoption or schema migration is implemented.

### Existing-only local manifest open
Local Manifest remains schema1 with identical canonical tables/constraints and
Node/Volume/File IDs. New existing_only is a constructor policy, not a data format
or migration. It requires existing format1 +matching Node and structure; no
creation/repair/downgrade of missing or unknown metadata. A supplied dev/inode
receipt must match. Default explicit creation path is retained for old callers.
SQLite DDL whitespace normalization preserves older Python indentation without
rewriting stored schema. Native encrypted volume-config contract is still next.

## Phase5 private access profile1
New optional separate access-plane config, not a Registry/Catalog migration:
format1, mode private-gateway, frontend_origin, upstream_origin, upstream_pin,
upstream_mode, max_body_bytes. No admin/node credential or session persistence.
Gateway TLS belongs to its separate private root; never adopt backend/Termux state.
No backup/recovery/volume identity/schema changes. Unsupported profile versions
refuse; removal of gateway leaves upstream state unchanged.

Phase5.2 NEW access profile2 (cloudflare-edge): existing frontend/upstream/pin/mode/
size fields plus listen_origin (loopback only), access_team and access_audience.
It is a separate root/format, not a migration of private profile1 or any Catalog/
Node state. Access JWT/claims are never persisted; public key cache is bounded RAM.

## Phase5.3 maintenance plan1
Operator-owned private JSON outside state/backup, <=8KiB when read by CLI. Exact
fields: format, kind=asc-private-maintenance, mode=single-writer-demo, action,
installation_id, role, current_release_id, target_release_id, backup_sha256,
state_formats, plan_sha256. SHA is canonical encoded body excluding plan_sha256.
Reject unknown fields/actions, bool version/formats, mismatched content/confirmation
and same-release target. No commands/credential paths or secrets in plan. Existing
Demo formats/Registry/Manifest/upgrade-journal1 unchanged; no migration/new catalog.
Activation optional preconditions are in-process arguments, not persisted authority.
Plan file never substitutes for current stopped-state/backup/release verification.

## Linux access distribution metadata1
access-release.json exact format1/kind=asc-linux-access/version/profile_formats
[1,2]/maintenance_format1/files SHA256 map/release_id(canonical body SHA excluding
release_id). Not Demo release.json; no state/schema compatibility adoption.
Separate env/access-env.json exact format1/release_id/edge_dependencies bool/Python
version tuple. Written only after successful env setup, no keys/IDs/tokens. New
code requires its own env receipt. Existing gateway profiles/Node/Cluster/volume/
journal/DB formats unchanged; source rollback never restores older user state.


## Operator diagnostic stdout1 (no persistence)
tools/check_access.py outputs format1/scope=operator-local/state/checks and explicit
non-authority fields. checks: profile, tls_identity, upstream_mode, listener_mode,
anonymous_gate; values VERIFIED/BLOCKED/UNKNOWN/NOT_REQUESTED. state CHECKS_PASSED
means no executed check blocked, including offline-only runs, not deployment.
writer_authority/live_deployment_accepted false; quorum_status/remote_reachability/
vpn_membership UNKNOWN; authenticated_access NOT_TESTED. No credentials/endpoints/
raw responses, no persisted receipt or schema/identity migration. Existing profile,
Catalog/Registry/Manifest/journal formats and immutable0.1.0 package remain intact.


## Dashboard owner management previews1 — no persistent schema change
Bounded32RAM entries/8owner, expiry <=120s and session. UUID preview maps public
intent, owner session hash, expected credential generation and approval SHA,
optional confirmed historical result. Hash covers administrative origin/pin/domain/
volume IDs/metadata+storage flags/approved_generation; live probe updates excluded.
No raw session cookie, machine secret, key, new DB/table/version or persistent
identity. Logout/server restart clears previews. Existing Registry4/Manifest1/
Catalog journals unchanged; no automatic retry after unknown crash outcome.



## Optional Dashboard accounts1
Private dashboard/accounts.json exact format1/cluster_id/kdf/iterations/revision/
accounts. kdf=pbkdf2-hmac-sha256, iterations600000; max8 usernames. Each row exact
account_id UUID/role(owner|viewer)/generation/salt16bytes hex/password_hash32bytes
hex/created_at/updated_at. Version/cluster/KDF/typed bounds checked; atomic existing
private fsync helper, no plaintext password. Single live Dashboard owns writes;
no independent CLI writer or DB. Generation CAS/last-owner constraints under its
thread lock, sessions RAM8global; runtime ownership prevents two live Controllers.
No Registry/Manifest/schema change, Node/Cluster/Volume/cert/key unchanged. Existing
backups include private auth file; never publish it. Legacy043 reader ignores it,
uses one-use codes; it does not authenticate password users or migrate state.


Dashboard checkpoint3 adds no persistent schema. Files/versions/jobs remain in
existing catalog_files/catalog_jobs/history; immutable IDs, upload keys, policy
and actual replica proof authority unchanged. Browse metadata_point reflects one
SQLite listing transaction only; availability later observed, not Core authority.
Pagination50/offset10000 does not raise Core256-file cap or create directories.


Optional Dashboard history1:private history.json +history-required.json witness
bind format/mode/Cluster ID/Catalog epoch/document UUID; no base schema changes
or new Registry setting. Document revision, snapshots(up to16), restores(up to64),
request receipts(up to128), maximum2MiB. Each snapshot immutable manifest includes
exact metadata revision/digest, label/prefix and ALL matching versions/size/SHA;
manifest digest, UNVERIFIED/VERIFYING/VERIFIED cursor/per-file actual2domain proofs
and observed timestamps. Restore source/snapshot link, reserved version, stable
target ID, PENDING/COPYING/VERIFYING/COMPLETED/BLOCKED, fixed error and final proof.
Request UUID/digest prevents changed-intent replay. No bytes/keys/tokens stored.
Witness published before first document; interrupted pair or lost member holds
503, never empty reset. Private0600 atomic temp/fsync/rename/parent-fsync; no-links/
single-link/owner/inode+mtime read checks. Every load binds immutable references
to canonical live Catalog. Retain records/references, no auto expiration/deletion.

Operator document directory IO uses a held original private directory descriptor
for file open/temp create/replace/fsync/cleanup, with namespace/inode rechecks;
interrupted publish may be unconfirmed, never silently rolled back or redirected
outside approved directory. Required witness and document are preserved for review.
