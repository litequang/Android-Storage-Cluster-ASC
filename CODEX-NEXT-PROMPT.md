# PROMPT GIAO CODEX — ANDROID STORAGE CLUSTER (ASC)

**Model đề nghị: GPT-5.6 Sol, Thinking: High** (thiết kế hệ thống phân tán, bảo mật và thay đổi kiến trúc). Với sửa UI đơn giản dùng Medium.

> Quy trình hiện hành nằm trong AGENTS.md. Phase 1.1 Windows đã được chủ dự án xác nhận 40 tests OK (skipped=3). Các mục bên dưới là backlog tham khảo; chỉ làm Phase được giao rõ ràng, không bắt đầu Phase 1.2A trong lượt xuất bản v0.4.1.

Repository ASC v0.4 đã có code chạy thử (single-writer LAN). Nhiệm vụ tiếp theo: kiểm tra luồng đăng ký node, hoàn thiện nền tảng production-grade từng phần, chưa được tự động mở Raft hay triển khai lên M51.

## Quy tắc bắt buộc
1. Đọc theo thứ tự AGENTS.md -> docs/CODEMAP.md -> docs/ARCHITECTURE.md -> docs/DECISIONS.md -> docs/NODE_PROTOCOL.md -> docs/DATA_MODEL.md -> docs/SECURITY.md -> docs/TROUBLESHOOTING.md -> docs/CHANGELOG.md.
2. Chỉ sửa các file liên quan tới mục tiêu được giao. Không quét đọc lại toàn bộ repository nếu CODEMAP đã đủ định tuyến.
3. Không truy cập production DB/logs, SSH điện thoại thật, AMH Panel hay dữ liệu M51. Chỉ được đọc/sửa source.
4. Codex được chạy test/typecheck/lint/build local: sau sửa mã chạy test mục tiêu, trước hoàn tất Phase chạy full suite áp dụng được; tự sửa lỗi hoặc báo blocker, không làm yếu test. Có thể dùng lại PASS chủ dự án cung cấp khi source/test không đổi. Không chạy production server, installer trên điện thoại thật hoặc sửa dữ liệu/private state production.
5. Không tự xây Raft giả dựa vào chấm điểm/ping. Phải chọn thư viện Raft uy tín, ghi ADR và chứng minh chạy trên Termux, thử network partition rồi mới cho phép failover ghi.
6. Sau MỖI thay đổi mã, cập nhật docs/CODEMAP.md và tài liệu liên quan nếu cấu trúc/giao thức/lỗi/thực thi thay đổi; cập nhật docs/CHANGELOG.md khi có nâng cấp chức năng, sửa bug đáng kể. Không chỉnh tài liệu không liên quan.
7. Cài đặt idempotent, không mất khóa/identity; không root, format thẻ, thay đổi thư mục hosting; có rollback và báo cáo migration.

## Công việc ưu tiên tiếp theo (đề xuất làm theo PR nhỏ)
A. Harden Phase 1: enrollment hai bước có admin approve, revoke/rotate token, rate limit, tự cập nhật agent có version/rollback, bảo vệ dữ liệu cục bộ, kỹ thuật bind/proxy LAN an toàn.
B. Build local StorageAdapter read-only inventory với internal + SD; không ghi ngoài app-specific path và không coi có quyền ghi là chắc chắn bền vững.
C. Thiết kế file catalog/event model + versioned migrations + integrity and idempotency tests; vẫn single-writer cho đến Phase 2 thực.
D. Kiểm chứng thư viện Raft thực dùng được trên Android arm64, vận hành 3 voter; voter quyết định bằng quorum, không bằng score. Tests gồm partition, stale leader, term/log recovery, fencing, membership joint consensus.
E. Dashboard PWA mobile-first chỉ sau khi auth và storage invariant được kiểm thử.

## Đầu ra mỗi PR
- Mã nguồn thay đổi, danh sách đường dẫn.
- Tài liệu đã cập nhật và lý do (nhất là CODEMAP, ARCHITECTURE, NODE_PROTOCOL, TROUBLESHOOTING, CHANGELOG).
- Lệnh và kết quả kiểm thử thực tế; phân biệt Codex chạy với kết quả chủ dự án cung cấp, nêu các skip/blocker. Không chạy lại vô ích khi source/test không đổi và đã có PASS phù hợp.
- Giới hạn chưa triển khai, rủi ro, rollback steps.
