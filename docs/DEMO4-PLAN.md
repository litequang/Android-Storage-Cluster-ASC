# DEMO.4 Dashboard Lite — 0.4.0 continuation contract

Base/verified start: 2d19eb06cee1b6bede0fbafac9d4704704c039a9 on
feature/android-demo-alpha, clean tree and matching fetched remote. Core WIP untouched.
User now explicitly authorizes DEMO.4; earlier Dashboard deferral is historical.
Read mandatory ordered AGENTS documents, then Demo plan/progress/acceptance/QuickStart/
pilot. Source/Linux synthetic only; no phone/M51/production/Termux system changes.

## Checkpoints

| Checkpoint | Scope / gate |
|---|---|
| DEMO.4a | Optional Controller HTTPS backend, explicit separate CA/IP SAN, owner one-use code/session/CSRF, read-only node/capacity/replica views, bounded Core upload/download. Targeted + distributed regression, docs/secrets, commit/push/remote verify |
| DEMO.4b | Local Vietnamese responsive HTML/CSS/JS, overview/nodes/files/replicas, observed-byte upload progress, SHA download, real offline/error states. Real Chromium trusted-CA integration + mobile viewport/XSS/security, publish before packaging |
| DEMO.4c | Versioned 0.4.0 package/assets/guide, exact published 0.3.0 -> 0.4.0 upgrade and old-code/new-state rollback tests, full Python/Go/vet/module/builds, public package SHA/secret audit, final acceptance/push/download verification |

Split if necessary. Every completed checkpoint must pass targeted checks, update
CODEMAP/contracts/progress, review tracked/index/public package secrets, normally
push Demo only and compare advertised remote SHA before the next checkpoint.
No reset, force/history edit, main merge or Core branch write. Stop on proxy:8080.

## Architecture and safety decisions

- Separate optional HTTPS browser listener in the SAME Controller process, same
  service/Catalog/worker and existing pinned Core ClusterClient. No second Catalog.
  run-controller without --dashboard remains CLI-only; explicit stopped dashboard-init
  creates separate browser CA/leaf identity with numeric private-IP SAN. Original
  Controller/node certificates/pins/IDs remain intact. No HTTP fallback/wildcard bind.
- Browser users explicitly trust ONLY public Dashboard CA after out-of-band SHA
  comparison. Never click through TLS errors or import/distribute private keys.
  Codex imports public CA only in isolated synthetic browser NSS profiles, not OS/
  phone trust stores. Android/PC trust UX and real runtime require owner acceptance.
- Locally authenticated CLI dashboard-code uses existing pinned Core admin route.
  Random single-use 5-minute grants live hash-only in bounded Controller RAM; no
  shared/default password. Browser receives HttpOnly/Secure/SameSite=Strict host
  cookie (30 minutes), never Core admin/node/grant/key. Sessions die on restart.
  Same-origin Host/Origin/Sec-Fetch checks, per-session CSRF, fixed safe errors,
  bounded login/IP budgets/workers, no CORS/external assets, strict CSP/no framing.
- Node approval/domain changes stay CLI-only. Views whitelist fields, retain null
  for unknown/stale capacity, use measured approved volumes and Core's domain counts.
  Shared-domain/multiple-volume free space cannot be blindly summed. No AI scoring.
- Upload metadata prepares existing replicated_2 plan/idempotency/job before body.
  One bounded 32 MiB browser transfer at a time spools in private temporary storage;
  real received counts differ from SHA-verified bytes and protection. Rehash full
  input before forwarding through unchanged Core client. Same-key retry preserves
  jobs/bytes; progress never implies two copies. Backend can return pending/202.
- Download uses existing Core fallback + seekable private spool, checks SHA/size
  before HTTP output; browser verifies SHA before offering a new download. No user
  path, physical deletion, policy reduction or arbitrary object/file API.
- Root/base formats unchanged. Optional dashboard/dashboard.json format 1 and own
  CA/leaf keys are backed up by existing complete-state contract. Partial identity
  is preserved/refused; Controller CLI-only may continue without completed Dashboard
  config. Stopped source upgrade/code rollback preserves identities/volumes; exact
  0.3.0 archive is the compatibility fixture, not a simulated version label.
- No Android Raft/failover/GC, membership/consensus change, 3D, public access, APK,
  auto-update or device deployment. Android runtime/SD/Doze/power-cut NOT TESTED.

## Handoff

Keep existing 0.3.0 archive/checksum/acceptance. Final new guide covers stopped
upgrade from 0.3.0, CA export/trust on owner Android and PC, Controller --dashboard,
one-use login, file/replica/SHA workflow, logout/stop and code-only rollback with
NEW verified private backup. No automatic DB restore or trust-store modification.
