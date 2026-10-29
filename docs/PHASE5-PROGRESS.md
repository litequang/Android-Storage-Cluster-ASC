# Phase5 progress — resumable source handoff

2026-10-28 owner explicitly defers phone acceptance and requests next roadmap work.
Physical Phase4/production remains NOT ACCEPTED; this authorizes source/synthetic
Phase5 progression, superseding the old requirement to wait for a phone pilot.
No new deployment authorization. Branch feature/phase5-remote-access starts from
verified HEAD/FETCH0877a15, clean tree; original branches/signers/AVDs preserved.

5.0: asc/access/policy.py version1 immutable private-gateway profile, numeric
RFC1918/loopback/100.64/10 frontend and pinned LAN Dashboard upstream. Exact mode,
limits and fixed browser route allowlist; unknown network evidence stays UNKNOWN.
Core/recovery cannot gain file-write routes; no node/admin/approval/enrollment/GC/
shell access. No runtime listener in this checkpoint. Seven new policy tests plus
existing owner-session test fresh PASS8/0skip/0failure0.002s, including final canonical
upstream validation. No Core/app/archive/schema/identity change.

Next AFTER GitHub verification:5.1a private gateway runtime/CLI and real TLS tests
against existing Dashboard with actual two-node file bytes; keep original owner
session/CSRF and explicit backend-mode/pin checks. 5.2 Cloudflare and5.3 private
maintenance not yet implemented. See PHASE5-PLAN. No real VPN configured in Cloud;
network membership/remote reachability and phones remain NOT TESTED/UNKNOWN.

5.0 audit correction: initial scanner flagged ONLY the explicit dummy userinfo URL
in test_access_policy (no real credential). The shell command chain continued to
commit/pushd56e84b despite the audit exit; this was a publishing workflow error.
Changed that fixture to shorter clearly synthetic u:p, preserving the same actual
userinfo refusal test, then reran all8 tests and full work/index secret scan. No
real secret/key was exposed; no scanner/test assertion relaxed. Subsequent publish
commands use set-e so audit failure stops commit/push. Verify this correction on
GitHub before starting5.1.

## 5.0 remote verified before runtime work
Initiald56e84b +dummy-fixture correction8774c60c14e56870055342bf8fc17c195c7bea88
normal-pushed; HEAD/FETCH_HEAD/advertised feature remote matched. Clean tree before
5.1.8targeted PASS0.003s after correction,432work/index paths/0secret findings.
No actual secret exposed, scanner/test assertions unchanged. Source baseline and
original branches remain intact.

## 5.1a private gateway runtime/CLI
New asc/access/gateway.py calls existing pinned HTTPS client, Dashboard browser
routes/sessions and bounded shared TLS server, existing private locks/control-file
primitives and identity generator. Separate access root, no DB/backend state access.
Explicit numeric bind, startup mode+pin proof, external origin/Host validation,
fixed upstream rebase, only Cookie/CSRF/content headers, no forwarded-identity trust
or bearer/admin/node/enrollment/shell/GC routes.64KiB streaming, body/metadata/header/
worker/rate/time bounds; existing backend remains authority. Linux desktop guard
unchanged; Android/Termux/M51/unknown runtime is not permitted by this entrypoint.
Init is compatible/idempotent, partial or conflicting existing state refuses.
CLI init/info/serve and actual trusted HTTPS/readiness/SIGINT stop now exercised.

Fresh actual command:
python -m unittest tests.test_access_policy tests.test_access_gateway tests.test_demo_dashboard -v
19PASS0skip/fail77.201s on source runtime. Separately added actual CLI foreground
regression1PASS7.041s. This is19+1scoped executions, not a fresh20/full suite.
Actual two Linux synthetic storage processes, owner code/cookies/CSRF, upload and
SHA download/two logical replicas/offline fallback, wrong CA/pin/mode, bad framing/
size, blocked management routes, gateway restart/session preservation and backend
loss503/restart session revocation. Same host, not VPN/phones/physical domains.

Initial test run had HTTPSConnection context-manager fixture errors; fixed using
contextlib.closing. Next19run had a wrong expected CSRF status (backend returns401
for wrong token,403for missing token); test now asserts BOTH existing exact refusal
contracts, no product/assertion relaxed. Final19PASS above. CLI readiness initially
sent only TLS then disconnected, causing a generic redacted diagnostic; changed
the test probe to complete actual HTTPS/api/mode before SIGINT. FreshCLI1PASS,
no production code/log suppression or security weakening. Raw logs remain private
/workspace/work/phase5-*. Source/generated test identities isolated; no old SDK/
signer/phone/Termux/production state touched. Original Core tests/source/APK bytes
unchanged. No fresh full Python/Go/build/platform claim; Phase5 not final accepted.

