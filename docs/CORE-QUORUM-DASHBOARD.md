# Core quorum Dashboard adapter v1

4.1c.1 implements Core observation endpoint/pinned collector/passive recovery
view. HTTPS gateway/shared browser UI follows c.2; status in Phase4.1 progress.
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
