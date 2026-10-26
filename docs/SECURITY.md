# ASC SECURITY & RECOVERY

## Phase 2B development trust boundary — Windows qualified

The opt-in runtime keeps distinct endpoint pins/admin credentials and node-local
TLS/IPC secrets. Replicated state includes credential hashes and public lease IDs,
not raw secrets or private keys. Existing metadata-mode guards remain untouched.
Every runtime mutation is quorum committed in its actual activation term; takeover
invalidates old grants/leases and rechecks physical evidence. Storage introspection
uses an exact nonce-bound committed receipt over pinned online HTTPS, with no
authorization cache/legacy fallback. Already-authorized immutable IO may finish;
fresh commit authorization and current Catalog lease fencing govern publication.
This assumes trusted preparation and non-Byzantine configured Controllers, as in
Phase 2A; receipts are not independently signed Byzantine quorum certificates.
No delete/GC API, score-driven election, phone deployment or production claim is
introduced. Read the executed fault matrix and limits before development use.

A conflicting frozen private Controller registry is an attachment blocker, proved
against the initial committed document receipt rather than inferred from matching
Catalog alone. Cache corruption or a dead worker withdraws Python liveness rather
than leaving an unhealthy Controller as permanent Leader. Held object resume does
not bypass revocation: exact fresh job scope and two matching retained hashes are
required, then commit reauthorizes. Corrupt/unknown bodies are preserved.

Agent bearer/re-pair/revoke and pinned Raft voter certificates are separate trust
layers. Revoking an Agent denies its heartbeat/grants; it does not remove a static
voter or rotate its peer key. Voter removal/certificate revocation requires a
separate reviewed membership/trust protocol and is not implemented here. Public
self hints expose no grant authority; the actual API still requires quorum and
current credentials. Owner bootstrap secrets never belong in Agent configuration.

## Security boundaries
- Separate owner/admin/user accounts from node machine credentials; authorization must not rely only on being connected to VPN.
- Do not expose node agent, SFTP or consensus traffic to public Internet.
- One identity key per node; enrollment requires out-of-band approval and token TTL.
- Credentials do not appear in ZIP distribution or logs. Avoid sharing actual machine IP/MAC/serial/SSH keys in reports.
- Keep local storage boundaries; agent never takes arbitrary absolute host path/shell command from UI.
- Endpoints that delete replicas, change membership or rotate keys require elevated privileges and audit logs.
- All database backups/snapshots are consistent and verified; database files for live MariaDB on M51 must not be copied directly.

## Failure modes

| Event | Behavior | Safety requirement |
|---|---|---|
| One voter fails (3 voter cluster) | Remaining two elect/retain valid leader | No older leader may commit without majority |
| Network partition 1/2 | Minority read-only for global metadata | Refuse all global mutation without quorum |
| Network partition 0/3 | Reconnect/catch up | No blind reconciliation of divergent catalogs |
| All but one voter fail | Local snapshot/catalog available, no new global writes | Manual disaster recovery only |
| SD removed/bad | Volume offline, reschedule repairs if other copies exist | Do not silently prune last verified copy |
| Controller metadata lost | Restore from validated replica and committed snapshot/log | Preserve cluster ID, epochs and trust state |
| Termux uninstalled | Risk of app-specific SD loss | At least one independent copy elsewhere beforehand |
| Public gateway down | Private VPN/LAN may continue | No public management port fallback |
| M51 hosting busy | Throttle/stop ASC tasks | Hosting stability supersedes storage tasks |

## Manual quorum-loss recovery (design, NOT a copy-paste procedure)
1. Stop/physically isolate every potentially surviving old voter and client writer; prevent accidental old-cluster restoration.
2. Inventory candidate snapshots, latest committed indices and local manifests without modifying source data.
3. Administrator selects authoritative snapshot with documented rationale, retains backups of all divergent states.
4. Initialize a replacement membership through the Raft library's **documented recovery mechanism** (not by editing SQLite fields or forging an epoch).
5. Validate invariants and reconstruct object placement from manifests; run read-only check before enabling writes.
6. Re-enroll old nodes carefully. Never allow an isolated former leader to accept writes under its outdated authority.

## External backups
For irreplaceable data, keep at least one disconnected/out-of-cluster copy; multiple phones on the same power/router/location are not a disaster-proof backup.

## Source publishing boundary — v0.4.1 Windows fixes

`.gitignore` excludes known ASC private/recovery state, TLS/SSH key material, runtime
DBs/WAL/journals, environment credentials, logs, temporary files and private archives.
Keep ASC_HOME outside the repository anyway. Ignore rules do not remove already tracked
files or detect secrets embedded under arbitrary source filenames; review staged paths
and the full staged diff before any commit/push. Do not use git add -f for these files.
If a real secret was previously committed, untracking alone is insufficient: revoke or
rotate it and plan a deliberate history cleanup; no history rewriting is done here.

The repository was initialized without prior local history. Origin is configured
without embedded credentials. The owner has confirmed Windows PASS (40 tests, skipped=3)
and explicitly authorized v0.4.1 commit/push on main. Audit both existing tracked files
and staged blob contents before publishing, then verify remote state and use a normal
non-force push. Preserve any remote history and report network/auth/approval blockers
without bypassing protections. No production workflow or GitHub Actions is introduced.
A safe.directory exception, if needed for sandbox-created metadata, is limited to a
single command and this exact workspace, not wildcard/global trust.

OpenSSL dependency errors do not skip HTTPS tests or weaken certificate pinning.
Installing/fixing PATH is an owner action on the development machine, not on M51.

## Implemented Phase 1.1 security boundary (0.4.1)

