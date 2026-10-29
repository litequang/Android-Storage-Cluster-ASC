# Phase4.1 operations — source candidate0.4.3-dev

Linux synthetic only. Read PHASE4-1-ACCEPTANCE for actual qualified commit/archive
SHA and remaining gates. This is NOT an Android release, APK, Termux cross-UID
bridge, migration or writable recovery. Do not run on phones/M51/production.
Existing Demo single-writer and Core quorum remain distinct. No new cluster,
Catalog, Storage Engine, identity, voter or recovery authority is created here.

## Verify candidate / compatible code upgrade

Use the archive in candidates/ on the verified feature branch; no invented release
URL/tag. Compare SHA with independently trusted acceptance/handoff BEFORE extract:

```sh
sha256sum -c asc-demo-alpha-0.4.3-dev.tar.gz.sha256
mkdir -m 700 asc-phase41-candidate
tar -xzf asc-demo-alpha-0.4.3-dev.tar.gz -C asc-phase41-candidate
```

Direct qualification covers exact published Phase4.0 source candidate0.4.2-dev
(SHA b7904a82c55e41866b374ecb42b873a6796a4f8e5e53a213f648e026467a64a3)
to this candidate, pending enrollment in BOTH directions and code-only rollback
with NEW-state backups. Historical0.3/0.4->0.4.1 and0.4.1->0.4.2 regressions are
separate; do not claim untested direct version paths. Exact source/rebuild and
acceptance must PASS before using the path. No schema/state-format change.

Stop ALL local bridge/gateway/Controller/Node foregrounds with Ctrl+C; wait for
owned children to exit. Do not kill foreign processes. On EACH synthetic Demo
installation use OLD launcher/actual paths, not new install/init over existing:

```sh
ASC_STATE="$HOME/.asc-demo"
ASC_PREFIX="$HOME/.local/share/asc-demo"
ASC_RUN="$ASC_PREFIX/bin/asc-demo"
sh "$ASC_RUN" --state "$ASC_STATE" backup "$HOME/asc-before-phase41-unique"
sh "$ASC_RUN" --state "$ASC_STATE" verify-backup "$HOME/asc-before-phase41-unique"
sh "$ASC_RUN" --state "$ASC_STATE" stage "$PWD/asc-phase41-candidate/asc-demo-alpha"
ASC_RELEASE='<release_id returned by checked stage>'
sh "$ASC_RUN" --state "$ASC_STATE" upgrade-preflight "$ASC_RELEASE"
sh "$ASC_RUN" --state "$ASC_STATE" upgrade "$ASC_RELEASE" --backup "$HOME/asc-phase41-activation-unique"
sh "$ASC_RUN" --state "$ASC_STATE" verify-backup "$HOME/asc-phase41-activation-unique"
```

Retain old release_id from private prefix/install.json before activation. Upgrade
Controller code then each node with writers stopped, start Controller as before,
then nodes. No live rolling-write availability promise. Preserve all pending
contexts/IDs/PINs/keys/volume markers. Never copy SQLite between runtime modes.

## Same-UID local bridge against EXISTING Demo node

Separate NEW private control root outside source/state/volumes. Existing device,
dependency, source-selection and installation binding checks apply. Linux synthetic
same UID + app grant only; neither PWA/browser nor another APK UID can call it.
Default read scope; add join/lifecycle ONLY explicitly required by local operator:

```sh
ASC_CONTROL="$HOME/.asc-phase41-control"
sh "$ASC_RUN" --state "$ASC_STATE" bridge-provision --control "$ASC_CONTROL" --allow-join --allow-lifecycle
sh "$ASC_RUN" --state "$ASC_STATE" bridge-run --control "$ASC_CONTROL"
```

In another PRIVATE terminal use the same variables/verified launcher:

```sh
sh "$ASC_RUN" --state "$ASC_STATE" bridge-status --control "$ASC_CONTROL"
ASC_REQUEST_ID="$(python3 -c 'import uuid; print(uuid.uuid4())')"
sh "$ASC_RUN" --state "$ASC_STATE" bridge-node-start --control "$ASC_CONTROL" --request-id "$ASC_REQUEST_ID"
```

Start requires already configured/approved volume and node; no init/approval is
performed. Only this bridge's retained child handle can be stopped, with NEW
request UUID via bridge-node-stop. Replaying start receipt never restarts a dead
process. Parent crash terminates OWN node; explicit fresh start is required.
Process running !=storage writable/fsync/replica/Controller authority. Read status
leaves untested write/fsync null, approved volume identity/actual free-space only.

Quick Join public bindings MUST be independently verified; code hidden prompt:

```sh
ASC_JOIN_REQUEST="$(python3 -c 'import uuid; print(uuid.uuid4())')"
sh "$ASC_RUN" --state "$ASC_STATE" bridge-quick-join --control "$ASC_CONTROL" \
  --request-id "$ASC_JOIN_REQUEST" --controller '<verified-private-HTTPS-origin>' \
  --pin '<verified-full-SHA256-PIN>' --cluster-id '<verified-cluster-UUID>' --name 'Synthetic node'
```

Lost reply: repeat SAME request/bindings with --resume (no original code needed
if engine saved pending/receipt). If asked join_code_required, provide original
code using same ID without --resume. For expired uncommitted code explicitly get
new owner grant, use NEW request ID +--new-code; underlying enrollment operation
stays unchanged. Never delete pending files or identity. Registration may remain
UNKNOWN/pending approval; storage/failure domain require original owner CLI flow.
Journal has256 permanent mutation IDs; exhaustion refuses, no receipt eviction.
Stop bridge before backup/upgrade; no background install/system/Boot changes.

