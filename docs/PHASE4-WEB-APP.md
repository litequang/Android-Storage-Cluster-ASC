# ASC Drive Web/PWA — hướng dẫn bản internal

Dashboard hiện hữu có owner login, node/volume, File Manager, upload/download,
SHA-256 và trạng thái replica. PWA chỉ thêm khả năng cài giao diện này vào trình
duyệt; dùng chung API/Registry/Catalog, không có backend hoặc Storage Engine mới.
Đây không phải production release hay bằng chứng nghiệm thu điện thoại.

## Mở và cài giao diện

1. Dùng Controller đã khởi tạo, giữ nguyên state. Theo PHASE4-HANDOFF để nâng cấp
   code bằng backup/preflight; không chạy init để cài PWA. Controller vẫn là
   QuickStart trên máy chủ/Termux được phép; Node APK không chứa Controller.
2. Chạy `run-controller --dashboard` qua launcher hiện hữu. Nếu Dashboard chưa
   được cấu hình, dừng runtime rồi làm `dashboard-init`/`dashboard-trust` theo
   DEMO-QUICKSTART. Không tạo lại CA đang dùng chỉ để chữa lỗi trình duyệt.
3. Xác minh fingerprint của **public CA** qua kênh tin cậy, rồi cấu hình trình
   duyệt/hệ điều hành tin đúng CA. Không chuyển CA private key hoặc bỏ qua lỗi
   certificate. URL phải khớp IP/hostname đã được certificate cấp, ví dụ
   `https://192.168.1.20:8444/`; dùng IP thực tế, không sao chép IP ví dụ.
4. Owner lấy mã đăng nhập bằng `dashboard-code` tại terminal Controller, nhập
   trong trang HTTPS. Mã này khác mã enrollment Node; không lưu/chia sẻ mã hoặc
   cookie trong báo cáo. Không có mật khẩu mặc định hay tài khoản đa người dùng.
5. Khi trình duyệt cho phép, bấm **Cài ASC Drive** hoặc dùng menu cài ứng dụng
   của Chrome. Nút chỉ hiện khi trình duyệt cung cấp khả năng cài thực tế. Nếu
   không có, tiếp tục dùng tab HTTPS bình thường; không hạ cấp sang HTTP.
6. Chọn file nhỏ, upload, chờ backend xác nhận hai replica trên hai điện thoại/
   failure domain đã được owner duyệt. Chỉ byte upload xong chưa phải protected.
   Download rồi đối chiếu SHA-256; thử fallback khi một Node thử nghiệm offline.

APK Node có thể mở URL Dashboard đã xác minh. PWA không start/stop Termux hoặc
Node, không truy cập thư mục Android và không giữ node/admin token hay private
key. Chủ dự án vẫn phải tự nghiệm thu Chrome Android/public CA/cài PWA thực tế.

## LAN và mất kết nối

Không cần dịch vụ Internet để xử lý request trong LAN nếu các thiết bị vẫn có
IP, kết nối được tới Controller và TLS hợp lệ. Chưa có nghiệm thu điện thoại khi
ngắt Internet router; không gọi SDK NAT là bằng chứng LAN vật lý. Không tự tạo
hotspot/Wi-Fi Direct. Cloudflare/remote access là Phase5, chưa triển khai.

Service worker chỉ chuyển request điều hướng `/` tới mạng. Không cache API,
file, mã đăng nhập hay catalog; không offline-write, background sync hoặc tạo
quyền ghi khi Controller mất. Nếu mất Controller, giao diện phải báo UNKNOWN/lỗi
và không xác nhận upload thành công. Không có trang offline được cache.

## Dừng, cập nhật và quay lại

Đăng xuất để hủy owner session; đóng/gỡ PWA chỉ gỡ giao diện trình duyệt, không
xóa state Controller/Node. Dừng Node bằng notification/app, Controller bằng
Ctrl+C và chờ thoát. Không uninstall APK để xử lý signer hoặc identity lỗi.

Trước cập nhật Controller: dừng dịch vụ, backup +verify, stage vào release mới,
preflight rồi upgrade theo PHASE4-HANDOFF. Quay lại chỉ bằng code-only rollback
tương thích với **backup mới**; không chép DB cũ lên dữ liệu mới. Nâng cấp APK
phải đúng signer/versionCode tăng, giữ dữ liệu. Android từ chối downgrade APK cũ
là bảo vệ cần giữ nguyên; không dùng uninstall/clear data hoặc ép `-d`.

Bằng chứng tự động: fixed asset/manifest/PNG/CSP/no-store, Chromium profile riêng
với CA tin cậy, service worker hoạt động, installability, upload/replicas/SHA,
XSS/mobile/offline và Core observer read-only. Cài/mở/gỡ thực tế cũng đã thử trong
Chromium Linux bằng CDP. Đây không phải kết quả cài PWA trên Chrome Android.
