# ASC Demo Track progress / account-independent handoff

Updated: 2026-10-25 UTC.
Branch: `feature/android-demo-alpha`.
Core base: `acea2aead8cfd50f8a8fc2b31e24f8f9ccaeb84c`.

## Verified start

- Fetched explicit WIP ref, local/advertised WIP HEAD match acea2ae, clean tree.
  Demo branch did not exist locally/remotely; created from verified WIP HEAD.
  Core branch remains untouched. Existing Cloud handoff draft stash retained.
- Ordered AGENTS/CODEMAP/architecture/ADR/protocol/schema/security/troubleshooting/
  changelog, roadmap, 3C acceptance/progress, README-VI and local/distributed
  acceptance read; actual installer/lifecycle/volume/Catalog code audited.
- Cloud environment: enforced unrestricted HTTP policy, inherited proxy/CA kept;
  no VPN/real-phone/production access. Existing activation:
  `/workspace/asc-cloud/activate.sh`, Python 3.13.5 / Go 1.27.3.
- 208 Core Python / 11 Go PASS belongs to accepted Core source, not fresh Demo evidence.

## Checkpoints

| Checkpoint | Actual state |
|---|---|
| DEMO.0 | PUSHED/REMOTE VERIFIED: 2b877ff6f4312110447e817210815794b2f84d87 |
| DEMO.1 | PUSHED/REMOTE VERIFIED: 789ea8f9675c3339287eace1486126bd886c17e3 |
| DEMO.2 | PUSHED/REMOTE VERIFIED: ae299c7981cd683cf61966c7ed64cfb05e557c51 |
| DEMO.3a | PUSHED/REMOTE VERIFIED: 597b3ff52e7ce58dc5d2bf7d505d5c35fe038380 |
| DEMO.3a.1 | PUSHED/REMOTE VERIFIED: aaf7d163fbac032bb31a033efe2ebb21406509bf |
| DEMO.3b | PUSHED/REMOTE VERIFIED: 52850b9072241ab4bb7643b06127965d25d96904 |
| DEMO.4a | PUSHED/REMOTE VERIFIED: 5db17aef375b5ebfd03ce680a3b0a52c3a993f99; 35 targeted PASS |
| DEMO.4b | PUSHED/REMOTE VERIFIED: 8e4661bbccc9c6b11e451e414907d190a55a799c; 21 targeted PASS |
| DEMO.4c.1 | PUSHED/REMOTE VERIFIED: 956bf8ebb23e57b07d4ec91cefec8d89539a8327; 22 targeted PASS |
| DEMO.4c | Full 230 Python/11 Go/all 8 Linux fault gates PASS; final package publication/remote review |
| Demo 0.4 source-ready | YES: Linux synthetic only; Android runtime NOT TESTED |

## Next action

DEMO.4 implementation and Linux synthetic qualification are complete from frozen
956bf8ebb23e57b07d4ec91cefec8d89539a8327. Full230 Python0skip, all8 Linux physical
fault gates and11 Go/vet/modules/builds PASS; exact0.3 upgrade/old-code new-state
rollback and final archive installer PASS. Final0.4 archive/SHA/receipt are below;
complete normal publication/remote verification before owner uses it. Then owner
alone follows DEMO-QUICKSTART (5a browser/CA,6a stopped0.3 upgrade/rollback) and fills
DEMO-ANDROID-PILOT with actual ZTE/Bphone observations. No Android or manual client
CA-install UX PASS is implied. Codex remains source/Linux-synthetic only. No pending
mandatory source gate remains after verified publication; do not redevelop Core3C.

Known gaps: old installer has fixed destination/version-only comparison; old
controller-run binds wildcard; one ASC_HOME cannot cohost Controller and enrolled
Storage Node. Dedicated Demo wrapper/private subhomes solve these without a Core
rewrite. Android/SD/Doze/real-device runtime remain owner acceptance, never inferred
from Linux fake-getprop tests or Android cross-build. No major environmental blocker.

## DEMO.1 evidence and handoff

Source: asc/demo/{__init__,package,installer,cli}.py and scripts/demo-alpha.sh.
Tests: tests/test_demo_installer.py; Core tests/test_installer.py unchanged.
Docs: QuickStart, CODEMAP, architecture, data model, security, troubleshooting,
changelog and progress; public installer-preview archive + checksum in releases/.