Guide PHASE5-PRIVATE-ACCESS: source CLI/new private profile, explicit public-CA trust,
existing owner code, file workflow, safe stop/rollback. Old archives not rewritten
and do not provide this entrypoint. NEXT after normal checkpoint push/verification:
5.1b actual Chromium via gateway +Core read-only/fault qualification, then separate
5.2Cloudflare adapter. No live VPN/Cloudflare credentials configured: remote actual
reachability UNKNOWN; do not call loopback PASS remote/production PASS.

## 5.1a published / 5.1b.1 real browser qualification
22bdcd935449f3c5bf7833835558bc8db7a2caf5 normal-pushed, HEAD/FETCH_HEAD/advertised
feature remote matched BEFORE next work.435work/index files audited/0findings.

New tests/test_access_browser.py uses UNCHANGED original demo_dashboard.cjs through
new gateway URL and its own trusted CA, no ignoreHTTPSErrors/root/proxy/CA bypass.
Actual Chromium/PWA1PASS12.565s: untrusted cert denied, trusted HTTPS/secure context,
owner invalid/valid login/Secure HttpOnly Strict cookie, existing UI/file listing,
actual upload/two logical replicas, mobile390 layout/XSS/node detail, actual Node
stop/offline protection/download fallback+SHA, unsafe new upload refusal, browser
network loss UNKNOWN/disabled actions/reconnect/logout, network-only PWA empty
cache/manifest/service worker/installability checks. Existing original150s deadline
and all browser assertions unchanged. No actual PWA installation claim from CDP
criteria alone, no Chrome Android/VPN/remote-public/hardware claim. Screenshot/
raw outputs PRIVATE /workspace/work/phase5-private-browser; sanitized combined
receipt qualification/phase5-private-access.json. This adds1browser execution to
prior19API/regression +1CLI, not a fresh full suite or production acceptance.

No product changes after22bdcd9; browser fixture/test/docs only. Existing source
bundles/APKs/signers/SDKs retained; current old archives do not contain this new
entrypoint. Guide still source checkout only, no new release. All owned synthetic
services cleaned up after tests. Core quorum/recovery THROUGH private gateway
is next5.1b.2, not inferred from mode-policy units. Then5.2Cloudflare edge identity/
header trust/source adapter; no live cloud account/tunnel/device operations.

## 5.1b.1 remote verified / 5.1b.2 Core and passive recovery
467b92c81a128d9eb2a300b79d183bd348b2b894 normal-pushed and HEAD/FETCH_HEAD/advertised
feature remote matched BEFORE next work;437work/index files/0secret findings.

New tests/test_access_observer.py2PASS0skip/fail14.866s. Actual existing three-Go/
three-Python cohost Core fixture, pinned TLS observer ->private gateway ->CA-trusted
owner request. Healthy quorum observed, actual three-island Raft transport partition
reported QUORUM UNAVAILABLE/UNKNOWN without writer authority, all mutations denied
before backend, heal/wait_ready and fresh positive quorum still read-only. No voter/
consensus/runtime source or authority change; test-only existing fault controls only.

Second test uses existing MemorySource UNIT fixture for synthetic archive metadata,
ACTUAL local backup/staging bytes and two HTTPS layers/owner session. Recovery
READ-ONLY/credentials_restoredfalse, activation/upload/GC denied, staged bytes
unchanged and no registry/controller identity created. This is read-only ingress
qualification, NOT live quorum capture or writable disaster recovery proof.
No HOME/global provider/guard patch in these new tests; new gateway/observer roots
are isolated fresh private directories under real development HOME, existing engine
fixtures separate. All services/test roots cleaned; old private SDK/signer datasets
untouched. No provider/production/phone calls or live VPN/cloud tunnel configured.

Private-access software subset5.1 now covers Demo API/CLI/browser plus actual Core
read-only and passive staging. Receipt lists19+1+1+2scoped targeted executions,
not a fresh full Python/Go/Android regression. Source gateway/policy unchanged since
runtime22bdcd9; test additions only. User guide and status updated. Phase5 overall
NOT ACCEPTED; physical campaign DEFERRED BY OWNER, actual VPN/Cloudflare/public-edge
and maintenance5.2/5.3 remain NOT TESTED/NOT IMPLEMENTED. Next5.2 source adapter needs
independent public-origin/connector/Access JWT-header trust, secure verified TLS to
loopback origin, no public Node/admin ports. No live account/tunnel deployment is
authorized by source work. Do not widen private profile or label VPN UNKNOWN as PASS.

