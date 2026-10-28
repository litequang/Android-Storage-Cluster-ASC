# ASC Architecture Decision Records

## Phase 2B design — Windows development qualified

- ADR-042: Extend the existing prepared-document CAS with a versioned bounded
  runtime envelope containing explicitly allowlisted authority rows, hashes and
  public lease IDs. Prepare old business transactions on disposable SQL, keeping
  original metadata-mode guards intact. Control revision is independent from
  Catalog history. No private keys/raw bearer tokens enter the envelope.
- ADR-043: Runtime commands must match the actual Raft apply term and local
  configured owner ID. Commit takeover before authority, invalidate grants/leases,
  retain checkpoints and reverify physical evidence. Online pinned per-operation
  introspection plus a fresh nonce-bound committed receipt authorizes Storage;
  client-supplied term and discovery hints never authorize it. No destructive API.
- ADR-044: A Python liveness watchdog explicitly armed over private IPC shuts
  down a voter through the upstream API after 12 seconds without heartbeat. This
  prevents a surviving sidecar permanently owning a dead Python Controller. It
  changes no election algorithm/membership. Retain healthy leadership rather than
  use oscillating scores; planned transfer remains disabled pending qualification.

These decisions passed the isolated Windows Phase 2B fault matrix and full
regression. Android runtime and production remain unqualified; see the limits
and exact executed evidence in PHASE2B-ACCEPTANCE.md.

## 2026-10-23 — authorized Go continuation

- ADR-039 (selected for Windows metadata consensus): Owner selects HashiCorp Raft first,
  etcd/raft only if unsuitable. Use official development Go 1.27.3 Windows AMD64
  (download SHA-256 f26081f438319757f8a1b46d7d0b2c5ec7583d4038e485e0aa725cfde7885fff),
  outside source, without changing global PATH. Pin raft v1.8.0 and
  raft-boltdb/v2 v2.4.2 with Go checksum verification. Backend defaults keep fsync
  enabled. Missing or inconsistent state quarantines; never automatically reset.
  No production/Android acceptance or physical power-cut claim follows.

  Pin bbolt v1.4.3 explicitly: backend's transitive v1.4.1 fails the actual
  Android/ARM64 compile (`bolt_android.go: undefined maxMapSize`). Upstream
  v1.4.2 fixes this; v1.4.3 also fixes backup corruption. No dependency source is
  patched. Primary source: https://github.com/etcd-io/bbolt/blob/main/CHANGELOG/CHANGELOG-1.4.md.

- ADR-040: Use a bounded prepared-projection CAS FSM rather than porting ASC's
  placement/jobs/business logic into Go or invoking Python/network IO during
  Raft apply. Trusted Python preparation validates canonical Catalog rows/events;
  Go commits immutable bytes with identity/expected SHA/intent-bound receipts.
  Go snapshots retain the entire authoritative projection and receipts even if
  Python has not applied it. Python's installation transaction includes Catalog
  state/events, applied index/term and receipts. Strong reads commit a Barrier;
  local views are explicitly stale with exact checkpoints. This is metadata
  consensus, not full Controller/storage failover. Static three-voter membership
  and 2 MiB/4096-receipt bounds are explicit; no unsafe eviction or recovery API.

- ADR-041: Persist SQL guards and deny normal writer/DDL connections after
  attachment; freeze private registry/approvals/jobs/grants and reject old storage
  authorization. Retain objects and RUNNING jobs unchanged. Attachment requires
  exact stopped-state seed equality; explicit new-voter import refuses nonempty
  histories. An external enrollment witness prohibits re-init after whole-state
  loss; restore only complete reviewed state. Go Android runtime stays refused
  despite a successful cross-build. Windows metadata configuration is an explicit
  local-development route, retaining protected-profile/unknown-Android guards.

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

## 2026-10-23 — Phase 2A engine gate (implementation blocked)