Actual Linux command: `source /workspace/asc-cloud/activate.sh; python -m unittest
tests.test_demo_installer tests.test_installer -v`: 6 PASS, 0 skips. Tests execute
extracted source and installed launcher in fake Android HOME, check deterministic
archive/file hashes, corruption refusal, dry-run/no mutation, exact rerun/private
state retention, M51/unknown/missing-dependency/unmarked/symlink refusal. Initial
launcher pycache defect found and fixed before PASS. No phone/package mutation.
Archive publication is installer-only, NOT the final cluster QuickStart Package.
Rollback: stop using preview launcher; preserve code/state, no database is created.
Usage: verify adjacent archive SHA, extract NEW directory, follow DEMO-QUICKSTART.
Git push uses the already authenticated gh credential helper for that command only;
no proxy/CA or stored credential changes. Core remote remains acea2ae.

Installer preview archive SHA-256:
`65e8dd503bebbf93c1d4efe3805e67bc120974e80de29411a30057f119eaa14f`.
77 public files; package checksum PASS from releases/ directory; package members
reviewed for private paths, links/special entries and credential material.

## DEMO.2 evidence / continuation

New source asc/demo/state.py and lan.py; expanded CLI/package state contract.
New tests/test_demo_lan.py; Core sources/tests unchanged. CODEMAP, architecture,
ADR-055, protocol/data/security/troubleshooting/changelog/QuickStart updated.
Actual targeted commands (activated Python 3.13.5):
- `python -m unittest tests.test_demo_lan tests.test_demo_installer
  tests.test_distributed -v`: 20 PASS / 0 skips (54.564s), including 15 unchanged
  distributed regressions.
- Final Demo-only run includes 3 LAN + 3 installer cases after guard refinements.
  6 PASS / 0 skips in 19.613s (demo2-six.log, Linux synthetic).

Actual subprocesses use separate fake Android HOME/properties and pinned HTTPS
loopback sockets, real file bodies/SHA and two distinct synthetic phone roots; ZTE
cohosts Controller/node in separate subhomes. Tested: two physical copies, same-key
retry, stopped-node download, preserved existing output, degraded count, no new row
when only one eligible domain; same-domain identities, missing actual volume,
double-copy quota refusal, wrong pin, owner-token isolation, blocked admin grant/
policy/GC surfaces, Controller loss rejecting a previously issued actual node grant.
Future schema/consensus state, wildcard/public binds, M51 and unknown runtime
refused without identity recreation. No physical object GC, policy reduction or
Raft runtime launched. Rollback: Ctrl+C, retain complete Demo state and matching
release; no schema change. Old installer preview remains immutable, intentionally
has no LAN capability. Final owner package waits for DEMO.3/full tests. Android
runtime/real SD/background/power-cut remain NOT TESTED.

## DEMO.3a upgrade implementation (full acceptance still pending)

Source: new asc/demo/upgrade.py; installer/CLI/LAN/state/package/version refinements.
Tests: new tests/test_demo_upgrade.py includes inherited LAN fault gates intentionally
rerun through installed launchers, plus compatible upgrade/code rollback, complete
private backup/readback, future/installer-only refusal, running-process refusal,
interrupted actual pointer/journal recovery, identities/certs/volume bytes, redacted
diagnostics, external approved synthetic directory-volume and copy-mutation failure.
Docs: CODEMAP, architecture/data/security/troubleshooting/changelog/owner QuickStart.

Initial installed-launcher tests exposed prefix ancestry refusal and a node re-exec
source lookup gap; fixed without weakening guards. Restart test exposed legitimate
Core catalog_inventory_cursor missing from compatibility allowlist; explicitly
allowed it while rejecting other extension/consensus settings. Complete backups
preserve empty staging/objects folders and external approved volumes. No automatic
data/schema restore or APK/Raft migration. Keep all state/releases on refusal.

