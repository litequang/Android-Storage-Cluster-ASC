# ASC CODING CONTRACT — MANDATORY FOR CODEX

## First reads, ALWAYS in order
1. `AGENTS.md` (this document)
2. `docs/CODEMAP.md` (ownership, path to modify)
3. `docs/ARCHITECTURE.md`
4. `docs/DECISIONS.md`
5. `docs/NODE_PROTOCOL.md`
6. `docs/DATA_MODEL.md`
7. `docs/SECURITY.md`
8. `docs/TROUBLESHOOTING.md`
9. `docs/CHANGELOG.md`

After reading maps, inspect only relevant source files, not the whole repo unless a broad change truly requires it.

## Non-negotiable user rules
- M51 is production web hosting. Codex has SOURCE ACCESS ONLY: no production DB/logs, live file inspection, edits or SSH. No modification of AMH, MariaDB, ports, service management, existing Termux or Termux:Boot.
- Codex may proactively run tests, typecheck, lint and build in the local development environment.
- After source changes, Codex must run the relevant targeted tests. Before completing a Phase, run the full applicable suite.
- Investigate and fix failures until the applicable checks pass, or report a concrete blocker. Never skip, delete or weaken tests merely to obtain PASS.
- Optimize work by running targeted checks first and the full suite afterward. An explicitly supplied owner PASS may be reused when source/tests have not changed; document its provenance and any platform skips.
- Local isolated loopback/test fixtures are allowed. Never run production servers, installers on real phones, operations changing real user data, or access production-phone databases/private state. Do not install/change system environments without authorization.
- Never root, wipe, format SD, delete or uninstall Termux; never silently overwrite keys or identities.
- Never claim Raft consensus, automatic failover, distributed file durability, or production readiness before actual implemented code and fault-injection acceptance tests prove it.
- No shared node passwords/secrets, public SFTP or management ports. All network writes must authenticate; HTTPS must be pinned or trusted.
- A missing telemetry value is UNKNOWN, not 0, not a guessed runtime measurement. Manufacturer specifications are merely baseline estimates.

## Current Android Demo Alpha task — separate Demo Track

The owner now authorizes `feature/android-demo-alpha` from verified Core WIP HEAD
(at least acea2ae), independent of Core. After ordered reads, read IMPLEMENTATION_PLAN,
PHASE3C acceptance/progress, README-VI, DEMO-TRACK-PLAN and DEMO-TRACK-PROGRESS.
Complete DEMO.0 then 1/2/3 with targeted PASS, documentation/secret/package review,
normal Demo-only push and remote verification before each next checkpoint. Reuse
single-writer components with separate Demo state, explicit private LAN binds and
upgrade compatibility; never enable Android Raft/failover/physical GC or weaken
M51/unknown-device guards. Dashboard Lite may follow the first CLI package; no APK,
3D or public access. Codex has source/Linux-synthetic scope only; owner alone will
try the tested checksum-verified package on actual ZTE/Bphone/XZ3. Keep all Core
modules/tests and Core branch intact. Earlier task scope below is historical.

## Current DEMO.4d authorization — Android storage /0.4.1

Owner now authorizes shared storage adapter/engine correction ON DEMO BRANCH from
verified ef6470d. Follow ordered reads + Demo plan/progress/DEMO4-ACCEPTANCE/
QuickStart, then DEMO4D-PLAN. Reproduce '/' denial while approved private root is
readable; preserve identity/no-follow/race/fsync gates, no path/permission bypass.
Complete4d.1 storage,4d.2 actual synthetic runtime/browser,4d.3 exact published0.3
AND0.4 direct-upgrade/backup/rollback/full qualification/package with each targeted
PASS/docs/secrets/normal push/remote verification before next. Old Core-source-
unchanged reports are historical; do not push Core WIP or change other Core logic.
4d.1 remote5050a79 (61PASS),4d.2 remote72bc61d (36+1PASS). Current4d.3
status in DEMO4D-ACCEPTANCE/progress; exact03/04 upgrade tests implemented, final
full/package gates pending. Follow dedicated DEMO-ZTE-0.4.1 owner guide after
qualified publication; code downgrade brings old Android defect back.
Preserve published archives/state/IDs/TLS/UI; no phone/M51/production/GC/Raft/
failover/3D access or activation. Android diagnostics supplied by owner do not
qualify the new runtime; only owner later tests ZTE/Bphone. Old-source rollback
may restore original Android write_denied bug; never recreate volume/identity.

