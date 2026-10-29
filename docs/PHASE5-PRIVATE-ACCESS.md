# Phase5.1a — private HTTPS gateway alpha (Linux source only)

This gateway reuses the existing Dashboard/File Manager. It owns no Catalog,
owner session DB, Node token or writer authority. Software qualified on loopback
Linux synthetic only. Actual VPN, public Internet/Cloudflare, Android/Termux gateway,
phones and production are NOT TESTED. Owner defers physical acceptance to a later
combined campaign. Existing Node APK5/Controller archives remain unchanged; the old
published139file archive does NOT include this new source entrypoint. Use the
verified feature/phase5-remote-access checkout; no new packaged release yet.

## Prepare

Use Linux with Python3.10+ and working OpenSSL (qualification Python3.13.5).
Existing Controller/Dashboard must already run in its supported mode. Do not init
it again or copy its private state. Obtain the public SHA256 LEAF pin of its
Dashboard certificate independently (not the CA pin, admin token or node pin).
Browser clients independently verify/trust only the NEW gateway PUBLIC CA below.
Gateway TLS -> pinned upstream HTTPS -> existing authorized services, all encrypted.

An optional operator-managed private VPN can supply an assigned100.64/10 address
on the Linux gateway. This tool neither installs VPN software nor configures ACLs/
routes/tunnels. An address is not proof of membership or connectivity: telemetry
remains UNKNOWN. Never port-forward this private alpha to the Internet. Begin on
loopback for local testing. If owner configures a private VPN later, use its actual
assigned IP with appropriate ACLs; do not widen existing Controller/Node LAN guards.

## Explicit new profile and root

From the verified source checkout, choose NEW names outside repository/engine/
volume/recovery roots. No global HOME or system configuration change:

```sh
ASC_ACCESS_ROOT="$HOME/.asc-access-alpha"
ASC_ACCESS_PROFILE="$HOME/asc-access-profile-v1.json"
# Noclobber refuses to replace an existing profile.
(umask 077; set -C; cat > "$ASC_ACCESS_PROFILE" <<'JSON'
{
  "format": 1,
  "mode": "private-gateway",
  "frontend_origin": "https://127.0.0.1:8445",
  "upstream_origin": "https://127.0.0.1:8444",
  "upstream_pin": "REPLACE_WITH_VERIFIED_64_LOWERCASE_LEAF_SHA256",
  "upstream_mode": "single-writer-demo",
  "max_body_bytes": 33554432
}
JSON
)
# Review the NEW profile; replace the pin and endpoints before init.
python3 -m asc.access.gateway --root "$ASC_ACCESS_ROOT" init --profile "$ASC_ACCESS_PROFILE"
python3 -m asc.access.gateway --root "$ASC_ACCESS_ROOT" info
python3 -m asc.access.gateway --root "$ASC_ACCESS_ROOT" serve
```

Pin/example intentionally invalid until reviewed. Bind is explicit numeric private
IPv4, never wildcard/DNS/public. Upstream must be existing RFC1918/loopback HTTPS
Dashboard, not Controller admin/storage/consensus. Publicly routed addresses fail.
Existing/partial root is never regenerated; identical init is idempotent, conflicting
profile refuses. First runtime startup verifies actual upstream TLS pin AND exact
mode before opening listener. Mode core-quorum/recovery-read-only supports login/
read-only observation only, never upload/refresh/GC/recovery activation.

`info` returns public CA path/hash. Transfer only `dashboard/ca.crt` to the browser
device through a trusted channel and compare its hash out of band. Never transfer
ca.key/server.key or bypass certificate errors. Open the exact frontend URL using
that trust. Issue a fresh one-use owner login code with the EXISTING Controller's
`dashboard-code` CLI and log in through this URL. No gateway password/admin token
or separate owner account is created. Existing backend sessions/CSRF remain the
only file permission authority. Cookie Secure/HttpOnly/SameSite=Strict; gateway
checks external Host/Origin BEFORE fixed upstream translation. It ignores forwarded
identity claims and refuses bearer headers, node/admin/enrollment/shell/GC routes.

File Manager: existing file list/upload/download/SHA/two-replica/protection UI.
Streamed bodies in64KiB blocks, configured upload cap<=32MiB, metadata8KiB,8workers,
idle/request deadlines and ingress rate bounds; existing backend limits also apply.
Do not infer two physical domains from synthetic node IDs. Unknown/degraded stays
as reported by backend. Quick Join/node approval remains local owner CLI, not this
ingress. No offline writes or machine secrets in browser storage.

## Stop / rollback / diagnostics

Ctrl+C (or SIGTERM) stops ONLY this gateway foreground process, with bounded active
request cleanup. Backend remains running and its state/identities/files untouched.
Compatible gateway restart preserves its TLS identity and backend session; restarting
backend invalidates old owner sessions, requiring a new existing-owner code.
For rollback stop gateway and use the original supported LAN Dashboard; never
restore an old registry, delete state or recreate Node identity. Keep the access
root private; no tested key rotation/root migration/phone export is promised.

Errors are fixed labels without request credentials. Wrong upstream pin/mode or
offline backend refuses startup; after backend loss requests return503, no cached
writer/session success. Keep profile/private keys/cookies/codes out of reports.
Report only fixed error labels, source commit, public cert fingerprints and OS.
Live cloud accounts, Cloudflare connector/Access validation, remote maintenance
and hardware acceptance are separate following checkpoints. No Android Raft/GC/failover/writableDR unlock.

Browser-through-gateway now PASS on real Chromium Linux (1targeted12.565s), including actual file bytes and original mobile/PWA/security assertions. This is not Chrome Android, VPN reachability or physical-phone acceptance.

Core/recovery ingress also qualified separately2targeted14.866s: actual three-Go/
Python cohost quorum loss/heal remains read-only, plus passive staging bytes
unchanged over verified TLS. Recovery uses synthetic MemorySource archive metadata,
not a live quorum-recovery authority proof. See exact receipt/progress.
