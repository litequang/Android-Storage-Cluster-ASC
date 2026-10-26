# Embedded existing ASC Engine / native Node boundary

Chaquopy16.1/Python3.13 embeds canonical public asc/**/*.py copied by Gradle Sync
from THIS checkout into generated assets; never a Kotlin Engine/Catalog/enrollment
rewrite. JVM app and Android JNI own one app UID, no Termux access/subprocess or
Go voter. ABI x86_64 actual emulator qualification; arm64-v8a package/build only.
Dependency hashes in Gradle verification-metadata, plugin/version pinned.

EmbeddedEngine.info imports actual asc.storage.engine.StorageEngine with bundled
SSL/SQLite. native_engine.self_test is internal Android instrumentation, NEW app-
private synthetic root, fixed NON-network actor android-qualification-only, real
existing initiate/upload/commit/download/verify/recover/SHA and writable/fsync probe.
It creates no network Node/Cluster identity/token/controller/listener. No physical
GC or data deletion beyond original owned probe cleanup. Existing root/link refuses.
Instrumentation never substitutes mock success or patches Core platform/device APIs.

First actual test correctly failed unsafe_path: Android Context.filesDir can use
/data/user/0 alias symlink. Trusted Context.filesDir.canonicalFile is selected BEFORE
approving a NEW synthetic root. Existing Core no_links/markers/dev-inode/namespace
checks remain unchanged. Never canonicalize away a swap of an already approved
volume or rewrite its marker to fit another path. Preserve ambiguous data.

Actual API35 emulator Engine stream/commit/SHA/fsync/restart PASS (see acceptance).
This proves the LOCAL LIBRARY, not a live Storage Node/Controller. Normal Binder
node_start/quick_join remain native_runtime_unqualified. The existing production
CLI workflow depends on guarded device probe/getprop, globally configured HOME,
hidden code input, subprocess workers and external OpenSSL certificate creation.
No accepted in-process Native Node TLS identity/enrollment/agent/lifecycle provider
exists yet. Do not monkeypatch guards/paths/getpass or copy Termux keys/SQLite.

Next integration must extract/reuse a reviewed explicit-context enrollment/runtime
provider from existing Core, bridge nonexportable Keystore credentials appropriately,
qualify TLS/introspection/device guard/ownership/foreground shutdown/pending resume
and actual two-node byte replication. No new Kotlin enrollment authority; no claim
that current app can join or store cluster replicas. Idle fake FGS stays absent.
Native private capability probes/drafts are separate foundation state, never
approved storage/failure domain, Raft membership or recovery writer. Migration from
Termux and old synthetic probe volumes requires its own tested contract.

4.2f.2 qualifies explicit stable TLS identity/provider separately (native TLS doc),
not the Node. Android returns a standard JSSE context; it is not directly usable
as CPython StorageServer.wrap_socket.4.2h must adapt owned native transport to
EXISTING Python Storage handlers/Engine, including bounds/fresh introspection and
secure protocols. No second Kotlin Storage Engine or product listener is created.

## g.2b enrollment boundary
NativeNodeContext now supplies the original app-private context/provider to
Core NativeEnrollment using the same shared contract/Registry/pinned transport.
Only real Core ACK supplies Node/Cluster identity. No Kotlin enrollment database,
global HOME/getpass/OpenSSL executable or plaintext config is added. This does
not supply a StorageServer TLS socket, live Agent/heartbeat/volume authority or
FGS. h must implement those separately against existing Core services. See
ANDROID-NATIVE-ENROLLMENT; dev ADB loopback is not direct LAN acceptance.

## h.1 shared Agent transport
asc.agent.heartbeat now exposes the unchanged Core heartbeat network/cluster
contract using explicit trusted node config/profile, no CLI HOME/getpass/probe or
filesystem. CLI wrapper reuses it while retaining its guards/capabilities/cache/
repair semantics. This is Linux-qualified source reuse only, NOT a running native
Agent, storage approval, byte proof or FGS. h.2 must implement an owned native TLS
socket adapter to existing StorageHandler/Engine; later owned Agent/FGS lifecycle
must use validated NativeNodeContext, trusted Build/profile and actual volume
probe, and stop on revoked credentials. No fake idle service or writer inference.
