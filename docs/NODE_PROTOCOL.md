# ASC NODE PROTOCOL — Design contract (not implemented)

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
This topology is **NOT** a global file catalog or consensus snapshot. No file upload/download APIs exist yet. Node profiles are self-reported and untrusted; never use them to grant privileged permissions.

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
