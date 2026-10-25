# Phase4.0 progress — account-independent handoff

Branch feature/phase4-core-demo-integration, Core baseline ca2504fa3bc9f2eef706cdf50ddf6835182ada53,
Demo reference c9c2660b5aad9fe347cb0b216f0d691144f74caa, common ancestor acea2ae.
Both fetched/advertised refs match; initial working tree clean. No Phase4 branch
existed; new feature created from Core, no merge/reset/old-branch edits.

|Checkpoint|State|
|---|---|
|4.0a|PUSH/REMOTE VERIFIED5d15cb71dc07e0e31b7b9da68e4aea85178e3847;16 targeted PASS|
|4.0b.1|PUSH/REMOTE VERIFIED4646f68b7e7e60d924a6beb25de93dcd2e597448;95PASS|
|4.0b.2a|PUSH/REMOTE VERIFIEDb96e4be43dd1228c025cb0305fd7372b559b9fb3;31PASS|
|4.0b.2b|PUSH/REMOTE VERIFIEDed07bbc3640d3f0f89efbafb6545b22fe4514dd3;17PASS|
|4.0c.1|PUSH/REMOTE VERIFIED4d1758ddac926853ffc43ae9b1aee428ab63bccf; candidate SHA fetched/verified|
|4.0c.2|NOT ACCEPTED: first full interrupted after3D error; standalone9/9 PASS; fresh full retry required|

Read AGENTS in mandatory order, then3D acceptance/progress and Demo4D acceptance/
QuickStart where available, then PHASE4-PLAN/this/ACCEPTANCE. Prior plan audit read
both branch additions/common documentation and actual relevant source. Common
Registry/server/CLI/client/identity/Catalog/StorageHTTP/manifest/Go byte-identical;
only storage shared patch differs, plus each branch's separate modules. Preserve
Core external backup/verify/read-only staging; writable DR remains BLOCKED.

Confirmed user choices: Core-first separate feature, selective port ONLY, Demo
single-writer UI first, source +synthetic candidate (not public Android release).
No second Catalog/Storage/enrollment engine. Candidate0.4.2-dev no schema migration;
legacy pending context must remain rollback-compatible. Native/PWA node bridge,
Core quorum Dashboard, APK/migration and real-device acceptance deferred.

Every checkpoint targeted PASS/docs/CODEMAP/secrets/commit/normal feature push/
advertised remote match before next. Never push Core3D/Demo/WIP/main. Do not claim
Phase4 ACCEPTED until final fresh applicable regression and fault gates complete.
Existing Cloud activate.sh selects Python3.13.5/Go1.27.3; Node/Chromium/certutil
already available. Keep inherited proxy/trust, stop on proxy:8080 errors.

4.0a actual: python -B -m unittest tests.test_lifecycle.ClientIdentityTests
 tests.test_lifecycle.DeviceSafetyTests tests.test_external_compatibility -v:
16PASS0SKIP0FAIL0.173s. No source edits. Plan/fences/links +git diff --check PASS;
normal feature push/remote receipt recorded next checkpoint.

## 4.0b.1 selective compatible port

4a normal-pushed/remote matched5d15cb7 BEFORE source port. Exact allowlist46 new
public paths from Demo c9c2660:17 Demo source/assets,10 historical Demo docs,
8 old archive/checksum files, launcher and10 test/helper/browser files. ONLY shared
source overwritten: reviewed volumes.py/engine.py Android anchor patch. Registry/
server/CLI/client/identity/Catalog/StorageHTTP/manifest/Go common bytes unchanged;
Core3D external modules and RuntimeHandler byte-identical to ca2504f. All original
Core tests unchanged. No merge/cherry-pick of an entire branch or state adoption.
Common docs retain Core3D sections, append reviewed historical Demo extensions;
Demo ADR055/056 map060/061, Core055/056 external meaning preserved,057–059 imported.

Actual command: `python -B -m unittest tests.test_android_volumes
 tests.test_demo_android_storage tests.test_demo_dashboard tests.test_demo_dashboard_browser
 tests.test_demo_installer tests.test_demo_lan tests.test_demo_upgrade
 tests.test_demo_release_upgrade tests.test_external tests.test_external_verify
 tests.test_external_recovery tests.test_external_compatibility tests.test_external_cluster
 tests.test_external_faults tests.test_gc_sandbox tests.test_gc_authorization -v`:
**95PASS0SKIP0FAIL290.653s**. Actual browser/CA/bytes, exact03/04 upgrades/rollback,
all9 actual3D faults +recovery child crash, root-denied volumes and sandbox/GC auth
units PASS together.4 archived packages/SHA/unpacked path audits PASS; port hashes
match pinned Demo bytes. Prototype package version remains historical0.4.1-alpha
ONLY for this compatibility checkpoint (source ID differs because Core3D is kept);
not republished or claimed as original released0.4.1. Next b.2 candidate0.4.2-dev.
Next only after normal push/remote equality:Quick Join backend/CLI then UI/browser.

## 4.0b.2a backend / guided CLI

b.1 pushed and advertised remote matched4646f68 BEFORE this implementation.
New Pairings session facade calls existing pinned admin/pair; sole durable state
remains Registry join_codes/enrollments. Hash-only RAM tickets,600s one-use
node grants,8/session32global, owner CSRF/exact origin, no GET secret. Logout/
restart discards tracking/session, DOES NOT revoke an unconsumed underlying code.
CLI quick-join executes Core enrollment with ASC_HOME bound before import; pin,
expected cluster, Demo mode/protocol/schema checked before code. Optional Core
--expected-cluster-id guards use existing pending field; no wire/schema change.
Lost ACK/replacement code retry preserves operation/token. Missing initialized
Demo state/M51/unknown device/RECOVERY_READ_ONLY refuse without state adoption.
Registered != storage approval; no volume creation/approval/start or domain claims.
Source candidate0.4.2-dev only. Historical03/04->04.1 test setup now extracts exact
published04.1 (SHA74932d474c71b57b4904bfa95ff240250fcf12afa400a85015c4c2d41a94edb1),
retaining ALL historical version/asset assertions; candidate upgrade gets a separate
4c test. Public archives unchanged.

Actual `python -B -m unittest tests.test_quick_join
 tests.test_lifecycle.ClientIdentityTests tests.test_lifecycle.DeviceSafetyTests
 tests.test_demo_dashboard tests.test_demo_release_upgrade -v`:
**31PASS0SKIP0FAIL114.232s**.9 new Quick Join tests include real pinned TLS lost
successful ACK/idempotent receipt, Controller restart, concurrent one-use race,
expiry/new-code same operation, pin/cluster/quorum refusal, session isolation/
CSRF/global32 bounds, no auto-storage, existing identity and setup/device guards.
Full qualification/candidate upgrade and owner UI still pending. Next only after
normal feature push/remote equality:4.0b.2b. Guide PHASE4-QUICK-JOIN.md.

## 4.0b.2b existing Dashboard Quick Join UI

b.2a normal-pushed/remote matchedb96e4be BEFORE UI changes. Same Vietnamese
mobile Dashboard now has Ghép điện thoại tab. Owner creates code and sees actual
registration plus separate storage approval/domain. No second UI/runtime or
approval control. Full Controller lifecycle origin/pin/cluster displayed; code
DOM/RAM only, cleared on non-waiting evidence/offline/logout/pagehide. Generation
guards discard old POST/poll replies after logout/disconnect. No auth grant in
persistent browser storage or URL. Logout/reload does not claim code revocation.

First browser gate failed in TEST delay hook because Playwright route.fetch has
a separate CA trust store. Fixed test to delay delivery AFTER Chromium validated
the actual TLS response; no TLS bypass, fake success or product fault flag.
Single corrected case PASS9.610s; fresh final command:
`python -B -m unittest tests.test_quick_join_browser
 tests.test_demo_dashboard_browser tests.test_demo_dashboard tests.test_quick_join -v`
**17PASS0SKIP0FAIL95.116s**. Actual trusted Chromium new mobile wizard ->actual CLI
node registered/unapproved, no persistent grants, offline clear and delayed reply
race PASS. Existing browser upload/two domains/SHA/node fallback/XSS/Controller
outage PASS, all backend/security cases PASS. Manual screenshot390px inspected,
no overflow; local screenshot contains no code and is not published. Node JS
syntax checks and diff whitespace PASS. Candidate upgrade/full qualification
still pending. Next only after feature push/remote equality:4.0c.

## 4.0c.1 exact candidate and compatibility freeze

b.2b pushed/remote matcheded07bbc BEFORE compatibility implementation. Added
one separate exact published04.1 archive ->candidate test (no version-label mock).
OLD installed backup/verify/stage/preflight/activate; two real pinned TLS replicas,
old file SHA; OLD pending after actual successful lost ACK resumes with candidate,
same operation/token/Node ID; candidate writes new file and creates NEW pending;
NEW full backups then code-only rollback to exact04.1, old code reads BOTH files
and resumes NEW pending identically. Cluster/Node/Volume/medium/credentials/PIN/
Dashboard CA bytes retained, no automatic storage approval or schema migration.
First new-test run caught incorrect test-only Registry table/field names; corrected
to actual enrollments/enrollment_hash and payload.enrollment_id; source unchanged.
Docs terminology corrected too. No historical regression weakened.