The failure-mode table above is a future consensus design, not current behavior.
Current code is a single-writer development registry. Owner-reported Windows acceptance
is 40 tests OK (skipped=3 POSIX installer cases); Linux/Termux and hardware acceptance
remain deferred. No HA, file durability or production-readiness claim.

- One-use 48-bit CSPRNG join codes, short TTL and per-IP/global admission budgets;
  manual certificate pin is verified BEFORE sending the grant or bearer credential.
  The code itself is the admin approval; keep it private and enter via hidden prompt.
- Administrator credential remains only in Controller private HOME; admin CLI calls
  pinned HTTPS loopback. Node bearer tokens cannot list/administer the registry via
  admin endpoints. A valid heartbeat does receive topology for existing v0.4 behavior.
- Revoke clears effective token hash, blocks future node auth, cancels targeted grants
  and excludes node from active advisory duties. New node-protected endpoints must
  check active state plus current token. Revocation cannot retract already-served or
  cached topology, or cancel a request authenticated before the revoke transaction.
- Rotation/recovery requires an explicit targeted grant and explicit node-repair.
  Token changes only after local backup and transactional server acceptance. Old
  credentials cannot auto-rejoin or use an old operation to restore a revoked identity.
- New enrollment operation/token is generated on node and saved before send. Only
  hashes plus routing IDs reach registry persistence. Exact retries require the saved
  secret; an explicit replacement initial grant keeps the same operation/token to avoid
  duplicates. The permanent hashed operation map is not a key recovery service.
- Private pending files, recovery copies and node_before_repair configs are secrets,
  as sensitive as node.json. Keep all outside source/ZIP/shared storage. No token/hash
  appears in routine status/list/detail/errors. Explicit controller-pair displays a
  newly minted code; it must not be captured in public reports.
- Inputs have bounded framing, schema, text/depth/collection sizes and finite numbers.
  SQL values are parameter-bound. HTTP logs and errors suppress reflected payloads,
  arbitrary exception text, headers and URL queries. Client errors allow known labels only.
- Join and auth failure rate budgets are synchronized, memory/key-count bounded and
  include a global cap; reset on restart and can throttle legitimate NAT users. TLS
  workers/read timeouts are bounded. This is not a full DDoS defense; no public exposure.
- Unknown model/manufacturer/SDK blocks install/run/enrollment/SD writes; recognized
  M51 stays blocked, including secondary device/product identification. No bypass flag.
  This cannot prove true hardware under spoofed Android properties. It grants no
  permission to operate M51: only source access was used for this change.
- Installer never mutates packages or replaces installed source. Explicit upgrade
  uses a separate versioned code directory; OS-held locks prevent duplicate new-version
  runtimes in one ASC_HOME, but old v0.4 processes must first be stopped manually.
- POSIX private directories/files use 0700/0600 for new state. Windows chmod is not a
  substitute for per-user ACLs; use a private account directory for local development.
  Atomic file replacement/fsync reduces partial writes, without a power-loss guarantee.

Before migration, stop every ASC process and privately copy complete per-device state,
including SQLite WAL/SHM. Rollback requires that pre-upgrade snapshot and old source,
not old code against schema 2. Restoring it can reactivate previously revoked secrets;
keep the LAN isolated if compromise is suspected. No M51 production DB/log/service
or Termux:Boot was accessed or changed.

## Phase 1.2A security boundary

Node bearer identity is not user storage authority. Owner admin explicitly mints a random short-lived volume/operation grant; registry stores only its hash and node generation. Agent introspects via pinned Controller HTTPS on each operation and before final manifest commit. Wrong pin, expired grant, revoke, re-pair or unavailable Controller denies access. Authentication failures share bounded IP/global rate budgets. Owner grants are not a completed multiuser ACL design; a compromised volume grant can read/write/list within its permitted operations until expiry/revoke.

Already-authorized streams can finish after grant expiry/revoke; commit rechecks authority. Uploaded staging remains unadvertised on failure. No anonymous file operations, delete API, stale authorization cache, public bind default or public SFTP. Runtime defaults loopback; explicit bind must be a numeric private/loopback address (not unspecified/multicast). This validation does not replace firewall/private LAN review.

Storage is explicit opt-in. Android CLI retains M51/unknown-device protection; only configured Windows local development is accepted without Android identity. No phone, hosting folder, production database, service or private state was accessed. Agent heartbeat refuses a storage probe if its profile is protected.

Only empty explicitly approved roots are registered. SD roots must descend from detected pre-existing Termux-owned app folders; no permission grant or formatting. Volume marker and observed medium/root identity are checked before access. Generated UUID paths, no-follow/reparse checks, single-link regular files, Windows directory handles and POSIX descriptor walking prevent path escape. Root/marker cloning or a malicious privileged local actor cannot be ruled out by filesystem identity; this is not a sandbox against the device administrator. Windows roots/private state need account ACLs.

SHA-256/size checks occur during upload, before/after copy, startup verification and download. This detects accidental mismatch, not authenticated provenance against an administrator able to rewrite both manifest and data. Final files are never overwritten/deleted; ambiguous objects and metadata conflicts remain for operator review. Only explicit local cleanup --apply expires old eligible staging, with dry-run default and final-object protection.

Secrets/config, keys, manifest/WAL, volume marker, object/staging bodies and grant files stay outside Git; ignore rules cover them but tracked/staged content must still be reviewed. Backup requires stopped complete state plus volumes, not a live DB-only copy. Windows fsync/SQLite FULL is not proof of power-cut durability. SD/Doze/SAF and real-device acceptance are deferred.

