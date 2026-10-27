# Phase4 — gói dùng thử và các gate còn lại

Bản internal, không phải production hoặc nghiệm thu điện thoại thật. Source/runtime
không đổi so với383Python PASS0skip/64fault banners, Go11/vet/modules/builds và
Android26+foreign1; xem PHASE4-2-ACCEPTANCE. Cold integrated run được ghi riêng,
không cộng PASS khi chưa có đủ host report +JUnit.

## Tải đúng gói

Checkpoint artifact3075f69e5fcc65687655afabf80733e1b55dac30 trên nhánh
feature/phase4-2-android-native. GitHub Release upload401, nhưng file đã push bằng
Git và tải lại bằng clone riêng từ GitHub: cả hai SHA256 khớp.

- [APK internal](../android-artifacts/asc-native-node-0.4.0-internal-debug.apk)
- [Checksum APK](../android-artifacts/asc-native-node-0.4.0-internal-debug.apk.sha256)
- [Controller source internal](../candidates/asc-demo-alpha-0.4.3-native-node-internal-source.tar.gz)
- [Checksum Controller](../candidates/asc-demo-alpha-0.4.3-native-node-internal-source.tar.gz.sha256)

APK39,000,362bytes, org.asc.foundation/versionCode4/min26/target35. NodeTLS cần30+;
API26–29 không được nghiệm thu. Signer công khai:
bba77b68e43ecfe885705442d2224977208bf77a397c216393c26fc151a6bc30.
Không có private signer/key/state trong gói. APK cần được kiểm checksum/signer trên
PC tin cậy trước khi chuyển sang máy thử và dùng trình cài Android thông thường;
không cần cài Termux chỉ để chạy Node APK. Controller hiện chưa nằm trong APK.

## Controller có sẵn: giữ dữ liệu, không init lại

Đường đã kiểm Linux synthetic:0.4.1->exact0.4.2-dev->CURRENT0.4.3-dev source.
Không gọi đó là bằng chứng direct0.4.1->internal0.4.3 hoặc phone runtime PASS.
Nếu đang0.3, dùng DEMO-ZTE-0.4.1 trước. Gói0.4.2-dev trung gian nằm trong candidates,
SHA b7904a82c55e41866b374ecb42b873a6796a4f8e5e53a213f648e026467a64a3.
Gói mới source-only có releaseIDe69ebeae3e5ab9a5372465caa8ed5e1882f352fd5f355157299091361f4c6706.

Dừng foreground Controller/Node/bridge/gateway bằng Ctrl+C, chờ thoát. Với MỖI
bước đã kiểm tương thích, xác minh checksum và giải nén vào thư mục MỚI rồi dùng
launcher hiện hữu (đường dẫn chuẩn dưới đây; kiểm lại prefix thực tế của bạn):

```sh
ASC_STATE="$HOME/.asc-demo"
ASC_PREFIX="$HOME/.local/share/asc-demo"
ASC_RUN="$ASC_PREFIX/bin/asc-demo"
ASC_BACKUP="$HOME/asc-before-upgrade-$(date +%Y%m%d-%H%M%S)"
sh "$ASC_RUN" --state "$ASC_STATE" backup "$ASC_BACKUP"
sh "$ASC_RUN" --state "$ASC_STATE" verify-backup "$ASC_BACKUP"
# ASC_UNPACK là thư mục MỚI đã giải nén gói có checksum được xác minh.
sh "$ASC_RUN" --state "$ASC_STATE" stage "$ASC_UNPACK/asc-demo-alpha"
# Đối chiếu ID trả về với gói đã xác minh, không tự đoán ID.
ASC_RELEASE='<release_id trả về từ stage>'
sh "$ASC_RUN" --state "$ASC_STATE" upgrade-preflight "$ASC_RELEASE"
sh "$ASC_RUN" --state "$ASC_STATE" upgrade "$ASC_RELEASE" --backup "$ASC_BACKUP-activation"
sh "$ASC_RUN" --state "$ASC_STATE" verify-backup "$ASC_BACKUP-activation"
```

Không chạy nếu preflight/backup/verify lỗi. Không ghi đè private state hoặc restore
DB cũ lên bytes mới. Giữ releaseID cũ/backup MỚI; chỉ code-only rollback qua preflight
đã kiểm, xem PHASE4-1-OPERATIONS. Không claim mọi direct downgrade đều hỗ trợ.

## Owner thử APK và file trong LAN

1. Chỉ ZTE/Bphone thử nghiệm, dữ liệu bỏ được; không M51/production/unknown-device.
2. Làm theo ANDROID-NATIVE-PILOT: app identity độc lập, Controller HTTPS/pin/Cluster
   do owner xác minh, mã pair dùng một lần, pending resume giữ nguyên operation.
3. Owner duyệt Node/volume/domain bằng CLI hiện có, không app tự duyệt. Termux và
   APK trên cùng điện thoại chỉ là MỘT miền lỗi. Đổi cổng APK nếu9443 đã bận.
4. Start Node từ màn hình đang mở, cho phép notification theo Android, xem heartbeat/
   writable/fsync thực tế. Notification Stop chỉ dừng Node APK. Restart không tạo
   lại identity khi khóa mất/hỏng; dừng để kiểm tra lỗi.
5. Chạy Controller với Dashboard, dùng dashboard-code tại terminal owner như
   DEMO-QUICKSTART. Cụm -> Mở File Manager web mở URL HTTPS LAN đã được owner cấp;
   trình duyệt cần tin đúng public CA, code owner riêng. Core observer chỉ đọc.
6. Upload file nhỏ, yêu cầu2VERIFIED trên2điện thoại/domain, download và so SHA256.
   Dừng một Node, download fallback và so SHA; restart, kiểm lại Node/Volume/PIN.
7. Ngắt Internet của router nhưng GIỮ Wi-Fi/IP, thử lại. Không có LAN thì chưa có
   tự tạo hotspot/Wi-Fi Direct. Không có offline-write hoặc Cloudflare hiện tại.

APK upgrade đã kiểm: EXACT Native3(d1847ce8...)->4, không uninstall/clear/-d.
Published Foundation2->4 direct chưa kiểm. Termux->APK không migration: không copy
khóa/DB/marker. Các bước phone/ARM64/ChromeAndroid/Doze/OEM/2hardware domains phải
owner ghi kết quả, chưa PASS từ emulator. Thu thập version/model/error sanitised,
không token/code/key/private DB/full logcat. Phase5 remote tách riêng, không mở SSH
public hoặc writable disaster recovery để hoàn thành Phase4.
