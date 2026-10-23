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