Actual frozen candidate command `python -B -m unittest tests.test_phase4_upgrade
 tests.test_demo_installer tests.test_demo_upgrade tests.test_quick_join_browser -v`:
**13PASS0SKIP0FAIL79.748s**. Includes unsupported-format/capability downgrade,
missing volume/corrupt backup, interrupted upgrade recovery and device guards.
Extra exact persisted candidate byte-equality +upgrade test after final assertion:
**1PASS0SKIP0FAIL19.422s**. New artifact equality checks lock source, not just version.
Go fresh11PASS, vet/module verification and Linux amd64 build/Windows amd64 and
Android ARM64 cross-build PASS; source unchanged from Core3D. Neither cross-build
is runtime acceptance.

Candidate ONLY, not GitHub Release/tag/public Android release: candidates/
asc-demo-alpha-0.4.2-dev.tar.gz,196386bytes106regular public source/doc/asset files,
SHA b7904a82c55e41866b374ecb42b873a6796a4f8e5e53a213f648e026467a64a3,
release IDf550f565836b44dc582001e3adabb34e1a594441bdd52dbfff51700b7c1e19c7.
Deterministic rebuild byte-equal, manifest/file/SHA/path and unpacked secret audit
PASS0findings. Existing03/04/04.1 archives byte-identical to Demo reference; all27
original Core test files and entire external/failover/Go source unchanged.
Packaged README explicitly routes candidate scope to packaged PHASE4-QUICK-JOIN;
no new formats, schema changes, release URLs or phone installation claims.

NEXT after c.1 normal push/remote equality: fresh `python -B -m unittest discover
-s tests -v`,287 unique cases (original276 +9 QuickJoin +1 browser +1 archive upgrade).
Freeze asc/tests/consensus/scripts/install.sh/tools/packaged guides/candidate bytes;
only reporting docs may change until result. Full physical/network fault gates
MUST actually pass; do not accept using targeted/historical evidence. Logs under
/workspace/work/phase4, no private artifacts in GitHub. If interrupted, inspect
python-full-result.json/process and complete remaining qualification; never claim
Android or writable DR. Original branches must remain unchanged.

## Live qualification handoff (reporting only)

c.1 normal-pushed/remote matched4d1758ddac926853ffc43ae9b1aee428ab63bccf;
fresh git fetch of feature/FETCH_HEAD confirms same commit and archive SHA
b7904a82c55e41866b374ecb42b873a6796a4f8e5e53a213f648e026467a64a3.
Full Python started2026-10-25T10:54:20.952148+00:00, frozen commit4d1758d.
Private runner/workdir /workspace/work/phase4/run-full.py,
python-full-result.json and python-full.log. Source fingerprint includes all
asc/tests/consensus/scripts/tools/install.sh, packaged guides and candidate bytes.
Only nonpackaged reporting docs can change. Current result RUNNING, NOT ACCEPTED.
If process/Cloud environment is lost, fresh rerun is needed; do not infer PASS
from this handoff or partial log. Expected287 unique cases,0 skips required.
No source changes are pending. After actual full PASS, verify frozen hashes,
fault groups, secrets and remote, update acceptance and normal-push final report.

## First full failure / diagnostic handoff (no source/test edits)

First full on4d1758d was interrupted after an ERROR in original3D fault matrix
following group06 (no07–09). Full did NOT PASS; interrupted owned synthetic test
processes only, exit-2 after519.918s, source fingerprint unchanged. Partial log
python-full-first-interrupted.log/result preserved privately; original failing
traceback was not emitted before interruption, so no specific cause is claimed.
Standalone unchanged `python -B -m unittest tests.test_external_faults -v` then
**1PASS0SKIP0FAIL57.558s, all9 actual fault groups**. This does not replace full.
No test/source/timeout/assertion/guard changed, no weakened gate or fake success.
Next fresh standard full uses unittest fail-fast `discover -s tests -v -f` so a
repeated failure preserves traceback immediately. PASS still requires all287,
all original faults and unchanged frozen source/candidate. If failure recurs,
investigate it before acceptance. Current NOT ACCEPTED; original branches intact.
