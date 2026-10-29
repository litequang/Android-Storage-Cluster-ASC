# Phase 4.1 — local engine bridge and Core quorum observability

Branch `feature/phase4-1-local-engine-quorum-ui` starts at fetched, advertised
Phase4.0 baseline `b9e75779670d5565d05a324751af02e48d2538eb`; initial tree clean,
no previous4.1 branch. Preserve Phase4.0/Core/Demo/WIP/main and every private state.
No merge/reset/force/history rewrite. Mandatory ordered documents plus Phase4
plan/progress/acceptance/Quick Join,3D acceptance and implementation plan read.

## Architecture / checked reuse

Existing `asc/demo/quickjoin.py` already validates marked state, pin/cluster/mode
and invokes Core durable enrollment in a private-HOME subprocess. Reuse it with
secret stdin, never a new enrollment engine or browser credentials. Existing
Catalog/Storage/Registry/volume guards remain sole implementations. Owner Dashboard
already has HTTPS/CA/Sessions/CSRF/CSP/Host/Origin and local assets: share those,
explicitly discriminate Demo versus read-only Core mode, never fallback to Demo SQL.
Core Runtime.view(strong=True) provides actual upstream Barrier; ensure_ready may
commit takeover and therefore MUST NOT be invoked by the new observation route.
Voter/Leader flags, process locks and heartbeats are observations, not writer proof.

## Checkpoints / serial publication gates

- 4.1a: versioned strict IPC contract + security threat model / process ownership /
  mode boundaries / Android future contract. Contract and historical compatibility
  targeted tests. Review, docs/CODEMAP, secrets, commit/normal push/remote proof.
- 4.1b: explicit private authorization provisioning, same-UID authenticated Unix
  socket, bounded request journal and real Quick Join adapter/status/lifecycle.
  May split b.1 IPC/read/join and b.2 controlled node lifecycle for reviewable gates.
- 4.1c: sanitized Core read-only observation endpoint, explicit pinned gateway
  adapter, shared owner HTTPS/session/assets and mode-dependent read-only UI.
  May split server/adapter and browser. Actual partition/quorum/stale/Controller
  loss/reconnect tests; no authority mutation/GC/membership/approval API.
- 4.1d: native app/migration contract, exact Phase4.0 candidate upgrade/code-only
  rollback/pending identity qualification, full applicable Python/Go/fault/security/
  build/package gates. Freeze source/tests/package guides before full; report only
  after it. No APK without a tested toolchain/runtime contract.

After EACH: targeted PASS/fix, related docs/progress, tracked+index/unpacked secrets,
commit, normal feature-only push and advertised HEAD match BEFORE next. On interrupt
read AGENTS/this/PROGRESS/ACCEPTANCE; no old full result substitutes new integration.

## Compatibility and package decisions

Keep all base state formats and historical0.3/0.4/0.4.1/Phase4.0 candidate archives
byte-identical. New source label0.4.3-dev is not an Android release. The old exact
04.1->Phase4.0 test now executes the frozen Phase4.0 archive, retaining its old
version/asset/exact-byte assertions; new4.1 compatibility gets separate tests.
Bridge control/auth/request journal and Core gateway config live in NEW dedicated
private roots outside Demo/Core/volumes/source. They are not Catalogs or migrations.
No node/cluster/volume identity is created by bridge setup, no stale DB restore.
Stop bridge/gateway/engine, fresh complete backup, compatibility preflight before
code selection; old source ignores separate bridge roots. Never copy SQLite to
convert modes. Phase4.0 candidate's supported upgrade/rollback remains preserved.

## Acceptance scope / risks

Linux synthetic actual UDS/peer creds, TLS, engine bytes, journal/ACK/crash and real
quorum partitions only. Same-UID local account trusted; not a hostile-admin sandbox.
Termux and APK have distinct UIDs: this UDS prototype does NOT grant cross-app access.
Native Binder/signature permission/Keystore/SAF/foreground service/Doze/network and
migration need Android4.2 implementation/device acceptance. PWA cannot start Termux
or own its keys/files. No phones/M51/production/system changes/SSH; no Android Raft/
GC/failover, writable DR, fabricated fencing/quorum/epoch or automatic approval.
