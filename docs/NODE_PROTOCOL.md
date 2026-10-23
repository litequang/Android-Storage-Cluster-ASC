# ASC NODE PROTOCOL — lifecycle/storage implementation and proposed consensus

The initial consensus sections are a future design; implemented lifecycle/storage contracts follow below.

## Compatibility
API base path `/api/v1`. Every request and response includes `cluster_id`, `protocol_version`, and required feature flags when relevant. Never reinterpret unknown version fields silently.

## Enrollment (planned)
1. Admin generates ephemeral one-time join token with TTL and restricted intended role.
2. Agent creates node private/public key locally; submits join request over authenticated channel.
3. Controller displays fingerprint/device capabilities for human approval.
4. A committed enrollment event registers node_id and public key; a node is not active until commit.
5. Node receives trust material, signed config version, and allowed storage volumes.
6. Rotation, revocation and reinstall cannot create uncontrolled duplicate node identity.

## Heartbeat
Agent -> controller (or current ingress) sends: node_id, firmware/app/protocol version, network reachability, uptime where accessible, battery/thermal *if allowed*, per-volume bytes, SD presence, local manifest checkpoint, current jobs, alerts. Missing sensors must be `unknown`, never fabricated zeros.

## Catalog reads
Available on up-to-date or stale replicas, always return `snapshot_index` / `stale` indicator. No login bypass when the leader is offline.

## Mutations and fencing
- A request gets an idempotency key and authenticated actor.
- Leader must verify policy and commit catalog mutations through quorum.
- Physical copies are staged to a restricted volume path under a generated object id.
- Agents verify a bounded, authenticated operation authorization and current approved cluster epoch for destructive actions. **Only a higher term is not sufficient to prove new leadership/commit**; the final proof mechanism depends on the chosen consensus library and gateway design.
- Delete and GC are never unrestricted leader shell commands.

## Failure semantics
- `NO_QUORUM`: no global catalog mutation, no unsafe automated promotion.
- `STALE_REPLICA`: reading allowed with explicit checkpoint; writing rejected.
- `VOLUME_OFFLINE`: mark placement unavailable; never assume data vanished.
- `INSUFFICIENT_SPACE`: reject pre-flight placement; preserve existing replicas.
- `UNAUTHORIZED`: reject before touching local files.

This is a design contract only. Endpoints and precise messages will be finalized with integration tests after a real Raft library is selected.

## IMPLEMENTED v0.4 PROTOTYPE (single writer, separate from proposed Raft protocol)
All endpoints HTTPS in private LAN. Self-signed controller certificate is SHA256-pinned by enrolling node. JSON <=64KiB on incoming POST.
- `GET /api/v1/info` unauthenticated: `{protocol_version, cluster_id, mode, raft_enabled:false, file_storage_enabled:false}`; do not expose private registry.
- `POST /api/v1/join` payload `{code,name,profile}` (one-time TTL code created locally by `controller-pair`); returns `{cluster_id,node_id,token,mode}`; node token stored only locally, never logged or returned again. Code itself is an enrollment grant created by trusted local admin; explicit per-node approval UI deferred.
- `POST /api/v1/heartbeat` authenticated `Authorization: Bearer <node-private-token>`; payload `{node_id, profile}`, returns current topology `{cluster_id,snapshot_at,consensus_status,nodes[],advisory_role_plan[]}`. Node stores this as read-only local topology snapshot.
- `GET /api/v1/nodes` authenticated with *admin token*; returns topology.
This topology is **NOT** a global file catalog or consensus snapshot. v0.4 had no file upload/download; Phase 1.2A adds a separate authenticated node-local storage API below. Node profiles are self-reported and untrusted; never use them to grant privileged permissions.

## IMPLEMENTED Phase 1.1 — 0.4.1 (still single writer; API v1)

This section extends/supersedes the v0.4 lifecycle details above. There is no Raft
commit proof or public API exposure. All requests use HTTPS, certificate SHA256 pin
or trusted verification; the bundled client always checks the exact pin before
sending HTTP headers/body. Responses include protocol_version=1. Older requests may
omit protocol_version; explicit versions other than integer 1 are rejected.

