# ASC SECURITY & RECOVERY

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