## Private software5.1 publication verified / next exact resume
Source checkpoint `fa0ada971585ee5151fc7b48ceeef47d03bdef75` normal-pushed and local HEAD=FETCH_HEAD=advertised
remote verified 2026-10-28T13:41:43.555080+00:00, clean tree. Original Phase4 remote still0877a15 unchanged;
Core/Demo/Go/Android/candidates/APKs unchanged; only new asc/access modules added.
All tested source hashes still match sanitized receipt,438work/index files audited
with0untracked/secret findings. Following docs-only publication note changes no
tested code or artifact. Separate named tests19+1+1+2PASS, no fresh full claim.

Completed5.0/5.1a/5.1b.1/5.1b.2 within Linux synthetic scopes, source CLI ready for
controlled development; no new packaged release. Read PHASE5-PRIVATE-ACCESS for
init/info/serve/private CA/existing owner code/rollback. No additional local Core/
Android/full rerun needed merely to repeat unchanged5.1 proof. NEXT5.2 source-only
Cloudflare edge adapter: review explicit public origin versus loopback binding,
connector TLS/public-CA trust, verified Access JWT/header identity, request/body/
edge limits and existing owner session/CSRF preservation. Current private profile
MUST NOT simply accept public/DNS origin or trusted forwarded headers. Real account/
DNS/tunnel deployment not authorized/configured; never open Node/admin/SSH ports.
Then5.3private operator maintenance,5.4fresh final applicable qualification. Physical
phones/ARM64/LAN/Doze/OEM/power deferred to overall owner campaign, not PASS; no
production/M51 access or Android voter/GC/failover/writableDR activation.

## 5.2a JWT/profile/dependency foundation
Resumed clean f47797f, fetch/HEAD equality verified, no reset/branch merge. Skill/
network policy reviewed, inherited proxy/CA unchanged; no live VPN/cloud identities
or credentials configured. Owner phone campaign remains deferred/not PASS.

Official Cloudflare Access/origin docs and PyJWT API checked (links in PHASE5-
CLOUDFLARE). Added AccessVerifier with real RS256/PyJWT verification, configured
issuer/audience/claims, bounded token/JWKS/cache/refresh, fail-closed stale-key handling.
EdgeProfile2 separates public DNS origin and loopback127 listener; private profile1
still refuses edge/public config. No new listener in5.2a, no owner-role mapping.
Optional requirements-cloudflare.txt hash-locks4official PyPI packages. Fresh
private Python3.13.5 env: PyJWT2.15.1/cryptography50.0.2/cffi2.1.1/pycparser3.12,
verified wheel hashes/local no-index install/pip check PASS. ensurepip absent,
used workspace-only --without-pip and existing pip --python, no system installation.

Fresh actual: /workspace/asc-access-dev/edge-env/bin/python -m unittest
 tests.test_access_jwt tests.test_access_policy -v:16PASS0skip/fail0.066s. Nine new
JWT/profile cases +seven existing private-policy regressions. Real in-memory RSA
signatures/negative algorithm/signature/issuer/audience/time/missing-claim cases,
key rotation/unknown-key cooldown/expired-cache offline/ambiguous JWKS and mode/
bind separation. Synthetic key-source callable ONLY, no live issuer claim. No raw
private key/JWT stored or logged. New optional imports do not change Node/Registry/
Engine/Go/Android/app/old archived artifacts. No fresh full suite or provider PASS.

Next AFTER normal commit/push/remote verification:5.2b edge origin runtime reusing
same browser gateway, JWT BEFORE forwarding, cookie/assertion stripping, pinned
backend and exact public Host/Origin, real local TLS/owner/file tests; connector
config with trusted CA/loopback/per-rule Access +404 catchall. No live tunnel run.


## Executor interruption handoff — 5.2b NOT QUALIFIED
Last tested source checkpoint783dd7d9a737fcdd58011c054a98fcc85e525618 was normal-
pushed/fetch+advertised verified before runtime work.16fresh targeted PASS0.066s
and optional private-env pip check are the ONLY new5.2 qualification results.

