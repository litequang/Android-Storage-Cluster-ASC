# ASC Demo Alpha 0.3.0 acceptance — DEMO.3b

Historical0.3 report preserved. Current Dashboard0.4 qualification: [DEMO4-ACCEPTANCE.md](DEMO4-ACCEPTANCE.md); do not infer0.4 PASS from this report.

**SOURCE-READY / ACCEPTED for Linux synthetic qualification only.**
**Android runtime, real SD, Doze, power-cut, 24/7 and production: NOT TESTED / NOT QUALIFIED.**

Branch: `feature/android-demo-alpha`. Date: 2026-10-24 UTC.
Final implementation/tests: `aaf7d163fbac032bb31a033efe2ebb21406509bf`.
Core base/remote: `acea2aead8cfd50f8a8fc2b31e24f8f9ccaeb84c`, unchanged.
Python 3.13.5, Go 1.27.3 linux/amd64, OpenSSL. No implementation or packaged-guide
change after the successful final fresh full run. This reporting/package commit
is identified by Git history; publication receipt is recorded in progress afterward.

## Actual final evidence

| Gate | Actual result |
|---|---|
| Final Demo targeted | **14 PASS / 0 SKIP / 0 FAIL/ERROR, 69.640s** |
| Fresh final full Python | **222 PASS / 0 SKIP / 0 FAIL/ERROR, 1422.541s**; completed 2026-10-24 17:59:37 UTC |
| Go `go test -count=1 -v -timeout 240s ./...` | **11 top-level PASS**, consensus 19.489s / launcher 0.003s; uncached |
| `go vet ./...` / `go mod verify` | PASS / all modules verified |
| Linux AMD64 Go build | PASS |
| Android ARM64 Go cross-build | PASS; not launched by Demo, not Android runtime PASS |
| Exact hardened archive install | PASS: deterministic rebuild byte match, dry-run/install/launcher/rerun/state retention/tamper refusal |
| Public archive review / SHA-256 | PASS; 83 public source/guide/manifest files, no private state, links or special entries |
| Python AST / shell syntax | 103 tracked Python files parse PASS; UTF-8 BOM-compatible read; `sh -n` PASS |
| Core preservation | Core source/tests/Go unchanged against acea2ae; only new Demo sources/tests added |

222 = all 208 unchanged Core tests + 14 Demo tests. Full run actually includes
Phase 3A history/snapshot/backup/restore acceptance, failover/distributed regressions,
scoring/preferences/replication and legacy/new physical-GC faults. No physical fault
was skipped, weakened or replaced by an assumed success. Go checks ran fresh during
this task; unchanged Go/Core source makes those results applicable after the
Demo-Python-only lock correction. They were not falsely reported as rerun afterward.

## Demo behavior / safety evidence

Actual shell/Python subprocesses, OpenSSL certificates, pinned loopback HTTPS,
real file bodies and SHA-256 are used in isolated fake Android HOME fixtures.
Synthetic phone roots are distinct directories with owner-approved synthetic domain
labels, not evidence of independent real hardware. ZTE cohosts Controller and an
enrolled Storage Node in separate private homes. LAN fault gates run both from
extracted source and through installed immutable launchers.

| Gate | Actual evidence |
|---|---|
| File replication | Two actual bodies, two VERIFIED/available synthetic domains; both SHA-256 match |
| Retry / output safety | Same-key upload preserves file ID; existing download output never overwritten |
| Node offline / fallback | Actual node process stopped, survivor download exact; protection DEGRADED; unsafe new upload denied before Catalog row |
| Medium / quota / domains | Actual volume renamed, insufficient double-copy quota, two node identities in one domain all deny new upload |
| TLS/auth | Wrong actual pin aborts; node/no-owner token denied owner Catalog |
| Controller lost | Actual Controller stopped; already-issued real scoped grant denied at actual Storage Node, new metadata denied; no promotion |
| Excluded features | Policy change/whole-volume grant/advanced backup/replication mutation routes excluded; actual node GC request locked 403 |
| Guard / compatibility | M51/unknown/invalid bind/future schema/attached consensus refused without identity recreation/migration |
| Upgrade / rollback | Running runtime denies activation; stopped compatible code selection + verified full backup; IDs/keys/certs/pins/volume marker retained; actual post-rollback file download SHA matches |
| Complete private backup | State/DB/config/keys/internal and separately approved external synthetic volume, original markers/empty folders; source and copied inventory SHA verified |
| Backup failure | Missing original medium, corrupt copy, link, insufficient measured space or concurrent mutation deny completion/activation |
| Interrupted activation | Inject failure after actual pointer write, before journal completion; PREPARED blocks runtime; changed state denies recovery; unchanged backup permits old-code selection without data restore |
| Coordination files | Existing root/controller/agent/engine/prefix symlinks and hardlinks refused BEFORE any outside-file write |
| Redacted diagnostics | Actual tokens, pin/origin, private paths/profile and logical filename excluded |