- ADR-037 (decided): Do not adopt unmodified PySyncObj 0.3.17. Its MIT official sdist was SHA-256 verified and exercised with tools/qualify_pysyncobj.py. A clean restart retains term/vote, but deleting or corrupting only .meta permits a second vote to another peer in the same term. Probe also observes absent fsync/mapping-flush boundaries and unauthenticated default address handshake. This does not assert measured physical power-cut loss or an exploit against ASC. Evidence, exact hash, primary sources and limits: [PHASE2A-ACCEPTANCE.md](PHASE2A-ACCEPTANCE.md). No patch, engine dependency or runtime mode is installed.
- ADR-038 (pending integration choice): Prefer investigating etcd-io/raft v3.7.0 (Apache-2.0) through a Go sidecar for deterministic engine ticks/messages and safe read barriers; a Go development toolchain and Windows/Android artifact qualification are still needed. HashiCorp raft v1.8.0 (MPL-2.0) is another native alternative. rraft-py 0.2.27 (Apache-2.0) has no matching published Windows CPython-3.14 wheel and requires unverified native build work; raftos 0.2.6 (MIT) has persistence and legacy pinned-dependency gaps. A reviewed PySyncObj fork with durable/fail-closed persistence and per-voter pinned transport is an alternative, not an accepted implementation. No engine is finally selected, no homemade Raft is authorized by this ADR, and no universal claim that all libraries are unsuitable is made. Report alternatives to the owner before crossing the task's custom-engine boundary.

## Phase 3A decisions

- ADR-045: Extend runtime schema 2 with optional bounded backup schema 1. Explicit
  enable after all Controllers upgrade; old validators fail closed. Preserve the
  frozen source registry and Engine. No automatic SQL or identity migration.
- ADR-046: Capture logical manifests at an exact quorum-confirmed source index;
  retain immutable version pins separately from current heads. Independently hash
  domain-separated replicas before backup verification. In-cluster logical backups
  are not disconnected disaster backups. Historical verification can become stale.
- ADR-047: Restore creates a new version with a durable job/reserved version and
  stable existing upload key. Takeover invalidates backup leases/proof progress;
  fresh verification and current Storage authority are required. Retention only
  marks EXPIRED, never deletes final bytes or permits stale-Leader physical GC.

ADR-045..047 passed the actual Windows Phase 3A fault matrix and full regression;
qualification evidence and remaining limits: PHASE3A-ACCEPTANCE.md.

## Phase 3B decisions

- ADR-048: Advisory deterministic score and separately reported confidence and
  observed probe reliability; UNKNOWN for absent/stale/future data, never use
  manufacturer readiness hints as measurements. No score-driven voter authority.
- ADR-049: Optional versioned bounded node-insights extension through existing
  actual-term prepared-document CAS. Hourly calendar aggregates preserve gaps,
  generation provenance and authority receipt limits. Owner preferences are
  replay-safe; restrictive choices survive re-pair, stale Preferred does not.
  Drain is an allocation preference, not automatic movement or physical GC.

- ADR-050: Reduction is a pure checkpoint-bound proposal in Phase 3B. Keep current
  policy minimum independent readable domains; retained snapshot/restore pins,
  non-LIVE versions, unfinished work and stale views hold reduction. Unknown/old
  proofs cannot count, Protected copies are held, and every future candidate needs
  fresh byte verification under a separately qualified apply protocol. No deletion
  grant/manifest writer/apply endpoint is added. Cloud full regression and 39 fault
  gates qualify this boundary; no physical GC or new platform runtime follows.

## Phase 3C decisions

- ADR-051: Extend bounded optional runtime state for replay-safe policy/moves and
  retired-object fences, reusing existing Go actual-term CAS and COPY Engine.
  Trusted preparation adds an explicit Catalog retirement/event boundary; no byte
  deletion occurs there. Require fresh streamed independent survivor proofs and
  current policy/retained-backup floor, then permanently fence the retired physical
  identity against reintroduction. Historical references are not silently evicted.
- ADR-052: Use a pure complete reference graph and graph/plan digests, not current
  replica count alone, for GC eligibility. Keep terminal job and event pointers as
  holds until an explicit audited release/ordinary retention genuinely removes
  them. Immutable fences and append/retention transition checks apply to all Runtime
  writers. A plan/estimated logical size never proves authorization or reclaimed disk.

- ADR-053: GC authorization is a separate exact-job scope, never a whole-volume grant. Each explicit execution commits a new hash-only generation/approval/endpoint-bound permit after streamed external-domain survivor proof. Final Storage introspection performs that proof again and commits a nonce in the actual term. Release the Runtime lock during network proof to allow ordinary scoped survivor reads. Persist only reservation/run/hash/proofs; same-job journal identity survives new permits and takeover. No background or real-device enable path.

- ADR-053 refinement (3C.5b): bind the complete graph digest across survivor IO and final authorization CAS, including survivor endpoint approval changes. Preserve exact prior evidence instead of accepting merely unchanged node/volume IDs after reapproval. This is ephemeral validation, not a new permit/persistence schema.

