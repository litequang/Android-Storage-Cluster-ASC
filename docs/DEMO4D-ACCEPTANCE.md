# ASC Demo Alpha0.4.1 — DEMO.4d acceptance

**SOURCE-READY / ACCEPTED for Linux synthetic qualification only.** Android0.4.1 runtime NOT
TESTED; owner-reported ZTE0.3 issue is evidence of the old bug, not a new PASS.
Branch feature/android-demo-alpha, verified baseline ef6470d4b91b9c6430591202047ad4c628c9a04a.
Core WIP remains acea2aead8cfd50f8a8fc2b31e24f8f9ccaeb84c; shared storage adapter
and engine correction now explicitly authorized ON DEMO BRANCH, no WIP write.

| Checkpoint / gate | Actual evidence |
|---|---|
|4d.1 fix |5050a7912baa58b51d1bf020c758aeb52f97918f, normal pushed/remote verified;61 targeted PASS0skip17.030s |
|4d.2 runtime/browser |72bc61d6c8445e4bc161dc9037515b90b26c269f, normal pushed/remote verified;36 targeted PASS0skip126.761s +new ancestor1PASS0.004s |
| Exact published0.3 and0.4 direct upgrades/rollback |2PASS36.243s; then2upgrades+3installer5PASS37.956s; both included in38 final targeted and246 fresh full |
| Final frozen0.4.1 targeted | **38 PASS /0 SKIP /0 FAIL/ERROR,149.451s** |
| Fresh full Python | **246 PASS /0 SKIP /0 FAIL/ERROR,1428.854s**; completed 2026-10-25T01:39:27.579046+00:00 |
| All eight Linux physical gates | **01–08 PASS**, plus legacy actual network unlink/lost TLS ACK/journal/quorum/Leader loss gates |
| Fresh Go/vet/modules/builds |11 uncached tests PASS (consensus24.114s/launcher0.004s); vet PASS; all modules verified; LinuxAMD64 build +AndroidARM64 cross-build PASS, not runtime |
| Exact final archive install | **3 PASS /0 skip,1.749s**; frozen source rebuild byte-identical; dry-run/install/launcher/rerun/state retention/tamper/guards PASS |
| Public archive audit / checksum |93 regular source/asset/guide/manifest files,175301bytes; unpacked0secret/private-path/link/special findings; immutable GitHub receipt follows normal push |
| Actual ZTE/Bphone/Android runtime/CA trust/SD/Doze/power-cut/production | NOT TESTED; owner only |

Old root-open walk reproduces readable=true/writable=false/fsync=null/write_denied
when only open('/') is denied. New approved-root descriptor pins persisted medium,
marker/root/folders/ancestors before/after no-follow child IO. No '/' directory open,
absolute child file fallback, permission/SELinux/root or identity bypass. Actual
probe write/read SHA/file+directory fsync and owned-file cleanup must ALL pass;
collision/replacement/hardlink/symlink/marker faults and real unprivileged EACCES
are regression-tested. Details/race/trusted-account model: DEMO4D-PLAN/SECURITY.
Base formats/IDs/credentials/media unchanged; Windows separate handle adapter kept.

Actual synthetic runtime uses private test-only os.open wrapper, not product flag;
TLS, Controller, two enrolled nodes, probes/physical file bodies/two approved domains,
SHA/offline fallback/restart and Dashboard all real. Wrapper advertises only actual
dir_fd capability it delegates; no simulated IO/ACK/success. Existing Chromium CA
trust/auth/CSRF/XSS/mobile/file/offline tests PASS; missing trust is still rejected.
New owner storage-status uses stopped-node Engine probe under existing device/state/
prefix/journal/operation/agent/engine guards; no new network API/initialization.

Both exact checksum-pinned published archives are used, not relabeled new source:
0.3 SHA3bf81c5d94891fa064e2f05f99d60d620b4c5db71c87bb2ee6c89ac72b9a445a;
0.4 SHAb9e186589bb4f5c698c7df2250f94ec32ce1e6e2acb41cf3923ade9e706a29f1.
Old launchers make/verify explicit full backups, stage/preflight/activate under root
open denial. New installed0.4.1 probes/reads old file through trusted Dashboard,
creates another two-copy file, retains Node/Cluster/installation/Volume IDs, PINs,
credentials/certs/keys/medium. Existing0.4 Dashboard private CA/config and all three
UI assets retained. NEW complete backup precedes compatible code-only rollback;
old source under root denial reports original write_denied (EXPECTED) and denies
new upload. In baseline Linux namespace both old and new files still download by
old source with exact SHA, proving code/schema/data preservation, NOT fixed Android
storage after downgrade. No old database restore, format edit or marker recreation.

