# ASC Demo Alpha0.4.1 — DEMO.4d acceptance

**PENDING final fresh full qualification/publication.** Android0.4.1 runtime NOT
TESTED; owner-reported ZTE0.3 issue is evidence of the old bug, not a new PASS.
Branch feature/android-demo-alpha, verified baseline ef6470d4b91b9c6430591202047ad4c628c9a04a.
Core WIP remains acea2aead8cfd50f8a8fc2b31e24f8f9ccaeb84c; shared storage adapter
and engine correction now explicitly authorized ON DEMO BRANCH, no WIP write.

| Checkpoint / gate | Actual evidence |
|---|---|
|4d.1 fix |5050a7912baa58b51d1bf020c758aeb52f97918f, normal pushed/remote verified;61 targeted PASS0skip17.030s |
|4d.2 runtime/browser |72bc61d6c8445e4bc161dc9037515b90b26c269f, normal pushed/remote verified;36 targeted PASS0skip126.761s +new ancestor1PASS0.004s |
| Exact published0.3 and0.4 direct upgrades/rollback |2PASS36.243s; then2upgrades+3installer5PASS37.956s; final combined/full follow |
| Final frozen0.4.1 targeted | **38 PASS /0 SKIP /0 FAIL/ERROR,149.451s** |
| Fresh full246 Python / all physical faults | PENDING |
| Fresh Go/vet/modules/builds | PENDING |
| Final exact archive/install/publication/SHA | PENDING |
| Actual ZTE/Bphone/Android runtime/CA trust/SD/Doze/power-cut/production | NOT TESTED; owner only |

Old root-open walk reproduces readable=true/writable=false/fsync=null/write_denied
when only open('/') is denied. New approved-root descriptor pins persisted medium,
marker/root/folders/ancestors before/after no-follow child IO. No '/' directory open,
absolute child file fallback, permission/SELinux/root or identity bypass. Actual
probe write/read SHA/file+directory fsync and owned-file cleanup must ALL pass;
collision/replacement/hardlink/symlink/marker faults and real unprivileged EACCES
are regression-tested. Details/race/trusted-account model: DEMO4D-PLAN/SECURITY.
Base formats/IDs/credentials/media unchanged; Windows separate handle adapter kept.

Actual synthetic runtime uses private test-only os.open wrapper, not product flag;
TLS, Controller, two enrolled nodes, probes/physical file bodies/two approved domains,
SHA/offline fallback/restart and Dashboard all real. Wrapper advertises only actual
dir_fd capability it delegates; no simulated IO/ACK/success. Existing Chromium CA
trust/auth/CSRF/XSS/mobile/file/offline tests PASS; missing trust is still rejected.
New owner storage-status uses stopped-node Engine probe under existing device/state/
prefix/journal/operation/agent/engine guards; no new network API/initialization.

Both exact checksum-pinned published archives are used, not relabeled new source:
0.3 SHA3bf81c5d94891fa064e2f05f99d60d620b4c5db71c87bb2ee6c89ac72b9a445a;
0.4 SHAb9e186589bb4f5c698c7df2250f94ec32ce1e6e2acb41cf3923ade9e706a29f1.
Old launchers make/verify explicit full backups, stage/preflight/activate under root
open denial. New installed0.4.1 probes/reads old file through trusted Dashboard,
creates another two-copy file, retains Node/Cluster/installation/Volume IDs, PINs,
credentials/certs/keys/medium. Existing0.4 Dashboard private CA/config and all three
UI assets retained. NEW complete backup precedes compatible code-only rollback;
old source under root denial reports original write_denied (EXPECTED) and denies
new upload. In baseline Linux namespace both old and new files still download by
old source with exact SHA, proving code/schema/data preservation, NOT fixed Android
storage after downgrade. No old database restore, format edit or marker recreation.

Candidate only:93 regular public source/assets/guides/manifest members,175301bytes,
release d022f29cb5d4f53835acf5a130a45fb921be73b875cdccaed8e9504e979ab08f,
SHA74932d474c71b57b4904bfa95ff240250fcf12afa400a85015c4c2d41a94edb1.
Unpacked secret/path review0findings. Do not use as a published final package until
full gates and GitHub receipt replace PENDING. Source freeze checkpoint follows
final targeted results; preserve all old archives and accepted Dashboard0.4 report.

Owner existing-ZTE copyable commands, safe stop/backup/SHA/stage/upgrade/identity
snapshot/status/HTTPS+CA/Bphone/replicas/download/rollback:
[DEMO-ZTE-0.4.1.md](DEMO-ZTE-0.4.1.md). General QuickStart/pilot packaged too.
Guide shell blocks pass bash -n; not executed on phones. Rollback requires stop-all
and NEW full private backup; old bug returns on affected Android, no stale DB restore.
