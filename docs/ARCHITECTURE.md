# ASC ARCHITECTURE 2.2 — PROPOSED

## Implemented boundary — 0.4.1 / Phase 1.1

The design below remains proposed. Implemented runtime is one foreground HTTPS LAN
Controller with one SQLite writer and foreground agents; no Raft, catalog, storage,
automatic failover or production integration.

- API stays `/api/v1`; registry schema 2 adds node credential lifecycle and hashed
  enrollment-operation routing without replacing v0.4 cluster/node identities.
- Admin CLI runs on Controller, reads its private admin credential and calls pinned
  HTTPS loopback. Node tokens authorize heartbeat only. Local status reads cached state.
- Enrollment persists a private client-generated operation ID/token before sending.
  Grant consumption, operation mapping and node creation/rotation share a transaction.
  Targeted re-pair preserves node ID and invalidates the previous token.
- Revoked nodes cannot heartbeat; role planning excludes them. Agents stop on rejected
  credentials and require explicit re-pair rather than silently registering again.
- Rate budgets are in-memory per source IP plus global windows; HTTP workers and
  request/response/profile sizes are bounded. They mitigate abuse, not Internet exposure.
- OS-held locks prevent duplicate foreground runs in the same private ASC_HOME.
  Stop is Ctrl+C, with no daemon, startup or boot integration. Old v0.4 processes must
  be stopped manually before upgrade because they do not participate in these locks.
- Unknown Android identity blocks installation/runtime and SD writes; recognized M51
  remains protected. Read-only profiling keeps unavailable telemetry null/unknown.

Phase 1.1 Windows acceptance: the owner reports 40 tests OK (skipped=3), with three
POSIX installer cases unavailable on Windows. Source/tests are unchanged in the
publication/workflow update, so that result is reused without claiming a Codex rerun.
Local testing follows AGENTS.md. Linux/Termux installer and real-phone acceptance
remain deferred; this is development code, not end-to-end storage or production readiness.

## Fundamental goals
- A unified logical file library across many standalone Android phones.
- Full, versioned metadata replicas at eligible nodes; local file manifests on every active storage node.
- No unique permanent controller. One valid leader within a quorum-controlled group.
- Remote access independent of any single storage phone.
- User data durability is separate from metadata durability.
- Non-root. Strong guardrails for M51 running hosting.

## Three separated planes

1. **Control plane**: node registry, memberships, policies, storage-object metadata, jobs, auth and Raft committed operations. Initially 3 voting nodes (ZTE, Bphone, XZ3) *if they pass hardware audits*. Non-voters receive verified snapshot/log replication and expose safe read-only catalog queries.
2. **Data plane**: immutable content objects in per-node volumes, checksum, size, replica state, local manifest; transfers direct between nodes where possible. Controller coordinates rather than transiting every large file.
3. **Access plane**: ASC Drive PWA, API, WebDAV later, LAN discovery, Tailscale private network first, optional HTTPS gateway(s). Gateways discover the current legitimate leader; routers cannot grant write authority.

## Leader election (important)
- No 'strongest node wins' shortcut. Raft safety conditions (majority, term and up-to-date log) are mandatory.
- Eligible nodes get health/uptime/network/thermal/capacity scores as *preferences*. Initial membership is static, changed only by consensus (or controlled disaster recovery).
- Avoid oscillation: do not switch leader when healthy; optional graceful transfer after a sustained, meaningful health difference.
- A node may host user-facing read-only catalog view even if it is not a voter.
- On loss of quorum, reject mutations to the global catalog. Local storage objects can be safely read; uncommitted uploads must remain unadvertised staging.
- Single remaining node cannot unilaterally become write leader. Emergency rebuild requires fencing/isolation of the old cluster and a deliberate recovery procedure.
- 'Any node can be controller' means it may be upgraded to voter when healthy and compatible, not automatic singleton write authority.

## Object lifecycle
`INITIATED -> STAGING -> VERIFIED_LOCAL -> COMMITTED_REFERENCE -> REPLICA_PENDING -> REPLICA_VERIFIED`

- Staging objects are immutable, keyed by unique object id and digest.
- Commit metadata only after at least one durable local object was acknowledged; UI must display `1 copy / backup pending` until replica target confirmed.
- Copies on the same device or same failing volume do not count as independent durable replicas.
- Delete logical file via tombstone and retention period; physical garbage collection must verify no retained snapshot or policy requires object.
- Content placement respects actual free space, per-volume min-free, and device role/health. M51 is never default heavy transfer destination.

## Storage media
- Prefer a stable StorageAdapter interface (`list_volumes`, `probe`, `put_staging`, `commit_object`, `read_range`, `delete_if_safe`).
- Termux app-specific SD access is limited and uninstallation can delete files. It is NOT an adequate sole long-term storage guarantee. A separate Android SAF bridge, when needed, must use scoped permission to user-selected folder and explicit persistence semantics. No premature assumptions that Termux can write SD root.
- Keep metadata in SQLite-like transactional storage on device internal app storage; do not put DB files on shared SD/exFAT.

## Failure and boot behavior
- Android background and boot behavior vary with OS/OEM. Termux:Boot is not a guaranteed auto-recover after power loss. Audit actual behavior.
- Node may boot before cluster; it reconnects and catches up. Non-voter may be offline for weeks; it verifies snapshots and obtains missing logs on return.
- Offline local read is only as fresh as last verified snapshot.
- Gateway may route reads to in-sync follower; writes must be forwarded to current authenticated leader, then quorum committed.

## Online
- LAN first. Tailscale private VPN preferred for remote access; no publicly exposed SFTP or node control port.
- Optional HTTPS edge tunnel after security review, with multiple independent connectors that validate current leader. HTTP upload chunk/resume required if using proxy limits.
- No external cloud dependency for LAN file access.

## Deferred deliberately
- No full RAID, erasure coding, browser-only background camera backup, active-active multi-leader, instant unbounded file access during partitions, or custom cryptocurrency/blockchain.
