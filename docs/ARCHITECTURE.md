# ASC ARCHITECTURE 2.2 — PROPOSED

## Phase 2B development boundary — Windows qualified

The new opt-in failover runtime prepares existing business SQL against disposable
in-memory state, commits a bounded schema-2 authority envelope through the same
Go CAS FSM, and caches only verified committed bytes/checkpoints in a separate
private runtime DB. The original guarded Phase 2A registry remains preserved.
Control revision is distinct from Catalog revision. Takeover commits the owner
and actual Raft term, invalidates old grants and leases, preserves stable job/
session/object identities, and invalidates placement probes before work resumes.
An authenticated liveness heartbeat withdraws a sidecar if Python dies. Discovery
uses provisioned pins only; storage requires fresh online committed authority.
The readiness audit and executed Windows qualification are in PHASE2B-ACCEPTANCE.md.

Runtime attachment proves the frozen original private state against the permanent
initial upgrade receipt. It refuses independent authority histories instead of
discarding them. A fresh follower must have the exact source Catalog and no private
authority to merge. Pending jobs run before background reconciliation, with one
physical verification per audit turn. A known scoped job can explicitly resume a
held immutable final copy only after rehashing matching retained staging/final
bodies and obtaining fresh authority; unknown/mismatched bodies remain held.

Public MetadataSource snapshot/delta envelopes retain their original exact schema,
digest and transaction revision. Runtime response labels are not injected into
these versioned payloads; node caches continue using the unchanged strict validator.

## Lifecycle boundary inherited from 0.4.1 / Phase 1.1

The lifecycle below is retained. Phase 1.2A local storage is documented at the end.
The early consensus target below is historical design. Later sections describe
single-writer storage and the opt-in Go metadata consensus continuation. Phase 2B
Controller failover is described above; production/Android integration is absent.

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
POSIX installer cases unavailable on Windows. That was the unchanged-source publication result for v0.4.1; Phase 1.2A runs new local tests.
Local testing follows AGENTS.md. Linux/Termux installer and real-phone acceptance
remain deferred; local storage acceptance does not imply distributed/production readiness.

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

## Implemented Phase 1.2A — local storage boundary

An explicitly configured Agent owns one private internal SQLite manifest and up to eight approved filesystem volumes. Windows uses empty configured directories; Android internal storage can use private HOME; SD registration accepts only a descendant of a currently detected pre-existing Termux app folder. Discovery only proposes candidates; it never approves an arbitrary root, formats media or grants Android permissions. LocalVolume is the adapter seam (check/open/remove_staging/sync_directory/allocated_files); kind SAF is rejected until an adapter provides equivalent semantics.

Agent-run starts pinned HTTPS storage alongside heartbeat only when storage.json exists. No configuration keeps Phase 1.1 topology-only behavior. Windows accepts this explicit local storage runtime; Android still requires the original non-protected known-device guard. Controller remains one registry writer, never an Agent-selected leader.

Owner -> pinned Agent /storage/v1 -> pinned Controller authorization -> local engine. The Controller issues short-lived volume/operation-scoped owner grants; node token only authenticates introspection/heartbeat. Registry schema 3 is additive from 0/2. No global file catalog is introduced.

Body processing uses 64 KiB chunks, one transfer per engine, default 8 MiB/s (configurable 1 byte/s–64 MiB/s), default max object 64 MiB (configurable up to 1 GiB). HTTP workers are capped at 32, idle socket timeout 12 seconds, upload body budget 60 + declared_size/rate seconds. Metadata operations serialize with mutations; sessions/files/volumes have explicit bounds (128 pending, 10,000 committed files, 8 volumes).

Commit creates a final UUID object exclusively and copies verified staging, fsyncs, verifies the final copy and reauthorizes before the manifest transaction advertises it. Pending quota reserves two bodies; actual orphan/retained bodies remain charged. Real free space is rechecked with configured reserve. No overwrite or final-object GC exists. Filesystem and SQLite are not one transaction: restart conservatively preserves ambiguous copies. Windows directory fsync and physical power-loss durability are not promised. Detailed states are in DATA_MODEL; portable recovery is deliberately conservative.

