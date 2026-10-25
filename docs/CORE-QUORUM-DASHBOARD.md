# Core quorum Dashboard adapter v1

4.1a architecture contract; implemented status in PHASE4-1-PROGRESS/ACCEPTANCE.
Explicit mode core-quorum, separate private gateway config/bootstrap and browser
TLS identity. Reuse Dashboard Sessions/HTTPS/security handler/local assets; retain
Demo single-writer upload/Quick Join in its own mode. No second Catalog/engine.

Add owner-authenticated read-only GET /cluster/v1/observability with consistency
local|strong on existing RuntimeHandler. Strong calls Runtime.view(strong=True),
existing authenticated upstream Barrier; never ensure_ready/operation/commit, no
CAS/takeover/worker trigger. Whitelist projection fields on server, not raw runtime
credential hashes/grants. Status, metadata checkpoint and time are observations.

Gateway accepts ONLY preprovisioned private numeric HTTPS endpoints, exact pins,
expected Controller IDs/cluster/epoch and endpoint-specific owner credentials.
No redirects, discovered endpoint adoption or SQL fallback. Query known endpoints,
verify returned identity/mode/version/checkpoint. Leader hint may route a strong
read but never supplies proof. Accepted strong evidence needs actual Barrier,
current matching Go term/role and committed authority binding; still supplies NO
writer capability. Same schema integer cannot select/adopt another mode.

Expose ONLINE/OFFLINE/DEGRADED/UNKNOWN/QUORUM UNAVAILABLE/RECOVERY READ-ONLY with
reason/source/checkpoint/as_of. Connection refusal proves Controller unreachable,
not that its voter/storage bytes vanished. Voter availability is UNKNOWN without
actual observation. Static membership stays3; storage-node list is not limited2.
Node heartbeat/profile/probe freshness and current approval/generation retained;
unknown capacity never0. File replica protection distinguishes historic verified
from presently available independent domains. Jobs and backup status remain
historical point-in-time evidence. External archives not configured/verified stay
UNKNOWN; passive recovery never has writer_authority.

Browser sees owner session and sanitized projections only. Read-only mode rejects
upload/download/refresh-writes/Quick Join/approval/policy/GC/membership/promotion/
recovery activation server-side; hiding buttons is not authorization. No Core
admin/node/private credentials enter JS/storage. Existing TLS CA trust and CSRF
login/logout preserved. No wildcard/public bind by default; LAN deployment requires
explicit approved private IP/trust, not an Internet management endpoint.

Partition/quorum/Controller loss, stale Leader, mode mismatch/TLS/wrong identity,
reconnect/cache floors and session/CSRF/browser tests are acceptance gates. Every
view is read_only=true/writer_authority=false, even ONLINE. Core3D writable DR is
BLOCKED. No writable restore/GC/failover/runtime activation on Android is added.
