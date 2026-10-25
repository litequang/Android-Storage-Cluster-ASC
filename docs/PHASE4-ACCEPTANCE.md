# Phase 4.0 acceptance — Linux synthetic foundation

**ACCEPTED for the bounded Phase 4.0 Linux synthetic scope below.**
Android/Windows runtime and production are NOT ACCEPTED. Full writable disaster
recovery remains NOT ACCEPTED / BLOCKED. Phase 4 application/migration work is
still future scope; this result does not accept all of Phase 4.

Branch: `feature/phase4-core-demo-integration`, from Core 3D
`ca2504fa3bc9f2eef706cdf50ddf6835182ada53`. Demo reference:
`c9c2660b5aad9fe347cb0b216f0d691144f74caa`. No branch merge, reset, history rewrite,
original Core/Demo/WIP push or state adoption. Frozen source/tests/packaged guides/
candidate: `4d1758ddac926853ffc43ae9b1aee428ab63bccf`. Full runner started on reporting-only commit
`8ea3c6aba08285f24418796b7eae834a9f118103`; all 164 frozen path hashes equal the
source-freeze commit and actual tested files. Only reporting changed afterward.

## Implemented and qualified

- Core/Demo audit matrix, selective port allowlist and ADR 062/063. Common Registry,
  Catalog, Storage HTTP, credentials and enrollment engine reused. Shared Core
  edits limited to reviewed approved-volume descriptor patch and optional CLI
  expected Cluster ID validation; original Core 3D external/failover/Go modules
  and all 27 original Core test files remain byte-identical.
- Existing Demo single-writer Dashboard has Vietnamese mobile Quick Join tab.
  Owner HTTPS/CA/session/CSRF and exact origin remain required. Same Controller/
  Catalog, no second database or storage engine. Session-bound hash-only tracking,
  8 tickets/session and 32 global; existing 600-second one-use Registry grant.
- Guided initialized-node CLI verifies lifecycle origin, full TLS pin, expected
  Cluster ID and explicit supported Demo mode before secret submission. Existing
  durable pending operation/token and receipt checks survive lost ACK and restart.
  Identity is preserved; unknown current confirmation stays UNKNOWN.
- Registration never creates/approves storage or a failure domain. Owner retains
  explicit CLI approval. Browser stores no admin/node credentials or pairing code
  in persistent storage/URL. Code clears on non-waiting state, disconnect, logout
  and pagehide; delayed replies cannot repaint it. Clearing tracking is NOT code
  revocation; an unconsumed unexpired grant may still work.
- Recovery markers/missing initialized state/quorum or unknown modes/protected
  device guards fail closed. Core 3D external backup, verification and passive
  staging remain separate; no recovery authority is created.

## Actual execution evidence

Python 3.13.5, Go 1.27.3, OpenSSL and trusted real Chromium in Cloud Linux;
synthetic temporary state/volumes, actual filesystem I/O/TLS/processes. No phones,
M51, production, system trust, packages or real-device state were accessed.

| Gate | Actual result |
|---|---|
| Fresh `python -B -m unittest discover -s tests -v -f` | **287 PASS / 0 SKIP / 0 FAIL / 0 ERROR**, 1709.879s |
| Full start / completion UTC | 2026-10-25T11:05:24.414959+00:00 / 2026-10-25T11:33:54.507185+00:00 |
| Source/candidate fingerprint | All 164 paths unchanged; exact frozen commit bytes |
| 4.0a identity/device/compatibility | 16 PASS, 0 skip/fail |
| 4.0b.1 selective port/storage/Core 3D/browser gates | 95 PASS, 0 skip/fail, 290.653s |
| 4.0b.2a backend/guided CLI | 31 PASS, 0 skip/fail, 114.232s |
| 4.0b.2b owner UI + existing browser/API | 17 PASS, 0 skip/fail, 95.116s |
| 4.0c installer/upgrade/browser | 13 PASS, 0 skip/fail, 79.748s |
| Persisted candidate exact-byte upgrade gate | 1 PASS, 0 skip/fail, 19.422s; also runs in fresh full |
| `go test -count=1 -v -timeout 240s ./...` | 11 top-level PASS, uncached |
| `go vet ./...` / `go mod verify` | PASS / all modules verified |
| Linux amd64 build | PASS, CGO disabled |
| Windows amd64 / Android ARM64 cross-builds | PASS, compile only; neither executed as those runtimes |
| Tracked/index/unpacked candidate secrets/paths | 0 findings; manifest/SHA/regular-file inventory verified |

Full fault markers: Phase 3A 12/12; Phase 2B 20/20; Phase 3B 7/7; Phase 3C
replication 3/3; network GC authorization 3/3; Linux physical GC 8/8; external
3D 9/9. These actually run in the fresh full: real quorum/term/Controller loss,
TLS ACK loss, checksum corruption/fallback, reference/last-copy protection,
durable journal crashes, snapshots/replay and passive recovery without authority.
Actual unlinks remain limited to isolated synthetic fault volumes, not ordinary
Demo/runtime or real devices. No assertion/timeout/guard was weakened or skipped.