Cloud executor then became unavailable. Last create/run integration command
failed CreateProcess with exec-server transport disconnected: no successful test
process or results. Provider environment_status still said connected; that does
not establish executor readiness. No5.2b runtime/TLS/file/connector acceptance,
cloudflared binary qualification, new APK/archive or live Cloudflare deployment.

The apply_patch acknowledgment covered shared asc/access/gateway.py hooks and new
asc/access/cloudflare.py, UNCOMMITTED/UNTESTED. Cannot reread disk/verify its exact
bytes now. Do NOT discard dirty files, reset/clean/force-checkout or assume source
already exists remotely. The test file creation command was not acknowledged;
check existence before reconstructing it. Original signer/SDK/Node/private state
and original branches must remain intact. No new5.2b services known to have started.

GitHub connector saved a TOOL-CALL RECONSTRUCTION/draft and full resume/test matrix
at docs/handoff/PHASE5-2B-EXECUTOR-INTERRUPTION.md, commit
b672f38247b204b21e9420ba47bae10b721e5b6b. This is recovery documentation, not active
source or a byte-verified workspace backup. Source16test checkpoint unchanged.
Read handoff first, inspect/reconcile original workspace/branch and docs-only
remote advances without overwriting dirty source. Recover only missing work, then
fresh JWT/private/edge/realTLS/file/browser/Core targeted gates. Keep5.2b UNKNOWN/
NOT QUALIFIED until those pass and are committed/remote verified. Physical-phone
campaign remains DEFERRED BY OWNER; do not wait for phones to resume source work.

## 5.2b executor recovered; loopback origin/source subset qualified
Original workspace recovered, gateway.py/cloudflare.py dirty bytes preserved.
Remote783->28fea21 docs-only handoff fast-forwarded after path review; no reset,
clean, branch merge, state/signer/AVD/artifact modification. Missing integration
file reconstructed from scenarios; no runtime source had to be reimplemented.
Inherited network policy/proxy/CA untouched, no live tunnel/account/DNS deployment.

Implemented separate `asc.access.cloudflare` init/info/serve/render-connector,
exact loopback TLS/public Host split, actual RS256 before upstream, ASC-only cookie
forwarding, no second owner DB/Engine or cloud credentials read. Shared gateway
hooks retain profile1 behavior/limits/pinning/mode/CSRF. See PHASE5-CLOUDFLARE for
source commands, contract, CA trust, offline connector evidence and stop rollback.
No new source archive/APK release; old installed bundles do NOT include this CLI.

Fresh /workspace/asc-access-dev/edge-env/bin/python -m unittest
 tests.test_access_jwt tests.test_access_policy tests.test_access_cloudflare -v:
22PASS0skip/fail41.118s. Six new actual loopback-TLS cases plus16foundation cases.
Real pinned HTTPS JWKS test source/ephemeral RSA verification; valid JWT still
requires ASC owner, invalid JWT never consumes owner code, actual two logical
replicas/upload/SHA/fallback after node stop, wrong CA/pin/mode/origin/CSRF/duplicate
assertion/cookie refusal, restart preserves gateway cert/session, real key-server
stop +expired cache503, actual recording TLS upstream has no CF credentials,
CLI init/info/render exclusive output/never reads tunnel credentials.
Synthetic key TRANSPORT maps configured issuer URL to local pinned HTTPS fixture,
not live Cloudflare tokens/provider. No production verifier bypass/CLI test mode.

Shared source regression: tests.test_access_gateway tests.test_demo_dashboard
 tests.test_access_browser tests.test_access_observer initial89.463s:15tests PASS,
1Core class-setup ERROR (default /usr/bin/go was unrelated executable; no Core test
ran). Existing gateway6+Dashboard7+actual Chromium1 =14PASS, passive recovery1PASS.
Resolved WITHOUT source/test weakening: command-only ASC_GO selects existing
/workspace/asc-cloud/go1.27.3/go/bin/go. Fresh tests.test_access_observer2PASS0skip/
fail67.221s including cold Go build/actual3-Go/Python quorum partition/heal and
passive recovery. Qualified coverage is22+14+2distinct cases, not a fresh full suite.
Private browser still uses original unchanged demo_dashboard.cjs, actual trusted/
untrusted CA/owner/PWA/mobile/XSS/bytes/offline fallback/logout. This private browser
is not proof of live provider/browser-through-edge. Existing Core source unchanged.

Initial new suite had1test-expectation failure (expected error lacked existing
protocol_version field), not a runtime fault. Corrected exact envelope expectation;
no assertion removed. Initial imported TestCase also discovered6duplicate existing
private cases; switched to module import, final22 count excludes duplicates.
Initial standalone connector validation used disallowed outside-HOME credentials
PATH, correctly refused; reran in fresh private HOME directory, no guard change.