ADR-053 proof-binding detail: canonicalize unrelated self-reported profile telemetry while preserving protected state and every reference/approval/policy field. Existing planner/confirmation digests are unchanged. This avoids false proof invalidation on ordinary heartbeat while retaining actual pinned freshness/readability gates and approval-race rejection.

- ADR-054 (Linux 3C.5): reuse pure structural Catalog validation only by exact
  immutable canonical JSON bytes, bounded to two admitted <=2 MiB Catalogs. Verify
  native JSON types before keying so Python tuples/non-string keys cannot alias
  valid input. Failures are not cached, caller objects are not retained/returned,
  and runtime/extension/authority/term/quorum/physical-proof checks remain fresh.
  Do not increase destructive freshness budgets to compensate for repeated work.

## Phase 3D external backup / recovery decisions

- ADR-055: Export an exact strong quorum-confirmed runtime schema2 projection,
  all Catalog versions and streamed size/SHA-verified bytes into a separate private
  versioned store. Preserve historical jobs/identities but exclude secret keys/raw
  tokens/local Raft databases. Conservative ALL-version coverage; missing pending
  upload bytes prevents COMPLETE. Source/provider and destination interfaces remain
  separate. External evidence never relaxes existing GC/pin protections.
- ADR-056: Require trusted separately retained manifest SHA for verification/staging
  authenticity, plus expected cluster and operator minimum-known index for staging.
  Self-contained SHA is not a quorum certificate or freshness proof. Recovery only
  writes a new isolated passive READ_ONLY bundle, never a live DB/config/voter.
  Writer activation is blocked until upstream Raft recovery, old-cluster fencing
  and credential/identity recovery are independently qualified. Retention is
  preview-only; no external automatic deletion or custom encryption algorithm.

## ADR-062 — Core-first Phase4 source integration without state convergence
Keep Core3D ca2504f as feature baseline; port reviewed Demo c9c2660 modules/tests/
public archives individually, never a whole merge/doc overwrite. Same base schema
numbers do not grant mode compatibility. Keep marked Demo single-writer runtime
separate from quorum/advanced state and passive recovery. Reuse durable Core
registration and owner-session Dashboard; no new Catalog/Storage/auth DB. No native
app/state migration or writable DR is implied. Candidate only, actual Android
qualification deferred. Imported historical Demo ADR055/056 map to canonical
ADR060/061; existing Core055/056 keep external/DR meaning, Demo057–059 are available.


<!-- Reviewed Demo c9c2660 historical extension; current Phase4 status is in PHASE4-PROGRESS. -->
- ADR-060 (imported Demo ADR-055): keep independently versioned immutable Demo code and marked
  state separate from Core/private legacy state. Reuse single-writer registry 4,
  Catalog transfer/proof/fallback and local manifest 1 with explicit private LAN
  binds; isolate Controller and enrolled node homes on a cohosted phone. Do not
  remove Android Raft guards. Exactly two owner-approved physical domains and
  measured double-copy capacity gate a new upload; report interruption/degradation
  honestly. No implicit migration, policy reduction, whole-volume grant or GC path.

- ADR-061 (imported Demo ADR-056): reuse Core OS _lock/_unlock primitives through a
  Demo-specific no-follow regular/single-link/inode opener. Reusing foreground_lock
  as a whole was unsafe for an existing symlink because its empty marker write
  precedes later path checks. Preserve Core source; reject unexpected coordination
  files and linked internal worker/engine locks before any Demo operation/constructor.
  Do not unlink/replace a suspicious lock to make startup pass. Fresh hardened
  targeted/full qualification supersedes the initial package candidate.

- ADR-057 (DEMO.4): browser trust uses separate explicit private CA/IP-SAN listener
  in the same Controller process, preserving all Core/node certificate pins. Never
  instruct a browser to bypass TLS errors. Owner CLI issues one-use RAM grants;
  browser gets scoped HttpOnly/Secure/SameSite session + CSRF, not Core credentials.
  Keep node approval CLI-only. Reuse Catalog and pinned ClusterClient for bounded
  private spooled transfers; received bytes/SHA/protection are separate facts.
  Root/base schemas unchanged; optional Dashboard format is independently validated,
  backed up and ignored by compatible old CLI-only source after stopped rollback.

