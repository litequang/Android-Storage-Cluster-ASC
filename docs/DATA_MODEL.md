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
