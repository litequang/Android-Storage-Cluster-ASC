# Native TLS identity/provider — checkpoint4.2f.2

This supplies a stable local TLS identity and tested TLS providers; it does NOT
supply enrollment, a Storage Agent, a running Node/FGS or writer authority.

## Explicit providers and format

Core NodeContext accepts an optional trusted in-process tls_provider. Android
NativeNodeContext passes NativeTLSLoader explicitly, not from Binder/config/URL.
The ordinary Linux CPython loader remains separate; Android with no explicit
loader refuses. There is no provider switch after an OS/pin/credential failure.

Explicit native_tls_prepare requires IPC1 UID/signature/device/consent/existing
app key/context. It generates once using BouncyCastle1.83 JCA: EC secp256r1,
SHA256withECDSA self-signed leaf, digitalSignature/serverAuth,365days. No external
OpenSSL/Termux/global HOME or OS provider registration. Existing TLS identity is
validated/reused; missing/corrupt context/wrapping key never triggers replacement.
Context format1 has a typed tls slot: exactly format1/certificate/private_key/pin.
All material is authenticated in the existing app/purpose-bound AES-GCM record;
only public pin/state return through Binder. Node/Cluster/pending/storage stay null.
Application ID, alias, existing draft/probe/Core schemas remain unchanged. Exact
published f.1 source refuses non-null TLS state; no silent old-code adoption.

The TLS key is an exportable SOFTWARE key in process memory, encrypted at rest by
nonexportable AndroidKeyStore AES key. It is NOT a nonexportable hardware TLS key.
No plaintext PEM/key/PKCS12 store is written. Existing app-UID/OS trust remains;
this does not defend against a privileged owner or guarantee RAM zeroization.

## Sealed memory and Android platform policy

Both providers first create anonymous memfds with CLOEXEC +ALLOW_SEALING. Prefer
os.memfd_create. Only if that wrapper is ABSENT on Android, call the documented
public Bionic libc.so memfd_create using typed ctypes(char*,unsigned)->int (API30+).
The UAPI flags are0x0001/0x0002. A denied call is final, not a reason to try another
provider, raw syscall, path or permission change. No root/SELinux/chmod workaround.

Write/readback via owned fd, then require F_SEAL_SEAL/SHRINK/GROW/WRITE, actual
F_GET_SEALS, FD_CLOEXEC and zero links. Descriptor closure is guaranteed on success
and error. Denied mutation/space/seal/readback/descriptor errors fail closed before
credential publication. Tests require actual seals and real readback, not flags only.

The recovered old Android run FAILED because opening /proc/self/fd/N was denied.
That failure is retained. Android now uses its explicitly selected JSSE loader on
bytes read from the already-open sealed fd (pread); it never attempts proc reopen.
This uses ordinary public Android APIs under the same UID/SELinux policy, with no
weakened permission. Linux's explicit CPython loader uses proc descriptors, and
refuses if unavailable; it never falls back to a named disk key.

NativeTLSLoader uses standard CertificateFactory/KeyFactory/Signature to check
self-signature, validity, non-CA EC serverAuth/digitalSignature and cert/key match
via a random challenge. A PKCS12 KeyStore and KeyManagerFactory live only in RAM;
SSLContext is the platform JSSE provider. Test listeners explicitly enable only
TLSv1.2/1.3. There is NO product listener at this checkpoint. Future4.2h must adapt
owned native sockets/lifecycle to the same Core StorageServer/Engine/services and
enforce the same protocol minimum, bounds and fresh Controller introspection.
A Java SSLContext is not a drop-in CPython SSLSocket/HTTP runtime; no claim of that
integration or second Kotlin Engine is made.

API30+ is the intended public Bionic boundary; actual qualification is ONLY API35
x86_64. API26–29 Native TLS is NOT QUALIFIED and refused by the native loader.
minSDK26 still describes the independent app foundation, not Node TLS support.
No ARM64 phone/OEM/Android production acceptance follows these synthetic tests.

Primary sources: Android Bionic libc/include/sys/mman.h (memfd_create API30),
libc/kernel/uapi/linux/memfd.h (flags), standard javax.net.ssl SSLContext/
KeyManagerFactory, java.security Signature and AndroidKeyStore/Cipher APIs.
https://android.googlesource.com/platform/bionic/+/refs/heads/main/libc/include/sys/mman.h
https://android.googlesource.com/platform/bionic/+/refs/heads/main/libc/kernel/uapi/linux/memfd.h
https://developer.android.com/reference/javax/net/ssl/SSLContext
https://www.bouncycastle.org/download/bouncy-castle-java/

## Tests, failure behavior and handoff

Fresh Linux tests cover actual handshake/SHA/wrong pin, key mismatch/corruption,
sealing/close-exec failure/FD closure, no native switch on denial/no disk fallback,
identity reuse and exact old-source refusal. Native instrumentation must cover
actual Bionic ABI/seals/readback/denied mutation, BC/JCA generation +key mismatch,
JSSE handshake against existing Core pin verifier, wrapping-key/cipher loss,
process-death identity retention, old upgrade receipt and original Binder/Engine.
Wrong-pin early close can produce TLS1.3 ticket BrokenPipe/reset before application
read. Fixtures record that separately ONLY for the rejected first peer, never as
success or a successful read; second valid body/SHA remains mandatory.

Results are recorded in PHASE4-2-PROGRESS/ACCEPTANCE and qualification reports only
after observed execution. Old interrupted receipts are not added to fresh PASS.
No direct LAN evidence is inferred from guest loopback or ADB development mapping.
No new public APK/release is implied by this source checkpoint. Future g enrollment,
h Agent/FGS, i read-only observer and j direct network/full regression stay separate.
Rollback requires tested same-signer compatible code at a nondecreasing version,
never uninstall/clear/downgrade-force, copying Termux or restoring stale databases.

## Dependency/lint review

Pinned bcpkix/bcutil/bcprov1.83 JAR+POM SHA256 values match Gradle cache; previous
verification entries unchanged. Initial hashes came over authenticated Maven TLS
(TOFU, not independent publisher signatures). No dependency-source patch.

Lint reports22warnings/0errors:17VN strings,3pinned-version notices,1synchronous
consent commit and1TrustAllX509TrustManager in bcpkix's EST utility. Inspection
identifies org.bouncycastle.est.jcajce.JcaJceUtils.getTrustAllTrustManager. It is
NOT referenced by app source: BC is used only for certificate/signature building;
JSSE uses standard KeyManagerFactory and default system TrustManagers (null init
argument means platform defaults, not trust-all). The native negative handshake
gate must actually reject an untrusted self-signed peer, in addition to the Core
wrong-pin gate. Warning is retained, not suppressed or called a clean security
scan. This bounded call-path/inventory review is not comprehensive binary SAST or
production cryptographic certification; do not use that EST helper in future work.