Actual intermediate targeted runs: 12 PASS/0 skips (59.012s) for installed upgrade
plus source LAN/installer; external volume and concurrent mutation case 1 PASS
(3.884s). Final combined 13-case run follows final source/QuickStart freeze. Linux
synthetic only; no Android runtime/real SD/background/power-cut qualification.
Rollback: stopped code-only rollback with NEW complete private backup; explicit
recover-upgrade after PREPARED verifies unchanged state and returns old code.
Usage: docs/DEMO-QUICKSTART.md now has full owner preparation/controller/cohost/node/
TLS/domain/upload/download/stop/backup/upgrade/rollback/diagnostic sequence. Final
package MUST wait for DEMO.3b acceptance; old preview remains installer-only.

Final frozen DEMO.3a command:
`python -B -m unittest tests.test_demo_installer tests.test_demo_lan
tests.test_demo_upgrade -v`: **13 PASS / 0 SKIP / 0 FAIL/ERROR, 65.492s**.
Includes malformed journal refusal, stale backup recovery refusal, traversal refusal
and original identity/file preservation after source upgrade/code rollback.
Candidate source-only package built outside repository for DEMO.3b, not released:
81 public files, release ID
`1b89251efe77dbff5de531ab055ed1e99a3ce351a819a13737df35801dd5714c`,
archive SHA `3510d37f9e54feb4884f9ed7f78b31891f9974bbd79ae73b06e0a21f5c878603`.
Deterministic build/unpacked secrets/inventory/README/checksum review PASS.
No full regression PASS claimed yet. Candidate source frozen; if changed, retest
and regenerate candidate. Next: fresh full 221 Python expected (208 Core + 13 Demo),
uncached Go tests/vet/modules and applicable Linux/Android cross-build; record exact
actual counts/results, inspect/copy final public package and publish DEMO.3b.

## DEMO.3b durable in-progress handoff (not a completion claim)

597b3ff52e7ce58dc5d2bf7d505d5c35fe038380 was pushed normally and advertised
remote HEAD verified before starting full qualification. Core remote still acea2ae.
Fresh full Python is running in this Cloud workspace, output
/workspace/work/demo3b/full-python.log, exec session 29010. If that session is gone
or completion evidence absent, rerun full suite; do not infer PASS from progress.
No implementation/packaged-guide change since frozen 13-case targeted PASS.

Go completed fresh: all modules verified, vet PASS, 11 uncached top-level tests
PASS (consensus 19.489s, launcher 0.003s), Linux AMD64 build and Android ARM64
cross-build PASS. Android binary is not launched by Demo; cross-build not runtime
qualification. Exact final candidate byte-for-byte matches deterministic rebuild
and was executed for dry-run/install/launcher/rerun/identity sentinel preservation/
tamper refusal in isolated fake Android HOME, PASS. AST: 102 tracked Python parse.
Core source/tests/Go verified unchanged against acea2ae. See provisional
DEMO-TRACK-ACCEPTANCE.md for actual fault matrix, candidate SHA and commands.
Full Python has no reported failure at this snapshot, but still RUNNING.

This reporting update changes docs only; it reuses the unchanged-source 13-targeted
PASS, checks links/whitespace/secrets, and intentionally does NOT release candidate
or mark DEMO.3b done. Next account should finish/rerun full 221 expected Python,
record actual result, reverify deterministic candidate SHA/public contents, copy
archive+checksum into explicitly allowlisted releases/, update acceptance/progress/
AGENTS/CHANGELOG, secret-review, commit/push Demo and verify advertised remote.
DEMO.4 deferred as authorized for initial CLI handoff.

## DEMO.3a.1 — final-review lock safety correction

Initial fresh full on source 597b3ff: **221 PASS / 0 SKIP / 0 FAIL/ERROR, 1444.112s**.
All eight Linux GC gates 01–08 plus prior Core acceptance/fault suites actually ran.
Before final publication, an added fault exposed a symlinked lifecycle lock writing
a space to an outside empty test-owned file before backup refusal (expected
regression FAILED before fix, 3.540s). No real device/data or release deployment.

New asc/demo/locks.py checks no-follow/regular/single-link/inode/content before
coordination writes, then reuses Core OS primitive. Demo wrappers and internal-lock
state preflight use it; Core source is unchanged. New test checks root/controller/
agent/engine/prefix symlinks and hardlinks preserve outside bytes. Full acceptance
is reset to NOT QUALIFIED until fresh full suite on hardened source (222 expected).
Old candidate SHA above is retired, never released. Preview 0.1.0 is historical,
not recommended; new prefix procedure and owner-only blank Android pilot now in
docs/DEMO-ANDROID-PILOT.md (also included in final candidate).

