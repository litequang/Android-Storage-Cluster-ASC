# DEMO.4d — Android storage compatibility / Demo 0.4.1

Verified clean local/fetched/advertised Demo baseline:
ef6470d4b91b9c6430591202047ad4c628c9a04a. Branch feature/android-demo-alpha;
Core WIP stays acea2aead8cfd50f8a8fc2b31e24f8f9ccaeb84c. Ordered mandatory docs,
Demo plan/progress/0.4 acceptance/QuickStart read before edits. Current owner now
explicitly authorizes shared storage adapter/engine corrections ON DEMO BRANCH;
prior Core-source-unchanged evidence remains historical. Do not push Core branch.

Owner reports ZTE9045/Android11/ARM64/Termux, initialized0.3 Controller+Storage,
readable online private volume but writable=false/fsync=null/write_denied; direct
open('/') EACCES while own volume/staging open works. This is owner evidence, not
Codex Android testing. Preserve all existing state/IDs/certs/credentials/media.

| Checkpoint | Required gate |
|---|---|
| DEMO.4d.1 | Reproduce old write_denied when ONLY '/' open denied; fix approved-volume descriptor access, audit check/open/remove/fsync/inventory/space/probe; symlink/root/folder/marker/real permissions/security/storage/sandbox targeted tests; docs/secrets/commit/normal Demo push/remote verify |
| DEMO.4d.2 | Real Controller+two enrolled nodes with root-open denial injected ONLY by private test launcher, actual TLS/probe/fsync/two-domain bytes/SHA/offline fallback/restart; existing Dashboard/API/real browser regression; docs/push/verify |
| DEMO.4d.3 |0.4.1 version; EXACT published0.3 and0.4 archive direct upgrade, backup/readback/stage/preflight/activate/IDs/pins/credentials/media/old+new bytes/code-only rollback; fresh full Python/Go/vet/modules/builds/all faults; source-only package/SHA/unpacked secret audit; owner current-ZTE copyable upgrade guide; normal push/remote + immutable public download SHA |

Every checkpoint must actually PASS targeted checks, update CODEMAP/contracts/
progress, inspect tracked+index secrets, normal push and compare remote before next.
Stop on proxy:8080; never change inherited proxy/trust/bypass network. Preserve
published0.3/0.4 archives/DEMO.4 UI/history; no source overwrite/reset/force/main merge.

## Access model / limitations

POSIX metadata-only lstat checks ancestors; it never opens/lists filesystem root.
Only approved absolute root directory is opened O_DIRECTORY|O_NOFOLLOW, and fstat
must match persisted st_dev:st_ino BEFORE opening marker/data. Pin root, staging,
objects and bounded regular single-link marker descriptors; capture/recheck every
ancestor/root/folder namespace identity, marker inode/content/version/change metadata
before/after operations. All child IO/unlink/scandir/statvfs/fsync is descriptor-
relative/no-follow. Replaced/symlink directory/marker fails; ambiguous bytes retained.
No path-based child fallback if required POSIX primitives are absent. Existing
Windows delete-sharing handle adapter remains; directory-fsync limitation explicit.
No volume marker/state/schema/identity regeneration or medium adoption/migration.

Probe success requires actual exclusive create/write/file-fsync/readback SHA,
directory fsync and exact owned-probe cleanup; an existing random-name collision
is never removed. Probe cleanup binds observed file identity and refuses changed/
linked data. Real EACCES stays denial; missing/failed evidence never becomes true.
Inventory/space now use pinned directory descriptors rather than path races.

Descriptor checks do not prevent a malicious owning OS user/privileged actor from
changing the filesystem at arbitrary final syscall boundaries; private approved
roots and trusted local account remain original security assumptions. A moved root
can retain private in-flight bytes on its pinned original descriptor, but postcheck
fails instead of publishing success; no IO is redirected into a replacement root.
No physical power-cut/Android/SD/SELinux qualification follows Linux fault injection.
GC executor's separate Linux-x86 temporary-only walk/capabilities remain unchanged,
not enabled on Android/normal Demo. No Raft/failover/GC/reduction/3D or phone/M51 access.

## Upgrade / rollback handoff

Base formats remain demo1/registry4/manifest1/metadata1/config1/wire1. Old stopped
backup reads marker/full private paths without the broken root descriptor walk;
prove exact old launcher activation against the new package. Never init/join/
storage-init an existing ZTE root to evade errors. Full NEW private backup before
activation and code rollback, no stale DB restore. Old0.3/0.4 code remains schema-
compatible but includes the original Android root-open bug: rollback on that phone
may return write_denied, so it is not a claim of restored working Android storage.
Only publish direct upgrade paths exercised with the actual archives; owner alone
performs real ZTE/Bphone runtime, public-CA trust and two-phone pilot acceptance.


## Completed qualification / publication

DEMO.4d.1/2/3 complete for Linux synthetic source-ready0.4.1. Frozen implementation
/tests/packaged guides dae8e7a:246 Python0skip/0fail,38 targeted, all8 actual Linux
physical faults,11 Go/vet/modules/builds and3 exact-archive installer checks PASS.
Exact published0.3.0 and0.4.0 direct upgrade/code rollback exercised. Public archive
normal-pushed and advertised remote verified at **2bef69ac300a19e7b792a57979596a421c8e0d8c**;
immutable downloaded archive+checksum match qualified SHA
**74932d474c71b57b4904bfa95ff240250fcf12afa400a85015c4c2d41a94edb1**. See DEMO4D-ACCEPTANCE and final
DEMO-TRACK-PROGRESS receipt. No pending mandatory source/release gate. Android0.4.1
remains NOT TESTED; owner-only existing-ZTE/Bphone pilot is next. No phone access,
state reinitialization, old-DB restore or safety unlock authorized.
