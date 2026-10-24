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
| DEMO.1 | Installer preview targeted checks PASS; publication follows final review |
| DEMO.2 | NOT STARTED |
| DEMO.3 | NOT STARTED |
| DEMO.4 | Deferred behind initial CLI package / owner pilot; optional UI |
| Demo source-ready | NOT QUALIFIED; Android runtime NOT TESTED |

## Next action

Publish/remote-verify DEMO.1, then implement DEMO.2 LAN runtime/CLI. Reuse existing Core functions; do not enable Raft/GC or change
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