### Enrollment and retry
- `GET /api/v1/info` adds schema_version=2 and features
  `node-lifecycle-v1`, `retry-safe-enrollment-v1`; no private registry data.
- `POST /api/v1/join` keeps required `{code,name,profile}`. Optional
  `{enrollment_id,enrollment_token}` must both be 32–128 URL-safe secret characters.
  New CLI generates both using CSPRNG and privately persists them before submission.
  Optional node_id requires these fields and a grant targeted to that exact ID.
- Codes have 12 hexadecimal characters, case-insensitive; spaces/hyphens are accepted
  for phone entry. TTL is 60–1800 seconds (default 600), expiration boundary exclusive.
- New enrollments return 201 `{protocol_version,cluster_id,node_id,token,token_version,mode}`.
  Legacy clients still receive a server-generated token; retry-safe clients receive
  their submitted token after transactional acceptance. Tokens are never in HTTP logs.
- Consuming the grant, creating/updating the node and saving the hashed operation
  mapping are one SQLite write transaction. Replaying another actor's consumed code
  is 403. Retrying the same operation/code/current token returns the same ID/version
  until 24 hours after code expiration, provided the credential is still active.
- A replacement valid general code plus the SAME enrollment operation/token resolves
  its existing node instead of creating another. Permanent operation routing prevents
  duplicate creation after cleanup of old codes. Revoked/rotated tokens cannot use
  this path to resurrect a node. Legacy v0.4 requests do not gain retry guarantees.
- Targeted re-pair retains ID, joined_at and admin-controlled name; rotates token,
  increments token_version and marks active. The previous token immediately fails new
  heartbeat authentication. Creating a replacement grant alone does not revoke an
  active token. One outstanding targeted grant per node; issuing another replaces it.

### Node versus administrator authority
- `POST /api/v1/heartbeat` remains `{node_id,profile}` plus the node bearer token.
  Unknown/invalid/revoked/rotated credentials all return 401
  `credential_rejected_repair_required`; do not reveal which one to unauthenticated peers.
  The node CLI marks repair-required, stops and preserves identity and last snapshot.
- `GET /api/v1/nodes` still requires the ADMIN bearer token; topology now adds
  schema_version=2 and nodes include state, token_version, revoked_at and joined_at.
  Revoked nodes remain visible and online=false, excluded from active recommendations.
- `GET /api/v1/nodes/{node_id}` ADMIN only: `{protocol_version,node:{...}}`, 404 if absent.
- `POST /api/v1/admin/pair` ADMIN only: `{ttl?:600,node_id?:existing_id}` -> 201
  `{protocol_version,code,ttl,node_id}`. No target means new-node grant; target cannot
  be local-controller. Code is deliberately displayed only by this explicit operation.
- `POST /api/v1/admin/rename` ADMIN only: `{node_id,name}` -> `{protocol_version,ok:true}`.
  Repeating same name is idempotent. Name is bound as a SQL parameter, never code.
- `POST /api/v1/admin/revoke` ADMIN only: `{node_id}` -> `{protocol_version,ok:true}`.
  First revoke invalidates the token, timestamps/increments generation and cancels
  targeted grants. Repeated revoke has no additional effect; local-controller is protected.
- No admin endpoint accepts a normal node token; admin token does not authenticate
  as a node. Local admin CLI reads controller.json, uses pinned HTTPS loopback and
  needs Controller running. Direct SQLite access is not a network authorization bypass;
  the private Controller OS account is trusted.

### Input bounds, failure codes and abuse limits
- POST body: JSON object, one Content-Length, no Transfer-Encoding, maximum 65536 bytes;
  oversized body returns 413. Invalid schema/content type, duplicate JSON keys,
  non-finite numbers, unsupported version or invalid UTF-8 return generic 400 bad_request.
