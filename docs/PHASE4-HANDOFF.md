# Phase4 — source mới và hướng dẫn bàn giao

**Linux software scope đã qualified:392PASS0skip/all64faults,314inputs không đổi.**
Toàn Phase4/4.2 trên Android thật vẫn NOT ACCEPTED; đây là internal source/debug,
không production release. Source Core8c54728 khắc phục GC authority quá hạn bằng
reuse kiểm tra cấu trúc, giữ mọi quyền/fence/physical proof. Native APK5 source3914
không đổi, không chứa host-only fix; Node không instantiate quorum Runtime.

New archive được rebuild byte-identical,139files/secret audit PASS, exact042->new
upgrade/pending/IDs/bytes/NEW-state rollback PASS21.649s. Direct exact e69/native-node và c831/PWA043 ->b423 mới cũng đã PASS2tests51.823s,
gồm rollback giữ NEW state; [receipt](../qualification/phase4-direct043-upgrade.json). [Full receipt](../qualification/phase4-core-decode-final.json).
Gói mới đã push và tải lại từ GitHub, checksum xác minh PASS; xem mục publication cuối.
Các archive/APK cũ giữ nguyên. Không dùng software PASS để bật Android GC/Raft/
failover/writerDR hoặc tuyên bố phone/LAN/ARM64/Doze đã nghiệm thu.

API35 latest: [network/Native receipt](../qualification/phase4-api35-network-native.json)
now qualifies SAME retained SDK/exact APK5: archived network1/TLS1/cold Node1/
retained1 PASS. Actual Engine/FSYNC/replicas/browser/SHA/fallback/Controller-loss503,
IDs/pin/context preserved, direct standard SDK eth0/15 (no ADB data relay). Two
startup-ANR failures retained; later real Ethernet became ready with no override.
Fresh15 isolated TLS/context/vault/Engine PASS209.708s/all6Main hashes equal; old
timeout still historical UNKNOWN. All task SDKs STOPPED;7API35 offline images/
32host files private backup/hash-verified. SDK exitSIGSEGV(-11), not clean-powerloss.
Main NOW provisioned; preserve all data, only --resume same private fixture after
fresh owner/network/pin checks. Never fresh init/reset/clone or adopt another Node.
Other SDK30 datasets/signer preserved. Full physical Android/Phase4 NOT ACCEPTED.

Exact direct APK4/7c4ba649 ->FINAL5/aec65c2c now PASS on API30 x86_64:17targeted
Android executions/0fail/skip +3host selection guards, no interim main5. Original
identity/Keystore/volume/bytes preserved, retained5 actual replicas/browser/SHA/
fallback/Controller loss/process death PASS; original4 bytes still readable after
new5 writes. [Final receipt](../qualification/phase4-direct-published45-final.json).
This supersedes old direct4->5 NOT TESTED wording ONLY for the two exact APKs and
this SDK path; not phones/physical LAN/API35 or a full Android acceptance.

Fresh FIRST-install APK5 cũng đã PASS trên blank API30 riêng: network1 +cold Node1
+retained/process death1, actual Engine/TLS/enrollment/replicas/browser/SHA/fallback/
Controller loss. [Fresh receipt](../qualification/phase4-fresh-final5-api30.json).
Không cần cài APK4 trước để đi đường cài mới đã kiểm này. Hai đường riêng20lượt
Android,0fail/skip; chỉSDK30x86_64, chưa ARM64/phone/physical LAN/API35 Node E2E.

## Gói đúng vai trò

- [Node APK5 internal](../android-artifacts/asc-native-node-0.4.1-internal-debug.apk)
- [SHA-256 APK](../android-artifacts/asc-native-node-0.4.1-internal-debug.apk.sha256)
- [Controller/PWA source](../candidates/asc-demo-alpha-0.4.3-core-decode-internal-source.tar.gz)
- [SHA-256 Controller](../candidates/asc-demo-alpha-0.4.3-core-decode-internal-source.tar.gz.sha256)

APK SHA-256: `aec65c2ca5541aab4060e19616204eef8caf4d2f0d6e7a3e27010dd819cf60f5`

Controller archive SHA-256: `6a60bd4180bc338d8c62eff4ef1347082a0e6c0ce36e06143ff53baa791b9d57`

Controller release ID: `b423c5d8e811876ae71a9e0ad41c6ba46acc5b4056b408a8e125875aabcf2aca`

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
(cd candidates && sha256sum -c asc-demo-alpha-0.4.3-core-decode-internal-source.tar.gz.sha256)
# Nếu có Android SDK, kiểm certificate rồi so fingerprint bên trên:
apksigner verify --verbose --print-certs android-artifacts/asc-native-node-0.4.1-internal-debug.apk
```

## Controller hiện hữu: không init lại

Đường launcher đã kiểm Linux synthetic: exact0.4.1 ->exact0.4.2-dev ->CURRENT0.4.3-dev.
Nếu còn0.3, đọc DEMO-ZTE-0.4.1 trước; không suy ra direct0.3->candidate đã hỗ trợ.
0.4.2-dev trung gian ở candidates, SHA
b7904a82c55e41866b374ecb42b873a6796a4f8e5e53a213f648e026467a64a3.
Đường direct **exact e69/native-node hoặc c831/PWA0.4.3 ->b423** đã kiểm thử
upgrade và rollback bằng đúng archive. Kiểm checksum/release ID; không suy ra cho
build043khác. Dừng runtime, backup+verify rồi stage/preflight/upgrade như bên dưới.
Không init lại, không khôi phục database cũ đè dữ liệu mới.

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
ASC_RELEASE='b423c5d8e811876ae71a9e0ad41c6ba46acc5b4056b408a8e125875aabcf2aca'
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
   uninstall/clear data hoặc ép downgrade để qua lỗi. Đường **direct exact
   published4/7c4ba649 ->FINAL5/aec65c2c** đã PASS API30 x86_64 với old bytes/
   Keystore/IDs và Node thật sau update. Không cần qua bản5 trung gian để đi đường
   đã kiểm thử này. Foundation2->final5 và update trên phone chưa được chứng minh.
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
integrated Node vẫn BLOCKED; transport final5 trên35 đã PASS5, không miễn gate hoặc cấp writerDR/
Android Raft/GC/failover để gọi Phase4 hoàn tất.


## Publication đã xác minh

Artifact commit `d3b1a9f303a03151d520154d850c407449bb69f9` normal-pushed; fresh
fetch/advertised remote khớp. Clone GitHub riêng tải actual archive248,278bytes +SHA
và APK5/sidecar lúc2026-10-28 00:09:15UTC; cả hai khớp đúng bytes đã audit. Không
phải copy local hoặc claim GitHub Release upload. [Publication receipt](../qualification/phase4-core-decode-publication.json).
Commit báo cáo sau đó không đổi artifact/source. Checksum chỉ chứng minh integrity,
không thay thế các gate phone/ARM64/physical domains/LAN/OEM/API35-final5 còn thiếu.
