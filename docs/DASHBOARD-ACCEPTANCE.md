# ASC Controller Dashboard0.5.0 — nghiệm thu source

**SOURCE-READY / COMPLETE cho phạm vi LAN Dashboard single-writer trên Linux
synthetic.** Không phải nghiệm thu Android/phone/production hoặc full Phase4/5.
Source freeze `5919c2c057348261a46c36e8ed646c2d2f84e2a8` trên `feature/dashboard-full`;
487inputs giữ nguyên hash `b017fb0ac3fb609dc2191f4d827ae2620efac3ffba4abdb525a92c296d6da3db`.
Thời điểm xác minh UTC:2026-11-03T03:23:26.457151+00:00.

| Gate thực chạy | Kết quả |
|---|---|
| Fresh full applicable Python | 509PASS /0FAIL/ERROR/SKIP, 2353.336s |
| Test inventory / frozen inputs | 509unique IDs exact, không input thay đổi |
| Required old fault markers | 64/64, Core3A/3B/3C/3D, failover, GC Linux synthetic, observer |
| Go uncached tests | 11top-level +12nested PASS |
| Go vet / module verification | PASS / all modules verified |
| Linux build | PASS |
| Windowsamd64 / Androidarm64 cross-build | PASS, COMPILE ONLY |
| Actual new archive / documented extraction / manifest / secrets | PASS, full suite includes package gate |
| Exact published043 ->new archive ->NEW-state rollback/forward | PASS, credentials/IDs/old+new bytes/operator files preserved |
| Original APK5 /old packages | byte hashes unchanged, no signer/app change |
| GitHub artifact download proof | PENDING separate publication receipt |

Lượt full bao gồm các targeted tests cũ/mới; không cộng các lượt lặp thành số
full lớn hơn509. Nested distribution reuses42old access gates; không gọi chúng
là42case mới. Private complete log/status ở work/dashboard-final, không upload
state/credentials/raw payload. Machine evidence:qualification/dashboard-final.json,
dashboard-final-source.json và dashboard-platform.json.

## Chức năng đã thực chạy

- Owner/Viewer/password/session/CSRF và mã operator bootstrap/recovery.
- Quick Join hiện có, owner preview/confirm/CAS approve/rename/revoke Node.
- File Manager:search/pagination/logical folders/sort/all-latest, explicit immutable
  versions/history, upload/download/replicas/SHA/fallback, durable Core jobs/retry.
- Snapshot metadata nhất quán, giữ toàn bộ selected versions; actual2logical-domain
  byte proof, historical VERIFIED. Restore tạo NEW immutable version với durable
  intent/key/target, lostACK/restart/resume, version collision không overwrite.
- Health/probe/fsync/UNKNOWN, optional UI label/read interval và owner redacted JSON.
- Trusted mobile Chromium, actual synthetic Node offline/restart/Controller loss,
  current/private/exact frozen old Access bundle và Core quorum/recovery read-only.

## Gói và sử dụng

`asc-controller-0.5.0-dashboard-alpha.tar.gz` (300514bytes, 158regular entries including
release manifest; 157hashed payload files).
SHA-256:`4ffcf623ee3d17e51fd191f4fa51ba74096b04274d236cb68c18dea536bed10d`. Release ID:`3e6a9332cf2c8535fabde405730e077d3f4071b357d82482a288d9211dcc5901`.
Base demo1/Registry4/manifest1/metadata1/config1/wire1 unchanged. New binary remains
unpublished until normal push/remote proof; see qualification/dashboard-publication.json
for actual immutable publication commit/download links when complete.
[DASHBOARD-INSTALL](DASHBOARD-INSTALL.md) gives copied Termux upgrade/backup/rollback
commands for existing043 ZTE; do NOT init again. [Operations](DASHBOARD-OPERATIONS.md)
describes all UI functions and scopes. Native Node APK5 is separate/unchanged.

## Giới hạn và nghiệm thu tiếp

Linux one-host fixtures use distinct LOGICAL domains, not two independent phones.
ZTE still has original043Lite; Cloud did not SSH/install/update any phone/M51.
Owner next tests current real SDK/known-device guard, public CA/browser login,
Node/pin/Cluster identity, volume write/fsync, two REAL phones/domains, SHA/fallback,
Controller loss/reconnect/restart, LAN with Internet disconnected and OEM/Doze.
API26–29 Native TLS remains unqualified; verify the unchanged APK pilot contract,
do not bypass its guard. This release does not claim new Android runtime PASS.

Catalog256versions, browser32MiB/file,16snapshots/64restores/128intents,2MiB history.
Viewer reads ALL files, no private-folder ACL/sharing. No physical delete/GC,
remote Node shell/quota/start-stop, auto failover/Raft, production migration or
writable DR. Snapshots are in-cluster references, not independent external backup.
Core/recovery remains read-only; remote gateways stay file-only, no new management
exposure. Unknown/corrupt progress is held, not reset.

## Rollback

Stop owned foreground processes, make and verify a NEW complete state/approved-
volume backup, select retained compatible old043 code via original rollback.
Never restore old SQLite over newer history or recreate identity. Old code keeps
new files/versions and optional account/history/preferences for forward; Lite/code
login replaces new UI until forward. Exact path is in full regression; no phone
or Termux->APK migration is inferred.
