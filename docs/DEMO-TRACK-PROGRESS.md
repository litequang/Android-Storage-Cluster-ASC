# ASC Demo Track progress / account-independent handoff

Updated: 2026-10-24 (Asia/Saigon).
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
| DEMO.3a | Targeted PASS / source checkpoint publishing; full gate/package in DEMO.3b |
| DEMO.4 | Deferred behind initial CLI package / owner pilot; optional UI |
| Demo source-ready | NOT QUALIFIED; Android runtime NOT TESTED |

## Next action

Publish/remote-verify DEMO.3a after final 13 targeted cases, then DEMO.3b fresh full Python/Go qualification, final candidate package verification and acceptance. Do not mark source-ready until those gates PASS. Reuse existing Core functions; do not enable Raft/GC or change
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
