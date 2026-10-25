# Phase4.1 acceptance

**NOT ACCEPTED — implementation and fresh qualification pending.**
Baseline b9e7577, separate feature/phase4-1-local-engine-quorum-ui. Architecture,
IPC/threat/Core observer/app contracts in4.1a; actual server/bridge/UI/fault gates
and full applicable regression still pending. No historical PASS reused.

Required: same-UID/auth/scopes/framing/paths/ownership, actual engine Quick Join/
lost ACK/restart/identity, lifecycle/parent-death controls if supported, Core actual
quorum loss/stale Leader/Controller loss/partition/reconnect, trusted browser TLS/
CSRF/read-only server enforcement, exact Phase4.0 upgrade/NEW-state code rollback,
all old Python/Go/fault/security/build/package gates. No skip/weakening for PASS.

Only Linux synthetic may be accepted after those gates. Android/Windows runtime,
APK/Binder/Keystore/SAF/Doze/real media/Termux migration NOT TESTED. Cross-builds
are compile only. Core3D writable recovery remains NOT ACCEPTED/BLOCKED; no quorum/
Leader/epoch/fencing reconstruction, state mode copying or recovery activation.
