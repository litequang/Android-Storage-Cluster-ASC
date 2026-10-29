# Phase4.1 progress / account-independent handoff

**COMPLETE: bounded Linux synthetic Phase4.1 ACCEPTED. Android/native/migration/
Windows runtime NOT TESTED; Core3D writable disaster recovery remains BLOCKED.**

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
|4.1c.2|PUSH/REMOTE VERIFIED40fb7c788a95434387e53d04065ddf4ca7721202;15PASS+final browser1PASS|
|4.1d.1|PUSH/REMOTE VERIFIED0a3ea839217156b69209a073f5d836ee1db4452b;38PASS, exact source candidate frozen|
|4.1d.2|PUSH/REMOTE VERIFIED38360d1bd3261dba730e9ac7f7e9ca8772a73b40;311 Python/11 Go/full gates PASS|

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

## 4.1d.1 exact source compatibility / source-only candidate freeze

c.2 pushed/remote matched40fb7c7 BEFORE d.1. Added standalone exact published
Phase4.0 archive ->new source candidate test. Original pending BOTH directions,
new-state code rollback, old+new download SHA/volume/Node/Cluster/CA/credentials,
installed private bridge status/root retained and unsupported old API refusal.
Initial1PASS0skip/fail21.408s; not reused for final frozen source. Final targeted
combined running after expected-epoch binding hardening. Wrong epoch must remain
UNKNOWN even when trusted manifest cluster matches; no recovery activation.

Candidate0.4.3-dev SOURCE ONLY,124 public files, deterministic exact source rebuild
and unpacked secret/path audit PASS. All original archives/candidate0.4.2 immutable;
all27 original Core test files byte-identical; asc/external and Go unchanged.
Core existing service change remains only owner observer delegation. Native app/
Keystore/SAF/Binder/Doze/migration contract +concrete Phase4.2 gates retained; PATH
probes found no adb/sdkmanager/gradle, no APK/toolchain/runtime claim. Operator
instructions PHASE4-1-OPERATIONS distinguish private control backup, request retry,
explicit approved Core endpoints/CA/owner session, unknown evidence and code-only
rollback; no old database restore. Separate control-root restore not implemented.

Candidate SHA96260f1709f6a9db6cb98869fbef8fc2313feaf68a4f12da354665ad04693c04,
release_id0568d5a91c32ab210fe8c39dc52be5e1862de994bf65ecd501a1e55af019e81f.
Discovery311 unique cases, no duplicate inherited test IDs. Fresh full required
AFTER freeze/push; prior287/targeted results never substitute full acceptance.

Final frozen-targeted command `python -B -m unittest tests.test_phase41_upgrade
 tests.test_bridge tests.test_bridge_contract tests.test_bridge_lifecycle
 tests.test_observer_gateway tests.test_observability tests.test_quick_join
 tests.test_runtime_validation tests.test_external_compatibility -v`:
**38PASS0SKIP0FAIL224.827s**. Includes final expected-epoch mismatch refusal and
exact rebuilt124-file candidate, installed bridge/new-state rollback; no weakened
gates. Tracked/index secret review245paths0findings, package separately audited.
Source/tests/packaged guides/candidate now frozen; NEXT only after normal push/
remote verification:4.1d.2 fresh full311 Python and Go/build/fault final reporting.

## Running final gate / interruption handoff

Source freeze0a3ea839217156b69209a073f5d836ee1db4452b was normally pushed and
advertised remote matched BEFORE final qualification. Go mod verify/vet and11
uncached Go tests PASS, Linux/Windows/Android builds PASS (cross-build only for
latter two). Full command python -B -m unittest discover -s tests -v -f started
2026-10-25T13:59:24.049377+00:00; still RUNNING at this handoff, NOT ACCEPTED.
12/12 Phase3A,20/20 Phase2B,9/9 Phase3D and3/3 GC network faults already PASS;
Linux physical faults still executing. No current FAIL/SKIP, not final full proof.
Private logs/status/frozen SHA inventory under /workspace/work/phase4-1, runner
run-full.py/result python-full-result.json. If environment/session lost, do NOT
infer full PASS; rerun fresh final gates on unchanged frozen source and record
actual results before acceptance. No source/test/packaged-guide/candidate changes.

Independent new bare fetch verified all191 frozen paths and published archive
SHA96260f1709f6a9db6cb98869fbef8fc2313feaf68a4f12da354665ad04693c04; protected
Phase4.0/Core3D/CoreWIP/Demo remote refs still exact original baselines. This
reporting-only handoff records partial running results, not a completed checkpoint.

## 4.1d.2 fresh final Linux qualification

d.1 pushed/remote matched0a3ea839217156b69209a073f5d836ee1db4452b BEFORE full gate. Fresh source unchanged
2026-10-25T13:59:24.049377+00:00 ->2026-10-25T14:29:25.438277+00:00:311PASS0SKIP0FAIL0ERROR
1801.144s, all legacy/new faults including3D9/9.11 uncached Go
PASS; vet/modules andLinux/Windows/Android builds PASS (latter compile only).
All 191 frozen source/test/packaged-guide/archive paths unchanged,
exact candidate rebuild/hash/secrets inventory PASS; original published archives
and27 Core tests unchanged. No retries/skip/weakening to obtain this full PASS.
See PHASE4-1-ACCEPTANCE for actual gates/limits, PHASE4-1-OPERATIONS for private
use/upgrade/backup/code rollback. Qualified only bounded Linux synthetic foundation;
Android/native/cross-UID/migration/Windows runtime NOT TESTED, writable DR BLOCKED.
Reporting docs only afterward; final commit/normal remote receipt follows.

Next work is Phase4.2, separately authorized: ANDROID-APP-CONTRACT concrete order,
verified SDK/emulator/Binder/signature/native lifecycle/Keystore/storage boundaries,
then OS/network/storage/device qualification before any migration promise. Do not
redo4.0/4.1 or merge source branches. Read AGENTS+mandatory docs then4.1 PLAN/
PROGRESS/ACCEPTANCE/API/native contracts. No unfinished mandatory4.1 Linux gates.

## Final publication receipt

Acceptance/reporting38360d1bd3261dba730e9ac7f7e9ca8772a73b40 normally pushed;
advertised branch HEAD matched, then independent bare GitHub fetch matched all191
frozen paths and actual published archive SHA. Original Phase4.0 b9e7577,Core3D
ca2504f,CoreWIP acea2ae,Demo c9c2660 remain unchanged on GitHub. Source/tests/
packaged guides/candidate still exact qualified0a3ea83; subsequent commits ONLY
reporting docs. No source after fresh311/11/fault/build PASS. Tracked/index245
paths reviewed,0 secret findings; unpacked124-file candidate separately audited.
This receipt is a docs-only follow-up; latest receipt commit is recorded in Git
history and verified advertised remote at handoff. Working tree clean after commit.
No unfinished mandatory Linux4.1 checkpoints; do not redo phases or start4.2 without
its own task. Operational/API/native/rollback contracts linked in acceptance.
