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