This is verified local storage, with no replication, backup, Raft, automatic election or availability when Controller authorization is offline. Android/SD/Doze/power-cut acceptance remains deferred.

## Implemented Phase 1.2B — distributed storage with one metadata writer

The Controller owns registry schema 4, including the Global File Catalog, ordered metadata history and private durable job queue. Every file/replica/policy change goes through Catalog.mutate in one BEGIN IMMEDIATE transaction with its revision/event. Agent local manifest remains schema 1. Each approved node also holds a separate read-only metadata cache schema 1. No global file writes originate from a metadata cache.

Owner explicitly approves a paired node's numeric private endpoint, out-of-band certificate pin, volume IDs, physical device domain and metadata/storage permissions. Metadata-only approval needs no storage endpoint. Re-pair changes generation and requires reapproval. Controller probes actual Agent volume status/quota/free space/read-write/hash/fsync before placement; manufacturer presets, self-reported heartbeat, unknown load and unknown stability never become measured storage evidence. Duplicate node/volume aliases in the same approved device domain count once.

Upload creates a durable UPLOAD job and returns a short-lived exact-target grant to the owner client. File bytes go to existing Agent staging/commit. Controller then verifies size/hash/identity, reads served bytes itself through a bounded SHA-256 stream and publishes a VERIFIED replica. COPY jobs use the same local Engine with a stable job/key/session/object across retries. Bodies currently relay through Controller in 64 KiB chunks; direct node-to-node pulls/chunk resume are future extensions. No raw node/admin secret is forwarded to a peer.

Policies single/replicated_2/replicated_3 are minimum targets across distinct approved device domains. Report desired, historically verified and currently available counts separately; availability uses recent measured volume status and active approved identity, not a promise of continuous reachability. Missing nodes or quota produce explicit degraded/under-replicated reports. Reducing policy does not delete excess objects or cancel an already authorized stream.

One OS-held catalog-worker lock owns scheduling/recovery; one Controller transfer runs at a time, with per-node conflict checks and existing one-transfer Engine admission. Default relay/readback rate 4 MiB/s (64 KiB/s–64 MiB/s), default RUNNING lease 300 seconds (30–900), five failed attempts with backoff. Size/rate/lease must fit a multi-pass verification; timeout preserves data. Pending owner uploads wait for owner completion/resume; grants expire and the same plan/key issues fresh authority.

Metadata snapshots are consistent read transactions, canonical SHA-256 protected, cluster/epoch/revision bound and limited below 2 MiB. Ordered digest-chained deltas retain 1024 revisions, at most 100 events and the byte limit/page. Nodes validate order/gaps/duplicates/checksums before atomic import; missing history triggers a fresh pinned snapshot. A lower revision, wrong cluster/epoch or conflicting same-checkpoint snapshot is refused. Offline caches remain lookup-only and explicitly stale; file authorization continues to require Controller.

Reconciliation rotates persistent per-volume inventory cursors (16 pages/run, 200 rows/page), verifies at most eight known replicas/run and caps diagnostic categories at 256 entries. It reports native v0.5 files and orphan objects without automatic adoption/deletion, repairs deficits only from physically valid sources and preserves suspicious/last copies. Failed target domains are held for explicit retry; spare eligible domains can still heal.

Catalog.mutate is an integration boundary, not a completed deterministic Raft apply. Phase 2 must separate nondeterministic preparation (IDs, time, placement) from replicated application, define fencing/epoch recovery and fault-test quorum behavior. No consensus, election, automatic Controller failover, disaster-proof backup or Android/power-cut readiness is claimed.

## Phase 2A — Go metadata mode and preserved initial investigation

