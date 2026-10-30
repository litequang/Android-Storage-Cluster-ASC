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



## Tài khoản Owner / Viewer (checkpoint2)
Lần đầu đăng nhập bằng mã owner từ Controller, mở Tài khoản, tạo tài khoản Owner
với tên3–48ASCII chữ thường/số/._- và mật khẩu12–128ký tự. Không có password mặc
định. Sau logout chọn tài khoản/mật khẩu. Mã owner cục bộ vẫn phục hồi quyền quản
trị nếu quên mật khẩu; không tự xóa account state hoặc init lại Controller.
Owner tạo thêm Owner hoặc Viewer. Viewer được đọc/tải TẤT CẢ file cụm, không phải
thư mục riêng hay file-sharing ACL. UI và backend cùng chặn upload/reconcile/
pairing/node/account changes. Không cấp Viewer khi cần cô lập dữ liệu theo file.
Sửa quyền/mật khẩu hoặc xóa: nhập lại tên để xác nhận; server CAS generation, thu
hồi các phiên của tài khoản. Sửa tài khoản đang đăng nhập sẽ yêu cầu login lại.
Giữ ít nhất1Owner. Thao tác đã được backend/Core authorize có thể đã chạy; thay
role không rollback bytes/jobs hoặc hứa hủy mọi thao tác đang truyền.

Account hash/salt lưu private trong dashboard/accounts.json1, gắn Cluster ID.
Không gửi file này/backup/cookie/password lên GitHub. Không có thay đổi Registry/
Manifest schema hoặc Node identity. File sai/quyền rộng/link/cluster mismatch bị
từ chối, không ghi đè/silent reset. Missing file không tự tạo account/default pass;
chỉ owner code +explicit create thiết lập lại web accounts, không đổi Node keys.
Rollback043 code-only vẫn dùng mã owner, giữ nguyên accounts file để forward;
exact package qualification cuối track mới công bố đường upgrade/rollback.


## File Manager / phiên bản / tác vụ (checkpoint3 source)
Tìm tên hoặc một phần đường dẫn, chọn sort và tất cả/phiên bản mới nhất rồi Tìm/
áp dụng. Mỗi trang50mục, Trang trước/sau. Duyệt thư mục/Thư mục trên là thư mục
LOGIC từ tên Catalog, không duyệt filesystem. Tìm có từ khóa đi đệ quy trong thư
mục đang chọn. Giới hạn Catalog256 của Core hiện tại vẫn giữ, chưa phải unlimited.

File mới mặc định phiên bản1. Muốn cập nhật cùng tên, chọn Thêm phiên bản, kiểm
tra số phiên bản được gợi ý từ Catalog, chọn file nội dung mới và Upload. File cũ
không bị ghi đè; concurrent owner có thể chiếm cùng số ->409, đọc lại trước ý định
mới. Khi upload dở/mất ACK, chọn ĐÚNG file/tên/phiên bản cũ; key nội dung được giữ
trong sessionStorage (không token). Không tự tăng version để che lỗi retry.
Lịch sử liệt kê các version bất biến và tải SHA từng bản. Đây không phải snapshot
hoặc external backup. Nút chuẩn bị file mới không xóa job đã tồn tại.

Tác vụ đọc queue Core bền vững và lịch sử. Owner có thể Yêu cầu thử lại khi
FAILED/RETRY; ACK chỉ nhận retry, không xác nhận bytes/protected. UPLOAD chưa có
bytes cần chọn lại file trong File Manager; Dashboard không giữ source bytes sau
request. Đủ replica chỉ sau canonical fsync/readback/SHA/physical-domain proofs.
Viewer đọc file/history/job, không retry/upload. File-only gateway cũng không
retry; bundle Access0.1 cũ vẫn giao diện file cũ có ghi giới hạn, không giả hỗ trợ
route mới. Core/quorum/recovery giữ observer-only. Không xóa vật lý/GC.
