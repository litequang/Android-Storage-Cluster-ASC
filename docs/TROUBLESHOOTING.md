# ASC TROUBLESHOOTING

| Symptom | Likely cause | Safe action |
|---|---|---|
| `getprop` missing on Windows/Linux | Probe is designed for Termux; other OS uses fallback | Run from Android Termux for hardware names; unknown telemetry is okay |
| `M51 PRODUCTION PROTECTED` | Hosting safeguard | Only `bash install.sh audit`; do not bypass without separate agreed deployment design |
| Termux path `~/storage/downloads` missing | Storage permission not established | `termux-setup-storage` after checking existing Termux app; Android Settings permissions |
| SD `not_tested` | Private app-specific directory absent or write probe not requested | Do not conclude card unwritable; later SAF bridge may be needed |
| `SERVER CERTIFICATE PIN MISMATCH` | Wrong controller fingerprint / MITM / regenerated controller certificate | Abort; recheck PIN via local `controller-pair`. Never disable pin verification |
| Join `invalid_or_expired_code` | Token expired/consumed/typo | Create a new `controller-pair` on controller; one-time by design |
| Agent heartbeat cannot reach controller | WLAN/IP changed, service closed, firewall, certificate mismatch | Verify LAN address and that controller-run is active; do not expose port to Internet |
| Already joined | Local identity preserved; re-run install doesn't add node | `python3 -m asc.cli status`; don't delete node.json for a retry |
| No quorum/failover yet | Raft has **not** been implemented | v0.4 only supports one controller; no production data should rely on HA claims |
| Lost `controller.json` or `node.json` | Secret/identity loss | Stop, restore private backup or controlled re-enrollment; no automated recreation/override |
| `Certificate verify` errors | Client needs exact 64-digit SHA256 PIN | Copy PIN exactly from controller; this build uses pinning instead of CA |

Never copy a live MariaDB database directory from M51 as a backup. This release does not access M51 hosting data.

## Windows v0.4.1 fixes — owner reports 40 tests OK (skipped=3)

- `FileNotFoundError: [WinError 2]` at certificate generation meant the external OpenSSL
  CLI was unavailable on PATH. Python's `ssl` module does not supply `openssl.exe`.
  `require_openssl()` now checks PATH first and raises actionable DependencyError.
  `make_cert()` invokes the resolved executable as one argv element (including paths
  with spaces), without a shell or insecure TLS fallback. If the executable disappears
  or OpenSSL fails, diagnostics stay generic; preserve partial TLS files for review.
- On this development machine `C:\Program Files\Git\usr\bin\openssl.exe` exists but
  was not in the current PATH. See README section 8 to add the verified bin directory
  in your own PowerShell session, then run Get-Command openssl / openssl version.
  No dependency was installed and no global PATH was changed by Codex.
- TLS tests are NOT skipped when OpenSSL is missing. Lifecycle TLS setup checks the
  dependency before allocating its temp directory and registers class cleanup even
  if later setup fails. Mocked dependency tests do not replace real TLS/pin tests.
- Migration fixture `with sqlite3.connect(legacy) as db` only committed/rolled back;
  it left the connection open. Windows therefore refused temp-file deletion (WinError 32).
  The fixture now uses outer contextlib.closing plus an inner transaction, with explicit
  cursor close calls. Registry.connect already commits/rolls back and closes in finally;
  migration SQL, schema 2, IDs and token semantics are unchanged.
- Regression assertions cover closed connection/cursor objects, rollback on exception,
  and immediate rename/delete with Python references still alive, without gc.collect,
  retry sleeps, forced garbage collection or suppressed PermissionError.
- Git may report dubious ownership because local .git was created by the sandbox user.
  Use per-command `git -c safe.directory=E:/CODE/ASC-QuickStart ...` for this explicitly
  trusted workspace. Do not add wildcard trust or alter global Git config. No previous
  local repository/history existed. Main/origin were prepared for the now-authorized
  v0.4.1 publication; inspect actual git status/log to determine publication state.