Go continuation: the development-only `consensus/` package wraps official
HashiCorp Raft and its synchronous Bolt backend. ASC supplies identity/integrity
and quarantine policy, not an election algorithm. Runtime open never calls
bootstrap; initialization is explicit and refuses an existing state directory.
An interrupted pair of upstream vote-term/candidate writes quarantines restart.
Engine qualification now includes durable three-voter loopback mTLS election,
partition, restart and snapshot tests. Windows metadata-only integration acceptance
passes all 15 scenarios and the full 95-test Python suite (3 POSIX skips).
`controller-run --consensus-config PRIVATE_FILE` opts into metadata-only consensus:
Python prepares DECLARE/POLICY documents, Go commits a SHA-preconditioned document
and durable replay receipts, then Python installs Catalog rows/events, applied
index/term and receipts in one SQLite transaction. State bytes are base64 on IPC
to preserve canonical UTF-8 hashes exactly. Snapshots include the Go authoritative
document and receipts even if Python has not yet projected committed changes.

Persistent SQL guards and default-deny connections block legacy Catalog, registry,
job and grant writers after attachment. Old grants no longer authorize storage.
The mode starts no storage worker/heartbeat refresh and exposes only a loopback
metadata API. Physical objects/manifests are untouched; no Controller/storage
automatic failover claim is made. Local reads are stale with exact checkpoint;
strong reads wait for an upstream committed Barrier and applied FSM. During Go
startup replay, the last verified Python projection remains explicitly stale.

### Initial PySyncObj investigation (historical)

Engine qualification rejected unmodified PySyncObj 0.3.17: missing/corrupt vote metadata permits another same-term vote; persistence synchronization and default voter authentication do not meet ASC requirements. See ADR-037/038 and PHASE2A-ACCEPTANCE.md for reproducible evidence and alternatives. At that initial stage no consensus runtime or v0.7 release existed; the Go continuation above subsequently qualified metadata consensus.

The proposed integration separates leader preparation (IDs, clock, placement and physical proof), an engine majority-commit boundary, deterministic Catalog apply, and a transactional applied-index/idempotency receipt. Apply must not consult live network, local clock, random values, unreplicated node approvals or queue leases. File revisions map to committed Catalog changes; engine no-ops do not create file revisions.

A safe read barrier/ReadIndex plus applied-index check is required for strong reads. A local leader flag/term/heartbeat is insufficient. Existing read-only caches remain stale. Public metadata exports need a separate validated consensus snapshot envelope rather than becoming Raft snapshots merely by renaming them.

At that initial stage, registry lifecycle, approvals/probes, job leases/grants and storage side effects remained single-Controller state. Metadata-only consensus must prohibit physical-write/job failover until distributed fencing is proved. Bootstrap/membership/recovery must preserve cluster identity and fail closed on lost state. These were the initial integration constraints; the separate Phase 2B boundary and qualification above describe the later opt-in runtime.

## Phase 3A opt-in backup boundary ? Windows development accepted

POST backup/enable adds bounded backup schema 1 to the existing schema-2 runtime
projection. All Controllers must use the matching source before enabling it.
Existing Go CAS, actual-term checks, private cache and Storage introspection carry
this extension unchanged. Base registry 4/manifest 1/public cache 1 are unchanged.
Snapshots capture exact committed index/term/control and Catalog revisions plus
immutable version descriptors; subsequent verification is historical evidence.
Backup jobs request existing domain-separated COPY jobs and independently hash
served bytes. Restore uses existing UPLOAD/session/commit/proof paths with one
persisted version and stable key; it creates a new version, preserving the source.
Retention expires logical references only. Physical immutable bytes are preserved.

The executed 12-gate Phase 3A matrix and fresh complete regression qualify this
bounded Windows development path only; see PHASE3A-ACCEPTANCE.md.

## Phase 3B optional node insights

Read-only score views derive from one verified runtime document, never live network
IO during apply. Explicit owner enable adds insights schema 1; upgrade all stopped
Controllers first. Existing prepared-document CAS, term authority and byte-proof
paths remain unchanged. Post-refresh capture samples fresh pinned probe observations
at most once/node/hour into UTC calendar-hour/day aggregates. Missing hours remain
UNKNOWN; observed probe success is not continuous uptime. Takeover preserves history;
probe freshness is still invalidated. No voter/membership/leadership decision uses it.

