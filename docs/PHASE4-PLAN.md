# Phase4.0 — Core/Demo integration and Quick Join foundation

Working branch feature/phase4-core-demo-integration from verified/fetched Core3D
ca2504fa3bc9f2eef706cdf50ddf6835182ada53; Demo reference
c9c2660b5aad9fe347cb0b216f0d691144f74caa. Preserve BOTH original branches and Core
WIP acea2ae. No whole-branch merge, main baseline/reset/force/history rewrite.
Mandatory ordered docs plus3D acceptance/progress and Demo4D acceptance/QuickStart
were read during audit; common unchanged text reused, branch additions compared.

## Confirmed architecture / compatibility matrix

|Boundary|Core3D|Demo0.4.1|Phase4 decision|
|---|---|---|---|
|Runtime|Opt-in actual-term quorum runtime; guarded original registry +runtime cache|Dedicated marked single-writer state, no automatic failover|Keep modes separate; Dashboard/Quick Join only Demo single-writer in4.0|
|Schemas|registry4/manifest1/runtime2 +3A/3B/3C extensions|demo1/registry4/manifest1/cache1/config1/wire1; refuses advanced state|Same schema integer does NOT prove interchangeable authority; no state migration|
|Identity|Cluster/epoch/voter binding, per-endpoint auth, original frozen SQL|Stable installation/cluster/node/volume identity, split controller/node homes|No adoption/copy of Core or recovery state into Demo; no identity regeneration|
|Common modules|Registry/server/CLI/client/identity/CatalogService/StorageHTTP/manifest and Go modules|Byte-identical at verified references|Reuse existing services/protocols, not another Catalog/Storage/enrollment engine|
|Storage|Original POSIX root-open walk|Approved-root descriptor patch in volumes.py and engine.py|Port ONLY reviewed storage patch +its tests; run Core3D and GC regressions against it|
|Browser|No Dashboard|Owner HTTPS/CA/session/CSRF +existing transfers/views|Port same Dashboard, preserve trust and read-only node approval|
|External backup/DR|Independent format1 backups, anchored verify, passive recovery staging|Not exposed by Demo runtime|Preserve all external modules/tests/docs; no new Demo routes/authority for3D|
|Upgrade|No new base schema in3D; writer recovery BLOCKED|Immutable code, stopped full private backup, exact formats, journaled code selection|Candidate0.4.2-dev, no public release; qualify exact0.4.1 archive upgrade/code-only rollback|
|Qualification|238 Python/11 Go historical Linux synthetic PASS|246 Python/11 Go historical Linux synthetic PASS; Android NOT TESTED|Fresh combined regression; never reuse either old full as new integration evidence|

## Approved sequence / publication gates

-4.0a: audit/contract/ADR062, plan/progress/acceptance, existing identity/device/
 baseline compatibility tests; docs/secrets, commit/normal feature-only push/remote.
-4.0b.1: allowlisted Demo modules, public assets, launcher, private-state-safe
 installer/upgrade, original Demo fixtures/archives/docs, reviewed storage patch.
 Preserve Core3D module/handler and original tests. Validate exact source provenance
 and targeted compatibility BEFORE checkpoint. No merge or wholesale doc replacement.
-4.0b.2: Quick Join owner Dashboard, API and local guided node adapter. May split
 b.2a backend/CLI and b.2b UI/browser for reviewable independently tested pushes.
-4.0c: exact published0.4.1 ->candidate upgrade/new-state rollback/pending resume,
 fresh full Python +all old fault gates, Go tests/vet/modules/builds, package SHA/
 secrets, accurate acceptance/guide and final feature push/remote verification.

After EACH complete checkpoint: targeted PASS/fix, CODEMAP/contracts/progress,
 tracked AND index contents/secrets review, normal feature-only push, compare
 advertised remote with HEAD BEFORE next. Full source freezes before final run;
 reporting only afterward. If interrupted, read AGENTS/this/PROGRESS/ACCEPTANCE.

## Quick Join contract

Owner browser retains existing manually trusted HTTPS CA, Secure/HttpOnly/SameSite
session, exact Host/Origin and CSRF, no CORS. Node pairing code is separate from
Dashboard LOGIN code. New owner-only POST /api/v1/quick-join/pairings {} creates a
Core existing600s one-use enrollment grant; returns pairing UUID/code/expiry and
Controller origin/full pin/cluster. GET same path/<id> reports waiting/registered/
expired/revoked/unknown and separate storage/domain approval. Maps are session-
bound RAM only (8/session,32global); only code hash retained after POST, never raw
node/admin/transfer token/code in logs/URL/sessionStorage/localStorage. Restart/
logout invalidates tracking; do NOT claim it revokes an underlying still-live code.
GET never reveals the code. Registry remains sole durable pairing/enrollment state.

