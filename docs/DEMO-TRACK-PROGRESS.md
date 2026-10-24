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
| DEMO.0 | Audit/plan/progress ready; docs checks and normal Demo push follow review |
| DEMO.1 | NOT STARTED |
| DEMO.2 | NOT STARTED |
| DEMO.3 | NOT STARTED |
| DEMO.4 | Deferred behind initial CLI package / owner pilot; optional UI |
| Demo source-ready | NOT QUALIFIED; Android runtime NOT TESTED |

## Next action

Publish/remote-verify DEMO.0, then implement DEMO.1 guarded preflight/immutable
installer/package. Reuse existing Core functions; do not enable Raft/GC or change
Core guards. Read DEMO-TRACK-PLAN for architecture, risk and upgrade contract.
Each checkpoint must record changed files, exact actual tests/results, hash/push
verification, current functionality, limits, rollback and short usage. Package
must be tested and SHA-verified before publication, with unpacked secret review.

Known gaps: old installer has fixed destination/version-only comparison; old
controller-run binds wildcard; one ASC_HOME cannot cohost Controller and enrolled
Storage Node. Dedicated Demo wrapper/private subhomes solve these without a Core
rewrite. Android/SD/Doze/real-device runtime remain owner acceptance, never inferred
from Linux fake-getprop tests or Android cross-build. No major environmental blocker.
