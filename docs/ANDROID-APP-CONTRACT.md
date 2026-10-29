# Android application contract — Phase4.2 prerequisites

Phase4.1 is Linux synthetic foundation, NOT Android runtime or APK acceptance.
No skeleton is built merely to claim app support. No available tested Android
runtime/toolchain is assumed; toolchain/device qualification is a separate gate.

Native application owns its own UID-private engine state/keys and exposes a
bound service with explicit signature permission and Binder caller UID checks.
Separate UI visibility from engine service ownership. App authorization maps to
read/join/controlled lifecycle; owner Dashboard session and node credentials stay
separate. PWA/browser cannot start Termux, read its keys, access arbitrary Android
files or invoke process/filesystem operations without a real native bridge.

## Required Android implementation and evidence

- Foreground service: choose applicable Android SDK/service types/permissions and
  start restrictions from current official SDK at implementation time; user-
  initiated start, ongoing notification/stop action, explicit error/health status.
  No promise of24/7 uptime, automatic boot or unrestricted background restarts.
- Keystore: native key provider boundary, alias/version/auth policy and rotation/
  invalidation; distinguish exportable legacy TLS keys from nonexportable keys.
  Never pretend raw Termux key copies import into Keystore without a tested plan.
- Storage: private metadata DB, existing Engine interface; SAF adapter must provide
  equivalent identity/no-traversal/write/readback/fsync or equivalent honest
  durability semantics. User-selected persisted URI grants, revoked/offline media
  UNKNOWN/denial. No guessed paths, broad storage permission/root/chmod workaround.
- Network: explicit owner-trusted TLS/pins, interface/IP changes require reviewed
  binding update preserving identity; no HTTP downgrade/discovery auto-trust.
  Distinguish Controller unavailable, quorum unavailable and storage offline.
- Doze/background: OS network deferral/CPU limits are not device failure proof.
  Persist pending operation before network; reconnect/resume same operation.
  Report gap/time/UNKNOWN and notification instead of fabricated continuous health.
- Process death: OS kill releases ownership; next explicit launch verifies schema/
  source/private state, resumes journal/enrollment safely, never re-init identity.
  Test swipe-away, kill, reboot, permission revoke, interrupted upgrade and power
  scenarios on actual supported SDK/OEM devices; Linux PDEATHSIG is not acceptance.

## Termux -> APK / Core authority migration

Termux and APK have DIFFERENT UIDs and private paths. No shared UID, direct private
folder copy, permission elevation or hidden chmod/provider workaround. Migration
is NOT IMPLEMENTED: design operator-approved export/import, consistent stopped
backup, authority/credential revocation/rotation, volume/medium identity mapping,
format compatibility and rollback. Preserve stable logical IDs ONLY after that
specific path is implemented and tested; copying metadata cannot clone authority.
SAF access cannot automatically adopt original inode/path-bound volume markers.
Single-writer ->Core quorum and writable DR are separate unqualified migrations.
Never initialize voters/epoch or launch recovery staging to get a writable cluster.

## Concrete Phase4.2 order

1. Select/verify official Android toolchain/SDK and native service/IPC contract;
   test authenticated Binder caller/signature/consent and lifecycle on emulator.
2. Implement local provider/Keystore/SAF interfaces with durable request/enrollment
   context, user notification/stop and explicit missing-permission/UNKNOWN flows.
3. Implement app UI against versioned bridge/observer model, verified code/QR
   payload with explicit trusted origin/full pin/Cluster ID; QR is not auto-trust.
4. Qualify real network changes/Doze/OS kill/storage revoke/restart and identity on
   owner-operated approved test phones; no Codex SSH/install/M51/production.
5. Only then design/test operator-approved Termux migration and staged rollout;
   preserve old source/full NEW-state backups and supported code rollback.
No APK, migration or production-ready claim follows Phase4.1 synthetic PASS.