Local `quick-join` runs AFTER verified install +explicit Demo init. Missing/unmarked
state => setup instructions, not auto-adoption/init. Preflight device/prefix/journal/
mode, private endpoint, full TLS pin and expected cluster BEFORE secret submission.
Use Core existing durable _enroll through a subprocess with ASC_HOME set before
imports (no global patches). Add minimal optional expected-cluster validation
using existing expected_cluster_id pending field; keep legacy CLI/wire/pending
formats unchanged. Hidden code input; optional explicit replacement code preserves
same enrollment operation/token. Network/ACK/crash ambiguity keeps pending and
reports resume-required. Existing identity is retained; unavailable current proof
stays UNKNOWN, never a false network-confirmed registration. No auto re-pair.

Enrollment !=storage readiness. Do not create volumes/start services/approve node/
physical domain automatically. Return registered/pending-approval and explicit next
CLI steps; owner confirms failure domain through existing approve CLI only.
A mode adapter must explicitly select supported marked Demo single-writer. Refuse
Core quorum/unknown modes/schemas/recovery markers before writes; never fallback.

Native app contract reuses pinned Core /api/v1/info +join with locally durable
private enrollment context. Owner/PWA uses browser session facade only. Browser
cannot silently persist Termux node credentials; future native/local engine bridge
is a prerequisite, NOT implemented/promised here. No APK/PWA worker/QR scanner/
cloud/discovery/failover/GC or writable-DR implementation in4.0.

## Compatibility, tests and future phases

Port static allowlist only; shared source changes limited to reviewed volume
adapter +Engine calls and minimal expected-cluster CLI check. No other Core3D/
consensus/business behavior edits. Original238 Core +38 Demo cases give combined
baseline276 before new QuickJoin cases. Historical03/04 ->04.1 archive assertions
stay attached to exact historical artifacts; add separate candidate tests rather
than weakening old version/asset checks for new UI. Existing release archives and
SHA files remain byte-identical. Candidate version0.4.2-dev is NOT a public release.

Test: one-use/concurrent/expired code, lost ACK/restart/same operation, pin/cluster/
mode/schema mismatch, user/session/rates/CSRF/XSS/TLS, no node auto-approval, no token
leaks, pending/identity preservation, missing/offline volume/Controller, real browser
file SHA/replica fallback, all Core3A–3D references/physical gates. Exact0.4.1
backup/readback/stage/preflight/upgrade, old/new data and NEW-backup code-only
rollback; unsupported downgrade refused. No stale DB restore. Only publish proved
upgrade paths; Windows/Android cross-build !=runtime acceptance.

Future4.1: app/local-engine interface and Core quorum UI adapter qualification;
4.2: Android Keystore/SAF and explicit tested migration contract; later APK/device
pilot. Termux UID/private paths/medium identity differ from APK sandbox: no promise
of preserving state/keys/IDs without tested migration. Single-writer->Raft and
writable DR need independent authority/fencing/key recovery qualification.

## Safety / rollback

No phones/M51/production/SSH, packages/Boot/root/format/system-trust changes.
Keep GC default absent and all guards; no quorum creation/membership change,
fake fencing or runtime on RECOVERY_READ_ONLY staging. Core3D writable recovery
remains BLOCKED. Linux synthetic only; actual Android/real media/CA UX/power-cut
not accepted. Stop all local services, NEW complete private state+approved-volume
backup/readback, compatible code selection only; preserve current state/data/
identities/keys and external backups/staging. Never restore old DB over new bytes.
## Current Phase4 closure track — 2026-10-27

This document's original4.0 audit below stays historical. The current continuation
reuses that Core-first integration plus completed4.1 private bridge/read-only
observer and4.2 native Node work; no whole Demo merge or second Catalog/Engine.

- Native5 candidate: original signer, Core Python Engine/Agent, encrypted context,
  actual TLS/enrollment, controlled Node/FGS and UI/observer. Final transport API30
  targeted28+foreign1, downgrade refusal/readback and normal retained network2PASS.
- Web/PWA: fixed manifest/icons/network-only worker and install UI on the shared
  Dashboard. Real Chromium criteria and independent install/launch/uninstall PASS
  on Linux; no cached catalog/files/offline writes or browser process bridge.
- Final gates: preserve failed full attempts; strengthen backup fault readiness
  with actual two-domain SHA proofs before cohost loss, not relaxed Core authority.
  Full4 on16c0717 FAILED184/1ERROR; resolve original GC target before new full384.
  Preserve archives/APK4. Keep APK5/exact Controller as audited INTERNAL DEBUG
  REVIEW snapshot with known failed gates, never label qualified release. Verify
  remote bytes independently. A qualified release still requires full PASS.
- Scope remains internal candidate. Native APK is a Node, Controller remains
  QuickStart/Termux or Linux. No native file backend, Termux-state adoption, Android
  voters/GC/failover/writerDR or Phase5 remote access. API30 emulator is not ARM64/
  physical-domain/LAN/OEM proof; API35 fresh cold remains blocked and new5 transport
  on35 NOT TESTED. Full Phase4 acceptance still requires owner device gates.

PHASE4-STATUS/HANDOFF and PHASE4-2-PROGRESS/ACCEPTANCE own the latest scoped result;
PHASE4-WEB-APP documents browser use. Resolve current GC blocker/full qualification, then
owner-controlled ZTE/Bphone pilot before broader acceptance or Phase5. No SDK/
state/guard workaround to mark missing phone evidence PASS.
