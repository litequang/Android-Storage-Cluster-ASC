# ASC Dashboard 0.5.0 — thao tác và giới hạn

Đây là Dashboard quản trị LAN của Controller single-writer hiện có, dùng chung
Registry/Catalog/Storage Engine. Đọc [DASHBOARD-INSTALL](DASHBOARD-INSTALL.md) để
nâng cấp từ đúng0.4.3, và báo cáo GitHub DASHBOARD-ACCEPTANCE/PROGRESS để biết bằng
chứng thực chạy. Không chép đè assets/source vào release được hash-verify. APK5
Storage Node giữ riêng; Web App không tự chạy Termux/Native Engine hoặc filesystem.

## Đăng nhập và tài khoản

Mở đúng HTTPS Dashboard đã trust public CA/IP SAN. Lấy `dashboard-code` bằng
launcher owner trên Controller, không phải mã ghép node. Mã một lần tạo phiên
Secure/HttpOnly/SameSite cookie +CSRF; không gửi code/cookie/token vào log/chat.
Lần đầu vào Tài khoản, tạo Owner/password do bạn chọn. Không password mặc định.
Tên3–48ASCII chữ thường/số/._-, bắt đầu bằng chữ; password12–128ký tự. Tối đa8
accounts/8RAM sessions. Code owner cục bộ vẫn bootstrap/recovery khi quên password.

Owner quản trị toàn cụm. Viewer đọc/tải TẤT CẢ file/snapshot/progress, không upload,
quản trị node/account/restore/settings hoặc lấy diagnostic export. Chưa có ACL/
private folder/sharing theo file. Không cấp Viewer khi cần cô lập dữ liệu riêng.
Sửa role/password/delete cần typed username +generation CAS; các phiên liên quan
bị thu hồi. Self-change phải login lại. Không được xóa/hạ quyền Owner cuối cùng.
Tác vụ đã được authorize có thể đã chạy; đổi role không hoàn tác bytes/Core jobs.
Private accounts.json không được chia sẻ; hỏng/cluster mismatch/quyền rộng/link
thì giữ lỗi, không xóa/reset để né kiểm tra. Không thay Node/Cluster identity.

## Ghép và quản lý Node

Ghép điện thoại tạo mã Node một lần cùng Controller HTTPS/PIN/Cluster ID. Node
app/CLI phải đối chiếu public bindings và dùng existing enrollment/resume; không
copy Termux state sang APK. Enrollment KHÔNG tự duyệt storage hoặc failure domain.

Trong Điện thoại ->Quản lý, owner nhập đúng HTTPS STORAGE Node (khác Controller/
Dashboard port), leaf SHA-256 PIN đã đối chiếu, UUID volume đã duyệt trên Node,
và physical failure domain đúng thực tế. Các Node/volume trên cùng một điện thoại
phải cùng domain. Gợi ý volume từ heartbeat CHƯA được Controller kiểm chứng.

Xem trước ->đối chiếu bindings ->typed full Node ID +physical-domain checkbox ->
áp dụng. Preview<=120s/không vượt session, tối đa8/session32/Controller. Existing
Controller checks approval/generation trong SQL transaction. Sau ACK, refresh
probe; chỉ actual read/write/fsync/SHA/replica proofs mới là bằng chứng lưu trữ.
Stale approval/generation409 cần đọc/xem trước lại, không tự bypass.

Đổi tên và thu hồi cũng preview/typed Node ID. Revoke có thể làm replica không còn
đọc qua mạng được; physical bytes vẫn giữ. Không tạo Node ID mới để né revoked
state. Preview/known ACK receipts RAM-only; restart/ambiguous ACK cần xem current
state rồi xác nhận intent mới, không suy ra chưa từng áp dụng. Quota/reserve/root
và start/stop vẫn do chính Node/app/CLI quản lý; không có remote shell hoặc FS API.

## File Manager / versions / tác vụ

Tìm literal Unicode trong đường dẫn, sort, lọc all/latest version và phân trang50.
Duyệt thư mục/Thư mục trên là logical prefixes từ Catalog, không filesystem.
Tìm có từ khóa đi đệ quy dưới thư mục chọn. Không tạo empty physical folders.
Core vẫn giới hạn256file/version, offset<=10000; đây không phải unlimited storage.

File mới version1. Thêm phiên bản ->kiểm tra số gợi ý ->chọn nội dung mới ->Upload.
Tên+version bất biến, không ghi đè. Concurrent owner có thể chiếm cùng version:
409 thì đọc lại trước ý định MỚI. Upload dở/mất ACK: chọn ĐÚNG bytes/tên/version cũ,
giữ idempotency key, không auto-bump version để che lỗi. Public pending metadata
ở sessionStorage/RAM, không phải credential. Đổi browser sau gián đoạn phải kiểm
Catalog/jobs trước intent mới; Dashboard không giữ file nguồn sau request.

Upload cần đủ chỗ/quota/reserve trên hai domain được duyệt, SHA chuẩn và actual
fsync/readback. Progress bytes Controller nhận không đồng nghĩa protected. Chỉ
báo đủ2replica khi Controller xác nhận. File thiếu replica vẫn degraded/UNKNOWN.
Browser transfer<=32MiB/file; giữ file gốc cho đến khi đã tự kiểm tra bản tải.