## Current DEMO.4 authorization — Dashboard Lite / 0.4.0

Owner explicitly authorizes DEMO.4a backend, 4b frontend, 4c compatible QuickStart
0.4.0 on feature/android-demo-alpha from verified 2d19eb0. After ordered documents
read Demo plan/progress/acceptance/QuickStart/pilot and DEMO4-PLAN. Implement and
target-test each checkpoint, update contracts/CODEMAP/progress, secret review,
commit/push/remote verify before next. Reuse sole Controller Catalog/transfer logic;
owner-only browser session, trusted HTTPS, CSRF/XSS/traversal/body limits. No Core
admin/node/key in browser, no Dashboard approval unless separately proved (current
design read-only node admin). Preserve 0.3.0 compatibility/IDs/keys/volumes and test
exact old package upgrade/rollback. Full Python/Go and checksum package before final
source-ready. Old Dashboard deferral below is historical, superseded by this task.
DEMO.4a is remote-verified 5db17ae, DEMO.4b remote-verified 8e4661b. Current
DEMO.4c full qualification/package status lives in DEMO-TRACK-PROGRESS and
DEMO4-ACCEPTANCE; do not reuse historical0.3 PASS as current evidence.
DEMO.4c final Linux qualification now PASS: frozen956bf8e source/packaged guides,
230 Python0skip/all8 physical fault gates,11 Go/vet/modules/builds,22 targeted and
3 exact-archive installer checks.0.4 public archive/checksum normal-pushed and
remote/download-SHA verified at aa1a834; read DEMO4-ACCEPTANCE and final publication receipt
in DEMO-TRACK-PROGRESS;0.4 QuickStart source-only, Android/real browser CA trust UX
NOT TESTED. Next step after verified publication is owner-only pilot, no pending
source gate/reimplementation. Preserve0.3 archive and exact upgrade/code rollback.
No real phone/M51/production/boot/system packages, Raft/GC/reduction/3D/public access
or consensus change. Browser integration uses isolated trusted-CA synthetic profile;
never disable TLS validation to claim PASS. Android runtime remains NOT TESTED.

## Demo Alpha first CLI handoff — Linux synthetic source-ready

DEMO.0/1/2/3a/3a.1/3b completed on feature/android-demo-alpha. Final implementation
source/tests aaf7d163fbac032bb31a033efe2ebb21406509bf: 14 targeted PASS, fresh
full 222 Python PASS/0 skips, all eight Linux GC gates, unchanged-source 11 uncached
Go/vet/modules/Linux build/Android cross-build PASS. Read DEMO-TRACK-PLAN/PROGRESS/
ACCEPTANCE, DEMO-QUICKSTART and blank DEMO-ANDROID-PILOT after mandatory docs.
Qualified source-only 0.3.0 package and SHA live in releases/. Git history/progress
identifies publication commit; Core WIP remains acea2ae, Core modules/tests unchanged.
Android runtime/real SD/Doze/power-cut/production NOT TESTED; owner alone tries the
phones. Codex remains SOURCE/Linux-synthetic only, no M51/phone/production/GC/Raft
activation. DEMO.4 deferred for initial CLI handoff. No pending mandatory source
acceptance gate remains after publication receipt; next step is owner manual pilot.
Keep compatible identities/bytes; migration/DB restore/mixed versions unsupported.

## Current Phase 3C task — authorized isolated-test development

Phase 3C is now authorized from `b1b46e527826617748a8bc68795259060e12d705`
on the same WIP branch. After ordered docs and Phase 3B handoff, read
`docs/PHASE3C-PLAN.md` and `docs/PHASE3C-PROGRESS.md`. Every checkpoint must
pass its checks and be pushed/remote-verified before continuing. Physical GC is
default disabled, isolated-test only, and forbidden on real devices/production.
Preserve all version/snapshot/job/history references and the last readable copy;
use copy-before-retirement and current quorum/term fencing. No 3D, Dashboard,
phone/M51/production or voter/membership change. Earlier phase scope below is
historical and does not cancel this explicitly authorized Phase 3C task.

