# Native TLS stream facade1 — h.2a

Scope: trusted in-process JSSE transport for reusing existing Python HTTP/Storage
services. No Storage Engine, Catalog, Registry, management IPC, Node start/FGS or
HTTP protocol is implemented here. No product listener is created by binding or
restarting the app. The raw echo/frame exists ONLY in the test APK.

NativeTLSListener accepts an already validated native SSLContext from the sealed
f.2 identity provider. Requires SDK30+ and original native M51/unknown-device gate.
Only explicit numeric RFC1918/loopback IPv4; no wildcard, DNS or public bind. Port0
is reserved for trusted synthetic tests; a product config must require1024..65535.
No default bind or automatic selection. TLS1.2/1.3 only, no TLS downgrade. Storage
HTTP will still require the original Controller-introspected bearer scopes; TLS
handshake alone is never Node/storage/owner authorization.

Owned accepted SSLSocket capabilities expose bounded read/write, peer address,
read timeout and close, no raw fd/path/PID/shell. NativeSocket adapts only the
Core stream handler's read-only binary makefile, sendall, timeout, peer and
shutdown/close operations. Java byte[] crossing preserves all256 byte values;
per-call/chunk limit65536. Buffered read1/readinto keep streaming semantics. File
wrapper close does not steal socket ownership. Unsupported file modes/unbounded
timeouts refuse. Java failure details are replaced by fixed OSError labels.
No hidden Android descriptor API, /proc reopening, plaintext key/file/tunnel or
OpenSSL executable. This is not a general drop-in CPython SSLSocket.

## Deadlines / ownership

setSoTimeout bounds Java reads, not writes. Every accepted connection separately
has an absolute deadline (default120s, allowed1..900s) which cannot be extended by
read timeout/trickle traffic. One task-owned scheduled executor closes ONLY its
exact socket object. Atomic close cause distinguishes actual deadline from normal
close; cancellation/cleanup idempotent. Owned active set and backlog bounded32.
Listener close unblocks accept, closes owned connections and stops watchdog; no
PID-based stop. read timeout default12s; accept timeout250ms for controlled stop.
Caller must finish Core handler then shutdown/close; facade shutdown closes the
owned TLS connection after handler completion, no unbounded half-close wait.

Real API35 tests proved deadline closes an idle raw peer stuck in TLS read and
interrupts an actual JSSE write while a correctly pinned peer does not consume
application bytes. Write test requires some bytes sent, less than64MiB, actual
OSError, real deadline cause/socket closed and no live worker/active connection.
It is not a success inferred from a timer flag. Linux fake-stream tests prove
only the Python facade contract, not Android TLS.

## Qualification / limits

Read current PHASE4-2 progress/acceptance and qualification/phase4-2h2a-socket.json.
Actual Android guest loopback only; no ADB tunnel or direct LAN claim for these
socket tests. Original signer, same-key install-r, retained enrolled Node/app/
context/TLS/cipher proof before/after faults; no uninstall/clear/re-seed. Existing
real Keystore/context/TLS/canonical Engine/foreign-caller gates rerun separately.
New crypto dependencies or Android permissions: NONE. No public APK/release.
API26–29 TLS NOT QUALIFIED, ARM64/phone/OEM/Doze/direct LAN NOT TESTED or unaccepted.
Prior Quickstep ANR means physical-touch usability remains NOT QUALIFIED.

## Next boundary (not implemented by h.2a)

h.2b must dispatch NativeSocket into the SAME Core StorageHandler/StorageEngine
with bounded original authorization/constraints, not copy HTTP/storage logic or
add an unauthenticated plaintext backend. Explicit encrypted local-volume config,
Node/manifest/volume/medium identity and partial-setup/corruption guards are
required before product serving. Never adopt APP_PRIVATE_PROBE_ONLY as network
Node storage. No absent manifest/marker regeneration. Owner Core storage/domain
approval remains separate from app-local quota consent.

Then an actual owned Agent/Foreground Service must use canonical heartbeat,
measured capabilities and real authorized transfers, safe lifecycle/Stop and
revocation/outage/restart tests. No fake idle FGS, Android Raft/GC/failover or
writable DR. Core observer remains read-only; direct LAN and fresh full regression
are later gates. Binary TLS echo is NOT physical file/replica proof or Native Node
acceptance. Full Phase4.2 remains NOT ACCEPTED.
