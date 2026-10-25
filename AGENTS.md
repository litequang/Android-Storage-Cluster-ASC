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

## Current Phase4.0 authorization — Core-first selective integration

Owner authorizes feature/phase4-core-demo-integration from Core3D ca2504f, selecting
reviewed Demo c9c2660 modules ONLY. Never merge whole Demo or push original Core3D/
Demo/WIP/main. Mandatory docs then PHASE3D acceptance/progress +Demo4D acceptance/
QuickStart (read via pinned Demo ref before port), PHASE4-PLAN/PROGRESS/ACCEPTANCE.
Complete4.0a audit,4.0b selective port +owner Dashboard/guided node CLI (split as
needed),4.0c exact04.1 upgrade/rollback +fresh full and Go/fault/security gates.
Each checkpoint targeted PASS/docs/secrets/normal feature push/remote before next.
Reuse existing Registry/Catalog/Storage/enrollment; no parallel authority system.
UI only Demo single-writer first; Core3D preserved including passive recovery.
Writable DR remains BLOCKED: no writer/quorum/epoch/fencing reconstruction or staging
runtime. No phones/M51/production/SSH/root/format/system packages/Boot changes,
GC/failover/Raft unlock, APK or untested migration. Source +candidate0.4.2-dev only,
not a public Android release. Historical earlier no-Dashboard language below is
superseded ONLY for this explicit bounded task. Read current Phase4 handoff.

## Current Phase 3D authorization — separate external DR branch

Owner authorizes feature/phase3d-external-dr from fetched Core acea2ae; preserve
Core WIP and Demo c9c2660 branches. After mandatory ordered reads, read
IMPLEMENTATION_PLAN, PHASE3A/3B acceptance and PHASE3C plan/progress/acceptance,
then PHASE3D-PLAN/PROGRESS/ACCEPTANCE. Implement3D.0/1/2/3/4 sequentially; each
checkpoint requires targeted PASS/docs/CODEMAP/secrets/normal feature-only push
and remote verification before next. No reset/force/main merge or Demo changes.
3D.0/1a/1b/2/3/4a are normal-pushed/remote verified (PHASE3D-PROGRESS).
Frozen source/tests50df5d79e1759cf5755d416d53c4bc47cc74e49b: fresh full238 Python
PASS0skip/all original faults +all9 new3D groups;54 targeted and Go11/vet/modules/
builds PASS. Acceptance normal-pushed/remote+fresh-fetch verified at
f4dae0bcdf0fb9343f14eba00c0a05f223978588; published source fingerprints match full.
Only final receipt reporting follows; no source drift.
External backup/anchored verify/passive recovery Linux scope ACCEPTED, Phase3D
PARTIALLY COMPLETE; full writable DR NOT ACCEPTED/BLOCKED. No unfinished source
gate after final report remote proof. Next separate platform/authority qualification,
not redo3A–3C or create a writer. Android/Windows runtime/real media NOT TESTED.
External independent bytes+metadata, anchored verify, immutable complete bundles,
resume and isolated READ_ONLY recovery; no source deletions/GC credit. Missing
writer/fencing/identity recovery proof => explicit partial scope, never new epoch,
quorum or Leader. Historical3C no3D language below is superseded by this task.
No phones/M51/production, system/root/format changes, GC/Raft unlock, membership,
Dashboard/PWA/APK/remote access. Existing Phase3A–3C tests/guards remain intact.

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