All Linux physical gates 01–08 ran again in the final full suite:
1. Actual all-voter partition before final TLS callback denies unlink.
2. New majority term invalidates paused old-run authorization.
3. Paused successful final receipt exceeds freshness budget: no unlink.
4. Real Node/cohost crashes before/after unlink recover the same durable journal job.
5. Actual Go snapshot/all-process replay preserves DONE/fences/journal and readable survivor.
6. Missing/corrupt sole survivor denies GC, retaining last readable retired bytes.
7. New snapshot/backup reference at paused final boundary denies unlink; versions/trash pinned.
8. Whole-cluster snapshot/replay retains backup/version pins and restores exact old bytes.
These Core tests delete only on issued isolated synthetic volumes; Demo ordinary
runtime has no GC executor/discovery/capability and remains locked.

## Final QuickStart Package

`releases/asc-demo-alpha-0.3.0.tar.gz` and adjacent `.sha256` are the qualified
source-only package. 83 regular members, with README + owner pilot guide.

SHA-256: `3bf81c5d94891fa064e2f05f99d60d620b4c5db71c87bb2ee6c89ac72b9a445a`.
Release/content ID: `ab229efb9179d356f7b4f363d0a82fa40d33a53164ca215f7c2625be8aaaece8`.

Package README equals `docs/DEMO-QUICKSTART.md`. Exact archive matches frozen-source
rebuild and was executed in a fake Android HOME. Inventory, unpacked contents and
tracked/index blobs reviewed separately for secrets. Verify archive SHA from the
same trusted GitHub publication commit before extraction; checksums are not signatures.

## Reproduce / logs

```sh
# Use this Cloud activation only if present; otherwise prepare the development toolchain.
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

Actual final log: `/workspace/work/demo3b/full-python-hardened.log`; Go logs adjacent.
Logs stay private/local, not in GitHub. Another account can rerun from repository
and toolchain without this workspace or the original prompt.

## Final-review correction / historical provenance

An initial full run on 597b3ff passed 221 tests (1444.112s). Additional final review
then reproduced a real unsafe existing-lock symlink path: reused Core foreground_lock
wrote one space to an outside empty test-owned file before backup refused it. The
new regression failed before correction (3.540s). Demo-only `locks.py` now checks
O_NOFOLLOW/regular/single-link/inode/content BEFORE writes and reuses Core OS lock
primitives; state preflight also checks internal Core worker/engine locks. Core source
was preserved. The final 14 targeted and fresh 222 full PASS supersede the initial
candidate/results. Initial candidate was never released; installer preview 0.1.0
is historical, not recommended. See pilot guide for a separate-prefix installation
if preview source already exists. No real device or real user data was touched.

## Handoff / limits / rollback

Owner reads DEMO-QUICKSTART and blank DEMO-ANDROID-PILOT. Only the owner installs
on ZTE/Bphone/XZ3; no Codex phone access/deployment/production DB/log or M51 interaction.
Single-writer LAN, no automatic failover/offline metadata writes, Android Raft,
physical GC/reduction, Phase 3D, APK, public access, auto-update or production promise.
DEMO.4 Dashboard Lite is intentionally deferred for the first CLI handoff.

Source and private state stay separate. Physical domains require owner confirmation.
Stop ALL cluster foregrounds before staged compatible upgrades, back up EACH phone,
then restart Controller followed by nodes and verify replica/SHA status. No rolling/
mixed-version qualification, automatic DB/byte restore, external DR, Termux->APK,
single-writer->Raft, medium-identity or production migration is implemented.
Rollback selects old compatible code only after a NEW complete verified private backup;
never overwrite current data with an old DB. PREPARED recovery additionally requires
unchanged current state matching its backup; otherwise preserve directories for review.

## Publication verification

Normal Demo branch push and advertised remote verification succeeded at
`52850b9072241ab4bb7643b06127965d25d96904`. Downloaded that commit's exact public
GitHub archive (141336 bytes) and verified identical bytes/SHA-256 to the qualified
local package. Core remote still acea2ae. See PROGRESS publication receipt and Git
history for checkpoint hashes, source/changed-file routes and owner next steps.
This later receipt is docs-only; implementation, package and test evidence unchanged.