The earlier owner run reported 30 tests, 3 errors, 3 skipped. The new owner run is
40 tests OK (skipped=3): only POSIX installer cases are unavailable on Windows.
Source/tests are unchanged in the subsequent docs/workflow publication update, so no
redundant rerun is required. This is an owner result, not a Codex-executed run.
Current AGENTS permits local test/typecheck/lint/build: targeted tests after code
changes, then the full applicable suite before Phase completion. Keep TLS cases active,
do not weaken tests, and report concrete blockers. Android trials remain deferred.

## Phase 1.1 (0.4.1) operator errors

These entries supersede older v0.4 instructions where behavior changed. Admin CLI
now needs a running Controller; detailed commands and rollback are in README sections 2–9.

| Symptom | Meaning | Safe action |
|---|---|---|
| M51 PRODUCTION PROTECTED / DEVICE IDENTITY UNKNOWN | Protected hardware, missing Android identity or SDK below 24 | Audit only; do not override, do not install on M51 |
| Missing dependencies | Installer made no package changes | On confirmed non-M51 test phone manually install listed Python/OpenSSL packages; never pkg upgrade for ASC |
| Installed release differs | Installer preserved old source | Stop old runtimes, back up private state, use explicit separate release directory |
| controller-pair/nodes cannot connect | Admin now uses authenticated pinned loopback HTTPS | Start controller-run in another terminal; never paste admin token into flags |
| 429 rate_limited | Join budget (8/IP,60 global/min) or auth failures (12/IP,120 global/min) | Wait 60 seconds, check credentials privately; no restart-to-bypass workflow |
| 400 bad_request / 413 payload_too_large | Invalid schema/version/text/frame or body >64KiB | Use supplied CLI; do not share raw secret-bearing requests |
| credential_rejected_repair_required, agent stopped | Revoked/rotated/invalid token; no automatic reenrollment | Keep node.json, issue targeted code on Controller, stop old agent, node-repair |
| status active but node revoked remotely | status is last observation/cache | Run agent-run --once to authenticate; cache is not present authority |
| Pending enrollment after network failure | Private retry operation retained | Repeat same node-join/node-repair; do not delete pending or start another identity |
| Initial pending code expired / retry window elapsed | Need a fresh grant while preserving operation identity | controller-pair (general), repeat node-join with original destination/PIN plus --new-code; same operation maps to same ID |
| Targeted pending grant replaced/expired | Old grant no longer authorizes re-pair | Fresh controller-pair --node-id ID, then node-repair --new-code; recovery copy retained |
| Pending operation differs | Origin/pin/cluster/target do not match saved request | Preserve state; verify correct Controller. Lost initial identity: targeted node-repair with full IDs/PIN and --new-code |
| already running or lifecycle operation in progress | OS lock held | Ctrl+C in owning terminal; do not delete .lock or kill an arbitrary PID |
| .lock file remains after exit | Normal reusable lock path | status tests the actual OS lock, not file existence |
| foreground field is null | Runtime lock state could not be read/verified | UNKNOWN; check private HOME permissions without guessing whether a process is running |
| Unsupported registry/config/profile version | Newer/incompatible schema explicitly rejected | Use matching release; do not edit version numbers to bypass validation |
| Migration cluster identity mismatch / registry missing | State inconsistent/lost | Stop, restore complete private backup; no new identity/DB over existing state |
| SD status unknown | No visible readable candidate | Not proof of no card or zero capacity; no SD root writes; SAF remains future work |
| SD probe fail | Small app-folder write/readback/fsync/delete failed | No writable-tested claim; cleanup is attempted only on its unique probe file; inspect that app folder manually if media removal prevents cleanup |
| New CLI enrollment to v0.4 Controller refused | Retry-safe enrollment requires Phase 1.1 server | Upgrade Controller first; existing v0.4 agents/tokens still heartbeat upgraded server |

Malformed legacy scores are ignored for advisory ordering without rewriting saved
profiles. New malformed profiles are rejected; no score grants voter/Controller rights.