- Unknown top-level request fields are rejected. Profile accepts bounded extensions:
  32768 encoded bytes, depth <=6, <=64 fields/list items, key <=64 chars, strings <=1024.
  Known role/measurement/protection/SD fields have type/range checks. Names: 1–64 chars,
  trimmed, no Unicode control/format/surrogate characters. Logical IDs: <=64 ASCII
  letters/digits/underscore/hyphen. Profiles never grant authority or trusted hardware status.
- Profile version 1 adds profile_version, score_basis, device_identity_status,
  installation_allowed and sd_status (`unknown`, `detected`, `writable-tested`).
  Missing numeric telemetry remains null; no SD discovery is unknown. Versionless
  profiles from v0.4 remain accepted under the same bounds.
- Join admission: 8 attempts/source-IP/minute, 60 globally/minute, including malformed
  or successful attempts. Authentication failures across protected endpoints share
  12/source-IP/minute, 120 globally/minute. Successful authenticated heartbeats/admin
  calls do not consume the failure budget. Once blocked, even valid auth waits for reset.
- Rate response: 429 rate_limited, Retry-After:60. Fixed windows are in memory, reset
  on restart; at most 1024 counter keys. Forwarded-IP headers are ignored. NAT users
  share a budget. This is abuse mitigation, not an Internet-facing security claim.
- At most 32 request workers, 12-second socket/TLS/read timeout. Saturated connections
  may close without JSON. Client timeout is 12 seconds; JSON responses bounded at 2MiB,
  so this development registry is not designed for unlimited nodes/profiles.
- 403 invalid_or_expired_code, 401 unauthorized for admin, 404 not_found, and
  503 registry_unavailable have generic bodies without secrets. HTTP/error logs do
  not reflect URLs, credentials, payloads or arbitrary exception text.

Any future node-protected operation must check active state and current token using
the same authorization boundary; no such file/storage operations exist in this release.

## Implemented Phase 1.2A — owner storage API v1

Earlier lifecycle sections describe their historical releases. Current /api/v1 remains backward compatible; info reports schema_version=3, feature local-storage-v1, file_storage_enabled=true, storage_mode=node-local-opt-in, global_file_catalog_enabled=false, raft_enabled=false. This indicates implemented capability, not that every node enabled a volume.

Controller routes (JSON v1, existing bounds/rate limiter):
- POST /api/v1/admin/storage-grant: admin bearer; body {node_id,volume_id,operations,ttl?}. operations nonempty subset read/write/list/verify; TTL default 300, range 30–900 seconds. 201 returns one explicit secret grant, principal=local-admin, target/operations/expiry. Save privately; no routine status prints it.
- POST /api/v1/storage/authorize: node bearer; body {node_id,grant,volume_id,operation}. 200 {principal,expires_at} only for active/current node token and matching unexpired generation-bound grant; rejected authority 403. Node token cannot itself read/write files or mint owner grants. Revocation/rotation invalidates prior grants.
- A grant is whole-volume owner delegation, not completed end-user login/file ACLs. Every network storage operation calls this pinned endpoint. Controller/pin failure fails closed.

Agent uses its separate certificate with an out-of-band confirmed pin. Every /storage/v1 request requires Authorization: Bearer <owner grant> and one X-ASC-Volume-ID: <UUID>. JSON responses retain protocol_version=1; storage wire version is the URL v1.

| Method /storage/v1 path | Operation | Body / response |
|---|---|---|
| POST uploads | write | JSON {idempotency_key,logical_path,size,sha256} -> 201 {session} |
| GET uploads/<session UUID> | write | {session}, scoped to principal/volume |
| PUT uploads/<session UUID> | write | application/octet-stream, single exact Content-Length -> {session}; no chunked transfer |
| POST uploads/<session UUID>/commit | write | JSON {} -> {file}; fresh authorization before visibility |
| GET files?offset=0 | list | {files,next_offset}; at most 200 entries; includes integrity state |
| GET files/<file UUID> | read | {file}, manifest consistency checked |
| GET files/<file UUID>/content | read | verified streaming bytes; Content-Length and X-ASC-SHA256 |
| POST files/<file UUID>/verify | verify | JSON {} -> {file_id,state,error,verified_at} |
| GET volumes | list | grant-bound volume only; no absolute root |