Qualified public package `releases/asc-demo-alpha-0.4.1.tar.gz`:93 regular public source/assets/guides/manifest members,175301bytes,
release d022f29cb5d4f53835acf5a130a45fb921be73b875cdccaed8e9504e979ab08f,
SHA74932d474c71b57b4904bfa95ff240250fcf12afa400a85015c4c2d41a94edb1.
Unpacked secret/path review0findings. All mandatory Linux source gates complete;
normal publication/advertised remote and independently downloaded GitHub checksum
verified at 2bef69ac300a19e7b792a57979596a421c8e0d8c (receipt below and in progress).
Old archives/accepted Dashboard0.4 report retained.

Owner existing-ZTE copyable commands, safe stop/backup/SHA/stage/upgrade/identity
snapshot/status/HTTPS+CA/Bphone/replicas/download/rollback:
[DEMO-ZTE-0.4.1.md](DEMO-ZTE-0.4.1.md). General QuickStart/pilot packaged too.
Guide shell blocks pass bash -n; not executed on phones. Rollback requires stop-all
and NEW full private backup; old bug returns on affected Android, no stale DB restore.

## Final frozen-source qualification / reproduction

Frozen source/tests/packaged guides **dae8e7ad8b9661b6ca4b7b6f2344652e8c2913e6**,
normal-pushed/remote-verified before the fresh full run. Started2026-10-25T01:15:38.556975+00:00,
completed 2026-10-25T01:39:27.579046+00:00; no source/test/packaged-guide changes during or
after successful qualification. Reporting/public archive/checksum files only follow.
Python3.13.5, Go1.27.3 linux/amd64, Chromium154.0.8037.57, Playwright/certutil/OpenSSL.
246 =208 unchanged Core test cases +14 original Demo +6 Dashboard API/session +1
real browser +2 exact archive upgrade cases +14 Android-like volume +1 actual
root-denied runtime integration. Existing assertions/faults remain, no skip,
fabricated success, time-budget relaxation or weaker security gate.

| Data-safety gate | Actual evidence |
|---|---|
| Root denied / private IO allowed | Before fix test FAIL exact write_denied telemetry; after fix never attempts root open, real private write/read/SHA/file+directory fsync/owned cleanup PASS |
| Actual permission denial | Unprivileged fixture staging chmod0500 gives actual OS EACCES; writable=false/fsync=null/denial retained, no fake readiness |
| Identity / namespace attacks | Root cloned-marker replacement, ancestor symlink back to SAME medium, staging real-directory/symlink swap, marker mismatch/link/swap/missing, hardlink/traversal, unsupported primitives all safely refuse; outside/original/replacement bytes preserved |
| Probe cleanup / durability errors | Only successfully created probe may be removed, original identity required; collision/unowned/linked files retained; fsync failure never reports true |
| Existing immutable lifecycle | Streaming upload/commit/download/verify/restart and quota/reserve/interruption/revoke/metadata-conflict/owned staging expiry regressions PASS |
| Actual root-denied runtime | Controller +enrolled two TLS storage processes, measured online/readable/writable/fsync, two domain copies, actual stopped-node SHA fallback, restart restores copies and same identities |
| Browser0.4 preservation | Three UI assets byte-identical to exact0.4 archive; existing04 CA/keys/config preserved, real Chromium trusted/untrusted CA, owner/session/CSRF/XSS/mobile/file/fallback/offline gates PASS |
| New owner local status | Reuses Engine probe on existing state; active node ownership/M51/unknown block, stopped node actual writable/fsync succeeds; no HTTP management expansion |
| Exact upgrades | Published03 and04 create/populate old clusters; old backup/verify/stage/preflight/upgrade under root denial; new source reads old bytes, writes another file; every core/browser credential/ID/pin/medium retained |
| Code-only rollback | NEW complete state+approved-volume backup, old pointer selected over NEW state, no DB restore; old Android bug honestly returns under root denial; baseline Linux old code reads BOTH old+new files with exact SHA |
| All physical fault/reference gates | Actual test-only unlink/lost TLS ACK/retry; quorum/term/stale paused final callback deny; node crash/journal restart; whole-cluster snapshot/replay; last readable copy/corruption and version/snapshot/trash/backup/job pins protect bytes |

Full also covers Phase3A backup/history/restore,3B scoring/preferences/retention,
3C policy/move/GC planner, consensus/failover/distributed/storage/lifecycle/installer.
Physical unlink remains ONLY separately issued Linux-x86 temporary test fixtures.
Ordinary Demo/Android/real-device GC has no executor/capability/enable, unchanged.
Raft/failover/consensus/membership and Phase3D remain outside Demo runtime.

Commands actually run (activation from private Cloud toolchain, no system install):

```sh
source /workspace/asc-cloud/activate.sh
python -B -m unittest tests.test_android_volumes tests.test_demo_android_storage tests.test_demo_dashboard tests.test_demo_dashboard_browser tests.test_demo_installer tests.test_demo_lan tests.test_demo_upgrade tests.test_demo_release_upgrade -v
python -B -m unittest discover -s tests -v
cd consensus
go test -count=1 -v -timeout 240s ./...
go vet ./...
go mod verify
CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -trimpath -buildvcs=false -o /workspace/work/demo4d3-final/asc-raft-linux-amd64 ./cmd/asc-raft
CGO_ENABLED=0 GOOS=android GOARCH=arm64 go build -trimpath -buildvcs=false -o /workspace/work/demo4d3-final/asc-raft-android-arm64 ./cmd/asc-raft
```

