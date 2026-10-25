# Android native local interface v1

Application org.asc.foundation/min26/target35, own UID/private data. This is NOT the
Termux Unix socket. No shared UID, browser control, source/identity/DB adoption.
Private exported=false EngineService +signature LOCAL_ENGINE permission; each AIDL
request checks Binder.getCallingUid==Process.myUid AND PackageManager signature
match before validation/state access. Same signer from another UID still denied.
No caller-supplied paths/PIDs/commands/Intents/Bundles. Activity ignores intent
commands/extras and grants consent only through explicit local checkbox.

AIDL ILocalEngine.request(int version,String requestId,String operation,String
controller,String pin,String clusterId,String name,String code,boolean trustConfirmed)
returns bounded sanitized JSON. Version exactly1, canonical UUID request ID,8192
aggregate UTF8 bytes, fixed operation whitelist. Non-join operations require all
extra fields empty/false. Join needs numeric RFC1918/loopback HTTPS+explicit port,
full lowercase64hex certificate SHA, Cluster UUID,name<=64,one-use12hex code and
explicit trust confirmation. Reject userinfo/URL paths/query/fragments/public host.
No code/token/key in response/log/browser. No reflection/raw exception text.

Current operations: status (FOUNDATION/UNKNOWN, no identity), volumes (UNKNOWN until
configured), quick_join/resume_join/node_start (native_runtime_unqualified),
stop_owned (owned=false/NOT_RUNNING when no actual owned runtime). Mutation needs
persisted explicit application consent; local app permission is distinct from
Controller owner/node authority. No automatic approval/failure-domain/voter grant.
A successful Binder request/Service process does NOT prove writable storage/Node.

Service is bound to UI, no sticky/startup/boot/foreground worker or external PID
kill. Unqualified starts refuse, START_NOT_STICKY. FGS/notification is NOT SUPPORTED
until actual owned background Engine work is integrated and Android FGS gates pass;
no idle fake FGS. Native Quick Join cannot mint Core pending operations without
existing enrollment engine integration. Any future encrypted form draft must be
labeled DRAFT_NOT_SENT, never an enrolled node/approved volume.

Actual Android/Binder and engine qualification is recorded in PHASE4-2-ACCEPTANCE,
not inferred from JVM policy tests/builds. Preserve Core3D read-only recovery and
all Android M51/unknown/runtime guards. No new Catalog/Storage/enrollment authority.
