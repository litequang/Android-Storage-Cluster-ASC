# Phase4 — internal debug snapshot và handoff

**FULL REGRESSION BLOCKED; Phase4/4.2 CHƯA ACCEPTED.**
Lưu artifact đã có targeted proofs để review/tiếp tục, không công bố qualified
release hay nghiệm thu điện thoại. Source Native3914b99/PWAa6bbced, fixture16c0717.
Full cuối184/1ERROR1537.737s; GC lost-ACK/replay chưa đạt. Hai bản thử retry/TTL
đều FAIL và đã loại, không đưa vào gói. [Blocker và next steps](../qualification/phase4-closure-gc-investigation.json).

Gói dưới đây là snapshot debug nội bộ, **không khuyến nghị như bản đã nghiệm thu**.
Giữ các bản đã công bố trước; chỉ chủ dự án tự thử sandbox/thiết bị được phép sau
khi đọc giới hạn. Các bước dưới đây là hướng dẫn, không phải proof phone đã PASS.
Artifact commit `ed1749b5d05dfc886ebdd8027b44df338dcfadcb` đã normal-push và
fresh fetch/ls-remote khớp. Clone GitHub riêng tải lại APK/archive +SHA lúc
2026-10-27 15:00:01UTC: cả hai khớp; [publication receipt](../qualification/phase4-web-native5-publication.json).
Đây chỉ là xác minh artifact debug, không làm full regression thành PASS. Không dùng snapshot để bật GC/Raft/writerDR.

## Gói đúng vai trò

- [Node APK5 internal](../android-artifacts/asc-native-node-0.4.1-internal-debug.apk)
- [SHA-256 APK](../android-artifacts/asc-native-node-0.4.1-internal-debug.apk.sha256)
- [Controller/PWA source](../candidates/asc-demo-alpha-0.4.3-native-pwa-internal-source.tar.gz)
- [SHA-256 Controller](../candidates/asc-demo-alpha-0.4.3-native-pwa-internal-source.tar.gz.sha256)

APK SHA-256: `aec65c2ca5541aab4060e19616204eef8caf4d2f0d6e7a3e27010dd819cf60f5`

Controller archive SHA-256: `c726bd36f107335452da5e59b87614052608ffa92816df727728c9eec4f027fc`

Controller release ID: `c8315bdb08973c4c8cca422a4aa8337362fedebb61bc1a61a721097fa37b9f55`

APK org.asc.foundation/versionCode5/0.4.1-native-node-candidate,39,000,831bytes,
minSDK26/target35. **Native Node TLS cần API30+**;26–29 NOT QUALIFIED. Chỉ x86_64
emulator đã thử; ARM64 chỉ build. Signer public SHA-256:
`bba77b68e43ecfe885705442d2224977208bf77a397c216393c26fc151a6bc30`.
Không chứa private signer/key/state. Kiểm checksum/signer trên PC tin cậy trước
khi chuyển sang máy thử. Các gói/Native APK4 cũ giữ nguyên, không bị ghi đè.

Node APK không cần Termux. Controller vẫn là QuickStart/Termux hoặc Linux; chưa
nằm trong APK. App và Termux khác UID/private state: không copy khóa/DB/marker,
không tự adopt Node cũ. File Manager là Dashboard/PWA chung, không backend mới.

Trên máy đã tải repository/gói đúng commit:

```sh
(cd android-artifacts && sha256sum -c asc-native-node-0.4.1-internal-debug.apk.sha256)
(cd candidates && sha256sum -c asc-demo-alpha-0.4.3-native-pwa-internal-source.tar.gz.sha256)
# Nếu có Android SDK, kiểm certificate rồi so fingerprint bên trên:
apksigner verify --verbose --print-certs android-artifacts/asc-native-node-0.4.1-internal-debug.apk
```

## Controller hiện hữu: không init lại

Đường launcher đã kiểm Linux synthetic: exact0.4.1 ->exact0.4.2-dev ->CURRENT0.4.3-dev.
Nếu còn0.3, đọc DEMO-ZTE-0.4.1 trước; không suy ra direct0.3->candidate đã hỗ trợ.
0.4.2-dev trung gian ở candidates, SHA
b7904a82c55e41866b374ecb42b873a6796a4f8e5e53a213f648e026467a64a3.
E69 old0.4.3 ->new package được thử bằng source-only staging/backup fixture giữ
state, **không phải** exact installed-launcher upgrade proof của đường đó.

Dừng Controller/Node/bridge bằng Ctrl+C và chờ thoát. Với mỗi bước đã kiểm:

```sh
ASC_STATE="$HOME/.asc-demo"
ASC_PREFIX="$HOME/.local/share/asc-demo"
ASC_RUN="$ASC_PREFIX/bin/asc-demo"
ASC_BACKUP="$HOME/asc-before-upgrade-$(date +%Y%m%d-%H%M%S)"
sh "$ASC_RUN" --state "$ASC_STATE" backup "$ASC_BACKUP"
sh "$ASC_RUN" --state "$ASC_STATE" verify-backup "$ASC_BACKUP"
# ASC_UNPACK: thư mục MỚI đã giải nén archive có checksum đúng.
sh "$ASC_RUN" --state "$ASC_STATE" stage "$ASC_UNPACK/asc-demo-alpha"
ASC_RELEASE='<release_id đúng của gói đã verify>'
sh "$ASC_RUN" --state "$ASC_STATE" upgrade-preflight "$ASC_RELEASE"
sh "$ASC_RUN" --state "$ASC_STATE" upgrade "$ASC_RELEASE" --backup "$ASC_BACKUP-activation"
sh "$ASC_RUN" --state "$ASC_STATE" verify-backup "$ASC_BACKUP-activation"
```

