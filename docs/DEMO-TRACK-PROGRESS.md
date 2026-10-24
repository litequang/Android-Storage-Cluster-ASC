# ASC Demo Track progress / account-independent handoff

Updated: 2026-10-24 UTC.
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
| DEMO.4 | Deferred behind initial CLI package / owner pilot; optional UI |
| Demo source-ready | YES: Linux synthetic only; Android runtime NOT TESTED |

## Next action

Final hardened source aaf7d16: 14 targeted PASS and fresh full **222 PASS / 0 SKIP**.
Final 0.3.0 source package/checksum and acceptance PUBLISHED/REMOTE VERIFIED at
52850b9072241ab4bb7643b06127965d25d96904; actual GitHub download SHA verified. Next functional step is OWNER-only ZTE/Bphone pilot using
DEMO-QUICKSTART and blank DEMO-ANDROID-PILOT. DEMO.4 remains deferred. Reuse existing Core functions; do not enable Raft/GC or change
Core guards. Read DEMO-TRACK-PLAN for architecture, risk and upgrade contract.
Each checkpoint must record changed files, exact actual tests/results, hash/push
verification, current functionality, limits, rollback and short usage. Package
must be tested and SHA-verified before publication, with unpacked secret review.

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
