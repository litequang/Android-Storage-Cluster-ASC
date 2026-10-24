# ASC Android Demo Alpha — independent Demo Track

Status: DEMO.0–3 Linux synthetic SOURCE-READY; final 222 Python/11 Go PASS and qualified 0.3.0 package. Android runtime NOT TESTED; DEMO.4 deferred. See acceptance/progress publication receipt.
Date: 2026-10-24 (Asia/Saigon). Branch: `feature/android-demo-alpha`.
Verified Core base: `acea2aead8cfd50f8a8fc2b31e24f8f9ccaeb84c` on
`wip/phase2a-raft-qualification`; never use main or publish Demo commits to Core.
Read AGENTS and its ordered documents, IMPLEMENTATION_PLAN, 3C acceptance/progress,
README-VI and relevant 1.2A/1.2B acceptance before continuation.

## Audit of implemented source

| Existing source | Reuse / finding |
|---|---|
| `asc/probe.py`, `identity.py`, `runtime.py` | Existing known-Android SDK>=24 / M51 refusal, read-only internal/SD discovery, exclusive private files, TLS pins and OS foreground locks |
| `install.sh` | Old source copy is rerunnable but compares only __version__; fixed code destination and no versioned package/upgrade contract. Preserve it; create separate Demo installer |
| `asc/cli.py` lifecycle / `store.Registry` | Existing retry-safe code enrollment/re-pair, private identities and single-writer registry 4. Controller CLI binds wildcard; separate Demo runtime must bind an explicit LAN address |
| `asc/catalog/{service,state,queue,placement,client,http}` | Working single-writer Catalog/copy/proof/fallback with durable jobs, independent owner-approved domains and actual double-copy capacity. Reuse, no engine rewrite |
| `asc/storage/{engine,volumes,runtime,http}` | Immutable local manifest 1, approved empty roots, volume identities, measured quota/free/reserve and bounded staged probes; reuse existing adapters |
| Controller versus Storage Node identity | Core CLI refuses both identities in one ASC_HOME; Demo uses separate controller/ and node/ homes so ZTE may cohost a node while Bphone supplies the second domain |
| `asc/failover`, `asc/consensus`, Go sidecar | Android runtime NOT accepted; excluded from Demo launch, no guard bypass or attached-state fallback |
| `asc/backup`, `asc/nodes`, `asc/replication` | Preserved in repository. Runtime-only 3A/3B/3C APIs and physical GC are not exposed in Demo flow |
| Existing acceptance | Core 208 Python / 11 Go PASS is historical baseline only. 1.2B already proves real TLS copy/fallback on synthetic nodes; new Demo CLI/package/upgrade must get fresh evidence |

## Architecture / non-disposable upgrade contract

Separate immutable versioned source releases, private Demo state and approved file
volumes. Demo state format 1 records track/mode, release/compatibility information
and stable installation identity. Controller registry 4 / node manifest 1 / metadata
cache 1 / config 1 / wire 1 remain Core formats. Never open an attached Raft state,
a legacy unmarked ASC_HOME or an unknown/future schema as Demo. New installation
must use its own directory; existing Core private state is not adopted/migrated.

One fixed Controller, real pinned HTTPS LAN, no leader election/failover. Require
explicit numeric RFC1918/loopback IPv4 binds/endpoints, never wildcard/public binds.
ZTE Controller and ZTE Storage Node use different private subdirectories and their
own credentials; Bphone/XZ3 use separate enrolled node homes. Physical-domain
labels require owner approval; two volumes/identities on one phone are not two
independent devices. Owner credentials stay on Controller.

Use Core StorageRuntime and agent heartbeat plus CatalogService. New upload must
request replicated_2 and have measured eligible capacity in two approved independent
domains. Replica acknowledgement requires streamed SHA proof; report incomplete
replication honestly and retain bytes/jobs on interruption. Downloads can use the
last readable replica while Controller remains available; Controller outage denies
new authority/metadata writes and never promotes a node.

