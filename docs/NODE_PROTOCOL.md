# ASC NODE PROTOCOL — lifecycle/storage implementation and proposed consensus

## Phase 2B development protocol — Windows qualified

Explicit runtime uses authenticated `GET /cluster/v1/leader` with self node ID,
cluster, mode, write_ready and term, never an arbitrary redirect address. Discovery
only calls configured endpoint/pin identities; readiness checks actual quorum.
Private IPC adds `POST /v1/runtime/heartbeat` (12-second armed watchdog) and
schema-2 commands require `authority_term` matching the actual applied log term.
Distributed Agent introspection requires a fresh nonce with the existing exact
scope; its pinned reply binds cluster/epoch/term/committed index/nonce/intent digest.
It has no legacy fallback. `controllers` bootstrap configuration opts clients and
Agents in; distributed Storage additionally pins `cluster_epoch`. Local Catalog
reads remain explicitly stale with exact Catalog/control revisions and applied
index; `consistency=strong` requires the runtime quorum gate. Distributed enrollment
requires the existing retry-safe operation/token fields. Old wire/config paths
retain their original behavior. Qualification: PHASE2B-ACCEPTANCE.md.

Metadata snapshot/changes responses keep the existing exact version-1 envelope;
only the existing transport protocol_version is added and removed as before.
Runtime labels (control_revision, applied_index, term, stale/read_only) must not be
injected into these digest-bound payloads or replace their captured revision.

Wire `/storage/v1/uploads/<session>/commit` keeps its existing empty JSON body.
For explicit distributed Storage only, a currently authorized exact target job
may resume NEEDS_REVIEW after both retained bodies match; commit reauthorizes
again before visibility. The client cannot request an unsafe recovery flag on
wire. Legacy whole-volume callers cannot use this behavior.

`/api/v1/info` also exposes a self node ID and explicitly non-authoritative local
Leader hint. A TLS-pinned hint can route a rejected Agent to the quorum-gated
heartbeat API for an authoritative repair-required response. It is never cached
as readiness, cannot authorize a Storage operation and cannot introduce an address.
Owner Catalog/admin CLI can opt in through private cluster-client.json with
distinct endpoint credentials. Explicit Agent re-pair retains pinned bootstrap/
epoch and pending operation identity and tries only those approved endpoints.

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

## Phase 2A Go metadata protocol continuation

Go continuation (not yet accepted): peer `/raft/v1/{append,vote,prevote,timeout,snapshot}`
uses TLS 1.3, exact per-voter certificates and ID/address/cluster validation.
Local loopback IPC has a separate private per-node bearer:
`GET /v1/status`, `GET /v1/state?consistency=local|strong`,
`POST /v1/commands`, `/v1/snapshot`, `/v1/shutdown`.
Strong state waits for a newly committed upstream Barrier and FSM apply; local
reads report stale/read_only. Commands contain schema/cluster/epoch/request ID,
intent SHA, expected projection SHA and base64 canonical prepared document bytes.
State/snapshots retain exact bytes, applied index/term and permanent receipts.
No membership-change/recovery endpoint exists. The supported membership is static.

Opt-in loopback Controller `/catalog/v1` requires the existing owner admin bearer:

| Method/path | Contract |
|---|---|
| GET files or files/ID | Local stale metadata by default; `?consistency=strong` requires local leader + newly committed Barrier; reports exact revision/applied_index/read_only/stale/metadata_only |
| GET metadata/status | Same consistency options, authenticated leader/role health; automatic_failover=false |
| POST metadata/declare | request_id/logical_path/version/size/sha256/policy; metadata declaration only, no upload/replica proof |
| POST files/ID/policy | request_id/policy; committed receipt and applied revision; replay uses same intent/ID |

All legacy upload/complete/download/grant/job/reconcile/node-approval writes are
denied with distributed_fencing_required; lifecycle mutations are DB-fenced.
Available replica count is UNKNOWN/null in this mode, not derived from frozen
per-Controller probes. Follower strong reads fail; no unauthenticated redirect
or blind forwarding is added. Status leader_id is a routing hint, never authority.
Repeated same policy with a new request commits a receipt/index without fabricating
a new Catalog event/revision. SHA-precondition rejection binds its request ID;
use a new request ID for a newly prepared intent after inspecting a conflict.