File metadata: file_id/logical_path/volume_id/relative_path/size/sha256/version/state/created_at/updated_at/last_verified_at. Physical relative names are generated IDs, never client-selected host paths. Size/SHA-256 are mandatory; hash is lowercase 64 hex. Key is 8–128 ASCII letters/digits/underscore/hyphen; logical name max 512 characters, rejects traversal/absolute/control/encoded-percent/backslash/colon components. Zero-byte objects are supported.

Conflicts return 409; checksum mismatch 422; missing object/session 404; invalid/framing request 400; unauthenticated 401; wrong scope/revoked/expired 403; upload deadline 408; too large 413; busy/auth budget 429; unavailable storage/controller/manifest 503; quota/full disk 507. Errors are fixed labels, never reflected secrets. TLS idle workers are bounded. Already-authorized downloads may finish after expiry/revoke; already-received upload data may remain private staging, but commit reauthorizes. This is not continuous per-byte revocation.

Only full-body retries are supported. No Range/resumable protocol, object deletion, remote cleanup, global catalog or distributed commit. Inventory and dry-run/apply staging expiry are local commands.

Heartbeat retains profile_version=1 (or legacy absent) and optional storage={storage_version:1,manifest_schema:1,volumes:[...],recommended_storage_role,max_upload_bytes,max_concurrent_transfers:1,bytes_per_second,resumable_upload:false}. Each volume reports IDs/kind/quota/reserve, actual total/free bytes or null, readable/writable/fsync_tested or null, state, checked_at, last_error. Role is advisory Storage/Backup/Metadata-only; never grants coordination authority or proves a backup exists.

Oversized JSON is rejected with 413. To avoid a Windows TLS close/send race, at most 128 KiB of a slightly oversized declared body is discarded (never parsed), with a 2-second budget and 1-second idle read; arbitrarily large bodies are not drained.

Role derivation: measured writable online volume -> Storage; readable online volume with write denial -> Backup (read-only archival source, not a writable backup destination); otherwise Metadata-only. Reading the approved marker establishes readable access only, not integrity of every stored file. No backup is created by these labels.

## Implemented Phase 1.2B — Catalog API v1

Controller-run enables /catalog/v1 and advertises global-catalog-v1, metadata-replication-v1, file-scoped-transfers-v1. /api/v1 remains compatible; registry schema is 4. All APIs use pinned HTTPS, existing JSON framing/bounds/rate budgets and protocol_version=1 responses. Global changes require owner admin authority. There is no node promotion/write API.

| Method /catalog/v1 path | Authority | Body / result |
|---|---|---|
| GET files?offset=0 | admin | files (at most 50 aggregates), next_offset |
| GET files/<global UUID> | admin | file, replicas, desired_replicas, verified_replicas, available_replicas, state, availability, protection |
| GET files/<ID>/replicas | admin | replica records and three separate counts |
| POST nodes/register | admin | {node_id,device_id,origin?,pin?,volume_ids?,metadata_allowed?:true,storage_allowed?:true}; storage needs explicit private endpoint/pin/nonempty approved volumes; metadata-only does not |
| POST uploads | admin | {idempotency_key,logical_path,size,sha256,policy,version?:1} -> 201 upload plan with completed flag, file, job_id, key/local logical path and short-lived exact-target grant/endpoint/pin/timeout |
| POST uploads/<job UUID>/complete | admin | {session_id,local_file_id}; a hint only, never accepted as proof -> job_state and physically verified/pending file report |
| POST files/<ID>/download | admin | {} -> verified available candidate plan with scoped short-lived read credentials |
| POST files/<ID>/policy | admin | {policy}; policy mutation + repair scheduling, no object deletion |
| GET jobs?offset=0 | admin | at most 100 public job states/next_offset |
| GET jobs/<job UUID> | admin | job/checkpoint detail (no run token) + latest 200 transitions |
| POST jobs/run | admin | {job_id?} -> one serialized worker attempt or null when busy/no due job |
| POST jobs/<ID>/retry | admin | {} -> explicit same-job retry cycle |
| POST reconcile | admin | {} -> bounded inventory/proof/repair report, with truncation/busy indicators |
| GET metadata/status or nodes | admin | epoch/revision/single-writer mode and approved node probe/sync checkpoints |
| GET metadata/snapshot?node_id=ID | approved current node bearer | consistent snapshot |
| GET metadata/changes?node_id=ID&after=N | approved current node bearer | ordered bounded delta page |
| POST metadata/ack | approved current node bearer | {node_id,epoch,revision,head_digest}; validate against known checkpoint, never proof of file bytes |

