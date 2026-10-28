# Phase5.2 Cloudflare adapter — source/synthetic only, no live deployment

5.2a provides a separate version2 edge profile and RS256 Access verifier;5.2b adds
a loopback-only HTTPS origin and connector rendering, not an active tunnel. Private gateway profile1 stays unchanged. Browser HTTPS DNS origin
is distinct from origin listener, which MUST remain127.0.0.1 with trusted TLS.
No public Node/storage/admin/SSH listener, no widening of private profile, no
Controller/identity/schema migration or writable recovery. Existing owner session/
CSRF and runtime-mode restrictions remain additional authorization boundaries.

## Qualified dependency context
Optional requirements-cloudflare.txt pins PyJWT2.15.1, cryptography50.0.2, cffi2.1.1,
pycparser3.12 using official PyPI release wheel SHA256 digests. Linux x86_64/Python
3.13.5 actually installed in /workspace/asc-access-dev/edge-env, pip check PASS.
Python>=3.11 for this lock; other platforms/interpreters NOT QUALIFIED. No global
packages/system environment/old app/SDK/signers changed. Managed image ensurepip
was absent: workspace --without-pip venv plus existing pip --python targeted only
that venv, local verified wheels/require-hashes, no apt/get-pip/network bypass.

On a development host with working Python venv/pip, install ONLY in a NEW private
venv with `python -m pip install --require-hashes -r requirements-cloudflare.txt`.
Keep inherited proxy and CA. Private gateway1 does not import these dependencies
unless the optional edge verifier is constructed; no dependency fallback crypto.
Do not publish generated credentials, bearer JWTs, private RSA keys or browser codes.

## Access contract
One Cf-Access-Jwt-Assertion header, bounded8KiB; no CF_Authorization-cookie fallback.
Only RS256, bounded known kid, no jku/jwk/x5u/critical-header trust. Verify exact
issuer https://TEAM.cloudflareaccess.com, configured64hex application audience,
exp/iat/sub and application type; require valid integer time bounds, <=24h lifetime,
no clock bypass. Standard PyJWT checks signature/issuer/audience/nbf/expiry. Claims
are discarded, never mapped to owner or machine credentials.

Public keys: fixed issuer/cdn-cgi/access/certs endpoint, standard HTTPS CA and
inherited proxy,8s timeout/64KiB body/at most8RSA2048–4096bit keys. Duplicate/private/
wrong-use keys refuse. Cache lifetime300s, global refresh cooldown30s; unknown kid
may refresh within bounds. Old key cannot be used beyond cache expiry if refresh
fails. Within fresh cache lifetime a known key can be used; this is NOT immediate
Cloudflare-policy revocation proof. ASC backend logout/session TTL remains separate.

5.2a tests use real ephemeral RSA signatures with synthetic issuer/key-source
transport. They are NOT Cloudflare-issued tokens/live provider/network proof.
Next5.2b implements separate loopback origin runtime, existing owner-session proxy,
connector config generator and real local TLS/file integration. Do not open a
public endpoint based on unit tests. Live Cloudflare/DNS/Access policy/IdP/tunnel
and real remote client acceptance remain NOT TESTED and require a separate owner
deployment task. Physical phone campaign stays DEFERRED BY OWNER, not PASS.

## Official references checked2026-10-28
- https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/authorization-cookie/validating-json/
- https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/configure-tunnels/origin-parameters/
- https://pyjwt.readthedocs.io/en/stable/api.html
- https://pypi.org/pypi/PyJWT/json and corresponding official cryptography/cffi/pycparser JSON release metadata.

Cloudflare documents signed assertion validation, team public keys and expected
issuer/audience. Tunnel origin parameters support CA trust/server-name/Host settings
and required Access audiences. We will render Access controls per hostname rule,
never depend on an untested top-level setting or noTLSVerify. No Cloudflare SDK/
API credential is available/configured in this managed task; source work does not
create/modify an account, zone, DNS record or connector.

## 5.2b loopback origin contract and source commands

`python -m asc.access.cloudflare --root "$HOME/.asc-edge-dev" init --profile "$HOME/edge-profile.json"`
creates a NEW, separate private gateway identity only; existing incomplete/different
roots refuse rather than regenerate keys. `info` reports public CA fingerprint,
UNKNOWN reachability, no writer authority. It never reads backend private state.

Profile JSON has format2, mode `cloudflare-edge`, frontend_origin canonical public
HTTPS DNS name WITHOUT port/path, listen_origin `https://127.0.0.1:8446`, exact
private upstream_origin, verified upstream_pin, upstream_mode, max_body_bytes,
access_team and access_audience (64lowercase hex). Keep profile owner-only0600,
root0700 outside source/Engine ancestry. Do not convert a format1 private root.
The upstream is the existing DASHBOARD listener, not Controller/node/admin ports.

`python -m asc.access.cloudflare --root "$HOME/.asc-edge-dev" serve` runs foreground
and requires actual configured team public keys before startup. No CLI option to
skip JWT/CA/pin validation or inject a key source. SIGINT/SIGTERM stops only this
owned gateway. Existing pinned backend must advertise the EXACT configured mode;
no Demo/Core/recovery automatic fallback. Core/recovery routes stay read-only.