## ADR-058 — 0.4 optional Dashboard state, exact published-package rollback
Keep every base state format unchanged and browser state optional/independent. Add dashboard-lite capability without changing existing required CLI capabilities, allowing exact old0.3 stager to verify/activate0.4. Test both old and new code/bytes rather than relabeling current code as0.3. Rollback makes NEW full state+volume backup, selects preserved old code, ignores optional Dashboard and keeps new file bytes/catalog; never restores stale DB. Browser TLS/CA import stays explicit owner procedure; no installer trust-store mutation. Mixed live versions/rolling update remain unsupported.

## ADR-059 — approved-root descriptor anchor without filesystem-root read permission
Use the already approved volume dev/inode and exact node/volume marker as the POSIX anchor. Absolute lookup opens only that directory; no-follow child descriptors plus namespace snapshots/rechecks prevent adoption or redirection to swapped roots/ancestors/folders/markers. Reading/lstat metadata of ancestors does not require opening/listing them. This is equivalent scoped access within the trusted private OS account, not a sandbox against a malicious privileged co-owner or a claim of atomic filesystem+DB/power-cut durability. Missing descriptor primitives fail closed, with no unsafe absolute-child fallback. Preserve marker/formats/IDs; share this fix in Demo branch only, leave Core WIP unchanged. Measured probe truth follows cleanup; random name collision is preserved, never deleted.

## ADR063 — Session facade and local enrollment adapter
Accepted for Phase4.0 Demo single-writer only. Use existing Registry one-use
codes and Core durable retry enrollment; no second enrollment store/engine.
Owner browser receives a short-lived code once, tracks a bounded session ticket;
only hashes remain server RAM, underlying grant lifetime is independent of UI.
Node identity belongs to the initialized local engine, not browser storage.
An optional expected-cluster CLI guard uses the old pending field, preserving
wire/schema compatibility. No automatic volumes/storage/domain permission.
Reject unknown/quorum/recovery modes; Core3D writable recovery stays BLOCKED.
Native application bridge, Keystore/SAF and single-writer-to-Raft migration need
separate contracts/tests; this adapter does not implement them.

## ADR064 — Local application bridge without cross-UID assumptions
Explicit separate app authorization+SO_PEERCRED/private UDS; fixed operations and
root, durable bounded retry receipts, existing Core enrollment/identity. No TCP/
browser arbitrary filesystem/process route. Controlled Node child only with actual
ownership/parent-death fence if supported. Linux same-UID qualification does not
implement Binder or grant APK access to Termux. No implicit init/approval/migration.

## ADR065 — Core observability is not writer authority
New sanitized GET view uses existing Runtime.view(strong=True) upstream Barrier;
never ensure_ready/commit/takeover. Explicit mode/pins/cluster/epoch/Controller ID,
no Demo SQL fallback. Share existing Dashboard HTTPS/session/assets, server-side
read-only enforcement and honest UNKNOWN/quorum/recovery states. Never activate
recovery, change membership, mint GC authority or infer writer from Leader flags.

## ADR066 — Native app UID and capability qualification before runtime authority
Use pinned Android/Kotlin/embedded canonical Python; private Binder/UID+signature
and explicit UI consent. Actual local Engine proof is separate from Native Node/
TLS/enrollment/lifecycle. Unsupported provider stays FOUNDATION, not mock/idle FGS.
No Termux shared UID/state copy or weakened guards.

## ADR067 — App Keystore and probe namespace never become cluster identity
Application UUID/nonexportable AndroidKeyStoreAES-GCM and encrypted unsent draft
are separate from Core pending/token/Node. Fixed private capability probe reuses
Core safety code and has its own application-bound namespace; never adopt synthetic
actor/volume as live Node. Lost state/key/schema/medium is held. SAF unavailable
until equivalent semantics proven; no custom encryption or writable recovery.

## ADR068 — Native diagnostic fence, stable Binder and upgrade evidence
Keep private Binder operation IDs explicit0/1 and reject foreign UID even with matching signature. Add native M51/unknown fence; debug AOSP emulator diagnostics do not bypass Core. Exclude CE/DE cloud+D2D backups because copying encrypted files cannot restore nonexportable keys. Qualify exact private prior-checkpoint APK upgrade on a FRESH AVD using same signer and real retained bytes/key/marker; Android version downgrade MUST refuse. No uninstall/adb-d/stale DB restoration, general native rollback or released Termux migration claim. Real default-network loss clears code/trust. Native Node/enrollment/FGS remains blocked on reviewed shared-Core native providers, not papered over by a mock or guard bypass.