If an initial operation was already revoked/rotated, a new general code cannot recover
its authority: use a fresh targeted re-pair grant. No duplicate-registration guarantee
can identify a phone after ALL identity/pending material is lost; an admin must select
the existing node and use controlled re-pair, never blindly enroll a second identity.

Old v0.4 Controller code cannot write schema 2 and does not understand revoke. Rollback
requires the complete stopped-state backup made before upgrade, per device, plus old
source. Preserve Phase 1.1 state separately. Restoring old state may re-enable compromised
tokens; keep LAN isolated and do not claim a safe downgrade if those secrets leaked.

## Phase 1.2A storage diagnostics

| Symptom | Meaning / action |
|---|---|
| storage_root_not_empty / unsafe_storage_root | Use a new empty explicitly approved directory outside source/private manifest ancestors; never adopt a user folder or follow a junction |
| unapproved_sd_root | Root must descend from an actually detected existing Termux app folder; discovery/status proposes candidates only; SAF is unimplemented |
| volume_identity_changed | Card/root/marker differs, including a reused mount path. Preserve both media/state. Do not recreate marker, alter stored identity or bypass verification; review stopped state and restore matching media |
| volume_unavailable / VOLUME_UNAVAILABLE | Restore original root/media/permissions; unknown space is null. Restart/verify when original medium returns |
| quota_exceeded / insufficient_space (507) | Pending upload reserves staging + final copy. Retained staging and orphan objects remain charged. Keep configured free-space reserve; no automatic deletion to make room |
| upload_interrupted / INTERRUPTED | Resend full body with same session/idempotency key. No byte-range/chunk resume. Interrupted or checksum-failed body is never listed as a file |
| upload_deadline (408) / storage_busy (429) | One transfer per engine; body deadline 60 + size/rate seconds plus bounded socket read timeout. Retry after the current transfer finishes; do not increase limits blindly |
| NEEDS_REVIEW / object_conflict | Commit may have a final/partial object, or grant changed while copying. Preserve staging and final. No automatic removal/adoption; compare stopped manifest/size/hash before an explicit recovery plan |
| MISSING / CORRUPT / METADATA_CONFLICT | Startup/verify found missing bytes/hash/reference disagreement. Preserve remaining copies and manifest; do not edit paths/version to make a false success |
| forbidden (403) | Wrong node/volume/operation, expired/revoked grant or old node generation. Mint a fresh owner grant only after reviewing active identity; node token is not a user grant |
| authorization_unavailable (503) | Restore Controller reachability and correct out-of-band pin. Never disable pinning or use an offline auth bypass |
| storage already configured / existing TLS files | Preserve identity. Repeated setup does not replace config/certificates; partial initialization needs explicit recovery, not deleting keys |
| storage-status says already running | Local inspection/cleanup uses the same engine ownership lock. Stop the development Agent first, inspect, then restart; authenticated network listing remains available |

Local inspection: python -m asc.cli storage-status (stopped Agent) performs a tiny actual read/write/hash/fsync probe and bounded object inventory; it does not adopt orphan objects. storage-cleanup --older-than 86400 previews eligible staging; add --apply only after review. Committed files/final objects are never GC'd. Changed quota/kind on re-register conflicts; live quota editing is deferred.

For repeatable Windows checks use docs/PHASE1-2A-ACCEPTANCE.md. Missing OpenSSL executable remains an error, not a TLS skip. SQLite registry/manifest contexts close in finally, including exceptions; stop runtimes before copying/restoring private DB/WAL/volumes. Rolling schema 3 back requires the original complete stopped-state backup and matching old release, not a PRAGMA edit.

Windows TLS early rejection: a small oversized JSON body could trigger WinError 10053 while the client was still sending, hiding HTTP 413. Handler now discards at most 128 KiB within a bounded 2-second/1-second-read budget before rejecting; payload is never parsed or accepted. Larger/malicious streams are closed without unbounded draining.

write_denied: the root identity marker was readable but the write probe received access-denied/read-only. writable=false and fsync_tested=null; the Backup label is a read-only archival-source suggestion, not eligibility as a writable backup target or proof of any replicated copy.