3B.4 placement consumes insights only after enable, preserving legacy ordering
without the extension. Hard checks run before any preference/score: active current
approved identity, non-protected profile, fresh nonfuture heartbeat/pinned probe,
approved readable+writable online volume, upload limit, double-copy free/quota
reserve minus pending reservations, no running target transfer, excluded/planned
physical domains. Eligible Preferred first, then score*confidence/100, available
bytes, stable node/volume ID. Existing policy/schedule still chooses at most one
new target per independent approved device domain; no score changes voter state.
Avoid/Drain/Protected exclude new target allocation, retaining authenticated reads
and existing work/bytes. Re-pair keeps generation-tagged history and collects new
samples separately; only current-generation reliability contributes to score.

Phase 3C.1 explicitly enables replication schema 1 on the same runtime schema 2.
Owner policies and reconciliation prepare existing Catalog SQL in memory and
commit policy/history/scheduled COPY jobs/intent receipt atomically through actual-
term Go CAS. Increasing policy schedules missing independent domains; decreasing
policy retains all current replicas and bytes. Existing physical proof worker,
reservations, failure/lease fences and read behavior remain. No physical GC path.

3C.2a adds durable move intents, not automatic source removal. Explicit owner Drain
sets 3B preference and schedules independent COPY work atomically; explicit move
can rebalance one replica. At most 128 intents; repeated requests/source IDs reuse
same intent/job. Required survivors include retained backup snapshot copy counts.
No target space/domain means a blocked report and preserved source. A READY plan
still requires fresh survivor-byte proofs before a later retirement checkpoint.

3C.2b owns an additional trusted prepared-Catalog retirement boundary. After the
existing COPY job commits physical completion, verify required survivors by actual
streamed SHA, excluding the retiring replica. Required domains include current
policy and retained snapshot backup copy counts. A final CAS rechecks term, current
policy, approvals/generations, freshness and unfinished source/target jobs before
removing only the current replica reference and appending its ordinary Catalog
event. Existing versions/snapshots/events/jobs and source bytes remain. A bounded
retirement record permanently fences that exact node/volume/local-object identity
against reintroduction. Background work advances at most one ready move per turn.
No retirement implies physical GC eligibility; all retained pointers still count.

3C.3a GC planning indexes every current-version physical pointer, trash content pin,
retained snapshot, all backup/restore jobs (including terminal evidence), every
Catalog job physical/source pointer (including COMPLETED), live scoped grants and
retained public event replicas. Only proven retired identities are candidates;
unknown/native inventory is held, never inferred reclaimable. Strong owner plan
binds graph and complete plan SHA, source epoch/term/checkpoint and 60-second
expiry, but supplies no delete authority. Logical excess and reclaimable bytes
remain distinct. Monotone Runtime transitions reject extension/receipt/retirement/
move erasure and retained-history edits; ordinary <=1024-event append/retention is
allowed only with the previous digest anchor, not arbitrary compaction for GC.

3C.3b explicit owner archive may release completed transfer-job physical pointers
only for a proven retired replica. Active/retryable jobs cannot be archived.
COMPLETED job-scoped grants already deny further authority and are removed with
those terminal rows. Retain job identity/file/kind/times, full-record SHA and exact
completion digest in bounded permanent audit receipts, plus unchanged state history.
No raw local-object/session/source pointer remains in archived receipts; the logical
file still resolves through its current verified replicas. Upload/completion replay
returns its original success without reviving the old physical target. Every writer
must prove archival against the prior exact terminal row; historical Catalog event
pointers still block GC until the ordinary existing retention window ages them.
No event eviction/archive/byte deletion is performed to create eligibility.

3C.4a separates overview planning from a durable selected-object plan. Prepare
requires fresh streamed survivors outside the target device domain, rechecks every
reference and stores an immutable 60s plan SHA. Exact owner confirmation plus an
in-process issued synthetic temporary Controller capability may reserve one target
through quorum. Ordinary runtime never constructs that capability; JSON/config/env
cannot supply it, and Android/ARM/non-temporary hosts are refused. Reservation and
retirement identity cannot be removed/reused. Takeover invalidates pending permits
and proofs; no physical executor or unlink is present in this checkpoint. GC job
survivor evidence itself is a retained reference; reserved targets are retirement
journals, not new data-use pins. Repeated confirmation with the same request replays.