Không chạy tiếp nếu backup/preflight/verify lỗi. Không sửa private state hoặc phục
hồi DB cũ đè bytes mới. Các lệnh trên chỉ backup state Controller/Termux, không
backup private APK/Keystore. Chưa có native export/import hoặc Termux→APK migration.

## Thử Node và File Manager

1. Chỉ thiết bị thử được owner cho phép, dữ liệu bỏ được; không M51/production.
   Kiểm model/SDK theo ANDROID-NATIVE-PILOT; không coi minSDK26 là NativeTLS26.
2. Cài APK bằng trình cài Android, giữ app hiện hữu khi update và so signer. Không
   uninstall/clear data hoặc ép downgrade để qua lỗi. Đường thực chạy: published4
   ->các5 nội bộ ->final5, UID/context/old bytes giữ nguyên; **direct published4
   ->FINAL5 chưa thực chạy**, Foundation2->final5 cũng chưa được chứng minh.
3. Theo ANDROID-NATIVE-PILOT: xác minh Controller HTTPS endpoint, leaf fingerprint
   và expected Cluster ID ngoài luồng, nhập mã ghép một lần, resume pending khi lỗi.
   Không tạo identity mới nếu mất khóa; dừng để owner xử lý.
4. Owner duyệt Node/volume/physical domain bằng CLI, không app tự duyệt. Node APK
   và Termux trên cùng phone là một miền lỗi. Nếu9443 bận, dùng cổng được phép khác
   như9445 trong app/cấu hình owner; không kill Termux để chiếm cổng.
5. Start Node từ màn hình đang mở, cấp notification theo Android; xem probe thực
   writable/fsync/heartbeat. Notification Stop chỉ dừng Node APK. Không cam kết24/7.
6. Chạy Controller với `run-controller --dashboard` và lấy `dashboard-code` bằng
   launcher như DEMO-QUICKSTART. App Cụm ->Mở File Manager web mở đúng URL HTTPS LAN.
   Browser tin đúng **public Dashboard CA** đã đối chiếu fingerprint; không copy
   CA private key/bỏ lỗi TLS. Node enrollment code và owner web login code khác nhau.
7. Theo [PHASE4-WEB-APP](PHASE4-WEB-APP.md): mở web hoặc cài PWA khi browser cho phép.
   Upload file nhỏ, chờ2VERIFIED trên2phone/domain, download so SHA-256; dừng một
   Node thử fallback rồi restart kiểm IDs/bytes. Một volume thứ hai cùng phone
   không được tính là domain thứ hai.
8. Thử ngắt Internet router nhưng giữ Wi-Fi/IP. Giao thức dùng LAN, không cần cloud;
   bước phone này chưa nghiệm thu. Không có tự tạo hotspot/Wi-Fi Direct. Mất
   Controller thì không xác nhận ghi mới. PWA không offline-write/cache API/file,
   không start Termux/Node. Cloudflare/SSH/VPN là Phase5, chưa triển khai.

| Endpoint thường gặp | Cách tin cậy |
|---|---|
|Controller API8443|Full leaf SHA-256 pin +expected Cluster ID|
|Dashboard8444|Đúng public CA/hostname +owner code/session riêng|
|Storage Node9443 hoặc cổng owner chọn|Node pin +grant được Controller xác thực|

Đây là cổng ví dụ, dùng đúng cấu hình thực tế và LAN riêng; không bind/public hóa API.

## Dừng và rollback giữ dữ liệu

Dừng Node bằng notification/app, Controller bằng Ctrl+C và chờ thoát; không kill
process theo PID đoán. PWA logout/gỡ chỉ gỡ giao diện, không xóa state Node/Controller.
Controller: backup MỚI +verify trước code-only rollback về release tương thích theo
PHASE4-1-OPERATIONS; không khôi phục DB cũ để mất lịch sử mới. APK4 bị Android từ
chối cài đè final5 đã kiểm và old bytes/identity vẫn đọc được. **Không có APK downgrade
rollback đã nghiệm thu**: giữ app/state, dừng Node và dùng bản sửa cùng signer với
versionCode hợp lệ; không uninstall/clear/-d/copy Keystore để chữa lỗi.

Không đăng token/code/key/private DB/full logcat/browser profile/HAR. Chỉ thu version,
model/SDK, public fingerprint, mã lỗi đã làm sạch, kết quả SHA và bước tái hiện.
Owner điền gate phone/ARM64/LAN/ChromeAndroid/Doze/OEM theo PHASE4-STATUS. API35 cold
vẫn BLOCKED, transport final5 trên35 chưa thử; không miễn gate hoặc cấp writerDR/
Android Raft/GC/failover để gọi Phase4 hoàn tất.