## Implemented Phase 1.2B — authority and evidence

Catalog mutation and upload/download plans require the owner's Controller admin credential. A node bearer authenticates only that node's heartbeat/introspection and explicitly approved metadata replication; it never grants global writes or owner file access. Metadata permission is generation-bound and opt-in. Revoke/re-pair/protected profile prevents current access; re-pair requires explicit node/volume/endpoint approval again.

Transfer authority is a separate random short-lived bearer stored only as SHA-256, bound to node/volume/current generation and exact file or persistent job/run lease. Agent enforces method/resource, expected key/name/size/hash and session identity; commit reauthorizes. Completion validates current target approval/generation and lease. Raw node tokens never move to another node; long-lived admin credentials reach only the pinned Controller. Same-job retries use stable IDs but fresh fenced credentials; old completed/expired/run-token grants cannot publish new copies.

An ACK, metadata snapshot, job record or score is not file proof. Controller asks Agent to verify, checks identity/size/hash/path, then independently reads and hashes served bytes before a VERIFIED catalog transaction. Agent retains existing immutable staging/copy/fsync/integrity checks. This proves retrievable bytes at verification time, not permanent availability, power-cut durability or resistance to a Byzantine storage owner. Every normal download independently hashes bytes and can fall back.

Snapshots/deltas project only global file/replica fields. They contain no node/admin tokens/hashes, keys, grants or private jobs/control state. File names and hashes remain sensitive metadata: only explicitly approved nodes receive the whole catalog. Canonical digest/hash chains detect corruption/order gaps through pinned transport, not consensus or a signature that grants leadership. Offline cache lookups are local private-OS operations, marked stale/read_only; network file operations keep Controller authorization.

Endpoint/pin/volume/domain approval is explicit; no network scan or automatic trust in heartbeat addresses/hardware scores. Storage origins must be numeric private/loopback addresses and manually confirmed pins. Physical device domains are owner assertions; two roots on one Windows machine simulate independent nodes and do not prove actual disaster independence. Unknown load/stability stays null. No M51/real-phone/production state was contacted in this phase.

Worker ownership is an OS-held Controller lock, not election. Queue leases bound work and stale confirmations; they do not provide distributed fencing against an independent Controller copy. Raft, membership, deterministic prepared commands and recovery fencing remain Phase 2 work. Current metadata replicas cannot promote themselves. A Controller outage preserves read-only cache lookup; it does not enable unauthenticated file access.

Reconciliation is bounded and non-destructive. Unknown v0.5 files/orphan objects remain on disk, suspect records stay visible, and no source/last copy is removed by timeout, failure, policy reduction or repair. Default one transfer, bounded relay/readback rate, rotating inventory and proof budgets reduce load; Android/SD/Doze behavior is unverified. Avoid production deployment.

Legacy v0.5 whole-volume authorization may omit the new optional scope after a 400 on the extra field, with unchanged certificate pin/current credentials. The Controller must still authorize; a job credential requires scope and is rejected without it. No TLS/security bypass is added.

Before publication inspect all tracked/staged blobs and ignore rules, including metadata checkpoint/export/cache files. Keep complete private state outside source. Stop processes for backups/rollback; keep original manifests/volumes and review restored credentials. Never force-push, lower schema numbers, erase uncertain copies or treat an old restored catalog as current authority automatically.

## Phase 2A historical engine investigation and Go security boundary

Go qualification continuation supplies a development-only authenticated transport:
TLS 1.3 verifies trusted configured certificates AND exact leaf fingerprints;
each RPC header ID/address must match its TLS identity and immutable cluster.
A configured peer cannot impersonate another configured voter merely by changing
the message header. Bodies, entry counts, snapshot sizes and deadlines are bounded.
Peer connections are capped at 32 before TLS handshakes; IPC connections at 16
and concurrent authenticated IPC handlers at 8. Decoder sizes/deadlines are bounded.
This is not phone/production certification.

Opt-in Python mode persists SQL guards across process restarts. Every normal
registry connection denies DML/authority DDL; raw/old SQLite writers lack the
apply function and cannot pass persistent triggers. Only the adapter apply
connection is authorized to install a committed projection. Missing guards are
an attachment blocker. Existing grants are denied; JobQueue cannot start. No
replication job transfers or physical evidence publication run after attachment.

Each voter has its own peer certificate/key and separate per-node random IPC
bearer. Config/key/seed/DB/witness files belong outside source/private account
storage; Go rejects config/state/key/seed paths under a Git checkout. Config
binding contains public certificates, membership and seed identity, never raw
IPC/admin/node secrets or private key bytes. Base64 in IPC/snapshots preserves
bytes and is not encryption. Private metadata still needs OS ACLs/backups.

The trust model includes trusted Python preparation and non-Byzantine voters;
Raft is not protection against a malicious device administrator able to replace
code/state/certificates. CAS preconditions/receipts prevent accidental stale
proposals and retries; local authorized code remains part of the trust boundary.
Windows filesystem sync is not a physical power-cut or Android durability proof.
Live stable/log errors latch quarantine in the store and gate RPC/IPC. Required
missing stable values never reach upstream's defaultable `not found` branch;
partial repair cannot resume writes in that process. A fatal engine storage error
may stop the process; startup still requires complete valid reviewed state.
Android executable is build-only and refuses runtime until separately qualified.

The following PySyncObj paragraphs retain historical pre-Go findings; no rejected
upstream package was enabled by this continuation.