## ADR069 — Explicit native context before Node authority
Use one fixed application-bound, Keystore-encrypted CAS record with durable
required-record witness and original private-directory receipt. No global HOME,
plaintext node tokens, legacy state adoption or new Kotlin enrollment logic.
Partial publication is held rather than reconstructed. Debug AOSP is a distinct
synthetic fixture scope, not unknown-phone/M51 permission or Core guard bypass.
Context UUID is not Node/Cluster identity; f.1 cannot start runtime or join.

## ADR070 — Explicit memory-only Android TLS provider
Keep Core context and encryption authoritative. Use standard BC1.83 only for
JCA/X.509 generation; Android platform JSSE/KeyManagerFactory consumes sealed-fd
readback in RAM with standard certificate/signature key-match checks. Bionic
public memfd API30+ supplies the missing Python wrapper, not an OS permission
bypass. Android proc reopen denial is preserved; no disk PEM/raw syscall/SELinux
change or automatic provider switch. Both platforms require actual seals/CLOEXEC/
readback/cleanup. TLS key is software/exportable in RAM, protected at rest by
existing Keystore AES, not falsely hardware-nonexportable. Agent socket/lifecycle
integration is a separate checkpoint; no duplicate Engine or writer authority.


## ADR071 — Network-only browser PWA shares owner Dashboard
Provide manifest/local icons and network-only navigation worker under the existing
HTTPS origin. Keep all API/file requests on the existing authenticated services;
no persistent offline catalog/cache, writes, credential store or app/Termux process
control. Install UX is consent-based, and CDP installability is separate from
actual user/Android installation. Source package uses the same fixed asset allowlist
as HTTP, preventing missing assets or accidental private frontend files.

## ADR072 — Native accepted transport owns deadline cancellation (2026-10-27)

The Android platform adapter retains only each TCP socket it accepted on an
approved private endpoint, layered with the existing server-mode JSSE context.
Core receives TLS streams only. Close the exact transport before TLS close to
interrupt blocked Conscrypt I/O; concurrent closers wait for completed cleanup
with a bounded failure path. A started-close flag is insufficient evidence that
the active connection slot has been released. No arbitrary fd/PID/process access,
plaintext dispatch, identity/schema change or certificate/pinning fallback.

SO_REUSEADDR permits restarting after actual TCP TIME_WAIT; never SO_REUSEPORT.
Actual Android rebind and concurrent-owner rejection tests distinguish these
semantics. Existing nonreading-peer read/write deadline, wrong-pin and binary SHA
tests remain unchanged. API30 x86_64 targeted28+foreign1 and normal Node/catalog
network/process-death qualification pass; final APK5/API35 and phones are not
inferred from historical APK4 evidence. See PHASE4-2-PROGRESS for failed attempts,
source3914b99 and the fixture-only physical-readiness qualification2131e83.


## ADR073 — Reuse exact-byte structure, never live authority
Profiling the unchanged1024-event synthetic GC workload observed repeated Runtime
view/SQL validation while nested survivor authorization exceeded the10s fence.
Reuse successful STRUCTURAL validation for at most two immutable <=2MiB inputs;
return independently parsed JSON each time. No mutable result/approval/receipt is
cached. validate(dict) and prepare_registry still validate their caller-owned
inputs normally. Runtime checksum, canonical wire, identity, revision/index/term,
fresh Go quorum and operation receipts remain mandatory. Keep GC10s/250ms fences
and physical SHA/last-copy/reference checks. Prior retry/TTL experiments failed
and remain excluded. This is a Core decode optimization, not Android GC/runtime
activation or a new Catalog. Actual qualification follows in current progress.

## ADR074 — Separate private access plane, preserve existing owner authority
Owner defers hardware acceptance while source/synthetic Phase5 proceeds. Use a
new explicit private HTTPS ingress forwarding only fixed existing browser routes
to an operator-pinned Dashboard. Keep its owner sessions/CSRF/Catalog/transfer
logic; no parallel database or machine-token browser login. Check external exact
Host/Origin before translating to the fixed pinned upstream. Mode is mandatory:
Demo file routes versus Core/recovery read-only, never fallback. Numeric private
or CGNAT address does not prove VPN membership; status stays UNKNOWN until actual
provider evidence. First version denies public/DNS/wildcard endpoints and all
node/admin/enrollment/GC/shell routes. Cloudflare/public trust and operator-only
private maintenance are separate later checkpoints. Deferred hardware is not PASS.
