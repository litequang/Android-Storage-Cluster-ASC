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

i.1 does NOT wire Android Binder/UI or claim Android observer runtime acceptance.
i.2 next: fixed authenticated Binder operations, Vietnamese Cụm view, actual
gateway/TLS/emulator qualification while preserving existing signer/Node/state.