The following paragraphs retain the historical pre-Go protocol status/design.

Engine selection is blocked; /api/v1, /storage/v1 and /catalog/v1 still implement v0.6 single-writer behavior. raft_enabled remains false. No Raft RPC, strong-read API, bootstrap, membership-change, leadership-transfer or recovery endpoint is available. Existing cache reads keep stale/read_only and known revision/sync-time semantics.

Future protocol requirements: per-voter authenticated pinned/trusted transport before message decoding; immutable cluster/membership identity; bounded versioned commands with idempotency/payload digest; majority commit and deterministic apply before successful write response; engine read barrier and applied-index check for strong reads. Never infer voting identity from a submitted node_id/address or use a shared long-lived admin secret.

All CREATE/POLICY/COMPLETE/REPLICA_STATE/REVERIFY callers and alternate direct writer paths require one enforced consensus authority boundary before such a mode can be advertised. Physical proof/late ACK alone must not publish a replica outside committed apply. Until distributed storage fencing is accepted, future metadata leadership changes cannot activate old Controller job/grant automation. Exact current routing and pending contracts are in PHASE2A-ACCEPTANCE.md; these statements introduce no new wire schema or active guarantees.

## Phase 3A owner backup API (opt-in runtime only)

`/catalog/v1/backup/*` requires owner admin and current Runtime quorum/term gate.
POST enable {request_id} explicitly enables backup schema 1 after all Controllers
upgrade. All mutations below require request_id (8..128 URL-safe characters) and
return the same committed result for the same intent; conflicting reuse is 409.
GET status/snapshots/jobs/schedules/policies/trash returns bounded records.
GET history?logical_path=URL_ENCODED_PATH returns immutable versions and state/pins.

| POST suffix | Additional body / result |
|---|---|
| snapshots | copies?:2 (1..3), retention_seconds?:604800 (60..315360000); snapshot_id/job_id |
| restore | file_id, snapshot_id?; durable job_id and new target_version |
| snapshots/ID/restore | one reserved restore job per captured file |
| delete | file_id; logical TRASH only |
| policies | logical_path, keep_last (1..256), max_age_seconds/trash_seconds (60..315360000) |
| retention/run | expired_versions, physical_deletions=0 |
| schedules | interval_seconds (60..86400), copies?, retention_seconds?; schedule_id |
| schedules/ID | enabled boolean |
| jobs/ID/retry | explicit same-job retry with fresh checks |
| jobs/run | optional job_id; one bounded worker turn, no request_id required |

GET files lists latest LIVE heads after enable; file/ID exposes version_state.
Local stale views use the same namespace rule. Strict version-1 node metadata
snapshot/delta envelopes remain unchanged and continue to retain all version data;
those caches do not implement current backup/trash authority. Normal download of
TRASH/EXPIRED returns 409 version_not_live; owner restore uses fresh scoped proof.
snapshot_unverified_head rejects an in-flight head rather than omitting it.
Physical delete/purge endpoints do not exist. Backup CLI commands use the same
pinned owner client; explicit --request-id supports retry after lost response.

## Phase 3B.1a Node Score contract (no API/placement change yet)

Score schema 1 uses five observations, each exactly
`{value, observed_at, source, samples}`. UNKNOWN is null/null/expected-source/0.
Known values have integer UTC timestamps and positive sample counts. Finite raw
ranges: capacity_ratio 0..1, reachable boolean, reliability 0..1, memory_mb
0..1048576, thermal_c -40..150. No manufacturer/baseline input is accepted.
Capacity/reachability source is controller-probe, reliability is
controller-probe-history; memory/thermal are explicitly agent-runtime self-reports.

