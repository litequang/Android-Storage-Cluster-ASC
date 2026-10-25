# Phase4.0 progress — account-independent handoff

Branch feature/phase4-core-demo-integration, Core baseline ca2504fa3bc9f2eef706cdf50ddf6835182ada53,
Demo reference c9c2660b5aad9fe347cb0b216f0d691144f74caa, common ancestor acea2ae.
Both fetched/advertised refs match; initial working tree clean. No Phase4 branch
existed; new feature created from Core, no merge/reset/old-branch edits.

|Checkpoint|State|
|---|---|
|4.0a|READY:16 targeted PASS0skip0fail0.173s; docs/whitespace checks PASS; normal push gate follows|
|4.0b.1|NEXT after4a remote proof: selective Demo/storage port +targeted compatibility|
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