3C.4b supplies a separately issued Node test-volume capability: Linux x86, existing
approved directory under temporary storage, exact node/volume/root/objects/staging
identities, and no pre-existing sessions/files/bodies when first issued. Retained
binding allows restart only on the exact same arena. Normal Agent constructs none.
Executor serializes through Engine.transfer (including in-flight reads), verifies
manifest/upload scope and SHA, journals identity before deletion intent, then calls
fresh authorization immediately before descriptor-relative single-object unlink.
A 250ms post-authorization local budget rejects delayed boundary work; no recursive
or arbitrary path removal. Recheck links/inodes/size/change times/root at the boundary.

The private FULL SQLite journal progresses PREPARED -> DELETING -> DONE across
unlink, directory fsync and manifest removal. Only a known matching DELETING/DONE
intent can acknowledge absence; unknown/corrupt/mismatched/reappeared data is held.
Retry does not repeat an unlink or claim additional bytes, and always reauthorizes.
No network GC endpoint is wired yet; this checkpoint qualifies local fake-callback
and filesystem behavior, not final quorum fencing. Physical execution stays locked
on Windows/Android/real devices and outside issued synthetic temporary arenas.

3C.4c connects explicit confirmed GC jobs to Controller/Storage authorization. Every run replaces the memory-only bearer and stores only its hash/run/term. Authorization rehashes independent survivors, rechecks the full target graph and current credentials, and commits a fresh nonce receipt. Storage accepts only an issued exact-volume executor, never a config switch; no background GC. A callback taking over 10 seconds is refused, followed by the existing 250ms local unlink budget. These bounds do not make network and filesystem atomic.

3C.5b additionally binds the complete reference/approval graph before and after streamed survivor proof. Current identity/domain/freshness checks alone cannot reuse proof from a formerly approved endpoint after its pin changes. The transient graph SHA is not persisted and changes no schema; any concurrent graph change requires fresh proof.

Proof fingerprint retains all references, policies, approvals, identities and effective protection. Only unrelated self-reported profile telemetry is canonicalized away; current pinned readability/freshness still uses the real document. Ordinary heartbeat free-space changes must not substitute for, or invalidate, independently streamed byte evidence by themselves. Confirmed plan SHA semantics are unchanged.

Linux qualification exposed repeated structural validation of identical 1024-event
Catalogs in runtime read/preparation. A bounded two-entry cache admits only
successfully validated exact canonical JSON bytes with native JSON types; no mutable
document, authority, time-dependent evidence or grant is cached. Changed bytes
validate again, including history/materialization checks. All other runtime
validation, digest verification, fresh quorum/nonce and streamed-proof gates remain
per-operation. Callback/local time budgets are unchanged.

## Phase 3D external archives (separate feature branch)

External BackupEngine consumes a source capture/stream/revalidate interface. Private
LocalStore pins approved destination descriptors and owns one exclusive store lock;
immutable capture and all Catalog version bytes live outside source state/volumes.
64KiB streams hash/fsync/readback before no-replace publication; complete replay
rehashes rather than trusting progress. Only a current source authority final gate
can publish new COMPLETE. Base runtime/registry/manifest/GC remain unchanged.
Offline recovery is planned as passive READ_ONLY data staging, never a writer.

3D.1b runtime source APIs reuse strong Runtime.operation and existing scoped
audit/read grants, not cached metadata as authority. Exact capture is nested so
transport labels cannot alter source checkpoint. Owner client streams candidates
over pinned Storage HTTPS and retries only its unpublished private partial. Final
current quorum check gates new COMPLETE; completed archives remain historical.
No backup code runs in Raft apply or mutates source content/pins/history.

3D.2 offline verification needs an independently trusted manifest digest; local
completion/self-hash alone is not authenticity. Same-cluster minimum known index
adds a historical rollback floor, not proof of newest history. Verification is
time-stamped and rehashes all bodies; list stays COMPLETE_UNVERIFIED. Retention
is non-destructive preview only; no completed backup is removed or used as GC credit.

