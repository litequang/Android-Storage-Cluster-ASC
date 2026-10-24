# Android Storage Cluster (ASC) — v0.9.0 development

Vietnamese project and historical setup guide: [README-VI.md](README-VI.md).
Current Phase 3A evidence and limits: [PHASE3A-ACCEPTANCE.md](docs/PHASE3A-ACCEPTANCE.md).

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