After final 14 targeted PASS, secret review and this source checkpoint push/remote
verification, rerun full Python. Existing uncached 11 Go/vet/module/build PASS may
be reused: Go/Core source identical; this correction affects Demo Python only.
Regenerate/inspect final candidate, record actual fresh full result and archive SHA,
then publish final DEMO.3b. Do not use the earlier 221 PASS as final-source evidence.

DEMO.3a.1 final actual targeted command:
`python -B -m unittest tests.test_demo_installer tests.test_demo_lan
tests.test_demo_upgrade -v`: **14 PASS / 0 SKIP / 0 FAIL/ERROR, 69.640s**.
Hardened candidate (still NOT released) has 83 public files, release ID
`ab229efb9179d356f7b4f363d0a82fa40d33a53164ca215f7c2625be8aaaece8`,
SHA `3bf81c5d94891fa064e2f05f99d60d620b4c5db71c87bb2ee6c89ac72b9a445a`.
Next full log: /workspace/work/demo3b/full-python-hardened.log (must finish/rerun).

## DEMO.3b final actual acceptance — Linux synthetic only

Final implementation/tests aaf7d163fbac032bb31a033efe2ebb21406509bf was normally
pushed/remote-verified before the fresh full run. **222 PASS / 0 SKIP / 0 FAIL/ERROR,
1422.541s**, completed 2026-10-24 17:59:37 UTC, full-python-hardened.log. All eight
Linux physical gates 01–08 plus legacy Core regression/acceptance/faults actually
ran and PASS. Final 14 Demo targeted PASS (69.640s); exact hardened archive and
launcher rerun/readback/preservation/tamper checks PASS. 103 Python AST / shell
syntax / Core source preservation PASS. Go 11 uncached tests, vet/module verify and
Linux/Android cross-build PASS from this task remain applicable (Go source unchanged
by Demo-Python fix); no false rerun or Android-runtime claim.

Final package releases/asc-demo-alpha-0.3.0.tar.gz + .sha256, 83 public members.
SHA `3bf81c5d94891fa064e2f05f99d60d620b4c5db71c87bb2ee6c89ac72b9a445a`.
Content ID `ab229efb9179d356f7b4f363d0a82fa40d33a53164ca215f7c2625be8aaaece8`.
Exact archive/tree/README/pilot inventory and unpacked secrets review PASS. Earlier
81-file candidate is retired/never released; preview 0.1.0 historical only.

DEMO.3b changes: qualified public archive/checksum and narrow ignore exception;
final acceptance/progress/plan, AGENTS and CHANGELOG/CODEMAP handoff. No implementation
or packaged-guide change after final fresh full PASS. See acceptance for full test
matrix, source/Go preservation and qualification limits.

Now source-ready for manual Android trials ONLY; no Android runtime PASS. Controller
single-writer/no automatic failover, pinned LAN TLS, real two-copy SHA/fallback and
upgrade/backup/code-rollback work in Linux synthetic. GC/Raft/real devices remain
locked/outside Codex scope; no production/data-protection promise. Rollback/usage in
DEMO-QUICKSTART; owner blank pilot not populated by Cloud tests. Complete per-checkpoint
changed-file routes are in entries above and CODEMAP; exact filenames follow the
Git history (Core and its tests are unchanged). Publication receipt is appended
after normal Demo-only push and advertised remote HEAD/package verification.

## Verified GitHub publication receipt — COMPLETE first CLI source handoff

DEMO.3b publication commit: **52850b9072241ab4bb7643b06127965d25d96904**.
Normal push succeeded; advertised feature/android-demo-alpha remote HEAD matched
that exact hash. Core WIP remote remained acea2aead8cfd50f8a8fc2b31e24f8f9ccaeb84c.
No force/reset/history edit/main merge or real-device access occurred.

Downloaded the archive from the immutable GitHub raw URL at that exact commit
through inherited network/TLS policy, 141336 bytes, then compared bytes and SHA-256
with the tested local publication: PASS,
`3bf81c5d94891fa064e2f05f99d60d620b4c5db71c87bb2ee6c89ac72b9a445a`.
No proxy/CA changes, network bypass, installer package mutation or secret exposure.