Engine contract: capacity 30%, reachability 20%, observed probe reliability 30%,
RAM 10%, thermal 10%. Normalize capacity/reliability linearly to 0..100, reachable
true/false to 100/0, RAM linearly to 8192 MiB capped 100, thermal 100 at <=35C and
0 at >=65C with linear interpolation. Freshness is 120 seconds, inclusive; future
or older observations become UNKNOWN. Score is weighted mean over known weights,
null when none known. Confidence is known weight percentage, with reliability
weight multiplied by min(samples/10,1); reliability is separately reported as a
probe-success percentage, never continuous uptime or disk durability. Report all
component values/status/source/time/contribution. Scores confer no Raft authority.

3B.1c: `GET /catalog/v1/nodes/scores?consistency=local|strong` is owner-admin only,
read-only and never probes or writes preferences/placement. Local (default) works
on a stale follower, labels exact source applied index/term/control and Catalog
revision; strong uses the existing quorum read gate. Unapproved/revoked/changed
node generation has UNKNOWN scores. Only pinned status capacity/reachability and
runtime memory are currently available; reliability/thermal remain UNKNOWN until
actual history/sensors exist. Normal node tokens do not authorize this route.

3B.2: owner `POST /catalog/v1/nodes/enable {request_id}` explicitly enables bounded
insights schema 1, with same-intent replay/conflicting-ID protection. Owner-only
`GET /catalog/v1/nodes/ID/history?window=24h|7d|30d&consistency=local|strong`
returns source checkpoint, generation, observed buckets, raw metric means/counts,
provenance and null continuous_uptime. UTC calendar buckets include current partial
bucket. Score reliability uses last 24h observed probe samples, with 3600-second
freshness rather than the 120-second live-input budget. Thermal stays UNKNOWN until
an actual supported sensor is collected. No sensor is inferred from device specs.

3B.3: owner-only `POST /catalog/v1/nodes/ID/preferences {request_id, mode}` persists
one of auto (Auto), preferred (Preferred), avoid-new-storage (Avoid New Storage),
drain (Drain), protected (Protected). Scores response includes effective preference.
Requests replay exactly; conflicting reuse is 409. Drain reports automatic_movement=false
and physical_deletions=0. Preference persistence is complete in 3B.3; allocation
consumption is enabled only in 3B.4, never by changing read or voter eligibility.

3B.5a: owner-only `GET /catalog/v1/files/ID/reduction-preview?consistency=local|strong`
returns checkpoint-bound schema-1 dry_run proposal, keep IDs, candidate IDs, required/
available independent domains and explicit holds. Default stale/local view proposes
nothing. Suspect/unavailable/old (>300s) proof cannot count toward retained domains.
Retained snapshot/restore pins, trash/expired versions and unfinished jobs hold all
reduction. Protected replicas remain held. Every candidate requires future fresh
byte verification. apply_supported=false and physical_deletions=0 always. No apply,
delete, destructive grant or final-manifest mutation endpoint exists in Phase 3B.

## Phase 3C owner replication API (explicit runtime only)

All `/catalog/v1/replication/*` routes require owner admin and the existing current-
term quorum gate. POST enable {request_id} -> enabled/schema and physical_gc_enabled=false.
POST policy {request_id,file_id,copies:1|2|3} -> desired/verified/available counts,
policy and scheduled COPY job IDs; reducing does not remove replicas or bytes.
POST reconcile {request_id} -> bounded per-file available/desired counts and jobs;
logically EXPIRED versions are not newly replicated. GET status reports explicit
enable/schema; physical GC remains false. Same request/intent replays the same
result, conflicting reuse fails 409; null/invalid request IDs are rejected.

3C.2a POST replication/drain {request_id,node_id} (requires 3B insights enabled)
sets Drain and returns move_ids/blocked_replicas, physical_deletions=0. POST
replication/move {request_id,replica_id} plans one rebalancing move. No immediate
source removal; moves use existing COPY jobs and cannot override safe placement.

3C.2b GET replication/moves returns bounded durable intents. POST
replication/complete-move {request_id,move_id} streams/hashes required independent
survivors, rechecks current authority/policy/generation/jobs and commits only logical
source retirement; physical_deletions=0. Pending/unverified COPY, stale/changed
proof or insufficient survivors returns 409; Protected source returns 403.
The existing Leader worker also advances one ready move per turn. Source physical
bytes and historical pointers remain retained until a separate future GC protocol.