The hash-pinned PySyncObj 0.3.17 probe reproduces another vote in the same term after missing/corrupt .meta. Default transport accepts a known address claim without a credential when password=None. This is qualification of an unintegrated upstream candidate: ASC exposes no Raft socket and has no dependency on that package. Do not enable the default transport, substitute a shared admin password or assume the ordinary-restart persistence fix proves fail-closed recovery.

tools/qualify_pysyncobj.py downloads only with explicit --download, checks a fixed official-artifact SHA-256 before importing selected Python modules from temporary state, and never runs packaging/install scripts or opens listeners. Treat external-engine execution as development qualification only; --archive supports an offline verified artifact. No private ASC identity/state is supplied. Synchronization-call observations are not physical power-cut tests.

Per-voter identity, durable vote-before-message ordering, exact cluster/membership binding, bounded authenticated decoding, recovery fencing and isolated-leader strong-read rejection remain unimplemented gates. No keys/tokens are replicated and no consensus log/snapshot containing user metadata is created in this investigation. Existing pinning, grants, lifecycle/rate limits and M51 protection remain unchanged. Full evidence/alternatives: PHASE2A-ACCEPTANCE.md.

## Phase 3A backup boundary

Enable only after all development Controllers run matching source. Every logical
delete/expiry, snapshot, schedule, job checkpoint and restore uses existing actual-
term Go CAS. Former/minority Leaders cannot commit these operations; no physical
delete grant, purge endpoint or object GC is introduced. Snapshot pins and active
restores prevent logical expiry. Hash verification uses actual served bytes and
approved physical-domain assertions; failure leaves suspect/last copies retained.

Snapshots/jobs remain inside the cluster. They are not offline/disaster backups,
and a metadata snapshot alone does not prove readable bytes. VERIFIED records
historical checks, never continuous availability. No production, Android/SD,
physical power-cut, Byzantine-Controller or disconnected-backup qualification.
Backup manifests contain private names/hashes; keep private state outside source.

As with the existing transfer contract, previously issued short-lived read grants
may remain usable until expiry; already-authorized streams can finish. Logical
trash is not a revocation/secure-erasure mechanism. No final bytes are overwritten.

Phase 3B scores expose owner-only operational telemetry, with source provenance.
Agent runtime RAM is self-reported and grants no trust; controller-pinned capacity
is a time-bound observation, not durability. Local score reads can be stale and
retain their source checkpoint. Score APIs do not grant storage or voter authority.

Phase 3B reduction preview never authorizes deletion. Even a strong read supplies
historical evidence only; proposed excess copies require fresh byte verification
in a separately qualified future phase. Stale views, pins, unfinished work and
insufficient independent available domains prevent proposals. Hardware protection,
node generation and owner authentication remain mandatory; no membership API added.

Linux Cloud qualification runs synthetic Controller cohosts using a test-only
platform/profile wrapper in tests/test_failover.py. The product entrypoint still
refuses plain Linux/Android runtime and protected devices; RuntimeSafetyTests
verify refusal before private-state access. This is not new Linux/Android runtime
or production authorization. Node mutation APIs reject null replay IDs.

Phase 3C logical retirement must first rehash served survivor bytes on independent
approved domains, bind current generations/term and preserve the current policy/
retained-backup copy floor. Delayed proof/new policy/current job references can
block retirement. Retired local-object identities are permanently fenced from
reintroduction; historical metadata/job references still prevent physical reclaim.
This checkpoint adds no final-object unlink, destructive grant or real-device flag.

Phase 3C GC plans are not destructive permissions. Terminal Catalog/backup jobs,
expired-version records with physical pointers, trash, snapshot and retained-event
history still count. No hidden eviction makes a target eligible. Every Runtime
writer preserves permanent retirement/receipt/move fences and ordinary retained
history through a transition check; the trust boundary still assumes configured
non-Byzantine Controllers/Python preparation, not a malicious OS administrator.

Terminal transfer-job pointer release is explicit owner authority, not ignored GC
references. A permanent exact-row audit hash, identity and exact-completion hash
replace the terminal record; state history remains. COMPLETED already denies the
old scoped grant; those invalid grants are removed atomically with archival.
Old request replay cannot restore a physical pointer or grant. Backup/restore-job
and retained Catalog event pointers are not archived by this operation and remain
GC holds. Physical execution must also serialize against local in-flight Engine IO.

GC confirmation requires a separately issued in-process fixture capability; a path,
boolean/config flag, owner token or forged JSON object cannot supply it. It is
bound to a real temporary home identity outside source on supported x86 desktop
hosts, refuses Android/Termux/ARM and is absent in ordinary runtime initialization.
This is an accidental-use boundary for trusted test code, not a sandbox against a
malicious administrator who can replace Python or unlink files directly. Actual
physical execution will need a separate fresh-volume capability and nonce-bound
last-boundary authorization/journal; no unlink exists at 3C.4a. Survivors must also
be outside the GC target's device domain to avoid self-dependency/IO-lock deadlock.

3C.4b physical unlink is possible only through an issued NodeTestVolume capability
for a fresh Linux x86 temporary directory volume, in addition to the later required
Controller authorization. Existing populated/native volumes are never adopted.
Real Android/ARM/Windows, non-temporary/source roots and normal Agent initialization
remain locked. Root/subdirectory/file identities, single-link regular body, exact
manifest/name/size/SHA and immediate fresh callback are mandatory. Existing Engine
transfer ownership prevents deleting through another active local stream. Known
journal absence is idempotent recovery, not fabricated reclaimed-space evidence;
reappeared/corrupt/unknown files are held. No physical power-cut guarantee follows.

