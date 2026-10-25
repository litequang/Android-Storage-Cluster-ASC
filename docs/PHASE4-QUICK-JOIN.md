# Phase4.0 Quick Join — Linux synthetic candidate, not Android release

Source candidate0.4.2-dev on feature/phase4-core-demo-integration. No Core/Demo
state merge. Owner Dashboard belongs only to marked Demo single-writer Controller.
Existing Core3D backup/verify/passive staging remains separate; writable disaster
recovery is BLOCKED. Do not run Demo on Core or RECOVERY_READ_ONLY state.

Use a verified installed candidate and existing DEMO-QUICKSTART for approved LAN,
Termux/dependencies, device guard, private state and HTTPS CA trust. Do not run on
M51/unknown models or important data. Cloud tests do not qualify Android runtime.
Phase4 final candidate archive/upgrade evidence is pending until4.0c.

## Owner and node workflow

1. Keep the existing Controller identity/state. Run its optional Dashboard with
   the existing `ascdemo --state "$HOME/.asc-demo" run-controller --dashboard`.
   Trust only the public Dashboard CA whose fingerprint the owner independently
   verified (`dashboard-trust`); never bypass HTTPS errors. Obtain a Dashboard
   login code using `ascdemo --state "$HOME/.asc-demo" dashboard-code` in another
   Controller terminal. This is a LOGIN code, not a node enrollment code.
2. Owner-session API below creates a separate one-use NODE code,600s. Quick Join
   UI is the next checkpoint; until then retain the existing `pair` CLI or use a
   trusted same-origin session client. Do not put either code in URLs/logs/history.
3. A new approved node needs explicit Demo init first. Do NOT init an existing
   initialized device again or copy someone else's state. Example ONLY for a
   new synthetic/private test installation (replace private LAN IP):

   ```sh
   ascdemo --state "$HOME/.asc-demo" preflight
   ascdemo --state "$HOME/.asc-demo" init --role node --host 192.168.1.22 --port 9443
   ```

4. From the owner, independently compare the Controller lifecycle HTTPS origin,
   full SHA-256 certificate PIN and Cluster ID. These are distinct from the
   Dashboard CA/port. Pass these public bindings; the code is requested hidden:

   ```sh
   ascdemo --state "$HOME/.asc-demo" quick-join \
     --controller 'https://192.168.1.10:8443' \
     --pin '<full-owner-verified-controller-SHA256-PIN>' \
     --expected-cluster-id '<owner-verified-cluster-UUID>' \
     --name 'Demo test node'
   ```

   Do not paste a real code as an argument. Missing options are prompted. On lost
   ACK/network failure, retain all state and repeat the same command; pending
   operation/token is reused. If the underlying code expired, obtain a fresh
   owner code and append `--new-code`; it replaces the code, not the identity.
   Never delete pending context/node.json to solve enrollment errors.
5. `registered` with confirmed_join_receipt proves the join response was checked.
   `identity_present` retains existing identity but current Controller confirmation
   may remain UNKNOWN. Neither grants storage access. Owner must use the existing
   explicit storage-init/approve CLI flow and independently confirm a physical
   failure domain (see DEMO-QUICKSTART). Two volumes/identities on one phone are
   not independent replicas. No auto-volume/start/approval occurs here.

## Owner API / future app contract

Same Dashboard HTTPS origin, existing Secure/HttpOnly/SameSite owner cookie and
CSRF header; no CORS/bearer credentials in browser. POST
`/api/v1/quick-join/pairings` with `{}` returns201 with version1, pairing_id,
code,expiry,Controller origin/full PIN/Cluster ID. GET that path plus pairing_id
returns current state waiting/expired/registered/revoked/unknown and separate
storage_approved/failure_domain. GET never reveals a code.8/session32global;
only hashes retained server RAM. Unknown approval stays null, not false success.
Logout/restart discards session/tracking; an unconsumed unexpired Core code may
still be valid. This is not a revocation control.

Node/app enrollment must persist its local private pending context before POST,
validate pinned /api/v1/info and trusted expected Cluster ID, then use the existing
Core join/retry protocol. Browser cannot become a storage node or store node/admin
credentials. Native bridge, Keystore/SAF and Termux-to-APK migration are deferred.
No automatic failover, Raft activation, physical GC or recovery writer.

## Upgrade / rollback boundaries

No schema change; legacy pending format unchanged. Stop every local service and
make/verify a NEW complete private backup before selecting compatible code.
Never restore an old database over newer bytes/history. Follow installed
backup/verify-backup/stage/upgrade-preflight/upgrade/rollback contract from
DEMO-QUICKSTART. Direct exact0.4.1-to-candidate and new-state code rollback are
NOT claimed until4.0c evidence is recorded. Old public0.3/0.4/0.4.1 archives and
checksums remain unchanged. No writable disaster recovery or single-writer/Raft
migration is supported.
