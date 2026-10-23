# CODEX TASK — ASC PHASE 1.1: SECURE NODE LIFECYCLE

**Model: GPT-5.6 Sol — Thinking: High.**

> Cập nhật quy trình 2026-10-23: tài liệu nhiệm vụ Phase 1.1 này tuân theo AGENTS.md hiện hành. Chủ dự án xác nhận Windows 40 tests OK (skipped=3 POSIX installer). Lượt xuất bản v0.4.1 chỉ cập nhật docs/Git, không mở Phase 1.2A hoặc triển khai điện thoại thật.

## Bối cảnh
Làm việc trên repository `ASC-QuickStart-v0.4` đã được giải nén và đưa vào Git. Đây là Android Storage Cluster (ASC) cho nhiều điện thoại Android dùng Termux; Samsung M51 đang chạy AMH Panel / hosting production và tuyệt đối không được tác động. Phiên bản v0.4 mới là single-writer LAN development registry: device profile, role recommendation, HTTPS one-use pairing, heartbeat, local topology snapshot. **Chưa có** Raft, auto-failover, upload/download NAS, backup, dashboard hay Internet gateway.

## Quy tắc bắt buộc
1. Trước khi sửa, đọc đúng thứ tự: `AGENTS.md`, `docs/CODEMAP.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/NODE_PROTOCOL.md`, `docs/DATA_MODEL.md`, `docs/SECURITY.md`, `docs/TROUBLESHOOTING.md`, `docs/CHANGELOG.md`, sau đó `docs/IMPLEMENTATION_PLAN.md`. Chỉ đọc những file nguồn được bản đồ chỉ tới và cần thiết cho công việc. Không quét toàn bộ repo không lý do.
2. Chỉ đọc/sửa mã nguồn trong workspace. Không truy cập SSH, điện thoại thật, database/log production, M51, cấu hình AMH Panel hoặc dữ liệu người dùng.
3. **Codex được chạy test/typecheck/lint/build trên môi trường local phát triển.** Sau sửa mã chạy test liên quan, trước hoàn tất Phase chạy full suite áp dụng được; tự sửa lỗi hoặc báo blocker thực tế. Không bỏ/xóa/làm yếu test để PASS. Dùng lại PASS chủ dự án khi source/test không đổi; không chạy production server, installer trên điện thoại thật hay sửa dữ liệu/private state production.
4. Không root, format SD, gỡ/xóa Termux, sửa Termux:Boot của M51, mở port Internet, tắt TLS verification, hard-code token, sửa thư mục hosting, ghi đè file identity/secret khi cài lại.
5. Không tự triển khai Raft giả, không gọi scoring là bầu Leader; vẫn single-writer LAN development. Không nhận dữ liệu quan trọng vào NAS ở phase này.

## Mục tiêu duy nhất của lần sửa
**Hoàn thiện an toàn và vòng đời đăng ký Storage Node để việc cài một điện thoại mới lặp lại được, có kiểm soát và có thể thu hồi quyền, trên nền tảng v0.4.** Tập trung vào kết quả dùng được, tránh viết lại framework hoặc chuyển đổi stack.

### A. Enrollment / identity
- Giữ mô hình mã ghép nối một lần, ngắn hạn do Controller tạo, pin chứng chỉ TLS. Mã ghép nối là sự cho phép rõ ràng của admin: không cần bấm duyệt thêm lần hai theo mặc định. Dễ nhập trên điện thoại.
- Chống brute-force/rate-limit các endpoint ghép nối và xác thực, không để lộ token, mã ghép nối hoặc dữ liệu nhạy cảm trong HTTP log/lỗi.
- Kiểm tra schema/kích thước và giới hạn dữ liệu gửi lên; tên node không được gây lỗi hoặc chèn dữ liệu. Giữ tính nguyên tử của tiêu thụ join-code và tạo node.
- Installer chạy lại giữ nguyên identity/token cũ; agent đã join không tự tạo node thứ hai. Nếu token bị thu hồi thì hiển thị trạng thái cần ghép lại, không tự ý tái sử dụng secret khác.
- Nếu cần persistent node key hoặc cơ chế rejoin, thiết kế migration có phiên bản, tương thích dữ liệu v0.4, không được làm mất identity đã có.

### B. Admin lifecycle
- Bổ sung CLI quản trị có xác thực để liệt kê node, xem chi tiết, đổi tên, vô hiệu hóa/thu hồi node và tạo mã ghép mới. Node bị thu hồi phải bị từ chối heartbeat và các request có bảo vệ trong tương lai.
- Cung cấp cơ chế rotate/re-pair an toàn, có hành vi idempotent và thông báo rõ khi dùng token cũ. Không hiển thị token đang lưu trong output thông thường.
- Giữ những thao tác này ở Controller; node thường không thể gọi endpoint admin.