Official cloudflared2026.10.5 linux-amd64 downloaded/workspace-only,40263303bytes,
SHA256 e1bc0cf084fd9e590554fe769a86b1db46701c3f847a43d902f7b974a4e16298 matches
release body AND asset digest. --version/offline ingress validate/matching rule0/
other hostname404rule1 PASS. No tunnel run/service install/provider account used.

Security review: tracked/index/untracked source inspected for private paths/PEM
material/access keys/token patterns/URL credentials. Four initial pattern flags
were existing PEM HEADER string validation constants and known u:p userinfo-refusal
fixture, manually reviewed; no actual PEM or credential material. Scan recognizes
real multiline key material and only that exact synthetic URL fixture. No original
security tests modified. Final staged scan/remote receipt follows publication.

Software subset5.2b qualified, Phase5 overall NOT ACCEPTED. Public-edge browser/
real connector/IdP/DNS/network behavior NOT TESTED; edge-mode Core/recovery E2E is
next5.2c qualification, then5.3 controlled private maintenance and5.4fresh final
applicable gates. No fresh full Python/Go/Android/fault run claimed at5.2b. Physical
phone campaign DEFERRED BY OWNER. WritableDR/Android voter/GC/failover stay locked.
Private raw logs /workspace/work/phase5-edge-{targeted-final,private-regression,
observer-final}.log; public sanitized receipt qualification/phase5-edge-access.json.

## 5.2b publication verified / 5.2c connector-browser and Core edge E2E
Checkpoint bf04868f875fb800db1e9f4b6af7dfc2511d1f39 normal-pushed, local HEAD=
FETCH_HEAD=advertised feature remote and clean working tree VERIFIED before5.2c.
448tracked/index files/0untracked/0actual-secret findings at publication. Original
Phase4 advertised remote still0877a15 unchanged. No APK/source archive/release.

5.2c adds test-only SyntheticConnector and EdgeBrowser/Core/Recovery fixtures.
Reuses every original Dashboard browser assertion and every actual Core partition/
heal/recovery staged-byte assertion; only trusted fixture/runtime hooks introduced.
No product source/authority/state/dependency changes afterbf04868. Shared original
private browser/Core cases rerun alongside edge modes. Actual RSA verification is
never mocked. Edge browser uses real pinned local HTTPS JWKS; observer cases use
synthetic in-memory public key transport with real RSA/PyJWT claims validation.

Initial3case suite23.704s: edge Core+recovery PASS, browser FAIL before untrusted-CA
assertion due public-origin test route. Original failure log mislabeled it from
expected regexp. Added secret-safe ACTUAL network-error reporting only; browser
retry8.104s confirms ERR_TUNNEL_CONNECTION_FAILED. No credentials/logs exposed,
no TLS assertion removed, no policy/proxy/CA override. Public-host DNS-mapping
experiment removed, NOT called PASS. Source fixture now explicitly local-only
connector front with valid independently trusted IP-SAN CA, exact local Host/Origin
validation before reserved public-origin translation. This is ONLY synthetic
adapter qualification, not real public hostname/Cloudflare/IdP/tunnel acceptance.

Fresh command (all original assertions remain):
 ASC_GO=/workspace/asc-cloud/go1.27.3/go/bin/go
 /workspace/asc-access-dev/edge-env/bin/python -m unittest
 tests.test_access_edge_qualification tests.test_access_browser tests.test_access_observer -v
6PASS0skip/fail55.833s: edge browser1 +actual edge Core1 +passive edge recovery1,
plus existing private browser1/Core1/recovery1. Browser actual two-node bytes, secure
HttpOnly owner cookie, PWA manifest/worker/criteria(not actual install),390px/XSS,
SHA/fallback after stopping actual node, browser offline UNKNOWN/refusal/reconnect/
logout. Test connector inserts signed JWT SERVER-SIDE, no bearer in browser JS;
three TLS layers/pinning and existing backend/Engine remain active. Not2physical
phones/domains, VPN or cloud deployment. Core runtime remains read-only across
actual three-island Raft partition/heal; staging bytes unchanged/no credentials.

