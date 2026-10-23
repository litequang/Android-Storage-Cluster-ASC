# ASC Architecture Decision Records

## 2026-10-23 — baseline design (proposed targets)
- ADR-001: Logical file catalog separate from actual phone volumes; no distributed RAID.
- ADR-002: Eventual full metadata replicas per eligible node, local manifests per storage node.
- ADR-003: Quorum 2-of-3 using vetted Raft implementation; never DIY elections.
- ADR-004: Scores guide candidate selection, not leader authority; prevent flapping.
- ADR-005: File staged and verified before catalog commit; deleted data protected by versioning.
- ADR-006: No-root; StorageAdapter; SD actual access tested, not assumed.
- ADR-007: M51 production protected; cannot self-elect or be heavy IO node by default.
- ADR-008: LAN and private VPN first; public gateway later and separately secured.

## 2026-10-23 — v0.4 working foundation
- ADR-009: Deliver *single-writer LAN registry prototype*, clearly labeled without Raft, rather than unsafe homegrown automatic failover.
- ADR-010: Python 3 standard library runtime; SQLite registry for low Termux setup burden.
- ADR-011: HTTPS self-signed X.509 pinned manually with SHA256 and one-time short-lived join code; node-specific random bearer token for heartbeat. No shared token.
- ADR-012: Preset device specs only as theoretical hints; actual sensors/volumes preferred if readable. Unknown stays unknown.
- ADR-013: Only pre-existing Termux-owned app-specific SD paths receive optional tiny write/read/delete probes. No format/no root/no general SD folder write.
- ADR-014: Installer refuses controller/node modes on M51; no upgrades or production service adjustments allowed. Later M51-specific safe integration needs explicit authorization.
- ADR-015: Installed code is not silently replaced on rerunning quick installer; future upgrade requires explicit versioned mechanism.

## 2026-10-23 — Phase 1.1 (0.4.1), Windows accepted
- ADR-016: Keep API v1 and migrate the registry additively/transactionally to schema 2.
  Preserve all v0.4 identities and hashes; reject a different cluster or newer schema.
  Old Controller code cannot run on this schema: rollback restores pre-upgrade private state.
- ADR-017: The locally issued one-use code is the administrator's enrollment grant;
  no second approval. Admin CLI uses its private token via pinned HTTPS loopback.
  Node tokens never authorize admin operations.
- ADR-018: Retry-safe enrollment uses a private client-generated operation ID/token,
  persisted before sending, plus a permanent hashed operation-to-node mapping.
  The one-use grant and node mutation commit together. Replacing an expired initial
  code preserves the operation identity, preventing duplicate nodes after a lost reply.
  v0.4 clients keep their original one-use, non-retry-safe enrollment behavior.
- ADR-019: Revoke is idempotent; rotation is explicit targeted re-pair, preserving node ID.
  No automatic resurrection or alternative-secret fallback. Save the previous node
  config privately before explicit replacement. A recovered/revoked identity needs
  a fresh targeted administrator grant; grant alone is the authorization.
- ADR-020: Bound input and authentication attempts with per-IP/global in-memory budgets,
  suppress HTTP payload/exception logs and bound TLS workers/timeouts. Remain private LAN.
- ADR-021: Fail closed when Android model/manufacturer/SDK are unavailable, also guard
  runtime entry points. Do not add an override for M51 or unknown hardware. Missing
  runtime measurements stay unknown; manufacturer estimates are labeled score inputs.
- ADR-022: Foreground OS advisory locks rather than PID-based kill or implicit services.
  Installer reports dependencies, never installs/upgrades them; upgrades use a separate
  versioned source directory and private stopped-state backup before migration.

## 2026-10-23 — Phase 1.2A (0.5.0)
- ADR-023: Keep independent node manifest schema 1, registry schema 3 and storage wire v1. Preserve lifecycle API/identities; generated UUID relative physical paths prepare for later metadata references without implementing consensus.
- ADR-024: Use portable exclusive final creation/copy, verify/fsync and then SQLite visibility. Reserve two pending copies plus retained/orphan physical bodies. Preserve ambiguous commits and require reauthorization; no overwrite or final-object GC. Costs an extra copy/hash and no atomic filesystem+DB/power-loss promise.
- ADR-025: Bind approved root to a random marker plus observed filesystem/root identity. Reject symlinks/reparse/hardlink file bodies; Windows directory handles deny rename during IO, POSIX component walking uses no-follow descriptors. Replacement at a reused path fails closed; fully cloned identity/media cannot be conclusively distinguished, and remount identity changes may require manual review.
- ADR-026: Separate owner data authority from node authentication. Short-lived hashed whole-volume grants are bound to node credential generation; Agent introspects Controller on every operation and again before commit. Controller outage denies network file access rather than using stale authorization. End-user ACL/login remains future work.
- ADR-027: Opt-in Agent storage runtime, separate pinned TLS identity, bounded local streaming (64 KiB, one transfer, configured size/rate/quota/reserve), full-body restart only. No implicit deployment/upgrades, replica placement or role election.
- ADR-028: Windows acceptance uses three separate temporary node states with actual loopback TLS and fault injection. Report POSIX installer skips and absent physical Android/SD/power-loss validation; do not reinterpret simulation as production readiness.

## 2026-10-23 — Phase 1.2B / v0.6.0

- ADR-029: Keep one Global Catalog mutation boundary with atomic materialization, persistent epoch, monotone revision and SHA-256 chained public history. It is single-writer, not consensus. Future Raft must externalize IDs/time/placement into deterministic prepared commands and fence all writers.
- ADR-030: Separate Global Catalog, unchanged local manifest 1, and independent read-only metadata cache 1. Use logical JSON snapshot/deltas rather than copying live SQLite/WAL. Cache imports validate cluster/schema/epoch/order/digest and cannot become an independent writer.
- ADR-031: Owner explicitly approves node endpoint/pin/volumes, generation and physical device domain. Use actual pinned capability probes, quota/reserve and measured readability; unknown load/stability remain null. Domain labels are owner assertions; Windows separate roots simulate, not prove hardware failure independence.
- ADR-032: Persist jobs/checkpoints before body transfer and retain a stable job key/principal/local object across retries. Lease/run-token/current-generation checks fence stale completion. One owned Controller worker/global transfer and per-node conflict checks bound concurrency. Backoff/terminal failure never erase bytes.
- ADR-033: Transfer minimum short-lived hashed file/job/volume/resource credentials; no peer receives another node token or long-lived admin credential. Controller independently streams/hash-verifies served bytes before publishing a replica, in addition to Agent Engine checks. This proves retrievability then, not long-term durability or Byzantine disk persistence.
- ADR-034: Relay bounded streams through Controller for this phase, reusing Phase 1.2A Engine. Direct peer pulls and resumable chunks are future transport interfaces. Accept extra hashing/IO costs to retain an auditable vertical slice.
- ADR-035: Bounded reconciliation rotates persistent inventory cursors, preserves uncatalogued/suspect/last copies, and queues repair only with valid independent sources/capacity. Keep failed target domains for explicit same-job retry instead of repeatedly cloning abandoned jobs.
- ADR-036: Windows real pinned HTTPS/temp-state acceptance precedes Android. Preserve legacy lifecycle/whole-volume grants; v0.6 scoped grants require method/resource constraints. Metadata-only approval needs no fabricated storage endpoint. No phone/M51/production actions or new deployment workflow.