### C. Tự đánh giá thiết bị và đề xuất vai trò
- Giữ thiết kế một bộ cài cho mọi máy; tự đọc những dữ liệu runtime Android/Termux cho phép. Dữ liệu không đọc được là `unknown`, không giả định bằng 0.
- Điểm phù hợp chỉ là recommendation; không tự biến node thành voter/Leader. Profile có version/schema rõ và báo trạng thái thẻ SD `detected`, `writable-tested`, `unknown` một cách trung thực.
- Các giới hạn trên M51 vẫn phải áp dụng ngay cả khi nhận diện phần cứng thất bại: mặc định không cài dịch vụ nào lên M51. Không thay đổi logic bảo vệ hosting khi chưa được cho phép.

### D. Vận hành và nâng cấp
- Làm rõ lệnh start/status/stop ở chế độ foreground an toàn, không tạo process trùng, không ghi vào startup/boot theo mặc định.
- Installer có thể chạy lại an toàn; không tự `pkg upgrade`; khi thiếu dependency, báo rõ hành động cần làm. Không tự động ghi vào `/storage` hoặc thẻ SD ngoài khu vực ứng dụng được phép.
- Cập nhật README-VI.md thành hướng dẫn từng bước cho ZTE (Controller), Bphone/XZ3 (node), kèm lệnh Windows/Linux để kiểm thử và cách rollback v0.4. Không yêu cầu cài lên M51.

## Bài kiểm thử phải viết và chạy local theo AGENTS.md
- Join hợp lệ; mã dùng lại; mã hết hạn; sai mã nhiều lần; payload quá lớn/sai schema.
- Restart/reinstall giữ node identity; đăng ký trùng không phát sinh node mới.
- Revoke token khiến heartbeat thất bại; admin và node không thể lẫn quyền; rotate/re-pair nếu triển khai.
- TLS pin sai dừng ngay; không fallback sang kết nối không xác thực.
- Profile thiếu quyền Android, RAM/SD info không đọc được; không đoán giá trị.
- Migration dữ liệu v0.4 -> bản mới không xóa registry/identity.

## Tiêu chí nghiệm thu
1. Node mới gia nhập bằng một bộ cài và một mã ghép nối, tự gửi profile, xuất hiện ở Controller.
2. Chạy lại cài đặt, kết nối lại hoặc reboot không tạo ID trùng; token/secret vẫn bảo vệ.
3. Thu hồi node có tác dụng, lỗi được hiển thị rõ cho người dùng.
4. Không thay đổi dịch vụ đang chạy trên M51; không có bước tự động cấu hình Internet.
5. Mọi lỗi và giới hạn được diễn đạt trung thực; không quảng bá khả năng Raft/backup/file NAS chưa có.

## Quy tắc tài liệu sau khi sửa
- Cập nhật `docs/CODEMAP.md` chính xác đường dẫn và entrypoint vừa đổi; các tài liệu `ARCHITECTURE.md`, `DECISIONS.md`, `NODE_PROTOCOL.md`, `DATA_MODEL.md`, `SECURITY.md`, `TROUBLESHOOTING.md`, `CHANGELOG.md`, `README-VI.md` chỉ khi có thay đổi tương ứng. Không sửa tài liệu không liên quan.
- Ghi rõ version của API/schema/migration, tính tương thích và kế hoạch rollback.
- Nếu phát hiện lỗi thiết kế nghiêm trọng, sửa trong phạm vi cần thiết và báo cáo, không âm thầm mở rộng sang Phase 1.2, Raft, UI hoặc Cloud.

## Đầu ra Codex phải trả
1. Danh sách file mã nguồn đã thay đổi và hành vi mới.
2. Danh sách tài liệu được cập nhật, đặc biệt CODEMAP và CHANGELOG, lý do chỉnh.
3. **Lệnh và kết quả kiểm thử thực tế** trên môi trường local; phân biệt Codex chạy và PASS do chủ dự án cung cấp. Nêu lý do skip/blocker, không tự nhận đã chạy khi chỉ dùng lại kết quả.
4. Checklist thử 2 máy ZTE/Bphone qua LAN; thông tin nào nhạy cảm thì yêu cầu che trước khi chia sẻ.
5. Các giới hạn còn lại, rủi ro bảo mật, cách khôi phục/rollback.

Hãy thực hiện chỉnh sửa code và tài liệu ngay trong repository hiện có, không chỉ đề xuất ý tưởng và không tạo dự án mới.