| Checkpoint | Published commit / verification |
|---|---|
| DEMO.0 audit/plan | 2b877ff6f4312110447e817210815794b2f84d87, remote verified |
| DEMO.1 installer preview (historical, not recommended) | 789ea8f9675c3339287eace1486126bd886c17e3, remote verified |
| DEMO.2 LAN | ae299c7981cd683cf61966c7ed64cfb05e557c51, remote verified |
| DEMO.3a upgrade-safe implementation | 597b3ff52e7ce58dc5d2bf7d505d5c35fe038380, remote verified |
| In-progress handoff | cb37dd42d78bedba70818d10317cc167e38189f0, remote verified |
| DEMO.3a.1 final lock hardening | aaf7d163fbac032bb31a033efe2ebb21406509bf, remote verified |
| DEMO.3b final acceptance/package | 52850b9072241ab4bb7643b06127965d25d96904, remote + downloaded package SHA verified |

No implementation/packaged-guide changes follow final 222 PASS. This receipt updates
reporting only and reuses that unchanged-source qualification; docs/whitespace/
tracked+index secrets are checked before its normal push and remote verification.
The receipt commit is the subsequent Git history entry, not an additional feature.

34 changed files through DEMO.3b (Core source/tests/Go untouched); obtain exact
per-checkpoint file lists with `git show --stat COMMIT` and aggregate with
`git diff --name-only acea2ae..52850b9`. Routes/files are recorded above/CODEMAP.

Next: OWNER follows docs/DEMO-QUICKSTART.md and blank docs/DEMO-ANDROID-PILOT.md
for ZTE/Bphone (optional Sony). Verify package SHA BEFORE extraction; keep all
existing private state/source and use new prefix if historical preview exists.
Stop all foregrounds before backup/upgrade/code rollback. No automatic DB/data
restore or APK/Raft migration. Android remains NOT TESTED until owner evidence;
Codex has no phone/M51/production/GC activation authorization. DEMO.4 Dashboard Lite
remains deferred, no pending mandatory source acceptance gate for first CLI package.

## DEMO.4a backend — actual implemented / targeted evidence

New asc/demo/dashboard/{auth,tls,views,http,runtime,__init__}.py, expanded Demo
Controller/CLI/state; new tests/test_demo_dashboard.py. Core modules/tests/Go and
Core branch unchanged; 0.3.0 public archive preserved. Node approval remains CLI.

Explicit stopped `dashboard-init --port 8444` creates separate private browser CA
and leaf with IP SAN, preserving Core/node certs. Export ONLY public CA through
`dashboard-trust --out NEW_HOME_FILE`, verify SHA out of band and trust manually
on owner client. `run-controller --dashboard` opts in; `dashboard-code` prints a
one-time private login grant over existing pinned owner admin API. No default
password/HTTP/TLS bypass or public bind. UI assets not implemented until 4b.

API uses process-local bounded owner sessions, Secure/HttpOnly/SameSite cookie,
Host/Origin/CSRF, rate/body/worker/transfer limits. Sanitized nodes/capacity/files/
replicas reuse Registry/Catalog. Unknown stays null; same physical domain counts
once. Upload prepares existing replicated_2 job and uses private bounded spool
with actual byte counter/full SHA before unchanged pinned client forwarding;
download reuses fallback and verifies whole spool before serving. No Core secrets,
grants or private paths returned to browser. No new persistent Catalog/schema.

Actual command (activation Python 3.13.5 / Go 1.27.3):
`python -B -m unittest tests.test_demo_dashboard tests.test_demo_installer
tests.test_demo_lan tests.test_demo_upgrade tests.test_distributed -v`:
**35 PASS / 0 SKIP / 0 FAIL/ERROR, 136.486s**. New tests use actual CA-verified
HTTPS: untrusted CA/wrong SAN fail, one-use login/cookie/CSRF/Origin/Host, token
isolation, two physical synthetic copies, SHA/fallback/idempotency, bad SHA, bounds
before body, ticket-session scope, traversal/disabled mutations, unknown capacity,
same-domain dedup, session invalidation after restart, public-CA export/no overwrite
and existing browser keys preserved. 14 unchanged Demo and 15 distributed tests PASS.

