# Phase5.2 Cloudflare adapter — source/synthetic only, no live deployment

5.2a provides a separate version2 edge profile and RS256 Access verifier, not an
active tunnel. Private gateway profile1 stays unchanged. Browser HTTPS DNS origin
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
