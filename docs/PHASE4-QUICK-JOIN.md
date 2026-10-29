# Phase4.0 Quick Join — Linux synthetic candidate, not Android release

Source candidate0.4.2-dev on feature/phase4-core-demo-integration. No Core/Demo
state merge. Owner Dashboard belongs only to marked Demo single-writer Controller.
Existing Core3D backup/verify/passive staging remains separate; writable disaster
recovery is BLOCKED. Do not run Demo on Core or RECOVERY_READ_ONLY state.

Use a verified installed candidate and existing DEMO-QUICKSTART for approved LAN,
Termux/dependencies, device guard, private state and HTTPS CA trust. Do not run on
M51/unknown models or important data. Cloud tests do not qualify Android runtime.
Consult PHASE4-ACCEPTANCE and PHASE4-PROGRESS for the actually qualified source,
archive SHA and upgrade paths. These instructions alone are not acceptance evidence.

## Owner and node workflow

1. Keep the existing Controller identity/state. Run its optional Dashboard with
   the existing `ascdemo --state "$HOME/.asc-demo" run-controller --dashboard`.
   Trust only the public Dashboard CA whose fingerprint the owner independently
   verified (`dashboard-trust`); never bypass HTTPS errors. Obtain a Dashboard
   login code using `ascdemo --state "$HOME/.asc-demo" dashboard-code` in another
   Controller terminal. This is a LOGIN code, not a node enrollment code.
2. In Dashboard open **Ghép điện thoại**, select **Tạo mã ghép node một lần**.
   It creates a separate one-use NODE code,600s. Compare the lifecycle Controller
   origin/full PIN/Cluster ID displayed there with the node. Do not put either
   code in URLs/logs/history. The page polls actual registration and shows
   pending storage approval separately; it cannot approve a node. On offline,
   logout or page close the code is cleared; reload does not restore tracking.
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
DEMO-QUICKSTART. Only use direct exact0.4.1-to-candidate and new-state code rollback when the
matching4.0c acceptance records the archive/source hash and passing evidence. Old public0.3/0.4/0.4.1 archives and
checksums remain unchanged. No writable disaster recovery or single-writer/Raft
migration is supported.

## Controlled code upgrade (already initialized Demo0.4.1 only)

Synthetic qualification does not authorize Cloud installation on phones. Owner
pilot is separate. Do not install this candidate over Core/Raft/recovery staging.
Obtain the source-only candidate and trusted expected SHA from the matching Phase4
acceptance/handoff, not an invented GitHub release URL. Do not use the old released
0.4.1 download command to obtain0.4.2-dev. Verify before extraction, for example:

```sh
sha256sum -c asc-demo-alpha-0.4.2-dev.tar.gz.sha256
mkdir -m 700 asc-phase4-candidate
# Destination must be a NEW empty approved directory, outside private state.
tar -xzf asc-demo-alpha-0.4.2-dev.tar.gz -C asc-phase4-candidate
python3 -B -m asc.demo.package --help
```

The checksum file must match the independent trusted handoff SHA; merely trusting
a checksum supplied beside an untrusted archive is insufficient. Package install/
stage additionally verifies release.json and every file. The Python help command
above is optional from the checked source tree; it does not install anything.

Stop foreground Controller and Storage Node on every synthetic installation with
Ctrl+C; wait for exit. Keep identities/data. For EACH installation, use its OLD
installed launcher and actual state/prefix (examples for the default layout):

```sh
ASC_STATE="$HOME/.asc-demo"
ASC_PREFIX="$HOME/.local/share/asc-demo"
ASC_RUN="$ASC_PREFIX/bin/asc-demo"
# Choose a NEW backup path on an approved private destination; never overwrite.
ASC_BEFORE="$HOME/asc-before-phase4-unique"
sh "$ASC_RUN" --state "$ASC_STATE" backup "$ASC_BEFORE"
sh "$ASC_RUN" --state "$ASC_STATE" verify-backup "$ASC_BEFORE"
sh "$ASC_RUN" --state "$ASC_STATE" stage "$PWD/asc-phase4-candidate/asc-demo-alpha"
```

Read the returned candidate release_id; retain the old installed release_id
from the private prefix install.json for compatible code rollback. These are code
hashes, not credentials. Then substitute the checked candidate release ID:

```sh
ASC_RELEASE='<verified-candidate-release-id>'
sh "$ASC_RUN" --state "$ASC_STATE" upgrade-preflight "$ASC_RELEASE"
sh "$ASC_RUN" --state "$ASC_STATE" upgrade "$ASC_RELEASE" \
  --backup "$HOME/asc-phase4-activation-backup-unique"
sh "$ASC_RUN" --state "$ASC_STATE" verify-backup "$HOME/asc-phase4-activation-backup-unique"
sh "$ASC_RUN" --state "$ASC_STATE" diagnose
```

Do not use candidate `install` to overwrite an existing code prefix or init state
again. Activation requires stopped services and makes/verifies a NEW backup.
Upgrade sequentially with all writers stopped, Controller code first then each
node; no rolling-write availability claim. After all succeed, start Controller
(with --dashboard if explicitly initialized/trusted), then nodes as before.
Node ID/Cluster ID/Volume ID/medium/PIN/credentials and pending context stay in
private state. A preserved pending0.4.1 join can resume with quick-join; no new code
is required for an already-committed lost ACK. Unknown status remains UNKNOWN.

If compatible code rollback is necessary, stop ALL services again. On each
installation use current launcher and retained old0.4.1 release ID; make a NEW
backup of the CURRENT state, including files written after upgrading:

```sh
ASC_OLD_RELEASE='<retained-exact-0.4.1-release-id>'
sh "$ASC_RUN" --state "$ASC_STATE" upgrade-preflight "$ASC_OLD_RELEASE"
sh "$ASC_RUN" --state "$ASC_STATE" rollback "$ASC_OLD_RELEASE" \
  --backup "$HOME/asc-new-state-before-code-rollback-unique"
sh "$ASC_RUN" --state "$ASC_STATE" verify-backup "$HOME/asc-new-state-before-code-rollback-unique"
```

This selects old compatible code and KEEPS new state/bytes; it never restores an
old database. Unsupported formats/capabilities/absent volume/corrupt backup must
refuse; preserve everything and inspect redacted diagnose output. Old0.4.1 lacks
Quick Join wizard but can resume its compatible pending context through existing
`join --controller ... --pin ... --name ...` and hidden code input. No promise of
Termux-to-APK, single-writer-to-Raft or writable-DR migration. Do not publish private
backup/keys/tokens/grants or raw logs when handing off diagnostics.