0.4.0 is not released/qualified; no browser UI/Android result claimed. Cloud has
Chromium 154, Playwright and certutil available for isolated trusted-CA real browser
4b tests, no dependency/system install needed. Rollback now: stop Controller and
restart without --dashboard (CLI-only), preserve optional private Dashboard files.
Existing source upgrade/code rollback remains stopped + NEW complete private backup.
Next checkpoint only after 4a normal Demo push and advertised remote SHA match.

## DEMO.4b frontend — actual targeted/browser evidence

4a normal push succeeded; advertised Demo SHA matched
5db17aef375b5ebfd03ce680a3b0a52c3a993f99 before 4b started. Core still acea2ae.
4b adds local Vietnamese mobile-first overview/node volume dialog/files/replicas,
owner code login/logout, exact backend byte progress, safe same-key upload retry,
WebCrypto download SHA before new browser save, UNKNOWN cache on disconnection.
Node approval stays CLI; no delete/GC/public API/cloud/CDN/extra database.
Approved unmeasured volumes keep their IDs with null metrics; truncated totals
remain UNKNOWN. Package allowlist includes and hashes three local web assets.

Actual final targeted command (Python 3.13.5, Chromium 154.0.8037.57):
`python -B -m unittest tests.test_demo_dashboard tests.test_demo_dashboard_browser
tests.test_demo_installer tests.test_demo_lan tests.test_demo_upgrade -v`:
**21 PASS / 0 SKIP / 0 FAIL/ERROR, 105.743s**; `node --check` PASS.
Real Chromium uses isolated HOME/NSS trust of only fixture public CA; untrusted
profile rejects TLS, trusted profile has normal certificate validation (no bypass).
Actual UI upload produces two distinct approved node/domain copies, literal HTML
filename cannot execute, Secure/HttpOnly/SameSite cookie is not JS-readable. Parent
stops the actual first replica node process; UI becomes degraded, fallback browser
download's saved bytes SHA matches, unsafe new upload refuses, browser network
loss sets UNKNOWN/disables writes and reconnect/logout works. No external requests
or page exceptions. Reviewed desktop 1280px and mobile 390px screenshots; no mobile
horizontal overflow. An initial browser assertion selected two matching SHA labels;
scoped it to download status; actual saved-byte SHA had already matched. No product
fault gate was skipped or TLS weakened.

4b ready for normal Demo-only publication after tracked/index secret review.
0.4.0 is NOT QUALIFIED/PACKAGED until 4c exact published-0.3 upgrade/rollback + fresh
full regression/package proof. Android/browser CA-install UX NOT TESTED. Rollback:
stop Controller, launch without --dashboard, retain all private state and bytes;
code rollback requires stopped cluster and NEW complete private backup.

## DEMO.4c.1 — compatible 0.4 source/guide checkpoint

4b normal push/advertised remote matched 8e4661bbccc9c6b11e451e414907d190a55a799c
before this checkpoint. Bumped source to0.4.0-alpha/dashboard-lite capability;
base state formats unchanged. Added exact published0.3 install/upgrade/new-state
old-code rollback test and updated QuickStart/blank owner pilot. Packaged sources
and two guides are frozen for full acceptance. Split 4c into this independently
resumeable targeted checkpoint and final 4c qualification/publication; no public
0.4 archive or source-ready claim yet.

Final targeted command: `python -B -m unittest tests.test_demo_dashboard
tests.test_demo_dashboard_browser tests.test_demo_release_upgrade
tests.test_demo_installer tests.test_demo_lan tests.test_demo_upgrade -v`:
**22 PASS / 0 SKIP / 0 FAIL/ERROR, 119.508s**. Syntax/shell/JS checks PASS.
Exact0.3 test also ran independently:1 PASS14.810s. Initial new-test helper shadowed
Python's http module; renamed helper before PASS, no product bypass. Old archive
SHA unchanged and checked at runtime. Old launcher stages/upgrades new release,
new code reads/writes real bytes, old code reads BOTH old/new files after rollback;
all IDs/keys/pins/certs/cluster/schema/browser private backup preservation pass.