Private evidence /workspace/work/phase5-edge-e2e{,-final}.log,
phase5-edge-browser-retry1.log, phase5-edge-browser/{result.json,desktop/mobile PNG}.
New sanitized receipt qualification/phase5-edge-integration.json. Original private
browser receipt is retained historically; latest test-only diagnostic/hook changes
have their own exact input hashes here. No fresh full Python/Go/Android run claimed.

NEXT5.3 controlled private maintenance: inspect existing stopped backup/verify/
stage/preflight/upgrade/code rollback contract, preserve identities and distinguish
Linux/Demo source from Android app/Termux/Core. No public SSH/custom shell API or
automatic update. Then5.4 fresh applicable final regression/fault/security/package
qualification. Live Cloudflare/IdP/DNS/tunnel/real public-browser STILL NOT TESTED/
BLOCKED, physical campaign DEFERRED BY OWNER, full Phase5 NOT ACCEPTED. WritableDR,
Android voter/GC/failover remain locked. Preserve all SDK/signers/states/artifacts.

## 5.2 source publication / exact next resume
5.2b bf04868f875fb800db1e9f4b6af7dfc2511d1f39 and5.2c
04a6ee0aa76f1c901c0b27e949039119a2eb7a12 each normally pushed/fetched and
local HEAD=FETCH_HEAD=advertised feature remote verified with clean working tree
BEFORE continuation. Final5.2c tracked/index451files/0untracked/0secret findings.
Exact current integration inputs and every unchanged product/access module match
sanitized receipt SHA256. Older5.2b fixture hashes are historical, new fixture/
browser diagnostic edits qualified separately in5.2c; no product drift.
This following publication note changes docs ONLY. No new tests or release claimed.

Resume5.3 from feature/phase5-remote-access latest HEAD after fetch/status, no reset
or whole branch merge. Read AGENTS/mandatory docs then current PHASE5 PLAN/PROGRESS/
ACCEPTANCE, PHASE5-CLOUDFLARE and PHASE5-PRIVATE-ACCESS. Use existing private Python
/workspace/asc-access-dev/edge-env/bin/python and explicit command-only
ASC_GO=/workspace/asc-cloud/go1.27.3/go/bin/go. No SDK/ADB/signing operation needed.
Review existing asc/demo/upgrade.py, scripts/demo-alpha.sh and upgrade tests for
controlled private operator backup/verify/stage/preflight/code upgrade/NEW-backup
rollback. Distinguish source-Demo, Android APK, Termux and Core quorum contracts;
no custom remote shell/public SSH/automatic update or compatibility promises.
Targeted PASS/docs/secrets/normal push/remote each, then5.4fresh final gates.
Do not repeat full historical Core/Android acceptance merely to recover context.
Live provider/public-browser and phone/production gates remain separate/unaccepted.

## 5.3 stopped private maintenance — source/synthetic qualified
Fetched feature/phase5-remote-access96d5293, HEAD/FETCH_HEAD/advertised remote equal,
clean workspace preserved. Mandatory maps/Phase5 handoff/upgrade/installer/state/
package/locks/test contracts reviewed. Skill/network policy checked; no inherited
proxy/CA/credentials change, account/SSH/VPN/provider/device operation or ADB.

New asc.access.maintenance preflight/apply CLI reuses existing stopped/install
locks, prefix binding, exact release/format/complete backup verification and
activation/recovery journal. Plan1 carries fixed operation/installation/release/
backup bindings, no commands/credentials. Explicit content digest confirmation,
private plan read bound8KiB, fixed safe errors. Under original activate locks,
optional expected_current+verified_backup preconditions close preflight/activation
race. Defaults and journal1 remain unchanged. Proven COMPLETE retry verifies actual
matching old/new/action/installation/backup/release and does not activate twice.
PREPARED still refuses and uses original explicit code-only recover-upgrade.
No runtime auto-start, schema migration, DB restore or new updater state engine.

Fresh /workspace/asc-access-dev/edge-env/bin/python -m unittest
 tests.test_access_maintenance -v:7PASS0skip/fail39.055s. Actual installed Controller
and two TLS Storage nodes/logical domains, original file upload, stopped upgrade
of Controller+peer, same plan lost-successful-local-ACK retry, exact identities,
new file writes after upgrade, NEW-state backup/code rollback and both files
still downloaded byte-equal. Wrong confirmation/state change/corrupt backup,
installation/release/backup CAS, source gap race, real PREPARED pointer/journal
interruption +existing recover-upgrade, protected/unknown/Core/recovery/symlink and
unqualified Android refusal. Linux fake-device/dependency context is the EXISTING
Demo fixture, not physical-phone runtime proof. Interruption uses actual journal/
pointer I/O with fault at completion, not fake success/network-ACK proof.
Initial6case run34.830s also PASS; final7cases supersede it, no double counting.