3C.4c GC is inaccessible without separately issued Controller and exact Node synthetic capabilities; normal Service/StorageRuntime never issues either. A per-run hash-bound target credential, current approved generation and endpoint, full reference scan and freshly streamed survivors outside the target device domain are mandatory. Node introspection commits a new nonce in the actual Raft term; final callback has no cached/follower/legacy authorization. Controller lock is released for survivor network IO and all inputs are rechecked before CAS. Network callbacks exceeding 10s and local post-proof work exceeding 250ms fail closed. This cannot recall a syscall already authorized at the boundary, provide instantaneous failure detection, or resist Byzantine trusted Controllers/device administrators. Permanent retirement/reservation fences remain essential. Windows tests cannot qualify the Linux-only physical boundary; real devices remain forbidden.

3C.5b review reproduced a survivor-approval race: a new endpoint pin during proof could otherwise leave node/volume/generation unchanged. An ephemeral full graph SHA now must remain identical across proof and final CAS for both permit issuance and final introspection. New references/approvals invalidate evidence; default physical/device locks remain.

Proof fingerprint ignores volatile self-reported profile telemetry only; effective protected state, generation, approved endpoint/pin/domain/volumes, policies and every reference remain bound. Original current-document freshness/readability and streamed SHA checks still run. The integration test exposed ordinary heartbeat noise; a regression explicitly distinguishes telemetry-only changes from protection changes.

Structural Catalog validation reuse during Linux qualification is not an
operation-authorization cache. It keys the complete exact canonical Catalog bytes,
checks native JSON types and admits only successful validation (two entries).
Mutation, history/hash/materialization mismatches and invalid Python type aliases
must fail. Runtime identity/extensions, hashes, quorum, term, references, streamed
survivors and final nonce checks still run. No time budget or real-device lock is
relaxed to obtain physical PASS.

## Phase 3D private external boundary

Local external stores must be explicitly initialized empty0700 operator-owned
roots, outside Git and all declared source HOME/volume ancestors/descendants.
All files0600, descriptor/no-follow/single-link checks, pinned directory identities
and exclusive OS lock. Trusted owning OS account remains required; not protection
against a malicious privileged administrator. Same-host directories simulate only.
SHA must be anchored separately by trusted operator; self-hash is not authenticity.
No encryption is invented; plaintext sensitive metadata/bytes cannot go to public
storage. No raw key/token/config/Raft database is exported. External verification
never supplies GC credit or permission to restore active state/old credentials.

External source API is owner-only/current-quorum. Ordinary node bearer cannot
export private authority hashes or read retained versions; only owner explicit
backup scope can do so. Read grants are current generation/approval/exact object
and expire under existing nonce-bound introspection. Captured hashes/IDs never
become credentials. Existing single-writer/Demo APIs are not expanded.

External CLI uses only a bounded existing private owner endpoint/bootstrap file,
no raw secret flags or exception strings. Linux desktop only; getprop/Termux/Android
refused rather than adding a device guard bypass. Local archive verification
requires separately trusted manifest SHA and reports known-history rollback floor;
no automatic credential/Leader revival. Operators still need privacy/encryption
for any future untrusted/public provider; current adapter rejects public roots.

Recovery staging requires anchored full source verification, expected cluster and
minimum-known index BEFORE new destination mutation; separate source/store roots,
new private empty root and fixed generated object names. Durable READ_ONLY intent
is passive data only. No restored tokens/private keys, fake epoch/quorum/Leader,
Raft log edit or active SQLite import. A lost authority/latest witness cannot be
replaced by a manifest self-hash. Same-intent retry binds floor; stage-verify checks
all hashes through shared existing lock without creating config/identity.

External completion and descriptors compare exact canonical native JSON; bool/
float aliases and mismatched bundle UUID cannot relabel a completed archive.
Bounded scandir stops at4096 entries. CLI parser/error whitelist avoid reflecting
private input. Fault controls are test subprocess wrappers only; no product
crash/partition/GC/authority enable switch. Stale isolated Controller actual upload
is denied; no ghost file. Physical ENOSPC is fault-injected at real fsync, not
claimed as a full-device test. Existing Core device/runtime/GC guards unchanged.


<!-- Reviewed Demo c9c2660 historical extension; current Phase4 status is in PHASE4-PROGRESS. -->
## Demo installer preview
Use the archive SHA from a trusted verified checkpoint before extraction. A self-
contained manifest detects corruption but is not a publisher signature. Installer
checks existing device/M51/unknown/dependency guards before any writes; no pkg or
system changes. Source/private paths stay in dedicated private HOME subdirectories
without symlinks. A mismatched existing source/launcher is preserved and refused.
Packages contain allowlisted public source only; inspect unpacked files before Git
publication. No cluster-ready or Android-runtime claim follows installer tests.

## Demo LAN safety (DEMO.2)
One Controller grants all writes; no fallback/election authority exists on nodes.
TLS pinning remains mandatory, and old node tokens cannot authorize owner routes.
All setup/runtime mutations recheck device/dependency guards. Root/controller/node
state compatibility is read-only checked before writable Core constructors. Existing
Core ~/.asc, Raft and advanced extension state is never adopted. Two phone labels
are an owner trust decision, not hardware attestation: never give separate labels
to two volumes/identities on the same phone. Node storage requires fresh per-request
pinned Controller introspection, including when a grant predates Controller loss.
Physical GC has no attached executor/discovery and remains locked; no Demo deletion
command or policy reduction route exists. LAN is trusted pilot scope, not production.

