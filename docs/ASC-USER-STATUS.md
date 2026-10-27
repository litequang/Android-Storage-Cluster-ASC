# ASC — trạng thái sử dụng và phần còn thiếu

Nguồn hiện tại: nhánh `feature/phase4-2-android-native`. Kết quả nghiệm thu chi tiết
ở PHASE4-2-PROGRESS/ACCEPTANCE; không suy ra điện thoại thật PASS từ emulator.
Các gói Demo/Native đã công bố và mã nguồn mới nhất có phiên bản khác nhau.

| Nhu cầu | Hiện trạng |
|---|---|
| Đăng nhập Dashboard web | Có mã owner dùng một lần và phiên HTTPS; không phải hệ thống tài khoản nhiều người dùng/mật khẩu |
| Quản lý file trên web | Dashboard Demo có danh sách file, upload/download, SHA-256 và trạng thái hai replica; không có xóa vật lý |
| Quản lý file từ APK | Candidate versionCode4 có nút mở File Manager web hiện hữu ở trang Cụm; chưa có File Manager native/file picker |
| Đăng nhập quan sát Core trong APK | Có ở 4.2i; chỉ đọc node/volume/replica/job/backup/quorum, không có quyền upload hoặc tạo writer |
| Storage Node native | Engine/TLS/enrollment/FGS/I/O và tích hợp Catalog/Dashboard/hai replica/fallback đã chạy thật trên emulator API35 +peer Linux; APK4 đã tải được từ GitHub; API30 Node/workflow+22regression+foreign1 PASS; API35 retained26+1 PASS, cold35 BLOCKED, chưa nghiệm thu điện thoại thật |
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

## Còn thiếu trước bản Native Node candidate hoàn chỉnh

1. Hoàn thiện các gate còn lại sau bài Catalog/Dashboard/replication đã PASS; cold-setup receipt và giới hạn được ghi riêng trong tiến độ.
2. APK candidate4 tăng versionCode, giữ signer/Keystore/Node/volume/bytes; kết quả nâng cấp ghi ở PHASE4-2-ACCEPTANCE.
3. Full383Python0skip/Go11/vet/modules/builds/64fault banners đã PASS trên runtime không đổi; driverAPI30 được kiểm riêng.
4. APK internal và gói Controller đã push/tải lại/checksum PASS; đọc PHASE4-HANDOFF.md.
5. Owner tự nghiệm thu ARM64/điện thoại thật, LAN, Doze/OEM và hai miền lỗi vật lý.

APK Node mới không cần Termux để chạy chính Node, nhưng không thay Controller
Termux hiện hữu và không tự nhận state của nó. Không cài lên M51/production.
Không dùng APK Foundation cũ để suy ra đã có toàn bộ Node/observer ở source mới.

Cloudflare không được bật ngầm trong Phase4.2. Phase5 cần thiết kế/kiểm thử riêng
cho gateway, xác thực, giới hạn quyền và vận hành; không đưa management API/Node
listener trực tiếp lên Internet hay can thiệp tunnel/hosting production hiện hữu.