Five original upgrade regressions passed in initial38.179s selector run (actual
installed upgrade/rollback/backup, incompatible/missing-volume/corrupt refusal,
interrupted activation/recovery, approved external-volume/mutation and linked-lock
safety). That run also had one TEST-SELECTION loader error: nonexistent class
CurrentPhase41UpgradeTests. Correct selector tests.test_phase41_upgrade.
CurrentSourceUpgradeTests then1PASS0skip/fail24.651s: exact published0.4.2 ->CURRENT
source, pending TLS enrollment both directions, bridge/identity/volume preservation,
new file bytes and NEW-state old-code rollback. No original tests/assertions
changed; no new provider/Android/full-suite PASS inferred from13scoped cases.

PHASE5-MAINTENANCE gives contract/operator commands, downtime/backup/stage/confirm/
apply/retry/recovery/code-only rollback and separate APK/Termux/Core boundaries.
Only source checkout contains new CLI; no new source archive/APK/release published,
old archives/signer/private SDK/phone data untouched. Module explicitly refuses
unqualified Android/Termux; existing device/dependency checks remain, no bypass.
Remote maintenance connectivity remains NOT TESTED: no SSH daemon/client session,
VPN/tunnel/DNS configuration, public SSH or custom command endpoint created.

Private logs /workspace/work/phase5-maintenance-{targeted-final,regression,
current-upgrade}.log; sanitized receipt qualification/phase5-maintenance.json.
After normal commit/push/remote verification NEXT5.4: fresh applicable integrated
Python/Go/fault/security/package gates. Historical Core/Android/full qualification
must not be relabelled fresh. Provider/public-browser, real SSH/VPN, physical ARM64/
LAN/Doze/OEM/power/phone campaign remain outstanding/deferred, full Phase5 NOT
ACCEPTED. WritableDR/Android voter/GC/failover stay locked; original branches kept.

### 5.3 final clean regression run
After correcting the selector, reran the complete intended regression command:
five named tests.test_demo_upgrade.DemoUpgradeTests upgrade/fault cases plus
tests.test_phase41_upgrade.CurrentSourceUpgradeTests.6PASS0skip/fail59.551s,
private phase5-maintenance-regression-final.log. Final checkpoint evidence is
7maintenance PASS39.055s +6regression PASS59.551s,13distinct scoped cases. Earlier
selector-error/individual reruns remain historical, not extra passes. Exact source/
test hashes match receipt, no executable changes after successful qualification.
Only docs/reporting updates follow. Source/target archives used by tests remain
private synthetic fixtures; no newly published release or Android upgrade claim.

## 5.3b pre-lock refusal fix / final exact-source qualification
5.3 source2521be8a6e2b6ce4f3caab39f21ec61471e82bab normally pushed/fetched;
HEAD/FETCH_HEAD/advertised feature remote matched and tree was clean BEFORE this
follow-up. Final review found original stopped() opens a coordination file before
checking marker/binding. New owner CLI could therefore refuse an unmarked state
but leave demo-operation.lock. No identity/data overwrite or writer was created.

Fresh actual filesystem regression reproduced failure on unmarked private fixture:
1FAIL4.892s, extra demo-operation.lock. Fixed maintenance.locked() to inspect state/
recovery and existing prefix binding BEFORE any coordination open, then retain all
fresh checks under original locks. No old guard removed or fallback added.
Test also asserts isolated recovery-marker directory and unbound private prefix
stay byte/file-inventory unchanged. Recovery case is a marker-only refusal fixture,
not a new live-DR qualification. Every directory/sentinel is synthetic/task-owned.

Fresh final tests.test_access_maintenance8PASS0skip/fail49.868s. Fresh final five
original upgrade/fault cases +CurrentSourceUpgradeTests6PASS0skip/fail59.793s,
phase5-maintenance-prelock-{final,regression}.log.14distinct scoped cases, superseding
prior7+6 as final current-source proof; no counts added for repetitions. Exact
published0.4.2 ->CURRENT package, original bytes/pending/identity/bridge/new-state
rollback assertions preserved. asc/demo/upgrade.py unchanged since2521be8, no
Engine/Node/Go/Android/DB/journal/schema/source archive/APK change from this fix.