3D.3 recovery is a passive data bundle on a NEW isolated empty root, not an ASC
HOME/volume. Exact captured projection and global-ID portable bodies plus READ_ONLY
intent/READY integrity receipt preserve history without constructing authority.
No runtime import/bootstrap/migration/credential reuse or server launch exists.
Full writable recovery remains blocked pending upstream library/fencing review.

The logical Destination protocol owns initialize/create/resume/inventory/verify/
retention-preview/stage. LocalDirectory dispatches to qualified POSIX transaction
implementation; no provider silently falls back. Future NAS/S3/cloud must supply
independently reviewed credentials/privacy/conditional publication and recovery
semantics, not emulate POSIX handles. Exact baseline source can validate/roundtrip
current captured schema; archives are additive and do not alter live base formats.


<!-- Reviewed Demo c9c2660 historical extension; current Phase4 status is in PHASE4-PROGRESS. -->
## Demo Track immutable installer boundary
DEMO.1 installs a public source-only release under a dedicated private code prefix;
private Core/Demo state is never adopted or initialized by installation. A content
SHA identifies each release, with a strictly verified inventory. The stable launcher
verifies bytes with stdlib before importing release code and runs Python without
bytecode writes. Explicit stopped upgrades are deferred to DEMO.3. No new network
runtime is delivered by the installer preview.

## Demo single-writer LAN boundary (DEMO.2)
A Demo Controller may cohost an enrolled Storage Node in a different private home:
<state>/controller versus <state>/node. It retains one fixed metadata writer with
Core registry 4; no failover bootstrap, consensus state or advanced Core extension
is adopted. ControllerRuntime binds explicit private IPv4 with Core pinned HTTPS,
Catalog jobs and byte proofs. Node runs Core StorageRuntime and agent_once in its
own process with ASC_HOME set before import, retaining OS engine/agent locks.
Demo lifecycle operation lock serializes setup/startup with future stopped upgrades.
Two identities on one physical phone MUST use the same owner-approved domain label.
New files require two independently labeled, fresh actually writable domains with
Core double-copy capacity; race/outage may leave retained incomplete jobs. CLI only
reports protected=true after two available verified domains; downloads may use one
readable copy while Controller is up. All node requests still introspect Controller
for grants; its outage denies new authority rather than selecting another writer.

## Demo stopped upgrade boundary (DEMO.3a)
An installed prefix binds exactly one dedicated Demo root. Setup/runtime rechecks
binding and PREPARED upgrade journal inside lifecycle startup fencing; activation
holds root operation plus controller/catalog-worker/agent/storage-engine OS locks.
No activation proceeds with any local runtime running. Candidate source is verified
and staged immutably, requires exact native integer formats and installer/LAN/
upgrade-safe capabilities; old installer-only releases cannot run initialized state.
Complete private state plus every approved original medium is inventoried, copied,
fsynced and independently hashed before atomic source selection. Changes during
copy, missing medium, links or unknown formats fail closed. PREPARED journal and
atomic pointer are separate durable writes; interrupted activation blocks startup
until explicit recovery verifies unchanged state+backup and selects old compatible
code. No DB/byte restore or implicit migration. Multi-phone upgrades require owner
stop-all/backup/change/start Controller then nodes; mixed versions not qualified.

Demo coordination-file hardening (DEMO.3a.1): Demo wraps the Core OS lock primitives
with an O_NOFOLLOW regular/single-link/inode-checked opener before any marker write.
Do not call Core foreground_lock directly from Demo. State preflight validates
existing internal Core worker/engine lock paths before invoking those constructors.
No Core runtime/schema is changed; existing immutable source/state boundaries hold.

