# Android native IPC1 / foundation only

This is Android Binder, distinct from Phase4.1 Unix-socket IPC and owner browser
sessions. Private org.asc.foundation.EngineService is exported=false and protected
by signature permission. Every Binder method checks actual calling UID equals the
service UID AND PackageManager signature match before state access. A same-signer
but different UID is still denied. No web/local TCP bridge is opened.

AIDL ILocalEngine has explicit stable IDs: approvePrivateProbe=0, request=1
(relative to FIRST_CALL_TRANSACTION). Keep IDs forever; add versioned methods,
never reorder transactions. A real raw-Parcel golden test verifies request ID1.
Version1 only; canonical UUID request ID; fixed fields, aggregate8192UTF8 bytes;
strict operation/argument allowlists. No path/command/PID/URI/provider arguments.

request(version,id,operation,controller,pin,clusterId,name,code,trustConfirmed):
status needs no consent and reports FOUNDATION/device policy, no writer/Node.
Other operations require explicit app-local consent and a qualified diagnostic
device policy. M51/unknown gets device_not_qualified before vault/Engine access.
app_provision creates ONLY application identity; draft_status returns no secret;
save_join_draft encrypts unsent form. engine_info imports actual embedded Core;
volumes reads the approved private capability volume; probe_private_volume performs
bounded real I/O. check_controller uses private numeric IPv4 HTTPS endpoint,
port1024..65535, lowercase64hex TLS pin and canonical expected Cluster ID; sends
only public GET via Core. No redirect, secret/code/token or enrollment authority.

approvePrivateProbe(version,id,quotaBytes,reserveBytes) accepts fixed app-private
scope, quota1..2^40/reserve0..2^40, explicit existing app identity and consent.
No cluster volume/failure-domain approval. Repeated matching binding is idempotent;
configuration conflict/root/marker/manifest loss refuses instead of recreating.

quick_join/resume_join/node_start return native_runtime_unqualified.
stop_owned reports NOT_RUNNING/owned=false, never terminates foreign processes.
Missing observer/measurement is UNKNOWN/null, never fabricated zero/online/protected.
Version/fields/device/consent/identity mismatch fail closed with generic bounded
JSON errors, no raw exception/credential log. Device policy never grants Core
writer/GC/Node authority. Build/emulator library proof !=native joined runtime.

Request ID1 draft retries must match exact retained form; conflict does not overwrite.
Status/GET reads are repeatable; provision validates existing identity and canary;
probe retries perform a fresh bounded capability measurement, not a durable upload.
No generalized mutation journal or native upload API is claimed. Serialized service
operations do not create consensus/owner session. Node/Cluster IDs remain null.

Binder consent/public TLS bindings/encrypted app draft/owner approval/Node TLS
identity are distinct. Native enrollment/resume needs the actual shared Core engine
with explicit native context and reviewed credential/lifecycle providers. No CLI
getpass/HOME monkeypatch, copied Termux private storage, or Kotlin identity/Catalog
fallback is allowed. See ANDROID-ENGINE-INTEGRATION and PHASE4-2-ACCEPTANCE.
