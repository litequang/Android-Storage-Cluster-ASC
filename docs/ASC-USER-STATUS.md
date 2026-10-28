# ASC — trạng thái sử dụng và phần còn thiếu

Nguồn hiện tại: nhánh `feature/phase4-2-android-native`. Kết quả nghiệm thu chi tiết
ở PHASE4-2-PROGRESS/ACCEPTANCE; không suy ra điện thoại thật PASS từ emulator.
Các gói Demo/Native đã công bố và mã nguồn mới nhất có phiên bản khác nhau.
Core fix8c54728 đã fresh392PASS0skip/all64faults +Go PASS. APK5 giữ nguyên scoped
API30 và API35 Native Node/replica/SHA/fallback/restart proof; phone/ARM64/LAN/OEM chưa nghiệm thu. Trạng thái
tải/checksum/nghiệm thu hiện tại: PHASE4-STATUS và PHASE4-HANDOFF.

| Nhu cầu | Hiện trạng |
|---|---|
| Đăng nhập Dashboard web | Có mã owner dùng một lần và phiên HTTPS; không phải hệ thống tài khoản nhiều người dùng/mật khẩu |
| Quản lý file trên web | Dashboard Demo có danh sách file, upload/download, SHA-256 và trạng thái hai replica; không có xóa vật lý |
| Quản lý file từ APK | Candidate versionCode5 có nút mở File Manager web hiện hữu ở trang Cụm; chưa có File Manager native/file picker |
| Web/PWA | Đã có manifest/icons/install prompt/network-only worker trên Dashboard chung; Chromium Linux criteria và cài/mở/gỡ PASS; Chrome Android chưa thử, không offline-write/cache API/file |
| Đăng nhập quan sát Core trong APK | Có ở 4.2i; chỉ đọc node/volume/replica/job/backup/quorum, không có quyền upload hoặc tạo writer |
| Storage Node native | Exact final5: API30 fresh install/direct4→5/retained Node PASS; API35 cold+retained Node/replicas/browser/SHA/fallback/Controller loss và15TLS/Keystore/Storage faults PASS. Hai miền logic cùng host chưa phải hai điện thoại độc lập; ARM64/phone chưa nghiệm thu |
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

Core GC blocker đã sửa và fresh full392PASS; không cần lặp lại full khi source
không đổi. Controller source mới b423 có exact042->current/NEW-state rollback
proof; exact e69/native-node và c831/PWA043→b423 cũng đã PASS. APK5 không rebuild:
exact published4→FINAL5 trực tiếp và fresh-first5 đã PASS trên API30. API35 cold+
retained Node và15TLS/context/vault/storage faults nay đã PASS; xem receipt
phase4-api35-network-native. Còn owner nghiệm thu phones/ARM64/LAN/2physical
domains/Doze/OEM/ChromeAndroid PWA và upgrade thực trên điện thoại.
Cloudflare/SSH/VPN/remote maintenance vẫn Phase5, chưa triển khai.

APK Node mới không cần Termux để chạy chính Node, nhưng không thay Controller
Termux hiện hữu và không tự nhận state của nó. Không cài lên M51/production.
Không dùng APK Foundation cũ để suy ra đã có toàn bộ Node/observer ở source mới.

Cloudflare không được bật ngầm trong Phase4.2. Phase5 cần thiết kế/kiểm thử riêng
cho gateway, xác thực, giới hạn quyền và vận hành; không đưa management API/Node
listener trực tiếp lên Internet hay can thiệp tunnel/hosting production hiện hữu.


Latest exact043 compatibility supplement: published e69/native-node and c831/PWA
archives ->b423/core-decode upgrade +NEW-state code rollback2PASS0skip51.823s;
qualification/phase4-direct043-upgrade.json. Product/old314inputs unchanged,
full392 retained and new2tests separately targeted, not fresh full394. Any older
NOT TESTED direct043 wording above is superseded only for these exact archives.
APK direct upgrade/Android API35/physical-device scope remains separate.

## Phase5 source continuation — owner authorization2026-10-28
Owner hoãn nghiệm thu điện thoại thật để tổng nghiệm thu sau; không tính PASS,
không chặn phát triển source tiếp. Nhánh feature/phase5-remote-access đã có gateway
HTTPS riêng trên Linux, tái sử dụng Dashboard/File Manager/owner code/session.
19API/regression+1CLI+1Chromium targeted PASS, upload/two logical replicas/SHA/
fallback/restart/offline theo đúng phạm vi synthetic. Xem PHASE5-PRIVATE-ACCESS và
PHASE5-PROGRESS. Source entrypoint, chưa có gói mới. Tailscale/VPN thực tế chưa
cấu hình/kiểm thử, Cloudflare/remote maintenance chưa triển khai; chưa được mở
private alpha này ra Internet. Không thay APK/Termux state hay quyền Controller.
