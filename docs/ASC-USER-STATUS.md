# ASC — trạng thái sử dụng và phần còn thiếu

Nguồn hiện tại: nhánh `feature/phase4-2-android-native`. Kết quả nghiệm thu chi tiết
ở PHASE4-2-PROGRESS/ACCEPTANCE; không suy ra điện thoại thật PASS từ emulator.
Các gói Demo/Native đã công bố và mã nguồn mới nhất có phiên bản khác nhau.
Candidate5 đã targeted PASS; full cuối FAIL184/1ERROR. Snapshot5 chỉ dành review/
sandbox, không phải release nghiệm thu. Trạng thái
tải/checksum/nghiệm thu hiện tại: PHASE4-STATUS và PHASE4-HANDOFF.

| Nhu cầu | Hiện trạng |
|---|---|
| Đăng nhập Dashboard web | Có mã owner dùng một lần và phiên HTTPS; không phải hệ thống tài khoản nhiều người dùng/mật khẩu |
| Quản lý file trên web | Dashboard Demo có danh sách file, upload/download, SHA-256 và trạng thái hai replica; không có xóa vật lý |
| Quản lý file từ APK | Candidate versionCode5 có nút mở File Manager web hiện hữu ở trang Cụm; chưa có File Manager native/file picker |
| Web/PWA | Đã có manifest/icons/install prompt/network-only worker trên Dashboard chung; Chromium Linux criteria và cài/mở/gỡ PASS; Chrome Android chưa thử, không offline-write/cache API/file |
| Đăng nhập quan sát Core trong APK | Có ở 4.2i; chỉ đọc node/volume/replica/job/backup/quorum, không có quyền upload hoặc tạo writer |
| Storage Node native | Final5 API30 x86_64:28regression+foreign1, normal Catalog/network2case, hai logical replicas/fallback/SHA/process death PASS; một host chưa phải2domain vật lý. APK4/35retained là bằng chứng lịch sử; final5/35 NOT TESTED, cold35 BLOCKED. Điện thoại/ARM64 chưa nghiệm thu |
| Controller chạy bên trong APK | Chưa có; giữ Controller theo QuickStart/runtime đã hỗ trợ, tách khỏi APK Storage Node |
| LAN không có Internet | Giao thức dùng HTTPS/IP nội bộ, không cần cloud/DNS công cộng/CDN; đã có bằng chứng synthetic/NAT, chưa nghiệm thu LAN trên điện thoại thật |
| Không có Wi-Fi/router/hotspot hoặc đường IP giữa các thiết bị | Chưa có tự tạo hotspot, Wi-Fi Direct/Bluetooth hay transport thay thế; phải có mạng nội bộ do owner chuẩn bị |
| Controller mất kết nối | Không tự promote Node/failover; các thao tác cần authorization của Controller bị từ chối |
| Truy cập từ xa qua Cloudflare | CHƯA TRIỂN KHAI/CHƯA NGHIỆM THU, thuộc Phase5 Remote Access |
| Tài khoản nhiều người dùng/ACL/end-user sharing | Chưa hoàn thiện; owner session khác machine credential/Node token |
| Termux → APK giữ nguyên identity/dữ liệu | Chưa hỗ trợ migration; không copy database/khóa/volume marker giữa hai UID |
| Writable disaster recovery | BLOCKED; Core3D staging vẫn chỉ đọc |

## Cách hiểu LAN khi “không có mạng”

Không có Internet vẫn có thể có LAN: các thiết bị cùng Wi-Fi/router hoặc hotspot
do owner bật. Controller và Node phải truy cập được IP/cổng riêng đã phê duyệt;
TLS/pin/CA vẫn giữ nguyên. Việc tự động thiết lập hotspot/discovery không được
giả định là đã có. Nếu không có cả đường mạng nội bộ thì chưa thể truyền file
giữa các thiết bị. Nếu mất Controller, có bytes trên Node cũng không tự cấp quyền
đọc/ghi qua mạng hoặc tạo Controller mới.

## Hai giao diện và hai loại phiên owner

Dashboard Demo dùng runtime single-writer và có File Manager. Owner lấy mã đăng
nhập theo DEMO-QUICKSTART; trình duyệt phải xác minh/tin public CA đúng nguồn.
Không bypass lỗi chứng chỉ. Node/failure-domain approval vẫn theo owner CLI.

Trang Cụm trong APK dùng gateway Core riêng, mã owner riêng và chế độ chỉ đọc.
Nó không biến Demo thành Core quorum hoặc mở upload/download trên Core observer.
Không nhập admin token, Node token hay private key vào các ô mã đăng nhập.

## Phần còn thiếu trước khi nghiệm thu

1. Sửa/qualify original Core GC lost-ACK/replay fault gate; hai trial retry/TTL đã
   FAIL và loại, không tăng budget hoặc bỏ test. Xem receipt blocker.
2. Fresh full384 khi targeted đã đạt. Full383 cũ không nghiệm thu PWA/native5 mới.
3. Snapshot debug5 có scoped Android28+foreign1/JVM17/network2 PASS, bảo toàn signer/
   state; remote SHA chỉ xác nhận artifact, không làm full regression thành PASS.
4. Exact direct published4->final5 chưa thử; đường thực chạy4->interim5->final5.
5. Owner nghiệm thu phones/ARM64/LAN/2physical domains/Doze/OEM/ChromeAndroid PWA.

APK Node mới không cần Termux để chạy chính Node, nhưng không thay Controller
Termux hiện hữu và không tự nhận state của nó. Không cài lên M51/production.
Không dùng APK Foundation cũ để suy ra đã có toàn bộ Node/observer ở source mới.

Cloudflare không được bật ngầm trong Phase4.2. Phase5 cần thiết kế/kiểm thử riêng
cho gateway, xác thực, giới hạn quyền và vận hành; không đưa management API/Node
listener trực tiếp lên Internet hay can thiệp tunnel/hosting production hiện hữu.
