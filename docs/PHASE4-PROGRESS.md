# Phase4.0 progress — account-independent handoff

Branch feature/phase4-core-demo-integration, Core baseline ca2504fa3bc9f2eef706cdf50ddf6835182ada53,
Demo reference c9c2660b5aad9fe347cb0b216f0d691144f74caa, common ancestor acea2ae.
Both fetched/advertised refs match; initial working tree clean. No Phase4 branch
existed; new feature created from Core, no merge/reset/old-branch edits.

|Checkpoint|State|
|---|---|
|4.0a|PUSH/REMOTE VERIFIED5d15cb71dc07e0e31b7b9da68e4aea85178e3847;16 targeted PASS|
|4.0b.1|READY: selective port95PASS0skip0fail290.653s; normal push gate follows|
|4.0b.2|NOT STARTED: owner Dashboard +guided CLI, may split backend/UI|
|4.0c|NOT STARTED: exact04.1 candidate upgrade/rollback +fresh full qualification|

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
