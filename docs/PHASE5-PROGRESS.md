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