Linux build PASS; Android ARM64 cross-build PASS only, not launched or counted as
runtime. Full Go11 uncached tests consensus24.114s/launcher0.004s, vet PASS/modules
all verified. Full tracked115 Python AST/shell/JS and ZTE guide Bash syntax PASS.
Exact final public candidate rebuilt from frozen source,93-file manifest matches,
archive byte-identical. Test-only root-denial launcher is NOT in package. All
private state/keys/certs/configs/databases/bodies/logs/browser profiles/builds excluded.
Old0.3/0.4 archive/checksum bytes unchanged; downloaded new archive verification
is recorded in DEMO-TRACK-PROGRESS after normal publication, no network bypass.

## Changed files and branch scope

Only shared Core source modifications: **asc/storage/volumes.py** approved-root
adapter/probe and **asc/storage/engine.py** descriptor space/inventory calls, ON
DEMO BRANCH explicitly authorized by this task. Core WIP staysacea2ae; all Core
consensus/backup/policy/GC logic and original tests/Go unchanged. Demo CLI local
status/version/package, new volume/runtime/fault-wrapper tests and extended exact
release upgrade tests; owner guide/general QuickStart/blank pilot plus AGENTS/
CODEMAP/architecture/ADR/protocol/data/security/troubleshooting/changelog/progress/
plan/acceptance/README docs. New public0.4.1 archive/SHA/narrow ignore exception.
Full exact paths: `git diff --name-only ef6470d..PUBLICATION_COMMIT`; checkpoint
hashes and source routing in progress/CODEMAP. No force/reset/main/Core merge.

## Owner ZTE/Bphone handoff / limits

Read **DEMO-ZTE-0.4.1.md** for copyable commands based on initialized ZTE0.3,
~/.asc-demo and existing Controller/Node/volume. Stop node then Controller; old
launcher backup/verify; trusted commit+archive SHA; stage/preflight/upgrade with NEW
backup; compare private identity snapshot; stopped-node storage-status requires
online/readable/writable/fsync=true/no error. New Dashboard CA only if absent,
manual public-CA fingerprint/trust, Controller --dashboard +original Node, fresh
owner code, new/compatible Bphone with distinct owner-approved domain, real
upload/two replicas/download SHA/offline fallback/restart. Never init/join/
storage-init existing ZTE or print/share keys/tokens/codes/private snapshots.

Rollback: stop-all, NEW complete private backup, select preserved compatible03/04
code over current state, no stale DB restore/identity regeneration. Old source
retains original Android bug; do not claim restored storage service on affected
phone. Keep service stopped/review if downgraded; old/new bytes and identities
remain. General QuickStart6/6a and dedicated guide8 give exact commands.

**Android0.4.1 runtime remains NOT TESTED**, including ZTE9045/Bphone actual private
FD/SELinux/fsync, Chrome/CA-install UX, SD/Doze/power-cut/24x7/production. Owner's
old ZTE diagnostic is not new acceptance; owner alone fills pilot with actual
writable/fsync/two-phone bytes/upgrade/rollback evidence. No phone/M51 access by
Codex. No unsupported-primitives/path fallback or permission bypass; failure keeps
UNKNOWN/denial and state. Private-account/privileged-actor trust and non-atomic
filesystem+metadata/final-syscall/power-loss limits in SECURITY/DEMO4D-PLAN persist.

Windows runtime was not rerun in this Linux task; the separate Windows directory-handle route is retained, without a new Windows or power-cut qualification claim.


## Verified public release receipt

Publication commit **2bef69ac300a19e7b792a57979596a421c8e0d8c**, normal Demo-only push;
advertised remote equals publication HEAD. Core WIP remains acea2ae unchanged.
Ordinary verified HTTPS downloaded archive AND adjacent checksum from immutable
commit at **2026-10-25T04:27:58.101266+00:00**. Archive175301bytes, byte-identical
to qualified local artifact, SHA-256 **74932d474c71b57b4904bfa95ff240250fcf12afa400a85015c4c2d41a94edb1**;
checksum file byte-identical and correct. No network/trust bypass.
[Archive](https://raw.githubusercontent.com/litequang/Android-Storage-Cluster-ASC/2bef69ac300a19e7b792a57979596a421c8e0d8c/releases/asc-demo-alpha-0.4.1.tar.gz) /
[Checksum](https://raw.githubusercontent.com/litequang/Android-Storage-Cluster-ASC/2bef69ac300a19e7b792a57979596a421c8e0d8c/releases/asc-demo-alpha-0.4.1.tar.gz.sha256).
No source/tests/packaged-guide changes after frozen dae8e7a full qualification;
only final reporting follows. All mandatory Linux synthetic release gates complete;
Android0.4.1/real phone/browser CA trust UX remain NOT TESTED, owner pilot required.
