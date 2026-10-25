# Android Storage Cluster (ASC) — v0.10.0 development

Vietnamese project and historical setup guide: [README-VI.md](README-VI.md).
Historical Phase 3A Windows evidence and limits: [PHASE3A-ACCEPTANCE.md](docs/PHASE3A-ACCEPTANCE.md).

## Phase 3C Linux synthetic qualification

Dynamic replication, copy-before-retirement and guarded GC are qualified on frozen
source `8b679bc`: **208 Python tests PASS (0 skips)**, all mandatory faults and
Go/vet/module/build PASS. Evidence, timing/rollback limits and handoff:
[PHASE3C-ACCEPTANCE.md](docs/PHASE3C-ACCEPTANCE.md),
[PHASE3C-PROGRESS.md](docs/PHASE3C-PROGRESS.md).
Physical unlink runs only with issued fresh synthetic Linux temporary-volume
capabilities. Ordinary runtime has no executor/capability or normal enable switch;
real-device/Android/production GC remains locked. This is not a deployment or release.

## Phase 3A Windows development — version history and logical backups

Use matching v0.9 source on every development Controller and retain complete
pre-enable private backups first. The existing v0.8 opt-in runtime/Go sidecar is
required; default single-Controller and metadata-only modes retain old behavior.
Owner commands share existing pinned cluster-client.json configuration. Examples:

```powershell
python -B -m asc.cli backup-enable --request-id owner-enable-001
python -B -m asc.cli backup-history 'documents/example.txt'
python -B -m asc.cli backup-snapshot --copies 2 --request-id owner-snapshot-001
python -B -m asc.cli backup-jobs
python -B -m asc.cli backup-delete FILE_UUID --request-id owner-delete-001
python -B -m asc.cli backup-trash
python -B -m asc.cli backup-restore FILE_UUID --snapshot-id SNAPSHOT_UUID --request-id owner-restore-001
python -B -m asc.cli backup-schedule --interval-seconds 3600 --copies 2 --request-id owner-schedule-001
python -B -m asc.cli backup-policy 'documents/example.txt' --keep-last 3 --max-age-seconds 604800 --trash-seconds 604800 --request-id owner-policy-001
python -B -m asc.cli backup-run-retention --request-id owner-retention-001
```

Retain the same --request-id and arguments when retrying a lost response. Restores
create a new immutable version; they do not overwrite the source or current bytes.
A snapshot is UNVERIFIED until durable backup jobs independently hash enough
approved physical domains. Retention/trash expiry is logical; no physical bytes
are garbage-collected. Keep disconnected backups for irreplaceable data. Exact
contracts, limits, results and rollback: docs/PHASE3A-ACCEPTANCE.md.

## Phase 3B node insights — v0.10.0 Cloud simulation accepted

After all stopped development Controllers upgrade and complete private backups:

```bash
python -m asc.cli node-insights-enable --request-id enable-nodes-001
python -m asc.cli node-scores --consistency strong
python -m asc.cli node-history NODE_ID --window 30d
python -m asc.cli node-preference NODE_ID --mode drain --request-id drain-node-001
python -m asc.cli replica-reduction-preview FILE_ID --consistency strong
```

Owner-only pinned client; use the same request ID after a lost mutation reply.
Auto/Preferred/Avoid New Storage/Drain/Protected affect new allocation after hard
safety gates. Drain never moves/deletes existing bytes. Score/confidence are separate;
missing/stale sensors remain UNKNOWN. History is bounded UTC calendar 24h/7d/30d
with hourly samples and explicit gaps, not continuous uptime. Reduction is preview
only, with zero physical deletions and no apply command. Permanent receipt/runtime
limits still apply. Plan/progress: docs/PHASE3B-PLAN.md and PHASE3B-PROGRESS.md.

Phase 3B exact new Cloud results/limits: [PHASE3B-ACCEPTANCE.md](docs/PHASE3B-ACCEPTANCE.md). Windows runtime and real-device execution remain separate.

## Separate Android Demo Track

`feature/android-demo-alpha` builds on the accepted Core WIP branch, with a bounded
single-writer LAN CLI and immutable source/private-state separation. See the
[Demo plan](docs/DEMO-TRACK-PLAN.md), [progress](docs/DEMO-TRACK-PROGRESS.md),
[acceptance](docs/DEMO-TRACK-ACCEPTANCE.md) and [owner QuickStart](docs/DEMO-QUICKSTART.md).
Use only a checksum-verified package with completed Linux acceptance. Android
runtime is a separate owner pilot; no Raft/GC/M51/production qualification is implied.

## Dashboard Lite — Demo 0.4.0

DEMO.4 adds a Vietnamese responsive LAN browser view, upload/two replicas and SHA-verified download through the existing Demo Controller. Current qualification: [DEMO4-ACCEPTANCE](docs/DEMO4-ACCEPTANCE.md); follow [QuickStart](docs/DEMO-QUICKSTART.md) for explicit trusted HTTPS/owner login and stopped0.3 upgrade/rollback. Use only a published checksum-verified package after final Linux PASS; Android runtime is NOT TESTED. Core/Raft/GC guards remain unchanged.