3C.3a GET replication/gc-plan (owner/current quorum) returns gc_plan_schema=1,
plan_sha256, graph_sha256, epoch/term/control_revision/applied_index, generated_at/
expires_at (60s), bounded retired candidates, eligibility/holds and reference counts/
examples. eligible_logical_bytes and held_logical_bytes are logical sizes, not a
measured filesystem-free delta. physical_deletions=0, physical_gc_enabled=false.
Unknown/native objects are held; their unobserved count is null. No apply route yet.

3C.3b POST replication/archive-jobs {request_id,retired_replica_id} explicitly
archives only related COMPLETED transfer jobs and invalid job-scoped grant rows;
returns archived_job_ids/history_retained=true/physical_deletions=0. Nonterminal
references fail 409. GET jobs/ID and list expose archived=true, completed identity
and audit evidence, with unavailable physical fields null/absent. Exact old upload
and completion retries remain successful; mismatched completion is rejected and
archived jobs cannot be retried/reintroduced. Retained event/history pins remain.

3C.4a POST replication/gc-prepare {request_id,retired_replica_id}: require full graph
eligibility and fresh survivor bytes; return durable plan_id/plan_sha256/expires_at
and required_confirmation. POST replication/gc-confirm {request_id,plan_id,confirmation}
requires exact `DELETE-ISOLATED-TEST-OBJECT:<plan_id>:<plan_sha256>`, nonexpired
current-term unchanged graph/proofs and issued temporary fixture capability; creates
RESERVED gc_job_id with physical_deletions=0. Default runtime returns 403
physical_gc_locked even for the owner; there is no runtime config/CLI/env enable.
Wrong/expired/changed plan returns 409; no physical executor/execute endpoint yet.

### Checkpoint 3C.4c - isolated GC authorization

Owner-only `POST /catalog/v1/replication/gc-execute {gc_job_id}` explicitly executes an already confirmed reservation. Job ID is the retry identity; retries renew the ephemeral run/permit, not the object or confirmation. DONE replays its single-object outcome. There is no enable flag/CLI/env, and ordinary Controllers return physical_gc_locked. No raw GC bearer is returned in the owner API or persisted.

Test-only attached Storage executor accepts `POST /storage/v1/gc/<gc_job_id>` with exactly `{}`, bearer and X-ASC-Volume-ID. No object/path body is accepted. Distributed pinned introspection uses operation=gc, exact scope `{method:POST,resource:gc/<id>}` and a new nonce. Reply constraints bind GC job/retirement/node/volume/local/global IDs, generated logical path, size/SHA, cluster/epoch/plan SHA, permit term/run/expiry; reply authority binds the request nonce and intent to an actual-term committed receipt. Every callback rehashes independent survivors and rechecks target references/current credentials, with no authorization cache or legacy fallback. A superseded/expired permit, new pin, changed approval/generation, stale Leader or missing quorum is denied. The executor reauthorizes immediately before unlink or known journal replay.

Ordinary Agent has an empty executor map; Windows/Android physical execution stays locked. Storage failure yields gc_execution_unconfirmed (503) and keeps the durable job/run. Retry the same GC job; only a matching exact node result can mark DONE. physical_deletions=1 is the historical one-object job outcome, never an incremental counter. Node replay reports unlinked_now=false and logical_bytes_removed_now=0.

3C.5b: stale_gc_proof (409) rejects any reference/approval graph change during streamed proof, including a survivor pin/endpoint change. Retry the same GC job to obtain new current evidence; no old proof is relabeled. Wire and persistence shapes stay unchanged.

Known GC error labels are now preserved by the pinned client whitelist; unrecognized server text remains request_failed. A stale/expired confirmation requires a newly prepared exact plan SHA; a stale proof requires fresh byte proof/nonce. No permission is inferred from a retry. Discovery may already recover a lost Node ACK; tests must prove actual unlink/reply loss rather than require an outer exception.

## Phase 3D owner-only external archive source