## Demo upgrade and diagnostic controls (DEMO.3a)
Stopped local OS locks plus operation fencing prevent runtime/activation races;
source prefix is bound to one marked root. Active and candidate releases must pass
full inventories before activation. Full private backups require actual approved
original volume markers and sufficient measured capacity, reject symlink/hardlink/
special files, and verify copy/source checksums; retain partial failure for review.
Backup contains identities/secrets and uses private 0700 directories / 0600 files.
Never publish it or restore an older DB over current objects. Source rollback does
not change state. A PREPARED journal blocks runtime, including a startup that raced
with activation; explicit recovery refuses if state or backup has changed. These
are Linux synthetic fault guarantees, not Android power-cut qualification. Diagnostics
whitelist status/counts/capacity only; no arbitrary error/config/profile/log dump.

DEMO.3a.1 corrects an existing-lock symlink hazard reproduced after initial full
qualification: Core foreground_lock can write its empty-file marker before later
backup path rejection. Demo now uses a separate O_NOFOLLOW/regular/single-link/
inode-bound opener BEFORE writes and reuses Core OS locks, preserving Core source.
Preflight also rejects linked Core engine/worker lock files. Fresh hardened full
qualification supersedes the first candidate; old preview is historical, not a
recommended install. Source/state remain private to the owner; no hostile co-owner
filesystem mutation or Android power-cut qualification is claimed.

## DEMO.4a browser boundary
HTTPS uses separate private browser CA/IP SAN, explicit manual public-CA trust after
out-of-band SHA, never click-through/insecure HTTP/TLS flags. Codex touches only
isolated synthetic trust profiles. CA/leaf private keys stay in private state; Core
and node certs/pins preserved. No shared/default password: pinned owner CLI produces
one-use high-entropy 5-minute grant, exchanged for RAM-only 30-minute host cookie
Secure/HttpOnly/SameSite=Strict and per-session CSRF. Exact Host/Origin/Sec-Fetch,
CSRF, no CORS, strict local CSP/frame denial/no-store, bounded login/auth budgets,
workers/metadata/transfers. Browser never receives Core admin/node/transfer secrets.
One private temporary spool <=32 MiB, exact framing/deadline, SHA before forwarding,
existing Core idempotent jobs/placement/byte proof/fallback. Authorized input receipt
is not checksum proof or replica protection. Download fully verifies before output;
no arbitrary host path or overwrite. Node approval remains CLI; no policy/GC/delete
route. Errors/logs suppress untrusted inputs and exceptions. Runtime defaults off;
no public/real-device/Android acceptance, Root schema/consensus/GC change follows.

### Dashboard frontend / real browser gate (DEMO.4b)
Every dynamic node/file/error value is rendered as text; no innerHTML/eval or third-party code. CSP remains same-origin with no inline script. Only idempotency metadata (logical path, size, SHA, random request key) may reside in sessionStorage; no owner/node token or cookie is readable by JavaScript. The chosen file is hashed before upload; download is hashed before Blob/new-download, user chooses destination. Retry retains original Core key until confirmed protected, never retries under a silently new key for the same pending file. Offline cache is explicitly stale/UNKNOWN. Synthetic Chromium checks trusted public CA (isolated NSS), rejects untrusted TLS, XSS literal filename, HttpOnly cookie/logout, distinct domains, actual node outage and browser network disconnection. This does not qualify Chrome Android runtime or owner CA-install UX.

### DEMO.4d scoped filesystem access
Only approved-root directory absolute open is allowed by the new adapter, O_DIRECTORY|O_NOFOLLOW then exact persisted medium fstat before marker/data. No opening '/', no absolute child body open, no permission/SELinux/identity bypass. No-follow relative children, regular/single-link marker/body, bounded marker schema, pinned folders and ancestor/root/folder/marker pre/post identity checks retain scope under symlink/replacement faults. Capacity/inventory use those descriptors. Unknown POSIX support fails closed. Probe collisions are preserved; owned cleanup requires original observed file identity and never unlinks objects. Real private-directory EACCES and fsync failure remain denial/unknown, not fabricated writable evidence. Existing private-account trust and final-syscall race limitations remain; metadata/physical publication is not atomic. GC capability/platform/authorization locks, Core WIP, TLS and M51/unknown guards are unchanged.

### DEMO.4d.2 synthetic integration / local status
Root-open denial lives only in tests/android_root_denial.py (not packaged); its Python wrapper preserves underlying actual dir_fd-support metadata rather than falsely pretending a different OS. No product mock/capability override. Real Controller/Storage/TLS/probe/bytes and authorization run unchanged. New Demo storage-status honors device/state/prefix and local ownership guards before reusing actual Engine probe, never creates volume/identity. Live node ownership/M51/unknown refusal is tested; old-certificate/browser TLS gates are rerun normally.

## Phase4.0 Quick Join boundaries
Owner pairing POST uses existing HTTPS CA/session/exact origin/CSRF; the one-use
node code is returned once and must not enter URLs, persistent browser storage,
logs or public artifacts. Session ownership and8/32 tracking limits apply; logout
or restart is not code revocation. Registry expiry/one-use rules still govern.
Node adapter checks private LAN origin, full TLS pin, expected Cluster ID and
explicit supported Demo mode before secret submission. Hidden code input and
redacted structured errors preserve pending retry identity. No shared password,
auto storage permission, failure domain inference or recovery writer. M51/unknown
model guards remain. Missing initialized state and recovery staging fail closed.

Phase4 owner UI retains pairing grant only in live DOM/RAM. It never writes that
grant, owner login code or node credentials to local/session storage or URLs.
Offline/logout/pagehide clear the code; generation guards discard delayed replies
from an earlier session/request. A code cleared from UI may still be valid at
Controller until used/expired; no false revocation guarantee. Existing upload
idempotency metadata in sessionStorage is unchanged and contains no auth grant.