Policies: single / replicated_2 / replicated_3. Global file fields: file_id, logical_path, explicit version, size, lowercase SHA-256, policy, created_at, updated_at, revision. Replica fields: replica_id, file_id, node_id, volume_id, local_file_id, state, created_at, updated_at, verified_at. IDs are separate global/local UUIDs; physical device independence is based on explicit owner-approved device_id, not two volumes or aliases.

Upload owner admin credential reaches only Controller. Transfer grant constraints are enforced at Agent before Engine calls: exact job principal/key/local name/size/hash, permitted method/resource, volume and persisted session/local ID. Every operation introspects Controller and commit rechecks authority. Source/read grants authorize one file; inspect grants authorize only status/files/inventory on an approved volume. Node/admin tokens are never transfer credentials.

Snapshot (metadata schema 1): {schema_version:1,cluster_id,epoch,revision,head_digest,created_at,files:[{file,replicas}],digest}. Digest is SHA-256 of canonical sorted-key compact UTF-8 JSON without digest and without transport protocol_version. Delta: {schema_version:1,cluster_id,epoch,from_revision,through_revision,current_revision,head_digest,events}. Each event has epoch/revision/previous_digest/payload/created_at/digest; hash excludes digest. File payload revision equals event revision. Retain 1024 changes, max 100 events/page and below 2 MiB including response margin. Missing history -> 409 resync_required; node retrieves a pinned snapshot and validates rollback/epoch/checkpoint consistency. Offline cache returns stale/read_only and last sync/revision; available replicas are UNKNOWN locally.

Existing /storage/v1 remains wire v1. New GET status returns one grant-bound volume with actual quota/used/free/reserve/read-write/fsync status, node ID and limits. GET inventory?offset=0 returns at most 200 manifest file records plus upload session/principal/key routing (no raw credentials), next_offset and bounded unreferenced physical objects on page zero. This is privileged inventory, not public metadata replication.

POST /api/v1/storage/authorize additionally accepts optional scope={method,resource}. v0.5 whole-volume owner grants remain compatible. A new Agent may retry without scope after an old Controller rejects the extra field with 400, using the same pin and credentials. Scoped job grants require scope and cannot succeed that way. Global jobs/status need v0.6 Agents; old Agents retain lifecycle and standalone owner storage.

RUNNING job default timeout 300 seconds (30–900), Controller relay/readback default 4 MiB/s (64 KiB/s–64 MiB/s). Metadata owner POST client timeout 300; node transfer timeout follows the bounded configured job timeout; old transport default remains 12. Full-body restart only, no Range/chunk resume. Download client verifies bytes and retries candidates using a new seekable output.

Relevant failures: 400 invalid envelope/ID/path; 401 owner unauthorized; 403 metadata_not_authorized / stale approval / changed credentials / wrong transfer scope; 409 idempotency/version/job/revision/checkpoint conflict or resync_required; 422 physical checksum mismatch; 429 busy/grant/rate bound; 503 unavailable Controller/source/catalog; 507 no eligible quota/capacity. Responses never echo secret-bearing input. Owner upload completion may remain pending if the owned worker is busy; only verified counts, never job existence, prove a replica.