## DEMO.4a optional browser facade
Dashboard listener is opt-in inside the existing Controller process/OS lifetime;
Core Catalog/worker and pinned metadata/Storage clients remain the sole storage
logic. Browser port uses its own private CA/leaf with IP SAN; Core/node TLS pins
and identities never change. Owner manually trusts public CA after SHA comparison.
Pinned local owner CLI mints a one-use login grant, redeemed for a bounded RAM-only
HttpOnly/Secure/SameSite session; restart clears grants/sessions. Browser never sees
Core admin/node/transfer bearer or key. Exact Host/Origin/CSRF and local CSP protect
browser routes. Node administration is read-only; domain approval stays CLI.
One bounded private temporary spool relays upload/download via existing Core client,
with actual received counts/full SHA and conservative protection from Core replica
counts. Unknown/stale metrics remain null; duplicate domains do not create copies.
No second Catalog, election, deletion, GC or public endpoint. Default runtime keeps
Dashboard disabled. Optional completed Dashboard config is versioned independently;
root/base schemas unchanged so old CLI-only 0.3.0 can ignore this feature safely.

### DEMO.4b browser client
Controller serves three local immutable release assets. Browser holds only owner session cookie/CSRF, whitelisted Catalog views and selected test file bytes; Core grants/keys stay in Controller. Fetch upload progress uses backend-observed counts, protection uses Core domain/readability results. Download buffers at most the Dashboard limit, rechecks SHA with WebCrypto then requests a new browser download (no filesystem overwrite API). On connection failure cached protection is UNKNOWN and writes/download actions disable. No second persistence authority, cloud dependency, offline write queue or PWA service worker.

## DEMO.4d POSIX storage anchor
Android may deny read-open of '/' while allowing search/stat and direct access to approved private volume. Replace system-root descriptor traversal with direct open of the approved root ONLY, checked against persisted medium dev/inode before child reads. Ancestor lstat snapshots and pinned marker/root/subdirectories are revalidated around IO; all actual child IO/scandir/statvfs/fsync/unlink stays relative to descriptors. No full-path child-file fallback or identity/schema rewrite. Windows existing handle route stays separate. Probe success follows real IO/SHA/fsync and owned cleanup. GC's distinct synthetic-only executor/authority protocol remains locked and unchanged.

## Phase4.0b.1 source convergence, modes remain separate
Reviewed Demo modules and approved-root adapter now coexist with intact Core3D
external backup/recovery in this feature tree. No state migration/authority change:
Demo keeps marked single-writer and refuses Core quorum/advanced state; external
module CLI/RuntimeHandler remain their own guarded development scope. Shared base
Registry/Catalog/Storage services remain sole implementations. Historical Demo doc
extensions above do not supersede current Phase4 plan/progress/acceptance.

## Phase4.0 Quick Join foundation
The marked Demo single-writer Controller owns the existing Dashboard facade.
Pairings explicitly requires DemoCatalog and matching local Registry/cluster/TLS
binding; unknown/quorum modes have no SQL fallback. Existing admin/pair issues
600s one-use grants, Registry is the sole durable enrollment authority. Session
tracking is bounded hash-only RAM and is lost on logout/restart; live grants are
not thereby revoked. The local CLI uses the same Core durable enrollment engine,
existing pending context and optional expected cluster guard. No additional state
schema or native/browser node-credential store. Recovery staging is rejected even
if somebody adds a Demo marker. Core3D authority and modules remain separate.

## Phase4.1 architecture contract
Private same-UID authenticated UDS/application scope facade reuses existing Demo
Quick Join/Core Engine in fixed private state; no browser/TCP process/filesystem
route. Node lifecycle only owned child, no Controller/Core writer launch. Separate
Core observer uses strong Runtime.view Barrier, never ensure_ready/takeover, and
existing Dashboard security/assets in explicit read-only mode. No Catalog/schema
migration or recovery writer. See PHASE4-1-PLAN and dedicated threat/API/app contracts.

Phase4.1c.1 reuses existing Runtime.view(strong=True) without readiness/takeover.
Public aggregation uses existing disposable prepared SQL with query_only +same
Catalog/Views, not a persistent database/live registry fallback. Explicit pinned
collector and separately configured passive-stage verifier provide read-only
observations only; writer_authority always false. Source authority/schema/Engine,
3D recovery writer and static membership remain unchanged.
