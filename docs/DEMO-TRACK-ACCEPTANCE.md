# ASC Demo Alpha acceptance — DEMO.3b

Status: IN PROGRESS / NOT SOURCE-READY until fresh full Python regression completes.
Scope: Linux x86_64 synthetic only. Android/real SD/Doze/power-cut/production NOT TESTED.
Branch: feature/android-demo-alpha. Core accepted base acea2ae remains unchanged.
Initial implementation: 597b3ff52e7ce58dc5d2bf7d505d5c35fe038380 (DEMO.3a).
Final lock hardening requires a new source checkpoint and fresh full run below.
Date: 2026-10-24 UTC. Python 3.13.5, Go 1.27.3 linux/amd64, OpenSSL.

## Actual evidence

| Gate | Actual result |
|---|---|
| Frozen Demo targeted | 14 PASS / 0 SKIP / 0 FAIL/ERROR, 69.640s (hardened source) |
| Fresh full Python (all Core + Demo) | Initial 221 PASS / 0 SKIP, 1444.112s on initial source; NEW hardened full run required |
| Go uncached `go test -count=1 -v -timeout 240s ./...` | 11 top-level PASS, consensus 19.489s / launcher 0.003s |
| `go vet ./...` | PASS |
| `go mod verify` | All modules verified, PASS |
| Linux AMD64 Go build | PASS |
| Android ARM64 Go cross-build | PASS; not launched by Demo and not Android runtime PASS |
| Exact candidate archive install | PASS: dry-run/install/launcher/rerun/state retention/tamper refusal |
| Package inventory / secrets / archive SHA | PASS, 81 public source/guide/manifest files; no private state |
| Tracked Python AST | 102 files parse PASS; UTF-8 BOM-compatible read |
| Core preservation | All Core source/tests/Go unchanged against acea2ae; only asc/demo and new Demo tests added |

Targeted Linux fixtures execute actual shell/Python subprocesses, OpenSSL-issued
certificates and pinned loopback HTTPS, real temporary file bodies and SHA-256.
ZTE Controller cohosts a separately enrolled Storage Node; Bphone is a second
synthetic physical domain. Inherited LAN fault gates deliberately run twice:
once from extracted source and once via installed immutable launchers.

| Demo safety gate | Evidence / actual behavior |
|---|---|
| Real file replication | Two distinct temporary phone roots with synthetic owner-approved domain labels; two VERIFIED/available domains, body SHA matches |
| Idempotent upload / output safety | Same-key retry retains same logical file; existing download output preserved |
| Offline node / fallback | Actual node process stopped; surviving replica downloads exact bytes; protection DEGRADED |
| Missing medium / quota / domains | Rename actual approved volume; insufficient double-copy quota; two identities same physical-domain label: new upload refused before Catalog row |
| TLS/authentication | Actual pin mismatch aborts; node/no-owner credentials cannot read owner Catalog |
| Controller outage | Actual Controller stopped; previously issued scoped grant is denied at actual Storage Node; new metadata denied, no promotion |
| Runtime surface | Policy change, whole-volume admin grant, advanced backup/replication routes excluded; actual node GC request locked 403 |
| Device/state guard | M51/unknown/invalid bind/future schema/attached consensus refused without new identity or migration |
| Installed rerun | Source checksums verified; node/cluster/volume identities, keys/certs/pins unchanged |
| Upgrade/rollback | Running runtime denies activation; stopped compatible source selection + new complete private backup; code rollback preserves IDs/body hashes and subsequent actual download |
| Complete backup | Includes private DB/configs/TLS, original internal and separately approved external synthetic volume, markers and empty staging; copy/source inventory and SHA readback |
| Backup failure | Missing original medium, corrupt copied body, link, insufficient space and mutation during copy refuse completion/activation |
| Interrupted activation | Inject failure after actual pointer write and before journal completion; PREPARED blocks runtime; stale state refuses recovery; unchanged verified backup permits old-code selection without data restore |
| Redacted diagnostics | Output excludes actual owner/node tokens, pin/origin, private path and logical filename |

## Reproduction

From the verified Demo branch and the development toolchain (Cloud activation
only when present):