Private candidate (NOT published yet):92 regular source/asset/guide/manifest files,
168292 bytes, release84849e9f1c269db1168d3adfa4f71fc0f720f92c5da63143c6d00811b9590277,
SHAb9e186589bb4f5c698c7df2250f94ec32ce1e6e2acb41cf3923ade9e706a29f1.
Unpacked public-content/path secret audit0 findings; full manifest matches frozen
source/guides. Historical0.3 archive retained. Final full230 Python + Go/vet/modules/
builds and exact-package install/public checksum remote proof remain PENDING.
Do not mark0.4 SOURCE-READY from these targeted results. If interrupted, fetch and
read AGENTS/DEMO4-PLAN/DEMO-TRACK-PROGRESS/DEMO4-ACCEPTANCE, preserve work, rebuild
candidate deterministically and finish remaining fresh full gates, then publish.
Rollback is CLI-only mode or stopped code-only0.3 with NEW complete private backup;
never stale DB restore, identity recreation or deletion of optional Dashboard state.

## DEMO.4c final qualification — running handoff

DEMO.4c.1 was normally pushed; advertised remote matched
956bf8ebb23e57b07d4ec91cefec8d89539a8327 before final qualification. Core WIP
remains acea2ae. Fresh Go1.27.3:11 top-level PASS (uncached, consensus20.037s,
launcher0.003s), go vet PASS, go mod verify all modules verified, LinuxAMD64 build
PASS and AndroidARM64 cross-build PASS (not launched/not runtime evidence).
Full Python230 cases now running from frozen956bf8e source/guides, no test changes
or physical-fault timing changes. If interrupted, full gates remain incomplete
until actual successful completion is recorded. Final archive stays private until
full PASS/exact-package verification; no0.4 source-ready claim yet.

## DEMO.4c — final Linux qualification / public package

Frozen source/tests/packaged guides956bf8e unchanged throughout full run. Fresh
`python -B -m unittest discover -s tests -v`: **230 PASS /0SKIP /0FAIL/ERROR,
1422.631s**, started2026-10-25T00:09:53.910328Z, completed00:33:36.679822Z.
All8 named Linux physical gates01–08 actually PASS, plus legacy lost-TLS-ACK unlink,
quorum/Leader loss, Phase3A history/snapshot/backup/restore,3B insights, replication,
Core consensus/failover/distributed/storage/installer/lifecycle. No skip, fake
success, guard removal, timeout relaxation or test weakening. Final22 targeted
PASS119.508s, exact final artifact3 installer PASS1.697s. Go11 fresh uncached PASS,
vet/modules and LinuxAMD64/AndroidARM64 builds PASS; Android cross-build only.

Final archive92regular source/asset/guide/manifest files,168292bytes. Release ID
84849e9f1c269db1168d3adfa4f71fc0f720f92c5da63143c6d00811b9590277.
SHA-256 **b9e186589bb4f5c698c7df2250f94ec32ce1e6e2acb41cf3923ade9e706a29f1**.
Full-tested source reproduced byte-identical archive after full PASS; every manifest
file matches frozen source/guide;112 tracked Python AST/shell/JS syntax PASS.
Unpacked public artifact review0 secret/private-path/link/special-file findings;
old0.3 archive/checksum still PASS and unchanged. Read DEMO4-ACCEPTANCE for exact
commands, source/file ownership, browser/upgrade evidence, limits and rollback.

Actual features: owner one-use login on trusted private-LAN HTTPS, Vietnamese mobile
Dashboard overview/nodes/volumes/files/replicas,32MiB upload with real observed byte
counts and Core replicated_2 jobs/key/SHA, safe new-download SHA/fallback, UNKNOWN
for stale/missing data/offline Controller. Core secrets stay server-side, no second
Catalog. Node approval/domain remains CLI. No Raft/failover/GC/reduction/3D/phone
access; runtime guards and Core source/tests/Go/WIP remain intact.

Rollback preserves state/identities/old+new bytes: stopped full cluster, NEW complete
private state+approved-volume backup, select preserved compatible0.3 release and
restart CLI-only (without --dashboard), keep optional Dashboard CA/keys. No stale
DB restore or identity recreation. QuickStart6/6a gives exact commands. Android,
actual client trust UX, SD/Doze/power-cut/24x7/production NOT TESTED. Final normal
Demo push/advertised remote/artifact download receipt follows below; until that
receipt the package is locally qualified, not yet verified published on GitHub.