Upgrade contract: staged content-addressed immutable release directories, verified
per-file/package SHA-256, explicit activation while stopped, schema/capability
compatibility preflight before opening state, verified private stopped-state backup
(including approved volumes), code-only rollback when compatible. Preserve node /
cluster IDs, tokens, pins, keys and volume identities. No automatic schema change,
background update, Termux->APK or single-writer->Raft migration. Incompatible versions
must fail closed and retain both source and state for a future tested migrator.

## Checkpoints / GitHub gates

| Checkpoint | Deliverable and qualification |
|---|---|
| DEMO.0 | This audit, architecture, risk/upgrade contract, progress and current task scope; docs/link/secret review; publish before code |
| DEMO.1 | Separate guarded Termux installer/preflight, versioned source package with checksums, safe rerun and clear errors. Linux fake-getprop/pkg fixture, no packages modified. Installer preview is not cluster-ready |
| DEMO.2 | Dedicated single-writer Demo CLI/runtime, separate controller/node homes, private LAN binds, enrollment/approval, two-copy verified upload/download/fallback, missing volume/node/Controller faults on actual synthetic TLS |
| DEMO.3 | Exact compatibility check, stopped-state/volume backup, explicit staged activation/code rollback, identity preservation and redacted diagnostics; final tested QuickStart package + owner ZTE/Bphone guide |
| DEMO.4 | Dashboard Lite deferred behind first CLI package/owner pilot, as allowed by requested priorities. No native APK or advanced UI in initial package |
| Final source-ready gate | Fresh full applicable Python suite including all Core regression/fault tests, Go tests/vet/module verification, installer/package/TLS/offline/identity/upgrade checks; exact Demo acceptance and final package checksum |

Split checkpoints into a/b if necessary. After EVERY completed checkpoint: targeted
PASS, fix defects, update CODEMAP/contracts/progress, inspect tracked+staged blobs
AND unpacked package contents for secrets, commit, normal push to Demo branch,
compare advertised remote SHA before the next checkpoint. Never force/reset/rewrite
history, merge main/Core, or lose local work. Stop on proxy:8080 errors; keep inherited
network/TLS. GitHub must contain enough source, results and next action to resume.

## Safety risks and controls

- Wrong phone / unknown hardware: existing guard at preflight AND mutation/runtime;
  no override, M51 audit only. Codex uses fake Android properties in Linux tests only.
- Existing private state/source overwritten: private Demo marker and strict mode/
  schema checks, immutable hash-verified releases, exclusive creation and lifecycle
  locks; preserve partial failures for review, never recreate missing identity.
- Insufficient copies/space: real pinned probes, double-copy reservations and domain
  checks; new upload refusal, pending/degraded states, no fake VERIFIED/zero telemetry.
- Wrong volume / SD permission: existing VolumeManager identity/no-follow checks;
  new empty internal root or descendant of pre-existing Termux SD app folder only.
  No format, permission grant, scan/write into user folders or physical GC.
- Unsafe upgrade/rollback: no automatic migrations, full stopped backup/checksums,
  reject running processes / unknown schemas / incompatible capabilities; never
  restore an older metadata DB over newer bodies or clear Raft/GC fences.
- Package/diagnostic secret leak: source allowlist, per-file manifest + archive SHA,
  no config/keys/DB/data/logs in packages. Diagnostics whitelist fixed status/counts,
  no tokens/codes, endpoints, raw profile, file names or arbitrary exception text.
- Android background/SD durability: unqualified until owner trials. No 24/7,
  production/disaster durability, power-cut, SAF or real-device runtime PASS claim.

## Owner handoff / rollback limits

Provide a tested checksum-verified downloadable QuickStart archive and README for
manual owner trials on ZTE + Bphone (optional XZ3). Include preparation, read-only
preflight, install, separate Controller/node startup, private code enrollment,
explicit storage/domain approval, upload/status/download, Ctrl+C stop, offline
backup/compatible upgrade/rollback and redacted diagnostics. No shell pipe from
Internet, APK/Termux:Boot/background service or automatic package upgrade.

Before Demo format changes, retain complete stopped private state, volumes and
matching old release. Compatible code rollback changes only the selected source
pointer and revalidates current schema; incompatible restore/migration is not
implemented and must remain a documented blocker. Termux uninstall can lose private
keys/data; Demo is for disposable non-important files and requires owner retention
of separate private backups. No actual phone access is authorized for Codex.