Bản sao &SHA hiển thị từng Node/volume, historical verified/current available khác
nhau. Download dùng canonical valid-copy fallback; browser tự kiểm size+SHA trước
lưu file mới. Lịch sử cho xem/tải mọi immutable version. Tác vụ đọc durable Core
queue/history, Owner retry FAILED/RETRY. ACK retry không phải COMPLETE; active
sender/verifier lease có thể409busy, UI đợi boundedly với SAME intent rồi báo
chưa xác nhận. Không chấp nhận403/SHA/pin lỗi như thành công. Retry không xóa bytes.

## Snapshot và khôi phục

Snapshot giữ TẤT CẢ immutable versions trong logical folder hoặc toàn Catalog tại
một exact metadata revision/digest. UNVERIFIED lúc capture, per-file SHA thật trên
2approved domains mới advance cursor. VERIFIED là bằng chứng LỊCH SỬ từng thời
điểm đọc, không bảo đảm luôn online, quorum snapshot hoặc external backup độc lập.
File pending/chưa có bytes không được tính verified. Snapshot không chứa keys.

Tạo và kiểm chứng ->đợi kết quả. Tạm dừng gửi bước mới/đóng trang giữ progress,
không hủy lệnh đã được authorize. Mở lại ->Đọc lại ->Tiếp tục đúng operation. Thiếu
Node thì sửa kết nối, đợi listener/probe thật sẵn sàng rồi tiếp tục; không init lại.
Mỗi lượt browser chờ tối đa120s/256steps, hết lượt vẫn giữ cursor cho lần tiếp.

Xem phiên bản của snapshot VERIFIED hoặc Lịch sử file ->Khôi phục thành phiên bản
mới. Nhập đúng source path, đối chiếu version/SHA, checkbox rồi xác nhận. Intent
và số version đích bền vững trước IO, Core target ID lưu trước bytes. Mất ACK/restart
resume SAME intent/key/target; không restore DB hoặc thay file cũ. COMPLETED chỉ
sau actual2domain readback. BLOCKED version_conflict giữ mọi dữ liệu, cần review
và ý định MỚI. Tải lại kết quả để đối chiếu SHA. Mỗi file khôi phục riêng, chưa có
atomic whole-cluster restore. Snapshot/history records không bị tự hết hạn/xóa.

Giới hạn16snapshots/64restores/128intent receipts và2MiB metadata. Đầy thì báo lỗi,
không tự xóa bản cuối. Private history.json +history-required.json gắn Cluster/
Catalog epoch/document ID; mất/hỏng một record giữ lỗi503, không reset. Bao gồm
chúng trong stopped backups. Compatible old043 code giữ file nhưng không có UI;
forward mới lại đọc progress. Browser storage bị chặn vẫn retry RAM trong trang;
reload sau ambiguous ACK cần đọc progress trước khi xác nhận operation mới.

## Storage / cấu hình / chẩn đoán

Cấu hình / Chẩn đoán hiển thị approved volume, adapter, quota/reserve, số đo free/
used/available và read/write/fsync. UNKNOWN khi không có probe còn mới, không phải0
hay bằng chứng có thể ghi. Fsync-tested không phải bảo đảm power-loss/Doze/OEM.
Nhiều volumes chung filesystem có thể làm available UNKNOWN, không cộng giả.

Owner đổi tên giao diện/read-refresh5..60s, không đổi Controller name thật, Node/
Cluster ID, heartbeat, TLS/PIN hoặc quota. Browser lấy cấu hình lúc login/mở tab;
CAS409 thì đọc lại trước save. Viewer chỉ đọc. Optional preferences.json private,
không phải Registry/schema migration; corrupt/unsafe/cluster mismatch giữ lỗi.

Diagnostic JSON chỉ Owner, số đếm/measurements/timestamps/jobs/history/limits,
không tên/IDs/endpoints/PIN/token/private key/path/raw logs. Kiểm tra trước chia sẻ.
Đây không phải writer/quorum/phone acceptance. Chưa có audit log đầy đủ mọi admin
operation/per-file ACL. Không có nút shell, remote quota/start-stop hoặc GC.

## LAN, remote và rollback

LAN không cần Internet/cloud nếu còn đường IP giữa các máy và Controller online.
Mất Controller từ chối ghi mới, không tự tạo Leader/failover. Web App không có
cached file/metadata/offline-write/background sync hoặc quyền launch Node.

Core quorum/recovery observer vẫn READ-ONLY. Phase5 private/edge ingress file-only,
không quản trị node/accounts/snapshot/restore/settings/diagnostics. Capability
scope/header không phải authority; không mở allowlist để vượt giới hạn. Cloudflare/
Tailscale/IdP/DNS/provider và Android/hardware acceptance là nghiệm thu riêng.

Nâng cấp/rollback theo DASHBOARD-INSTALL:stop ->backup MỚI+verify ->staged exact
code ->preflight ->activate. Giữ mọi release/identity/volume marker/bytes/private
history; không restore SQLite cũ đè dữ liệu mới. Core/Raft/GC/failover/writableDR
không được bật bằng Dashboard này, không đổi mode bằng cách copy database.