Only opt-in RuntimeHandler adds POST /catalog/v1/external/{capture,read,check}.
Existing owner admin +current actual-term quorum gate required; no node bearer
access. capture {} returns nested capture {document:exact runtime2,state:{index,
term,document_sha256}} without transport relabeling inside. read {cluster_id,epoch,
file:{file_id,logical_path,version,size,sha256}} compares exact current immutable
version and issues fresh exact-local-file audit/read grants for all currently
approved/readable replicas. Owner archival scope includes TRASH/EXPIRED; ordinary
download lifecycle gates unchanged. Grants returned only to owner client, never
backup manifest. check {cluster_id,epoch,source_index} requires current same-cluster
quorum at >=capture index; returns current_authority/current_index, no writer proof
for recovery. No destination path, secret config, restore, bootstrap, or GC route.


<!-- Reviewed Demo c9c2660 historical extension; current Phase4 status is in PHASE4-PROGRESS. -->
## Demo LAN restriction of existing v1 protocol (DEMO.2)
Demo reuses pinned Core enrollment, heartbeat, Catalog and per-request Storage
introspection (no new wire schema). Controller endpoint must be numeric RFC1918/
loopback IPv4 HTTPS with explicit port, never wildcard/public/hostname. Owner sees
one-time codes only via explicit `pair`; joining node uses hidden interactive entry
and Core durable enrollment retry. Owner token stays in Controller home. Approve
binds node ID/generation, storage pin, approved volume and owner physical domain.
Only replicated_2 new uploads are permitted with two measured independent domains;
policy change/reduction, whole-volume admin grant and backup/replication/GC mutation
routes are excluded. Existing node-scoped metadata cache is not write authority.

## DEMO.4a browser API (separate optional trusted-HTTPS origin)
Core pinned owner `POST /demo/v1/dashboard/code {}` returns one explicit private
5-minute one-use browser grant + browser origin/public CA SHA. Node/session tokens
cannot authorize this Core admin route; disabled Dashboard returns unavailable.
Browser POST /api/login {code} requires exact Origin/Host, sets __Host-ASC-Demo cookie
Secure/HttpOnly/SameSite=Strict/Path=/ (30 minutes), returns anti-CSRF nonce only.
GET /api/session bootstraps nonce for that cookie. All other browser APIs require
cookie + X-ASC-CSRF, exact Host, same Origin when present; mutations require Origin.
No CORS. Sessions/grants/tickets are process-local and bounded; restart denies old ones.
GET /api/state, /api/nodes/ID, /api/files/ID, /api/uploads/ID are sanitized owner views.
POST /api/refresh {} invokes existing bounded reconcile. POST /api/uploads takes
logical_path/size/sha256/idempotency_key, prepares existing replicated_2 plan and
returns a session-bound transfer ID (never Node grant). PUT /api/uploads/ID requires
exact octet-stream Content-Length and bounded full SHA before Core forwarding;
200/202 reports actual protection/replication, not upload percentage success.
GET /api/files/ID/content requires CSRF, verifies existing fallback into private spool
before attachment output with X-ASC-SHA256. POST /api/logout {} invalidates session.
32 MiB maximum browser body/download, one transfer, eight request workers; metadata
max 8 KiB, no chunked/ambiguous frames. No node approve/policy/delete/GC browser route.

### DEMO.4d.2 owner local probe (no wire change)
`ascdemo storage-status` requires the existing enrolled/initialized Demo state and stopped local Storage Node; reuses existing capability shape with readable/writable/fsync_tested/state/last_error. Demo prefix binding/compatibility/journal, root operation and agent/engine OS ownership guards apply; Controller may remain running. No data/volume initialization, network authorization change or new HTTP endpoint. Private local owner authority only; M51/unknown still refused before probe.