The FIRST full was interrupted after an original 3D matrix ERROR after group 06;
exit -2, 519.918s, unchanged source. Its traceback was not emitted before interrupt,
so no root cause is claimed. Unchanged standalone 3D then passed all 9 groups in
57.558s. The fresh fail-fast full above passed all 287 and all 9 groups; the first
partial run is NOT counted as PASS. Private diagnostic logs retain both runs.
If the intermittent issue recurs, retain immediate traceback and investigate;
these synthetic results are not a real-network availability SLA.

## Exact compatibility / rollback evidence

Separate new test uses the EXACT published 0.4.1 archive, SHA
`74932d474c71b57b4904bfa95ff240250fcf12afa400a85015c4c2d41a94edb1`, plus exact
persisted candidate bytes. OLD installed launcher performs backup/readback,
stage, compatibility preflight and activation. Cluster/Node/Volume/medium identity,
PIN/credentials/keys and Dashboard CA bytes are retained. Old data downloads with
matching SHA; candidate writes and protects a new file on two independent synthetic
domains. Pending enrollment from actual lost successful TLS ACK resumes with the
same operation/token/Node ID after upgrade. A NEW full backup of NEW state precedes
code-only rollback to exact 0.4.1; old code reads BOTH files and resumes a pending
operation created by the candidate. No old database is restored over new bytes.
Unsupported format/capability downgrade, missing volume, corrupt backup and
interrupted activation all refuse safely in retained installed-launcher tests.

Only **exact 0.4.1 -> this candidate**, and compatible NEW-state code-only rollback,
are newly qualified. Historical 0.3/0.4 -> 0.4.1 tests keep their exact old archive/
version/asset assertions and run in full; they do not prove direct 0.3/0.4 -> 0.4.2.
No schema migration: demo1/registry4/manifest1/cache1/config1/wire1 unchanged.
Same registry integer does not authorize Core quorum/Demo/DR state interchange.

## Candidate and use

`candidates/asc-demo-alpha-0.4.2-dev.tar.gz`: 196386 bytes,
106 regular public source/doc/asset files; deterministic rebuild byte-equal.
No binaries, private state/keys/tokens/backups/logs or user bytes.

- SHA-256: `b7904a82c55e41866b374ecb42b873a6796a4f8e5e53a213f648e026467a64a3`
- Release ID: `f550f565836b44dc582001e3adabb34e1a594441bdd52dbfff51700b7c1e19c7`
- Manifest format 1, added `quick-join-foundation` capability; base formats unchanged.
- Existing 0.3/0.4/0.4.1 public archives and checksums retained byte-for-byte.
- Source-only synthetic candidate on feature branch; no GitHub Release/tag or
  public Android release. Packaged README routes to candidate guide first.

Read [PHASE4-QUICK-JOIN](PHASE4-QUICK-JOIN.md) for verified SHA, owner-trusted
Dashboard CA, separate login/node codes, guided CLI, explicit storage approval,
old-launcher stage/preflight/upgrade, NEW backup and compatible code-only rollback.
Read [PHASE4-PLAN](PHASE4-PLAN.md) for audit/next work and
[PHASE4-PROGRESS](PHASE4-PROGRESS.md) for checkpoints and remote receipts.

## Remaining risks / next Phase 4

No Android runtime, actual media/removal, device CA UX or physical power-cut
acceptance. ZTE/Bphone/XZ3 owner pilot needs a separate approved candidate/device
qualification; cross-build is not runtime evidence. No M51/unknown-device bypass.
No automatic storage/domain approval, browser-to-local storage-node bridge, APK,
Core quorum Dashboard, Controller failover/Raft on phones, GC unlock or automatic
replica reduction. Phase 4.1 should define/qualify the native/local-engine interface
and a Core quorum UI adapter; Keystore/SAF and Termux-to-APK migration need explicit
contracts and tests. Termux paths/UID/medium/keys cannot be promised portable.
Single-writer-to-Raft migration and writable DR require separate authority/fencing/
key-recovery qualification; no recovered writer, synthetic quorum or invented epoch.
Acceptance normal-pushed/advertised remote verified at `f0d9bd1e68354056bee756723ccff0aa78af848f`.
Independent fresh bare clone at 2026-10-25T11:35:31.785820+00:00 matches all164 frozen source/
test/packaged-guide/candidate hashes and published archive SHA. Original Core3D,
Demo and Core WIP refs unchanged. Final receipt is reporting-only; final remote
HEAD is recorded in the operator handoff, not claimed by a self-referential hash.