## Phase4.1 trust model
Local app authorization is distinct from owner browser session/node token. Same-UID
UDS+per-app scopes does not expose Termux state to an APK/browser. Fixed roots/ops,
no raw secret logs/argv/env, bounded retry receipts and owned-child lifecycle.
Core observation needs actual Barrier/identity/term evidence, supplies no writer.
Threat/API/native limits: LOCAL-ENGINE-THREAT-MODEL, LOCAL-ENGINE-BRIDGE,
CORE-QUORUM-DASHBOARD, ANDROID-APP-CONTRACT. No Android/DR authority unlock.

Phase4.1 lifecycle uses a retained supervisor thread (Linux parent-death signal
follows parent THREAD), a fixed child that sets PDEATHSIG/checks parent before exec,
and only actual Popen handles for signals. No handler-thread spawn/PIDfile kill/
Controller/Core start. Bridge SIGKILL releases Node locks and retains bytes; this
is Linux process-death evidence, not Android/physical power loss. Socket recovery
requires exclusive owner lock/private exact app+inode receipt/refused connection;
unknown/live/link endpoints stay untouched. Installed source/root binding retained.

Phase4.1 Core observer authenticates owner BEFORE Runtime access; POST denied
before readiness. Actual Barrier/stable role+term/committed binding needed for
Leader confirmation; even then no writer authority. API whitelists records, never
raw projection/token hashes/keys/run grants. Old/unknown snapshots make current
availability/protection UNKNOWN. All configured reads failing, not process counts,
defines quorum-read unavailability. Passive recovery only after existing shared-
lock full-byte anchored check; corruption UNKNOWN, no runtime/config/key creation.

Phase4.1 Core HTTPS gateway reuses owner Sessions/Host/Origin/CSRF/CSP/TLS, with
unique cookie name per gateway (cookies do not isolate ports). No fallback between
Demo/Core/recovery. All Core mutation and byte-download routes403 even with owner
session; browser receives no Core owner token/bridge app grant. Explicit local
one-use login issuance only; no shared password or public issuance route. Gateway
private root/keys/bootstrap cannot nest within existing engine/volume/recovery;
Linux host guard remains, no Android runtime bypass. Trust public CA SHA separately.

Phase4.2 developer toolchain/signing/SDK/cache stay in workspace outside Git.
Official SHA pins+HTTPS and initial Maven checksum inventory, no system/proxy/CA
mutation. Initial Kotlin APK is FOUNDATION; build is not native Node/emulator proof.
App backups disabled, cleartext disabled; no management IPC in toolchain checkpoint.
Private emulator/ADB only, never phones or USB/M51. Debug signer is not production.

Native EngineService is nonexported with signature permission; per-call Binder
UID/signature checked before validation/private state. Canonical UUID/bounded typed
arguments/private HTTPS/pin/cluster/trust checks, no code reflection/log/secret return.
Explicit local UI consent, no external Intent commands, no sticky/boot/idle mock FGS,
foreign PID control or automatic node/volume/approval. Native Node remains unsupported.

Native4.2c uses AndroidKeyStore nonexportableAES256 and standardAES-GCM randomIV/
app-purposeAAD, not custom crypto. Key/state loss/cipher or schema mismatch refuses
without new Node/Cluster/application identity. Draft secret never returned/logged;
no Termux key import. Explicit private capability volume only, original Core guard/
root/marker/descriptors/quota/reserve/probe cleanup unchanged; missing manifest/root
replacement holds before constructor. App actor is not network Node/approval.
No broad external permission, SAF fallback or hardware-backed/power-loss claim.

## Native qualification publication
M51/unknown deny before native private state; known model status is NOT ACCEPTED. Actual separate-signature app verifies UID/signature/permission mismatch and explicit bind refusal (not timeout proof). Same-UID Binder still validates every request/consent. Stable explicit AIDL IDs prevent accidental old-client dispatch. Real default-network loss clears secret/trust. Backup XML excludes CE/DE cloud and D2D, no nonexportable-key folder restore assumption. Internal debug signer must remain private and stable across operator/Codex accounts; public debug APK is never production trust. Test-only seed/upgrade instrumentation and foreign APK are not shipped. No credential/Node/Cluster authority created by diagnostic probe or public GET.

Native direct NAT10.0.2.2 failure is preserved as NOT PASSED. Explicit ADB loopback development transport keeps real Core TLS/pin/cluster validation and never qualifies LAN/phone readiness. It changes neither proxy nor TLS policy, has no automatic fallback and removes only successfully owned no-rebind mappings on the verified emulator. Main runtime does not create any such mapping.

## Native context credential boundary (4.2f.1)
Fixed in-process provider, authenticated AES-GCM record/witness/CAS, explicit
app identity and trusted Build, no generic Binder secret/path API. Descriptor-
relative exclusive receipt and root/ancestor identity checks preserve scope.
M51 dominates and unknown phones remain blocked; only actual DEBUG AOSP fixture
identity gets SYNTHETIC scope. No TLS/enrollment/runtime/writer authority yet.
Partial initialization/lost state is held, not repaired; no power-cut promise.