## Phase4.0 owner Quick Join facade (Demo single-writer only)
Authenticated Dashboard POST /api/v1/quick-join/pairings with empty JSON object,
existing exact Host/Origin +CSRF, returns201: quick_join_version1,pairing_id,
code,expires_at,expires_in,controller,pin,cluster_id,runtime,storage_auto_approvalFalse.
GET /api/v1/quick-join/pairings/<UUID> requires the same owner session; returns
state waiting/expired/registered/revoked/unknown, optional node_id and separate
storage_approved/failure_domain evidence, checked_at. GET never returns the code.
8 tickets/session,32 global, tracking expires with session; logout/restart erases
tracking, not existing Core join-code validity. No CORS/new bearer/token route.
Local quick-join first GETs pinned /api/v1/info (protocol1/schema4, explicit
single-writer-development, raft_enabledFalse, retry-safe enrollment feature).
Then calls the unchanged Core join/retry wire contract. No code in CLI arguments.
Expected Cluster ID check uses the existing pending expected_cluster_id field;
no new wire/config/schema. Registration is not owner storage/domain approval.
Native/local-engine bridge and Core quorum mode remain future qualification.

## Phase4.1 contract routing
LOCAL-ENGINE-BRIDGE defines version1 authenticated same-UID UDS frames (not browser
HTTP); existing enrollment wire unchanged. CORE-QUORUM-DASHBOARD defines planned
owner-only read-only observation endpoint and explicit browser mode. No writer,
PID/path/shell, membership/recovery/GC/approval protocol is authorized.

Phase4.1b.1 implements the LOCAL-ENGINE-BRIDGE version1 UDS contract. Actual peer
UID plus distinct app grant/scopes; bounded newline frames/secret-safe responses.
Reads fresh; same-ID binding/code-hash checks and FULL receipt replay. Code may be
omitted on resume while original pending/receipt retains operation. No enrollment
wire or browser API changes; no lifecycle implementation yet.

## Phase4.1c.1 read-only Core observation API
Owner-admin GET /cluster/v1/observability?consistency=local|strong only; other
methods403 read_only_observer before runtime readiness. observer_version1,
read_only=true/writer_authority=false; nodes/volumes/files/policy protection/jobs/
backup timestamps, runtime checkpoint and actual Barrier evidence. No raw private
projection/hash/token/grant. No ensure_ready/takeover/CAS. Follower/failed strong
read returns explicit stale/null availability; gateway must check all provisioned
identities and never infer quorum from roles alone. Full contract in
CORE-QUORUM-DASHBOARD; no Core browser gateway route before c.2.

### Phase4.1 owner gateway mode contract
Shared browser GET /api/mode exposes only explicit mode/read_only; authenticated
/api/session adds those fields. Core/recovery modes allow only authenticated GET
/api/state and /api/files/<UUID>, plus existing secured login/logout. All other
Core routes403 (including downloads/mutations); Demo routes are unchanged in Demo
mode. Unique owner cookie per gateway, same Origin/CSRF/CA policies. No browser
node credentials or local-app authorization. See CORE-QUORUM-DASHBOARD/API contract;
owner observation never supplies writer capability, even with confirmed Barrier.

Phase4.2 native Binder uses ANDROID-NATIVE-API version1 typed AIDL, separate from
Linux UDS/owner session/node token. Private own UID+signature+explicit consent;
no path/PID/shell/arbitrary management request. Enrollment wire unchanged and
native runtime unsupported until qualified, no fake Core pending/approval.

## Native Binder1 publication
See ANDROID-NATIVE-IPC. Explicit approvePrivateProbe0/request1 transactions, actual per-call UID/signature, consent/device policy before state. Public pinned Controller GET is not enrollment, approval or authority; encrypted native draft remains NOT SENT. No new network write/Node/Core quorum API.

Phase4.2f.1 adds private IPC1 native_context_init/native_context_status only, with
empty extra fields, existing UID/signature/device/consent/app-key checks. Sanitized
CONTEXT_READY/null Node+Cluster/configuration and no writer/runtime authority.
No network protocol change. Exact contract: ANDROID-NATIVE-CONTEXT.

Phase4.2f.2 IPC1 adds native_tls_prepare (empty extra fields, same UID/signature/
consent/device/existing app/context). Returns only TLS IDENTITY_READY/public pin
with null Node/Cluster IDs and runtime_start_supported=false. Original transaction
IDs0/1 unchanged. No network mutation/listener/enrollment/approval added.

4.2g.1 changes NO wire/config/pending schema. Shared Core enrollment client
functions preserve original private format1/request/token/ACK checks. Existing
CLI device gates, repair/grant/discovery and persistence contracts unchanged.