`python -m asc.access.cloudflare --root "$HOME/.asc-edge-dev" render-connector --tunnel-id CANONICAL-UUID --credentials-file "$HOME/.cloudflared/OWNER-ISSUED-UUID.json" --output "$HOME/edge-connector.json"`
creates a NEW0600 JSON configuration; never reads credentials, overwrites output,
starts cloudflared or creates account/DNS/Access resources. JSON is accepted by the
qualified cloudflared YAML/JSON parser. Use a verified pre-existing owner-managed
named tunnel only in a future separately authorized deployment. No Quick Tunnel.

Rendered configuration has one public hostname ->loopback HTTPS, verified public
caPool/IP SAN, exact public HTTP Host, noTLSVerify=false, per-rule Access required/
team/audience and final404. The public CA is not a private key; independently verify
its fingerprint before connector installation. Each request ALSO validates the
signed assertion in ASC before connecting to backend. Only the correct __Host ASC
owner cookie passes upstream; CF cookies/assertion/email/forwarded identity never
pass. Existing owner session/CSRF remain mandatory, limits/deadlines/routing remain
in the shared private gateway. No session/Catalog/Registry/Engine duplication.

Stop with Ctrl-C for rollback; return to existing LAN/private access. Keep edge
identity/config for diagnosis, never restore old Controller DB or regenerate Node
IDs. No release/archive/APK/installed service changed by this source checkpoint.

## Qualified connector binary (offline only)
Official cloudflare/cloudflared2026.10.5 linux-amd64,40263303bytes,
SHA256 e1bc0cf084fd9e590554fe769a86b1db46701c3f847a43d902f7b974a4e16298.
Digest matched BOTH official release body and asset digest, then actual download.
Workspace-only executable, no system install. Actual `--version`, `tunnel --config
FILE ingress validate` and `ingress rule` for matching hostname/final404 passed.
No `tunnel run`, provider login, DNS/API change or live edge traffic was executed.
https://github.com/cloudflare/cloudflared/releases/tag/2026.10.5

Synthetic tests use actual loopback TLS/owner/Storage bytes and ephemeral real RSA
signatures, with a trusted in-process key TRANSPORT mapping to a real pinned local
HTTPS JWKS server. This is not a Cloudflare-issued token/IdP/account qualification.
CLI init/info/render tested locally; production CLI serve with real issuer keys and
live connector/edge/browser flow remain NOT TESTED. Existing private browser/Core
regressions qualify shared gateway behavior, not edge-provider reachability.

## 5.2c synthetic connector/browser and read-only qualification

Actual Chromium ->separate loopback HTTPS synthetic connector ->verified loopback
edge TLS ->pinned Dashboard ->actual two-node Storage passed. Browser CA trust,
untrusted-CA refusal, owner cookie/CSRF, Vietnamese responsive UI390px, original
PWA criteria/XSS assertions, upload/two logical domains/SHA, actual node stop/
fallback, offline refusal/reconnect/logout all execute. RSA assertion is inserted
server-side by the fixture; not handed to browser JavaScript. Real JWT validation
and real pinned HTTPS JWKS run in the edge. No signature or storage mocks.

TEST-ONLY connector validates its own local Host/Origin before translating to the
reserved public-origin profile. Its public CA/leaf and private leaf key are fresh,
local/private and removed with fixture cleanup. It is NOT a cloudflared replacement,
provider implementation, public DNS path or IdP simulation acceptance. Product
has no second proxy/session/backend added in this checkpoint.

Attempt to use asc.example.com with test Chromium DNS mapping failed BEFORE TLS
with observed ERR_TUNNEL_CONNECTION_FAILED. Original diagnostic misleadingly cited
expected CERT_AUTHORITY_INVALID regexp; it now reports actual bounded error codes,
never URLs/credentials. No proxy/CA/policy override or no-proxy flag was used.
DNS mapping experiment removed, initial failures preserved in PROGRESS. Therefore
REAL public-host browser/Cloudflare/IdP/tunnel remains NOT TESTED/BLOCKED; local
synthetic connector PASS must never substitute for that gate.

Actual Core quorum and passive recovery also pass THROUGH EdgeRuntime: owner login
with real signature,3Go/Python transport partition/heal, no writer/mutation rights;
recovery READ-ONLY with unchanged staged bytes/identity absent. Those two tests use
an in-memory synthetic public-key transport (real RSA/PyJWT), not local JWKS HTTPS;
separate edge browser/API tests provide actual JWKS HTTPS evidence. Passive recovery
metadata comes from existing MemorySource fixture, not live quorum recovery proof.

Command (private hash-locked env, existing Go SDK; no global PATH/HOME changes):
```
ASC_GO=/workspace/asc-cloud/go1.27.3/go/bin/go /workspace/asc-access-dev/edge-env/bin/python -m unittest tests.test_access_edge_qualification tests.test_access_browser tests.test_access_observer -v
```
Fresh6PASS0skip/fail55.833s (edge3 +existing private3), separate from5.2b22+14+2.
No product source changed after5.2b. Full5.4 Python/Go/security/fault gates remain
pending, and no new release/Android runtime/provider deployment is qualified.
Next5.3 operator-controlled private maintenance reuses existing stopped backup/
verify/stage/preflight/code upgrade; no public SSH/custom shell/automatic updater.