Update qualification/phase5-maintenance.json with final hashes/results. Stop/plan/
apply/retry/rollback guide is PHASE5-MAINTENANCE. Full Phase5 remains NOT ACCEPTED;
no remote SSH/VPN/provider/device proof and no fresh full regression claimed.
NEXT5.4 after this normal publication: freeze inputs; fresh applicable full Python
under optional hash-locked env and explicit private Go SDK, Go tests/vet/module
verify/applicable builds, integrated security/fault/package checks. Preserve old
archives/APKs/signers/SDKs/identities and real-phone acceptance deferred by owner.

## 5.3 final publication verified / next resume5.4
Source checkpoint2521be8a6e2b6ce4f3caab39f21ec61471e82bab and final fix
c5c1cb0526b1eb09f888dbd649b494d1ea6c3488 each normally pushed, fetched and
HEAD=FETCH_HEAD=advertised feature remote verified, clean tree before next work.
Final source tracked/index455files/0untracked/0secret findings. All exact final
receipt source/test SHA256 verified unchanged. This publication only updates docs/
receipt; no executable/artifact/test changes or extra qualification claimed.

NEXT5.4 from fetched feature/phase5-remote-access latest HEAD, preserve dirty work:
- Mandatory ordered docs, then PHASE5 PLAN/PROGRESS/ACCEPTANCE and access/maintenance
  guides. No redo accepted feature implementation, whole branch merge or reset.
- Freeze exact current source/test/package inputs and record hashes. Use existing
  /workspace/asc-access-dev/edge-env/bin/python (optional dependencies hash locked)
  and command-only ASC_GO=/workspace/asc-cloud/go1.27.3/go/bin/go; default go is NOT
  the qualified SDK. No proxy/CA/HOME/global PATH changes needed.
- Fresh applicable Python discovery including Phase5+legacy/fault/security gates,
  Go tests/vet/module verification/applicable builds, deterministic source-package/
  exact compatibility/secret audits. No old full392/Go/Android receipt relabelled
  fresh. No required fault weakened/skipped to pass; preserve failures/blockers.
- Current old APK/source archives are immutable and no new public release exists.
  Unchanged Android artifact evidence is historical scoped proof only; no need to
  start AVD/ADB merely for this local CLI. Original private signer/SDK/Node data
  preserved, no Termux migration/adoption or phone operation authorized.
- Real Cloudflare/public-host browser/SSH/VPN/provider, ARM64/phones/physical LAN/
  independent domains/OEM/Doze/power/production remain NOT TESTED or deferred by
  owner. Software final qualification cannot mark those PASS. WritableDR and
  Android voter/GC/failover remain locked; full Phase5 NOT ACCEPTED.

## 5.4a source/environment freeze — 2026-10-29
Fetched26ad88e74f7379402946246cb44da0215506cc51; local HEAD/FETCH_HEAD/advertised
feature remote matched, clean tree. Mandatory maps/Phase5 handoff and managed
skill/network policy checked; inherited proxy/CA unchanged, no live credentials/
VPN/provider configured. No phone/SSH/production or SDK/signing operation.

445unique Python tests discovered,0loader errors;42Phase5 cases. Freeze449tracked
inputs SHA e98f57ca952692f33228a46d8b708139bf13f7aa914fe2a8c81bb7bee212d065,
public qualification/phase5-final-source.json +private work/phase5-final/freeze.json.
Six mutable report docs excluded; all code/tests/Go/requirements/packaged guides/
old public archives/APKs/other qualification fixtures included. No executable
change. Fresh smoke JWT/profile/maintenance contract18PASS0skip/fail0.087s; private
optional-env pip check PASS. Full suite/Go/fault/package gates NOT YET RUN at freeze.

Qualified existing workspace Python3.13.5 and Go1.27.3, actual cgroup2CPU/8GiB.
GOMAXPROCS=2 matches prior source qualification and CPU allocation, not timeout/
fence changes. Historical stopped SDK processes are zombies/RSS0, no active guest;
no ADB/signals/recreation attempted. Actual user phone gates remain deferred.

Next5.4b run private work/phase5-final/run.py: fresh uncached Go tests/vet/module
verify/Linux build and Windows/Android cross-build only, then fresh full Python
445 with original fault assertions/64required old markers and all42Phase5 cases.
Use existing private Go/Python paths; no global HOME/PATH/network changes. Logs/
status JSON private, source unchanged checks each phase. NOT ACCEPTED until actual
final gates pass; never label an interrupted run PASS. New source package/provider
release not implied; actual Cloudflare/SSH/VPN/physical/production still outstanding.