## Core read-only owner Dashboard gateway

Separate Linux-only process, never Demo/Core runtime launcher. Core actual runtime
must ALREADY exist and retain its original guards. Source checkout/candidate at
verified path can run module from its root. Explicit bootstrap is a PRIVATE0600
JSON file outside repository, manually approved by owner, shape:
`{cluster_id,controllers:[{node_id,origin,pin,token},...]}` with EXACTLY3 existing
static voter/Controller endpoints and corresponding owner credentials. Never paste
these credentials into browser, terminal args, docs, logs or public storage.
Storage-node count is not limited3. No discovery/redirect adoption/SQL fallback.

```sh
ASC_GATEWAY="$HOME/.asc-phase41-core-observer"
python3 -B -m asc.observability.gateway --root "$ASC_GATEWAY" init \
  --bootstrap '<private-owner-bootstrap-file>' --cluster-id '<verified-UUID>' \
  --epoch '<verified-existing-epoch-UUID>' --minimum-index '<trusted-minimum-index>' \
  --source-root '<existing-core-state-root>'
python3 -B -m asc.observability.gateway --root "$ASC_GATEWAY" info
python3 -B -m asc.observability.gateway --root "$ASC_GATEWAY" serve --issue-login-code
```

Default HTTPS127.0.0.1:8445. Explicit approved private numeric LAN IP requires
--host at init and independent public CA trust. No wildcard/public bind or HTTP
fallback. Provide ALL known source/volume roots via repeated --source-root;
gateway cannot nest under engine/volume/recovery markers. Never trust self-asserted
CA blindly: compare info CA SHA over independent trusted channel, transfer ONLY
public ca.crt, install in isolated owner browser trust and verify URL/IP-SAN. Never
--insecure/ignore certificate errors/private-key export.

Operator explicit serve flag prints a one-use login code to PRIVATE foreground
terminal, valid300s. Do not redirect into shared logs. Sessions1800s/8max, no shared
password/default owner credential. To issue another code after expiry, stop and
restart serve with flag (revokes all volatile sessions). In browser use HTTPS URL,
enter owner login code. View nodes/files/policy1/2/3/quorum/controllers/jobs/backup;
all storage/approval/GC/membership/download/runtime/recovery mutations403. Refresh
is read-only GET. Existing Demo upload/Quick Join stay only on Demo Dashboard.

Strong Barrier +term/identity observations are point-in-time evidence, NEVER writer
capability. OFFLINE Controller doesn't prove voter dead; UNKNOWN remains UNKNOWN.
Known history floor is operator minimum plus monotone RAM observations, not proof
of globally newest history after gateway restart. Backup VERIFIED is historical;
external archives unconfigured stay UNKNOWN, never authorize GC.

Optional PASSIVE staging: init with --recovery-stage '<verified-stage-root>' and
--manifest-sha256 '<independently-trusted-anchor>' INSTEAD OF --bootstrap, plus
expected cluster/epoch and minimum index. Existing3D verifier checks whole bytes
under shared lock on EACH view. Result RECOVERY READ-ONLY, writer=false; corrupt
stage UNKNOWN, no controller/keys/config/quorum/epoch generation or activation.

## Private backup / safe code-only rollback

Existing Demo backup covers its actual registered engine state/volumes; separate
bridge control and gateway roots are NOT included. Stop those processes and keep
separate complete owner-private backups of these roots (credentials/keys/journals)
on approved private destination; verify exact inventory/SHA/permissions before
changing them. Never upload backups/raw logs to GitHub. There is no automatic
control-root restore/migration tool in4.1; retain original root/inode and fail
closed on binding mismatch, never edit authorization/DB to bypass refusal.

Stop all runtimes again, stage retained exact0.4.2 if absent, use CURRENT launcher
and old checked release ID. NEW backup of CURRENT state includes new bytes/history:

```sh
ASC_OLD_RELEASE='<retained-exact-0.4.2-dev-release-id>'
sh "$ASC_RUN" --state "$ASC_STATE" upgrade-preflight "$ASC_OLD_RELEASE"
sh "$ASC_RUN" --state "$ASC_STATE" rollback "$ASC_OLD_RELEASE" --backup "$HOME/asc-phase41-new-state-before-rollback-unique"
sh "$ASC_RUN" --state "$ASC_STATE" verify-backup "$HOME/asc-phase41-new-state-before-rollback-unique"
```

Never restore an old database over new bytes. Old0.4.2 lacks bridge/Core observer
APIs: stop them and retain separate private roots unchanged; unsupported commands
refuse. Original Demo engine/Dashboard/pending resume remain; existing data download
must match SHA. Standalone Core gateway removal is stopping process and retaining
private config, not reverting Core metadata. Unknown schema/source/identity or
failed backup refuses upgrade. Diagnostics share fixed error labels/redacted test
results only, never grants/tokens/keys/pending context/source configs.

Android runtime, Binder/cross-UID, Keystore, SAF, Doze, native foreground services,
OS kill/reboot/real media and Termux->APK migration require Phase4.2 acceptance.
Core3D writable disaster recovery remains BLOCKED. No APK skeleton is shipped.
