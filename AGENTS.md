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

## Scope in v0.5.0 / Phase 1.2A
Working: all v0.4.1 node lifecycle features plus opt-in local volumes/manifest, pinned owner-authorized streaming storage, immutable commit/download/integrity, conservative recovery, staging expiry and capability heartbeat.
Phase 1.1 Windows acceptance: owner-reported 40 tests OK (skipped=3 POSIX installer). Phase 1.2A source changes require new Codex-run checks; see docs/PHASE1-2A-ACCEPTANCE.md for actual results and platform limits.
NOT working: distributed/global file catalog, multi-node consensus, automatic election, replication/backups, PWA, VPN gateway, SD SAF bridge or M51 production integration. No Android/physical power-loss readiness is claimed. Phase 1.2B needs its own explicit task.

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
