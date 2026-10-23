# ASC CODEMAP — Source routing (v0.4.1 / Phase 1.1)

Read `AGENTS.md` FIRST. This map describes present source; proposed distributed storage remains future work.

| Concern | Main files | Entry points | Tests / state |
|---|---|---|---|
| Android identity, fail-closed hosting guard, baseline/runtime distinction, SD states | `asc/probe.py` | `inspect`, `_detect_sd_locations`, `probe_sd_write` | foundation + lifecycle DeviceSafetyTests |
| Advisory roles; exclude revoked/protected/offline, tolerate legacy untrusted scores | `asc/planner.py` | `recommend` | foundation + lifecycle role cases; no authority |
| Bounded profile/name/code/envelope validation | `asc/validation.py` | `name`, `node_id`, `code`, `secret`, `profile`, `payload` | lifecycle validation/HTTP cases |
| HTTPS lifecycle API, generic errors, rate budgets, bounded workers | `asc/server.py` | `RateLimiter`, `Server`, `Handler.do_GET/do_POST`, `serve` | LifecycleHTTPTests, LimiterTests |
| Registry schema 2/additive v0.4 migration, closed transaction handles, grants/retry mapping, revoke/rename/re-pair | `asc/store.py` | `Registry.connect/initialize`, `add_pair_code`, `join`, `heartbeat`, `rename`, `revoke`, `detail`, `snapshot` | RegistryLifecycleTests |
| HTTPS pin before credentials, bounded response/errors | `asc/client.py` | `ClientError`, `request_json` | foundation + LifecycleHTTPTests |
| Private config, atomic updates, OpenSSL dependency diagnostics, TLS files | `asc/identity.py` | `DependencyError`, `require_openssl`, `ensure_private_home`, `save_private`, `replace_private`, `read_private`, `make_cert`, `fingerprint_from_pem` | `tests/test_identity.py`, ClientIdentityTests + real TLS suites |
| OS-held foreground locks/status | `asc/runtime.py` | `foreground_lock`, `running` | ClientIdentityTests |
| Controller init/run, authenticated local admin commands | `asc/cli.py` | `controller_init/run/pair/nodes/node/rename/revoke`, `_admin_request`, `_registry` | lifecycle + manual LAN |
| Node pending enrollment/recovery, explicit re-pair, rejected-token state | `asc/cli.py` | `_enroll`, `node_join`, `node_repair`, `agent_once/run`, `local_status`, `main` | ClientIdentityTests + manual LAN |
| Install without package mutation/implicit source replacement | `install.sh` | audit/controller/node | `tests/test_installer.py` (POSIX fake HOME) + manual Termux |
| Foreground launch, optional explicit code path | `scripts/run-controller.sh`, `scripts/run-agent.sh` | shell, `ASC_CODE` | manual duplicate start/stop |
| Release identifier | `asc/__init__.py` | `__version__` = 0.4.1 | installer release comparison |
| Local regression/acceptance (Codex + owner) | `tests/test_foundation.py`, `tests/test_lifecycle.py`, `tests/test_installer.py`, `tests/test_identity.py` | unittest discovery; explicit SQLite fixture/cursor closing and immediate file-release assertions | owner Windows: 40 tests OK, skipped=3 (POSIX installer); source/tests unchanged in publication update |
| Git publishing exclusions / authorized commit and push | `.gitignore`, `.gitattributes`, `README-VI.md` section 10 | audit tracked + staged paths/content; LF shell checkout; review diff; non-force push | v0.4.1 main publication authorized; report actual commit/push result |
| Operator dependencies, tests, Git preparation and deferred Android instructions | `README-VI.md` | sections 1–10 | Windows-first; phone install/rollback reference deferred |
| Runtime/design boundary | `docs/ARCHITECTURE.md`, `docs/DECISIONS.md` | implemented Phase 1.1 versus proposed target | no Raft/storage |
| Wire/persistence/security/errors | `docs/NODE_PROTOCOL.md`, `docs/DATA_MODEL.md`, `docs/SECURITY.md`, `docs/TROUBLESHOOTING.md` | implemented lifecycle sections | API v1 / registry schema 2 |
| Work scope and release history | `docs/IMPLEMENTATION_PLAN.md`, `docs/CHANGELOG.md` | Phase 1.1 | Windows accepted; Linux/Termux installer and hardware acceptance remain deferred |

## Lookup rules
- Enrollment/retry/re-pair: cli `_enroll` -> pinned client -> server validation/rate-limit -> registry `join`.
- Rejected heartbeat: cli `agent_run/agent_once` -> server auth budget -> registry `heartbeat/revoke`; do not remove identity.
- Admin commands: cli `_admin_request` reads only controller credential; server `_admin` then registry mutation.
- Migration/rollback: registry `initialize`, DATA_MODEL, README sections 7/9; never run old controller against schema 2.
- Device/SD unknown or refusal: probe `inspect`, installer hardware guard, SECURITY/TROUBLESHOOTING.
- Duplicate runtime: `runtime.foreground_lock`; status does not signal/kill processes.
- Windows TLS dependency: identity `require_openssl/make_cert`, `tests/test_identity.py`, README section 8; missing OpenSSL is an error, not a skip.
- Windows WinError 32: migration fixture in `tests/test_lifecycle.py`; use `closing(connection)` around the transaction and close cursors. Registry contexts already close handles in `finally`.
- Acceptance order: Phase 1.1 Windows accepted (owner: 40 tests OK, skipped=3); future v1.0 modules and Windows multi-node simulation precede Android installation trials.
- Test policy: `AGENTS.md` governs local targeted checks after code changes, then the full applicable Phase suite. Reuse owner PASS only for unchanged source/tests; keep platform skip reasons visible.
- Historical task prompts: `ASC-CODEX-PHASE1-1.md` and `CODEX-NEXT-PROMPT.md` follow current AGENTS test/publishing rules; they do not authorize starting Phase 1.2A in this publication task.
- Protocol changes require matching client/server/store tests and NODE_PROTOCOL updates.

## Still absent
No `consensus/`, `storage/`, `gateway/`, `dashboard/`, `backup/` modules, file catalog or file transfer.

