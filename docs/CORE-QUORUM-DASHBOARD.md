# Core quorum Dashboard adapter v1

4.1c.1 implements Core observation endpoint/pinned collector/passive recovery
view and c.2 shared HTTPS browser gateway; status in Phase4.1 progress.
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

## Implemented Core observation shape / semantics

Owner-only GET /cluster/v1/observability?consistency=local|strong returns
observer_version1/read_only=true/writer_authority=false, whitelisted existing
Dashboard-shaped nodes/volumes/files/counts/capacity, runtime checkpoint/index/term/
control revision/epoch, Controller role/voter-process observation, bounded jobs and
backup snapshot/job states. Backup VERIFIED retains verified_at/source index and
is historical. External archive without configured verification stays UNKNOWN.
Local/stale views make available/protected/capacity availability null; known old
IDs/history remain visible. No response contains the raw projection/credential
hashes/node tokens/grants/source paths. Server delegates only this path; POST403.

Observer(cluster,epoch,three explicitly pinned owner endpoints,minimum_index) calls
only GETs, bounded3 concurrent requests and exact identity/mode/version/floor checks.
All endpoint strong-read attempts must fail before QUORUM UNAVAILABLE is reported;
one valid majority remains observable during1/2 partition. No quorum is inferred
from counting online processes. Leader confirmation needs Barrier +stable actual
role/term +committed authority binding, still NO writer capability. An unreachable
Controller is OFFLINE but its voter process UNKNOWN until observed. Remembered
index floor is RAM +operator minimum; restart does not prove globally newest history.

RecoveryObserver(root,trusted_manifest_SHA,expected_cluster,minimum_index) holds an
existing shared stage lock and uses Core3D full-byte anchored verification, then
same sanitized projection. Valid stage =>RECOVERY READ-ONLY, credentials/writer=false;
corruption/wrong anchor/floor/missing bytes=>UNKNOWN, never a healthy recovered cluster.
Disposable existing Core SQL workspace is query_only and in RAM solely to reuse
Catalog/Views logic; it is not a second persistent Catalog or authority fallback.

## Implemented shared gateway (4.1c.2)

`python -B -m asc.observability.gateway --root <NEW-private-root> init` accepts
exactly one explicit source: private Core bootstrap plus cluster/epoch, or anchored
recovery staging. Default loopback8445, optional explicit private numeric LAN IP.
Linux host guard excludes Android/Termux; dedicated root cannot be inside engine,
volume/recovery/source ancestry. New private TLS identity is a gateway identity,
never a new Node/Cluster. Existing engine/source roots remain separate/unmodified.
Bootstrap format: `{cluster_id,controllers:[{node_id,origin,pin,token},...]}`;
exactly three authenticated existing voter endpoints, stored0600 only. No automatic
credential export/discovery. Browser receives only sanitized owner session views.

`... serve --issue-login-code` explicitly issues one short-lived one-use owner
login code to the private foreground operator terminal. Never redirect it to public
logs. Restart revokes RAM sessions and permits a fresh explicit code; no permanent
password/default credential or public code-issuance endpoint. Verify `info` public
CA SHA independently and trust only public CA, never skip TLS errors. Cookie namespace
is unique per gateway, separate from Demo even on the same host/different port.

Shared DashboardHandler/assets enforce mode BEFORE routing. Public /api/mode has
only mode/read_only. Authenticated GET /api/state and /api/files/<UUID> are the only
Core data operations; authenticated login/logout retain Origin/CSRF/session controls.
Other mutations and downloads403 server-side. Core refresh uses GET and never calls
Demo /refresh. Existing Demo upload/download/Quick Join remain in Demo mode only.
Core UI shows policy1/2/3, source checkpoint/barrier, controllers/voters, jobs and
historical backup. UNKNOWN remains UNKNOWN; no transfer percentage/protection/writer
is fabricated. Browser never owns local bridge scopes or private source credentials.