## Phase 3C.5 completed handoff — Linux synthetic only

Phase 3C is ACCEPTED for Linux x86_64 isolated synthetic qualification. Final
source/tests: `8b679bc42077ab68f6bb00063f13e744fa171258`; fresh full 208 Python
PASS (0 skips), all mandatory legacy/new physical faults, 11 uncached Go tests,
vet/module verification and Linux/Windows/Android builds PASS (cross-builds only
for Windows/Android). No source/test changes after the successful final run.
After the mandatory ordered reads, read PHASE3C-PLAN, PHASE3C-PROGRESS and
PHASE3C-ACCEPTANCE. Final docs-only reporting commit is identified by Git history.
No unfinished mandatory Phase 3C checkpoint remains. Fetch/verify WIP and preserve
local work before any later explicit task. Ordinary runtime issues no GC capability
or executor; real-device/Android/production GC remains locked. No 3D/Dashboard,
phone/M51/production or voter change is authorized by this completed handoff.

## Phase 3B handoff — v0.10.0

After the mandatory ordered reads, read `docs/PHASE3A-ACCEPTANCE.md`,
`docs/PHASE3B-PLAN.md`, `docs/PHASE3B-PROGRESS.md` and
`docs/PHASE3B-ACCEPTANCE.md`. WIP branch is `wip/phase2a-raft-qualification`;
Phase 3A base is `0550967f57f145ff75179c20500e4aafe9c5cb31`. Fetch GitHub and
preserve local work; never use main/reset/force push to continue. Every checkpoint
must pass targeted checks, update progress, undergo tracked/staged secret review,
commit/push and remote verification before starting the next checkpoint.

Phase 3B is qualified for Linux Cloud synthetic simulation only. Product failover
entrypoint still permits Windows development only; test launchers do not authorize
real Linux/Android/phone deployment. Scores/preferences never change voter/quorum
or grant byte proof. Drain does not move data. Reduction is preview only; no
physical GC, Phase 3C/3D or Dashboard is authorized by the Phase 3B handoff.
Historical scope below is not the current feature list; consult current CODEMAP/
CHANGELOG/acceptance. Respect separate task authorization before future phases.

## Historical scope in v0.6.0 / Phase 1.2B
Working: prior lifecycle/local storage plus single-writer Global Catalog, approved physical-domain placement, durable scoped replication jobs, verified read-only metadata snapshot/delta caches, bounded reconciliation and download fallback.
Phase 1.2B Codex Windows acceptance: 92 tests OK (3 POSIX installer skips); see docs/PHASE1-2B-ACCEPTANCE.md for provenance, three-node simulation and limits. Historical 1.2A gate was 61 tests.
NOT working: Raft/consensus, automatic Controller failover/election, Dashboard/mobile/cloud integration, SAF, production or Android/power-cut readiness. Cache replication is not write authority or proof of file bytes. Phase 2 requires its own explicit task.

## Documentation update discipline
After EVERY source change:
- Update `docs/CODEMAP.md` if functions, responsibility, source files or entrypoints changed.
- Update `docs/ARCHITECTURE.md` for runtime or component boundary changes.
- Append/modify ADR in `docs/DECISIONS.md` only for changed important technical choices.
- Update `docs/NODE_PROTOCOL.md` when request/response/authentication contracts change.
- Update `docs/DATA_MODEL.md` when persistence schema changes.
- Update `docs/SECURITY.md` and `docs/TROUBLESHOOTING.md` for relevant new risks and resolved errors.
- Append an entry in `docs/CHANGELOG.md` for each user-visible feature, schema migration, behavior/compatibility change or significant bug fix.
Do NOT touch unrelated docs or auto-generate giant maps; keep accurate module-to-function routing.

## Before marking work finished
Explain: changed source/documentation files, behavior, risks, rollback, exact check commands, actual results and blockers. Distinguish Codex-run checks from owner-supplied results and state why any applicable checks were not rerun.
Before publishing, inspect tracked AND staged paths/content for secrets (ignore rules alone are insufficient), preserve remote history, and push only within explicit authorization. Report commit hash and verified push status.
Use versioned API/schema, backward compatibility and idempotent changes; avoid silently overwriting installed agent code. Preserve credentials under private HOME, outside repo.
