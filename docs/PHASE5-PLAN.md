# Phase5 — Remote Access & Production Qualification

Owner2026-10-28 authorizes continuing after Phase4 software qualification and
DEFERS physical-phone acceptance to a later combined campaign. Deferred is NOT
PASS or production permission. Baseline0877a15b0dd34f7c5db3b056bb912f89bb7be3af;
separate feature/phase5-remote-access, no original Core/Demo/Phase4 branch changes.

1. 5.0 access architecture/profile contract and negative tests; publish first.
2. 5.1 private HTTPS gateway reusing existing owner Dashboard/File Manager and
   Core read-only observer. Pinned upstream, exact external Host/Origin, existing
   owner cookie/CSRF, bounded streaming, explicit bind, no machine credentials.
   Split5.1a runtime/API qualification and5.1b browser/fault qualification.
3. 5.2 optional Cloudflare edge adapter only after separate edge identity/header/
   Access trust review and synthetic qualification. No live account/tunnel/domain
   changes without an explicit deployment task. Private gateway is NOT public-ready.
4. 5.3 maintenance contract over approved private connectivity: operator-controlled
   stopped backup/verify/stage/preflight/forward upgrade using existing engine.
   Standard private SSH may be documented separately; never public SSH/custom
   arbitrary shell API or APK/Termux UID/state sharing. No automatic remote update.
5. 5.4 integrated synthetic faults/security/compatibility and fresh applicable
   final gates. Phone/ARM64/real LAN/Doze/OEM/power/production acceptance DEFERRED
   BY OWNER; list separately, never implemented as unittest skips or fake PASS.

Gateway is access plane, not a new Registry/Catalog/Engine, Controller, authority
cache or recovery writer. Existing single-writer Demo remains one writer. Core
quorum/recovery observer stays read-only. No Raft/voter/GC/failover/DR unlock.
LAN remains functional independently of VPN/cloud. Node/storage/consensus/admin
ports are never public; first gateway exposes only existing browser file routes,
no enrollment, node approval, shell, GC or membership routes. 100.64/10 is an
approved-address class, not proof of Tailscale membership or remote reachability.

Gateway has independent private TLS identity/root; upstream leaf pin is operator
verified. Browser independently verifies public frontend CA. Owner login/session
remains in the existing backend. Gateway never reads backend DB/private admin/node
keys, creates catalog state, or claims writer authority. External same-origin checks
MUST precede fixed upstream Host/Origin translation. No forwarded-header trust.
Stop gateway for rollback; upstream state/sessions/IDs/bytes remain untouched.

Each checkpoint: targeted PASS, docs/CODEMAP/secrets, normal feature-only commit/
push/fetch/advertised remote verification before next. No live phones/M51/SSH/
production/system/network policy changes; all work source and synthetic Linux.

5.3 implementation: owner-local bounded plan1 +existing activation CAS, no remote
executor/listener. Qualify actual installed Controller/Node upgrade and NEW-state
code rollback, local lost-ACK/interruption/refusals and exact historical-source
compatibility. Live SSH/VPN and Android maintenance remain separate NOT TESTED.
5.4 follows only after5.3 normal publication/remote verification; freeze tested
inputs, run fresh applicable full Python/Go/security/fault/package gates and keep
provider/hardware/production acceptance explicitly outstanding.

Status2026-10-29:5.0–5.4 LINUX SOURCE/SYNTHETIC SOFTWARE SUBSET ACCEPTED, fresh445
Python/64faults +Go/vet/modules/builds and integrity/package checks. Overall Phase5
PARTIAL/production NOT ACCEPTED; PHASE5-ACCEPTANCE exact scope overrides historical
pending notes. No new release: source checkout only. Remaining independent work:
complete Linux access distribution/install/upgrade/rollback qualification; owner-
configured VPN/SSH/Cloudflare/IdP/DNS/live-client deployment tests; deferred physical
ARM64/phone/LAN/Doze/OEM/power campaign and production approval. Do not infer live
connectivity or recovery/Android writer authority from synthetic software PASS.

5.4d.1/d.2: separate Linux Access0.1.0-internal bundle now has qualified safe
install/env/lifecycle/compatible code switch/rollback and actual canonical access
regression. Exact archive +SHA published only after remote bytes verify. This
closes the old Linux distribution gap, not real provider/hardware/production gates.
No automatic deploy, new consensus authority or Android/Termux installer.


## Separate source checkpoint5.4e — operator-local readiness
Reuse profile1/2 loaders and existing TLS/pinned client for offline validation and
explicit fixed anonymous probes. No default network/state writes, listener start,
issuer fetch or account configuration. PHASE5-ACCESS-CHECK documents source-only
commands. Prepare live acceptance without claiming remote/provider/quorum/writer
proof, reopening accepted software gates or changing immutable0.1.0 distribution.