## Native TLS provider boundary (4.2f.2)
Explicit trusted Android JSSE loader uses only sealed anonymous-fd readback: no
proc reopen after Android denial, filesystem plaintext key, raw syscall, SELinux/
permission change, insecure TrustManager or fallback on failed memfd/sealing.
CLOEXEC/all seals/readback/anonymous links and cleanup checked. Public Bionic
API30+ only when Python wrapper absent; API26–29 NOT QUALIFIED. Standard JCA
self-signature/validity/EC serverAuth/key-match proof before in-memory KeyManager.
Software TLS key stays in app process RAM and existing Keystore-encrypted context,
not hardware-backed TLS-key claim. Missing/corrupt key/record/witness cannot rotate
identity. No key in Binder/browser/logs; provider/cert input never supplied via
IPC. Protocol1/UID/signature/consent/M51/unknown/GC/Raft/DR guards preserved.
Private guest-loopback test listener enforces TLS1.2/1.3; no product listener exists.
Future Agent adapter must enforce secure protocol/bounds/fresh authorization itself.
See ANDROID-NATIVE-TLS for scopes, dependencies, compatibility and remaining work.

BC dependency lint retains an unused EST getTrustAllTrustManager helper warning.
App uses no EST/trust-all helper and native default-system-trust negative TLS
gate rejects untrusted self-signed peers. No suppression; see native TLS dependency
review for exact scope. Do not confuse inventory/pattern checks with full SAST.

4.2g.1 shared client extraction supplies no authority: callers still guard device,
verify pinned expected cluster, persist private pending BEFORE sending and refuse
cluster/target/token mismatch before saving identity. Registry remains sole grant/
node transaction. Native wiring is not implemented by this shared helper alone.

### Native enrollment state boundary g.2a
Only trusted in-process context adapter accepts node configuration, using Core
pinned HTTPS/expected cluster + retry-safe shared contract. Initial runtime must
explicitly advertise single-writer-development/schema4/protocol1/retry feature;
Core quorum/recovery is not silently selected. Context device guard/ownership lock
and authenticated atomic provider apply before mutations. No token/code in public
status, logs or plaintext node files. TLS identity alone never grants enrollment,
storage/domain approval, observer or writer authority. Existing receipt is marked
historical; revoked token is NOT automatically replaced. Request conflict and
missing/corrupt provider fail closed. Android encrypted pending/Binder evidence is
still required separately; test-only memory CAS must not be used by application.

### Native enrollment IPC g.2b
quick_join/resume_join/replace_join_code reuse the original private Binder checks,
explicit consent, app/Keystore identity and M51/unknown device fences. No path,
profile, Node-ID, credential/provider or repair argument is accepted. Native OS
Build/RAM supplies diagnostic profile; memory never authorizes storage/voters.
Owner trust +verified binding precedes UI first send; network/background clears
transient code/trust verification. Public_request maps failures to bounded fixed
labels and safe state; no exception/server text/token/code is reflected. The old
encrypted form draft is not a Core operation and is never silently sent. Existing
node retry is explicitly historical and cannot refresh revoked credentials.
No automatic storage/domain approval or runtime start. Test fixture secrets travel
only stdin to a task-owned private file, remain outside Git/main APK and are not
operator credentials. Original signer/UID/retained state must match before install.

### Positive native UI/Binder qualification g.2c
Only test-APK fixed phases invoke real native views/private Binder/Core. No new
main APK permission/provider/backend, trust bypass or production operation. New
fixture tool excludes original retained upgrade AVD; setup resume requires same
private Controller bindings, zero Nodes/approval, no prior UI logs and actual
vault NOT_PROVISIONED before explicit UI provision. No identity reset/DB restore.
Debug signer/owned guest/process checked, private fixture via stdin. Programmatic
View integration does not establish physical touch usability; TCG launcher ANR
and initial emulator crash remain recorded limits, never hidden as Android PASS.

### Explicit Agent primitive h.1
Shared heartbeat is transport only, not an Android guard/runtime bypass. It has no
HOME/getpass/probe/identity creation/filesystem/lifecycle effects. Native callers
MUST validate original device/context/enrollment/ownership before invoking it.
Optional direct send callback is trusted in-process only, not caller-controlled
IPC/network input. Existing CLI M51/capability/repair/cache behavior remains; Core
Discovery still owns distributed pin/term routing. Returned topology never grants
storage/GC/voter/writer rights. Wrong pin never updates server metadata; revoked
credential/cluster mismatch/offline refuse without new identity or local state.

### Native transport h.2a
Internal constructor requires existing native TLS context, SDK30+ and original
device guard; explicit numeric RFC1918/loopback bind only, TLS1.2+, no default
listener/start hook. Trusted test port0 is not a product config. Bounded32 socket
ownership/65536-byte callbacks, finite read and absolute read/write deadline.
Real blocked-write test requires actual bytes sent +OSError/closed socket/worker
exit, not timer-flag inference. No hidden FD/path/PID API, plaintext key/tunnel,
new permission/dependency or external executable. No new Binder/network auth
capability: HTTP/Storage authorization must remain Core's per-operation scoped
Controller check. Raw TLS echo belongs only to instrumentation and proves no
file/replica/approval/writer rights. Source/limits in ANDROID-NATIVE-TRANSPORT.

### Existing-only Manifest/Engine boundary (h.2b.1a)
POSIX private approved metadata only, no shared/source root, symlink, hardlink,
foreign UID or changed inode. SQLite mode=rw refuses recreation if file disappears
between check and open; inode is checked again before yielding a connection and
transaction return. Missing/empty/future/inconsistent Node/schema refuses with
no DDL/identity insertion/chmod repair. Canonical DDL is shared, not a new schema.
Approved app-private same-UID filesystem is the threat boundary, NOT arbitrary
untrusted shared media or a compromised same-UID process. This API is not a
portable descriptor-pinned SQLite VFS; no hidden Android FD/proc workaround is
introduced. Native volume setup/status/runtime must still validate encrypted
root/manifest/volume/medium bindings and preserve partial state. No HTTP/Agent/
FGS/approval or authority is added by this library option.
