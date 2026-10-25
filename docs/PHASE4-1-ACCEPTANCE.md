# Phase4.1 acceptance

**NOT ACCEPTED — implementation targeted gates passed; fresh full qualification pending.**
Baseline b9e7577, separate feature/phase4-1-local-engine-quorum-ui. Architecture,
IPC/threat/native contracts, real private bridge/lifecycle/Quick Join and Core
read-only endpoint/shared HTTPS browser gateway implemented. Per-checkpoint targeted
evidence in PHASE4-1-PROGRESS; full applicable regression still pending. No
historical full PASS reused.

Required: same-UID/auth/scopes/framing/paths/ownership, actual engine Quick Join/
lost ACK/restart/identity, lifecycle/parent-death controls if supported, Core actual
quorum loss/stale Leader/Controller loss/partition/reconnect, trusted browser TLS/
CSRF/read-only server enforcement, exact Phase4.0 upgrade/NEW-state code rollback,
all old Python/Go/fault/security/build/package gates. No skip/weakening for PASS.

Only Linux synthetic may be accepted after those gates. Android/Windows runtime,
APK/Binder/Keystore/SAF/Doze/real media/Termux migration NOT TESTED. Cross-builds
are compile only. Core3D writable recovery remains NOT ACCEPTED/BLOCKED; no quorum/
Leader/epoch/fencing reconstruction, state mode copying or recovery activation.

## Pre-full source candidate

0.4.3-dev source-only,124 files/228052 bytes; SHA
96260f1709f6a9db6cb98869fbef8fc2313feaf68a4f12da354665ad04693c04;
release ID0568d5a91c32ab210fe8c39dc52be5e1862de994bf65ecd501a1e55af019e81f.
Exact deterministic source rebuild/unpacked private path/secret audit PASS. Original
archives and27 original Core tests unchanged; external/Go source unchanged, original
Core observer delegation is bounded/read-only. New0.4.2->candidate test includes
pending two ways/installed bridge/private control/new bytes/code rollback. This
is NOT Android acceptance or a public release. No adb/sdkmanager/gradle on PATH;
no APK skeleton/toolchain/runtime qualification. Full311 unique cases pending.
