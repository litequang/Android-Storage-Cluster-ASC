# Phase4.1 progress / account-independent handoff

Branch feature/phase4-1-local-engine-quorum-ui from fetched/remote verified
b9e75779670d5565d05a324751af02e48d2538eb. Initial tree clean, no existing4.1 branch.
Original Phase4.0/Core/Demo/WIP untouched; no reset/merge/force/history rewrite.
Mandatory ordered reads and specified Phase4/3D/implementation documents complete.

| Checkpoint | Current state |
|---|---|
|4.1a|PUSH/REMOTE VERIFIED5c26ccf92337ddf2026702a1f8310d4f07b2d689;14PASS|
|4.1b.1|PUSH/REMOTE VERIFIEDfca0c37349ec65ce62220da52f9c1e8d4b6ae632;21PASS|
|4.1b.2|PUSH/REMOTE VERIFIED182d366a53548ab08364edb9ad23f5bf64a35ff7;19PASS|
|4.1c.1|PUSH/REMOTE VERIFIEDfb05323708f3147cee1a8e9a4a3093ae39306d9a;28PASS|
|4.1c.2|READY:15 targeted PASS0skip/fail149.641s; final browser1PASS54.828s; normal push gate follows|
|4.1d|NOT STARTED: app contract qualification/exact upgrade/full regression|

Read AGENTS then PHASE4-1-PLAN/this/ACCEPTANCE and bridge/threat/Core adapter/app
contracts. New user authorization supersedes prior4.0 no-bridge/Core-UI language
ONLY for this bounded4.1 task, never real devices/writable DR. Existing287 full
was Phase4.0 evidence and is not reused as4.1 acceptance. Full fresh regression
required after source freeze. Keep Core3A–3D and Demo Dashboard/Quick Join working.

4.1a implements strict version/type/key/framing/operation contract. No actual IPC
server/authority/runtime starts yet. Historical Phase4.0 exact-archive test fixture
now extracts published0.4.2-dev rather than treating new source as old candidate;
ALL old version/exact-byte/identity assertions retained. New source version0.4.3-dev,
not a release; base formats unchanged, old archives untouched. New exact candidate
upgrade/code rollback gets separate4.1 qualification. Bridge/gateway control state
will be outside engine state and is not a new Catalog/Storage implementation.

Stop on proxy:8080 error, preserve proxy/CA. Existing Cloud activate.sh selects
Python3.13.5/Go1.27.3; Node/Chromium/certutil existing. Logs/private artifacts under
/workspace/work/phase4-1 only. No subagents, phones/M51/production/system/Boot/root/
format/SSH or Android Raft/GC/failover activation. Writable DR remains BLOCKED.
After EACH targeted PASS/docs/secrets commit+normal push+remote equality BEFORE next.

4.1a actual command: `python -B -m unittest tests.test_bridge_contract
 tests.test_phase4_upgrade tests.test_lifecycle.DeviceSafetyTests
 tests.test_external_compatibility -v`:14PASS0SKIP0FAIL20.014s. First new contract
run exposed CatalogError escaping fixed-label parser; caught existing StorageError
base correctly, all malformed/secret/type/operation tests now PASS. Exact old
Phase4.0 upgrade/new-state rollback still executes real TLS/bytes from original
archive; M51/unknown and original DR platform guards PASS. No active server or
engine authority added. Security/code/docs reviewed; next only after push/remote:
4.1b.1 private UDS/status/durable Quick Join using existing engine.

## 4.1b.1 private IPC/status/enrollment

a pushed/remote matched5c26ccf BEFORE b.1. Implemented actual AF_UNIX/peer UID,
private owner-only root/socket/files, separate app scopes and bounded FULL request
journal. Existing marked-state/installation directory binding; approved adapter
read/free-space only, writable/fsync null, no second Engine/DB/approval. Quick Join
reuses existing worker via fixed argv +secret stdin, prefix/source guards and
ASC_HOME before import. Same request binding+code-hash checks; codeless resume
reuses saved pending/receipt. Success replay explicitly historical, not current
proof. Runtime device guard runs BEFORE private control access.

First target exposed a fixture HOME scope omission and missing-state error-label
normalization. Corrected test environment and explicit setup_required refusal;
no filesystem fallback/test weakening. Earlier corrected10PASS27.724s,21PASS89.561s,
then7 guarded bridge PASS38.763s. Final after code-hash/codeless-resume refinement:
`python -B -m unittest tests.test_bridge tests.test_bridge_contract
 tests.test_quick_join -v`:**21PASS0SKIP0FAIL94.158s**. Includes actual lost UDS
success response/durable replay, lost successful pinned TLS ACK+bridge restart/
same Core token/operation, no auto storage approval, response/journal secret checks,
M51/unknown-before-private-access, root replacement, framing/auth/scopes/foreign
socket/journal bound and all old Quick Join cases. No Android/other-UID runtime
acceptance. b.1 has graceful restart; hard-crash socket recovery/Node lifecycle
still b.2 pending. Next only after normal push/remote match:4.1b.2.

## 4.1b.2 owned lifecycle / real bridge process loss

b.1 pushed/remote matchedfca0c37 BEFORE this work. Owned Node only: fixed guarded
Demo worker argv, retained supervisor thread/Popen handle, Linux PDEATHSIG before
exec, no browser/PID/shell/process manager or Controller/Core/Raft launch. Scoped
start/stop keeps process evidence separate from UNKNOWN writable/fsync/protection.
Hard-crash socket recovery requires exclusive bridge OS lock +exact owned private
socket receipt +matching inode +actual connection refusal; foreign/live/unknown
socket is preserved. Optional receipt changes no engine/control base format.
Verified installed Demo launcher exposes bridge-provision/run/status/node-start/
node-stop/quick-join, existing root/prefix/source/journal checks apply.

