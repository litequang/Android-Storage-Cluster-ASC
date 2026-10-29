# Dashboard owner — sử dụng và giới hạn hiện tại

Đọc DASHBOARD-PROGRESS trước: checkpoint đang ở source, chưa phải tất cả tính năng
hoặc gói cập nhật đã phát hành. Không chép đè assets/source vào release được hash-
verify trên ZTE. Gói mới/upgrade exact043 sẽ có sau qualification cuối track.

## Quản lý Node (checkpoint1)

1. Mở HTTPS LAN Dashboard trực tiếp, public CA đã trust. Đăng nhập bằng mã owner
   hiện có. Tab Ghép điện thoại tạo mã node/pin/Cluster ID và theo dõi enrollment.
2. Trên Node, chuẩn bị identity/volume và chạy runtime qua app/CLI hiện có. Node
   không tự được duyệt vì đã ghép. Không copy Termux state vào APK.
3. Trong Điện thoại chọn Quản lý. Nhập đúng HTTPS STORAGE endpoint/PIN, volume IDs
   và tên miền lỗi vật lý. Volume IDs gợi ý từ heartbeat chỉ là thông tin Node
   báo cáo; quyền ghi/durability vẫn UNKNOWN đến Controller probe thực.
4. Chọn Xem trước. Đối chiếu toàn bộ thông tin trả về, dán Node ID đầy đủ và xác
   nhận đã kiểm tra binding/physical domain. Hai Nodes/volumes trên cùng một phone
   cùng domain; không đổi tên domain để giả độc lập.
5. Áp dụng: server owner-session/CSRF, preview binding và credential generation/
   approval CAS được kiểm trong transaction Core. Sau ACK, UI refresh qua existing
   probe. Chỉ báo đủ replica khi bytes/SHA/domain hợp lệ, không từ approval ACK.
6. Đổi tên và thu hồi dùng cùng preview/confirmation. Thu hồi mất quyền Node và
   có thể làm file không đọc qua mạng được nếu thiếu survivor; physical bytes vẫn
   giữ. Không xóa identity hoặc tạo Node mới để vượt trạng thái revoked; repair
   giữ Node ID cần quy trình lifecycle hiện có, chưa phải nút re-enroll ngầm.

Preview tối đa120s/không vượt session,8/owner/32Controller. RAM-only: restart mất
preview, logout quên preview của phiên đó. Retry ACK đã xác nhận trong cùng phiên
trả replayed=true/historical confirmed_at; không chứng minh Node hiện đang online.
Nếu crash giữa commit và receipt: kiểm tra current state rồi preview lại; không
coi outcome UNKNOWN là chưa từng áp dụng và không auto-reset state.

Core quorum/recovery giữ chỉ đọc. Phase5 private/edge gateway vẫn file-access-only,
không forward management/pairing/admin APIs. Capabilities qua gateway bị scope
node_management=false và X-ASC-Access-Mode:file-access-only; browser ẩn controls.
Không đổi allowlist hoặc trust forwarded headers để mở chúng lên Internet.

Quota/reserve/root của Node do app/CLI trên chính Node cấu hình; Dashboard không
có API remote filesystem/quota/start/stop/shell. API chưa có backend an toàn không
được hiển thị thành thao tác thành công.

Rollback source/code: dừng runtime có chủ sở hữu, backup mới, chọn code tương
thích qua upgrade contract; không restore DB cũ. Checkpoint1 không thêm schema
hoặc file state. Authority changes đã áp dụng không bị hoàn tác bằng rollback
code. Original packages/APK/signer/Node/Cluster/Volume identity giữ nguyên.
