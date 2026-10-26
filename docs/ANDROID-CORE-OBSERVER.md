# Native Core observer — Phase4.2i

## i.1 canonical client (Linux synthetic qualification)

`asc.observability.native.NativeObserver(endpoint,pin,cluster_id,epoch,mode,
minimum_index=0)` consumes the EXISTING Phase4.1 owner gateway. It does not connect
as a Node, import bootstrap credentials, construct a Catalog, or start a runtime.
Explicit mode is `core-quorum` or `recovery-read-only`; no Demo fallback.

Owner independently verifies the gateway leaf certificate SHA256, expected Cluster
ID/epoch and mode. The native client uses the existing Core pinned transport before
HTTP headers/secrets, checks `/api/mode`, then exchanges the gateway's short-lived
one-use owner code via `/api/login`. This is a gateway observation grant, NOT a
Node enrollment code. The existing secure cookie and CSRF protocol remains intact.
The client checks authenticated state identity/epoch/checkpoint before returning
any data. The current public mode endpoint does not disclose Cluster ID/epoch;
a mismatched authenticated state refuses publication after login, not before code
redemption. Obtain a fresh owner code after an unconfirmed login/lost ACK.

Only `login(code)`, `state()` and `close()` are exposed. Fixed network operations:
GET `/api/mode`, POST `/api/login`, GET `/api/state`, POST `/api/logout`.
There is no arbitrary URL/method/token/path, Node approval, storage upload/download,
membership, GC, promotion or recovery activation operation. Server-side gateway
read-only enforcement is unchanged.

Session cookie/CSRF live only in object RAM. No observer database, preferences,
Keystore record or Node-context schema is added. Process/service death loses the
observer session and requires a NEW owner login; Node identity/enrollment/storage
are untouched. Close attempts logout, always clears local credentials. Gateway
restart invalidates the server session; offline data is UNKNOWN with null capacity/
counts rather than a stale healthy cache. No automatic login retry/code reuse.

The original gateway supplies actual Barrier/term/identity proof, controller/voter
observations, node/volume health, replica protection, jobs and historical backup
evidence. Native client preserves the separate statuses, rejects regressing index
within a session and downgrades unconfirmed quorum/Leader claims. Successful reads
always return read_only=true and writer_authority=false. Recovery data requires
the existing full-byte anchored staging verifier; it never activates a writer.
The RAM index floor is not proof of globally latest history after restart; use an
operator-known minimum when required. Existing Core3D writer recovery stays BLOCKED.

`tests/test_native_observer.py` exercises actual TLS/sessions, wrong-pin/mode before
grant submission, cluster/epoch/floor refusal, server/process session loss,
corrupt passive staging and real three-voter partition/stale Leader/quorum loss/
Controller crash/reconnect. Unit-only leader-flag normalization is separately
identified; it does not replace the actual Raft fault case.

i.1 qualifies only the Linux client. i.2 adds the native integration described
below; its actual receipt and limits are recorded in PHASE4-2-PROGRESS/ACCEPTANCE.

## i.2 native IPC/UI

Stable AIDL transactions0–3 remain unchanged; new `observeCore` transaction4:
`(version=1, requestId, operation, endpoint, pin, clusterId, epoch, mode, code,
trustConfirmed)`. Operations are exactly login/state/logout. Login requires an
explicit private numeric IPv4 HTTPS endpoint, port1024–65535, full lowercase leaf
SHA256, canonical cluster/epoch UUIDs, explicit mode and independently confirmed
owner trust. State/logout accept NO extra bindings/secret/trust. Unknown versions,
paths, hostnames/public addresses, arbitrary operations and Node enrollment codes
refuse. Request UUID identifies a call; login is NOT a durable replay receipt.

Existing own-UID/signature/device/consent gates apply. Existing app Keystore identity
must validate; no automatic provisioning or Node/context mutation. Owner observer
credentials remain in the canonical Python client's RAM, never Binder replies,
preferences, browser or Node context. Logout remains available after consent is
withdrawn. A separate observer lock prevents gateway requests holding the Node
lifecycle lock. Service destruction clears/logs out only its own session. No FGS
is created for passive observation. Payloads over192KiB return UNKNOWN rather than
exceed Binder limits or silently claim complete coverage.

The Vietnamese Cụm page takes gateway endpoint/leaf PIN/Cluster ID/epoch/mode and
one-use OWNER login code, distinct from Quick Join. It displays sanitized source
nodes/volumes, controllers/voters, confirmed Leader, quorum, file protection and
desired/verified/available replica counts, jobs and historical backup states.
UNKNOWN is never zero. Network changes/background clear transient code/trust and
the displayed healthy view; fresh explicit read rechecks the same configured
gateway, no address/discovery fallback. Session is lost after process death; use
a NEW owner code. The observer may be explicitly configured for a separate Core
cluster; this does not migrate or reinterpret the APK's single-writer Node.

Owner setup uses the existing gateway procedure in PHASE4-1-OPERATIONS. Keep its
source owner bootstrap private. Native pin is the gateway LEAF, not the browser CA:

```sh
openssl x509 -in '<private-gateway-root>/dashboard/server.crt' -noout -fingerprint -sha256
python3 -B -m asc.observability.gateway --root '<private-gateway-root>' serve --issue-login-code
```

Read fingerprint, expected cluster/epoch/mode and fresh login code from a trusted
owner channel. Never copy gateway source tokens/private keys into the APK. On Cụm,
enter those bindings, explicitly confirm trust, choose Đăng nhập quan sát; use Đọc
trạng thái Core for a fresh observation or Đăng xuất quan sát. A successful view
grants no approval, writer, quorum configuration, GC or recovery activation rights.
Do not use a browser TLS-error bypass; browser CA trust procedure is unchanged.

Developer qualification uses already-installed task app/test APKs, original signer
and retained Node state. `tools/qualify_native_observer.py` verifies the owned AVD,
creates the existing actual three-voter/TLS/Core gateway fixture, streams a real
replicated_3 file, passes only a private session fixture through ADB stdin, and
executes the actual native UI/Binder test. Gateway HTTPS data goes directly to an
explicit task host private IP, not ADB reverse. ADB carries only test controls;
real Raft transport partitions/heal are required. Temporary control ACK publication
is atomic, not a substitute for actual faults. Never run this on a physical phone.

```sh
python -B tools/qualify_native_observer.py --adb "$ANDROID_SDK_ROOT/platform-tools/adb" \
  --adb-port 5038 --serial emulator-5556 \
  --emulator-owner '<fresh-verified-task-AVD-receipt>' \
  --host '<explicit-task-host-private-IPv4>' --out '<NEW-private-output-directory>'
```

Synthetic same-host storage domains do not prove independent phone hardware.
Android API35 x86_64 emulator evidence does not qualify ARM64/physical LAN/Doze/
OEM/production or Termux migration. Full Phase4.2/final integrated qualification
and increased-version candidate are separate; writable DR remains BLOCKED.