First lifecycle target caught real Linux parent-thread semantics: a short-lived
IPC handler spawned the child, so PDEATHSIG killed it when that handler ended.
Fixed spawn ownership to one retained supervisor thread, no test/timeout weakening.
Corrected3 lifecycle PASS24.780s. Added actual bridge SIGKILL DURING paused successful
TLS201 enrollment: original worker/pending identity finishes; same bridge request
resumes with unknown current confirmation, exactly one enrolled Node/token and
no storage approval. Final `python -B -m unittest tests.test_bridge_lifecycle
 tests.test_bridge tests.test_bridge_contract tests.test_demo_installer -v`:
**19PASS0SKIP0FAIL74.287s**. Actual Node start/stop/restart/SHA, external foreground
untouched, parent SIGKILL/lock release/socket restart/historical no-autostart,
installed verified source/root binding, enrollment loss/security/installer gates.
No Android/cross-UID/real power-cut acceptance. Next only after push/remote match:
4.1c.1 sanitized Core GET observer and pinned read-only gateway adapter.

## 4.1c.1 Core sanitized observation / explicit pinned adapter

b.2 pushed/remote matched182d366 BEFORE c.1. Only existing Core change:3-line
GET-observer delegation before readiness routing. New owner-only /cluster/v1/
observability?consistency=local|strong calls Runtime.view Barrier, NOT ensure_ready/
operation/commit/takeover. Reuses existing disposable prepare_registry/Catalog/
Dashboard Views with SQLite query_only for sanitized public aggregation, never
opens live original registry or adds a persistent Catalog. Policy1/2/3 protection,
three-controller/voter-process observations, jobs, historical VERIFIED backup/time
and externally UNKNOWN evidence. No raw token/hash/private profile exposed.
Pinned explicit cluster/epoch/Controller IDs/static3 endpoints; no redirects or
mode/SQL fallback. Offline cache downgrades availability/protection, no writer.
RecoveryObserver verifies existing exact anchored staged bytes under shared lock,
reports RECOVERY READ-ONLY without configs/keys/runtime activation.

Initial tests found missing recovery projection import and shared class fixture
reuse; fixed helper fixtures without test duplication. Adding real enabled snapshot
coverage caught nested manifest created_at (not top-level); projection now carries
source index/verified_at from original record. A quorum test incorrectly called
partition(i) repeatedly (each resets all split groups, leaving a valid majority).
Fixed to ONE actual three-island split, unchanged strict assertion; no Raft change,
no weakened gate. Final `python -B -m unittest tests.test_observability
 tests.test_external_cluster tests.test_failover.RuntimeStateTests
 tests.test_runtime_validation tests.test_gc_authorization -v`:
**28PASS0SKIP0FAIL62.475s**. Includes real TLS3-voter stale Leader/all-island quorum
loss/heal/Controller kill/rejoin; actual3 independent stored replicas and VERIFIED
snapshot, node-owner auth/pin rejection, original registry byte preservation,
unit no-takeover fake-hint boundary, actual passive stage readback/corruption denial,
existing external capture/metadata envelopes/native validation/GC authorization.
Core gateway/browser UI still c.2 pending. Next only after normal push/remote match.

## 4.1c.2 shared HTTPS/session/assets Core UI

c.1 pushed/remote matchedfb05323 BEFORE c.2. Dedicated Linux-only private Core
quorum or passive-recovery gateway, separate TLS identity and unique root cookie
namespace, explicit source/cluster/epoch/floor. Same Dashboard handler/Sessions/
CA factory/assets, explicit mode before dispatch. Only authenticated Core GET
state/file-detail; all writes/download/runtime/approval/GC/recovery activation403.
Default loopback, explicit private LAN only; original platform guards retained.
UI shows actual Barrier/checkpoint/controllers/voter observations/jobs/backup and
policy1/2/3. Nulls remain UNKNOWN, no Core upload/Quick Join. Never browser tokens.

First browser run failed after reconnect because unscoped badge locator matched
both file row and retained closed detail dialog; stage-only secret-safe diagnostic
confirmed reconnect-protection. Scope to visible file row, preserve actual strong
policy3/quorum-loss/heal assertions; no timeout/assertion weakening. Also close
replica dialog when strong quorum evidence is lost; empty Core list gives no upload
instruction. Actual3-voter transport faults, CA-trusted Chromium at390px, XSS/no
persistent code/no mutation requests; server auth/TLS/CSRF/mode/forbidden paths and
full-byte passive-stage preservation PASS. Existing Demo browser upload/SHA/fallback
and Quick Join regression retained. Combined command:
`python -B -m unittest tests.test_observer_gateway tests.test_observability
 tests.test_demo_dashboard tests.test_demo_dashboard_browser
 tests.test_quick_join_browser -v`:**15PASS0SKIP0FAIL149.641s**.
Final browser repeat covers final dialog/empty-state text change:1PASS0skip/fail54.828s.
No Android/native/cross-UID/production or writable DR acceptance. Next checkpoint
only after normal push/remote equality:4.1d exact archive compatibility and fresh
full qualification/source-only candidate (not Android release).