```sh
source /workspace/asc-cloud/activate.sh
python -B -m unittest tests.test_demo_installer tests.test_demo_lan tests.test_demo_upgrade -v
python -B -m unittest discover -s tests -v
cd consensus
go mod verify
go vet ./...
go test -count=1 -v -timeout 240s ./...
CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -trimpath -buildvcs=false -o /workspace/work/demo3b/asc-raft-linux-amd64 ./cmd/asc-raft
CGO_ENABLED=0 GOOS=android GOARCH=arm64 go build -trimpath -buildvcs=false -o /workspace/work/demo3b/asc-raft-android-arm64 ./cmd/asc-raft
```

Full Python log: /workspace/work/demo3b/full-python.log (local evidence only;
not published because runtime logs can contain private fixture details). Go logs
are adjacent. A different account needs the repository/toolchain, not this path.
No physical fault tests were skipped, weakened or replaced by an assumed result.

## Initial candidate (RETIRED / NOT RELEASED; superseded by lock hardening)

Archive: asc-demo-alpha-0.3.0.tar.gz, deterministic source only, 81 entries.
Archive SHA-256: `3510d37f9e54feb4884f9ed7f78b31891f9974bbd79ae73b06e0a21f5c878603`.
Release/content identity: `1b89251efe77dbff5de531ab055ed1e99a3ce351a819a13737df35801dd5714c`.
Package README equals docs/DEMO-QUICKSTART.md. Per-file manifest verified after
extraction, unpacked paths/content reviewed for secrets/links/special files.
Exact candidate archive matches deterministic rebuild and runs installer/launcher
checks in a fake Android HOME. Publisher identity still requires trusted GitHub
commit/digest; self-contained checksums are not signatures.

## Limits / rollback / owner handoff

Read DEMO-QUICKSTART.md in full: manual Termux preparation, checksum verification,
explicit LAN Controller/cohost/node start, pair/approve, upload/status/download/SHA,
Ctrl+C stop, private backup, staged compatible upgrade/code rollback/recovery and
redacted diagnostics. Owner alone tries actual ZTE/Bphone/XZ3. No Codex real-device
access, deployment, production logs/DB or M51 interaction occurred.

Single-writer LAN demo only; no automatic failover/offline writes, Android Raft,
physical GC, replica reduction, Phase 3D, native APK, public access, auto-update or
24/7/production durability. All Core modules and tests are preserved. Labels require
owner confirmation of physical independence. Full cluster stop is the controlled
upgrade path; rolling/mixed versions not qualified. Backup is private and includes
secrets, does not provide external disaster recovery, automatic state restore,
Termux->APK / single-writer->Raft / medium-identity / production migration.

Rollback uses stopped compatible code selection after a NEW verified full backup,
never an older database overwrite. PREPARED recovery additionally verifies current
state still matches its backup; otherwise preserve directories and seek review.
DEMO.4 Dashboard Lite intentionally deferred, as authorized for first CLI delivery.

## Final-review defect and DEMO.3a.1 safety correction

After the initial full 221 PASS, a new synthetic fault test reproduced a real issue:
an existing coordination-file symlink let reused Core foreground_lock write one
space into an empty outside test-owned file BEFORE backup rejected the symlink.
The new case FAILED before the correction (3.540s); no phone/real data was involved.
Core source remains unchanged. New Demo locks.py opens with O_NOFOLLOW on Linux,
checks regular/single-link/inode identity/content BEFORE writing, then reuses Core
OS lock/unlock primitives. Demo lifecycle/install/stage/backup/activation wrappers
use it; read-only state preflight also rejects linked internal Core engine/worker
locks before their constructors. Symlink/hardlink failure test checks outside bytes
unchanged across root/controller/agent/engine/prefix locks.

The initial candidate and old installer preview are historical only; do not install
them for owner trials. A hardened candidate/full run is required before source-ready.
Package now includes blank owner Android pilot checklist and the safe separate-prefix
procedure if preview source already exists. All Android results remain NOT TESTED.

Hardened candidate: 83 entries, includes lock adapter + owner pilot record.
Release ID `ab229efb9179d356f7b4f363d0a82fa40d33a53164ca215f7c2625be8aaaece8`,
archive SHA `3bf81c5d94891fa064e2f05f99d60d620b4c5db71c87bb2ee6c89ac72b9a445a`.
Hardened fresh full Python must complete before any source-ready/publication claim.
Go source unchanged by this Python-only fix; actual uncached Go/module/vet/build
results above remain applicable and are not falsely reported as rerun.
