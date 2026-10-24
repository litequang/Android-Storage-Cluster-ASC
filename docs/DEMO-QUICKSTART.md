# ASC Demo Alpha QuickStart — thử nghiệm LAN trên ZTE/Bphone

Chỉ dùng file bỏ được, không chứa thông tin quan trọng. Đây không phải bảo vệ dữ
liệu production. Codex chỉ kiểm thử Linux synthetic; Android, microSD thật, Doze,
power-cut và chạy 24/7 chưa nghiệm thu. Chủ dự án tự thử ZTE V40/Bphone A40, sau đó
có thể thêm Sony XZ3. Tuyệt đối không cài M51/thiết bị production/unknown-device.
Không root, format, thay Termux hiện hữu, Termux:Boot, public port/Cloudflare, APK,
Raft/failover tự động, giảm replica hoặc physical GC.

## 1. Chuẩn bị và xác minh gói

Dùng Termux từ nguồn chính thức còn được hỗ trợ. Không uninstall/reinstall Termux
đang chứa dữ liệu. Tự kiểm tra và chuẩn bị Python >=3.10 và OpenSSL; installer chỉ
kiểm tra, không chạy pkg install/upgrade và không đổi quyền hệ thống. Runtime đã
kiểm thử bằng Python 3.13.5; Android runtime phải thử riêng. Không cần Go/sidecar.

Tải `releases/asc-demo-alpha-0.3.0.tar.gz` và file `.sha256` cạnh nó từ CÙNG commit
đã xác minh trên nhánh `feature/android-demo-alpha`. Chỉ dùng khi báo cáo
`docs/DEMO-TRACK-ACCEPTANCE.md` tại commit chứa gói ghi đủ Linux PASS và SHA khớp.
Không dùng archive installer-preview 0.1.0 để chạy cụm. Kiểm tra digest công bố từ
checkpoint tin cậy; checksum cạnh archive không thay thế xác thực nguồn tải.

```sh
# Chạy trong thư mục chứa archive và file checksum.
sha256sum -c asc-demo-alpha-0.3.0.tar.gz.sha256
# Tạo thư mục giải nén MỚI, ngoài state/source đang dùng; không ghi đè thư mục cũ.
mkdir "$HOME/asc-demo-unpack-0.3.0"
tar -xzf asc-demo-alpha-0.3.0.tar.gz -C "$HOME/asc-demo-unpack-0.3.0"
cd "$HOME/asc-demo-unpack-0.3.0/asc-demo-alpha"
sh scripts/demo-alpha.sh preflight
sh scripts/demo-alpha.sh install --dry-run
sh scripts/demo-alpha.sh install
```

Dừng nếu preflight/checksum từ chối. Không có cờ bypass M51/unknown/TLS. Preflight
không ghi thử: dung lượng đo được không chứng minh quyền ghi. Internal/SD chưa truy
cập được có thể UNKNOWN. Không tự cấp quyền, format hay ghi vào thư mục người dùng.
Cài lại đúng gói chỉ xác minh source; không tạo/thay node, cluster, khóa hay cert.

Mỗi terminal sau đây định nghĩa lại hàm này (không cần sửa cấu hình shell):

```sh
ascdemo() { sh "$HOME/.local/share/asc-demo/bin/asc-demo" "$@"; }
ascdemo preflight
```

Code ở `~/.local/share/asc-demo/releases/<release_id>`; private state mặc định ở
`~/.asc-demo`, tách controller/ và node/. Một code prefix gắn với đúng một Demo root.
Không dùng private Core `~/.asc`, không copy Raft metadata vào Demo. Không sửa file
release, không xóa identity hoặc marker khi lỗi; giữ lại để chẩn đoán.

## 2. Controller trên ZTE

Dùng LAN Wi-Fi riêng cùng subnet. Ví dụ ZTE=192.168.1.20, Bphone=192.168.1.21;
THAY bằng IPv4 Wi-Fi thật. Không dùng 0.0.0.0, hostname, IP public hoặc link-local.
Không mở port management ra Internet. IP/pin đã lưu không tự đổi; nên giữ DHCP/IP ổn
định trong pilot. Đổi endpoint/identity cần quy trình riêng, chưa hỗ trợ tự migration.

```sh
ascdemo init --role controller --host 192.168.1.20
ascdemo run-controller
```

Giữ terminal foreground này. Mở terminal ZTE khác, định nghĩa lại ascdemo:

```sh
ascdemo pair
```

Giữ kín mã dùng một lần; đối chiếu pin Controller ngoài luồng, không tin pin được
người lạ gửi. Pair code mặc định 600 giây. Join nhập tương tác, không truyền mã qua
CLI/history. Nếu bị gián đoạn, chạy lại join cùng endpoint/pin để dùng enrollment
đã lưu, không tạo identity mới. Không tự xóa enrollment_pending.json.

## 3. Storage Node trên ZTE và Bphone

ZTE vừa làm Controller vừa lưu trữ, nhưng dùng private home và credential riêng.
Trong terminal ZTE khác (Controller vẫn chạy):

```sh
ascdemo join --controller https://192.168.1.20:8443 --pin CONTROLLER_PIN --name ZTE-demo-storage
# Nhập mã vừa lấy khi được hỏi.
ascdemo storage-init --host 192.168.1.20 --quota 268435456 --reserve 67108864
# Ghi lại volume_id, storage PIN và capabilities trả về.
ascdemo run-node
```

Trên Bphone đã cài cùng gói/checksum:

```sh
ascdemo init --role node --host 192.168.1.21
# Lấy một mã pair MỚI ở ZTE, rồi join và nhập mã tương tác.
ascdemo join --controller https://192.168.1.20:8443 --pin CONTROLLER_PIN --name Bphone-demo-storage
ascdemo storage-init --host 192.168.1.21 --quota 268435456 --reserve 67108864
ascdemo run-node
```

Mặc định volume duy nhất là private `~/.asc-demo/node/data`. Chỉ tạo volume khi chủ
thiết bị chủ động gọi storage-init; probe chỉ ghi/readback/xóa file tạm do ASC tạo
trong staging của volume đã duyệt. Giữ quota/reserve cho file nhỏ (double-copy cần
ít nhất 2 lần kích thước file trong quota còn trống mỗi node). Không dùng tổng dung
lượng dự kiến của nhà sản xuất làm bằng chứng.

microSD tùy chọn: đọc preflight, chọn thư mục thử nghiệm MỚI/RỖNG nằm dưới app-folder
Termux đã tồn tại và truy cập được, rồi dùng `storage-init --kind termux_sd --root
APP_FOLDER/asc-demo-test ...` thay internal. Không trỏ vào ảnh, thư mục shared hay dữ
liệu hiện hữu. Không có SAF đầy đủ hoặc thay đổi permission tự động. Nếu SD không
truy cập được, dùng internal; marker/volume ID phải khớp khi gắn lại, không đổi SD
hoặc tạo marker mới để vượt lỗi. SD thật chưa được Codex nghiệm thu.

## 4. Duyệt node và physical failure domain

Ở terminal owner trên ZTE:

```sh
ascdemo nodes
ascdemo approve --node-id ZTE_NODE_ID --volume-id ZTE_VOLUME_ID --origin https://192.168.1.20:9443 --pin ZTE_STORAGE_PIN --domain zte-phone
ascdemo approve --node-id BPHONE_NODE_ID --volume-id BPHONE_VOLUME_ID --origin https://192.168.1.21:9443 --pin BPHONE_STORAGE_PIN --domain bphone-phone
```

Dùng node IDs của hai Storage Node đã enroll, không dùng local-controller. Chủ dự
án xác nhận hai domain là hai điện thoại thật. Hai volumes/identities trên cùng một
điện thoại PHẢI cùng label; đây là quyết định tin cậy của owner, chưa có hardware
attestation. Node overview hiển thị heartbeat/online/offline và storage telemetry;
không suy diễn UNKNOWN thành dung lượng hoặc quyền ghi.

## 5. Upload, kiểm tra hai bản sao, download

Tạo một file nhỏ bỏ được trong HOME của Controller, rồi:

```sh
ascdemo upload "$HOME/demo-input.txt" demo/input.txt --key unique-demo-upload-001
ascdemo files
ascdemo replicas FILE_ID
ascdemo download FILE_ID "$HOME/new-demo-output.txt"
sha256sum "$HOME/demo-input.txt" "$HOME/new-demo-output.txt"
```

Upload dùng replicated_2. Chỉ protected=true khi có hai domain đã verify/available.
Exit 4 = replication chưa đủ: giữ file/jobs/state và retry CÙNG key, CÙNG nội dung,
CÙNG logical path. Exit 3 = từ chối validation/TLS/state/network; xem chẩn đoán.
Không ghi đè file download hiện hữu. File download dở có thể được giữ lại để kiểm
tra; lần thử tiếp dùng tên output mới. SHA-256 phải khớp.

Thử dừng một Storage Node bằng Ctrl+C: download có thể dùng replica còn tốt khi
Controller vẫn chạy, replicas báo DEGRADED và upload mới bị từ chối nếu thiếu hai
node độc lập có khả năng ghi. Khi Controller mất, node không tự thành Leader;
metadata và authorization thao tác mới bị từ chối. Không có offline-write/failover.
Giữ các byte và khởi động lại chính Controller cũ, rồi nodes, reconcile qua replicas.

## 6. Dừng, backup, nâng cấp và rollback

Ctrl+C trong các terminal node trước, Controller sau; không kill PID đoán mò, không
đăng ký boot/background auto-update. Trước pilot chỉ dùng release có báo cáo nghiệm
thu. Khi có gói tương thích mới: xác minh SHA từ commit tin cậy, giải nén thư mục MỚI.
Nâng cấp nhiều node có kiểm soát bằng **dừng toàn cụm**, backup từng máy, đổi code
Controller rồi từng node, kiểm tra phiên bản, khởi động Controller rồi nodes và
kiểm tra replicas/SHA. Không cam kết rolling upgrade liên tục hoặc mixed versions.

```sh
# Trên TỪNG điện thoại, mọi foreground phải dừng. Tên backup phải MỚI, parent tồn tại.
ascdemo backup "$HOME/asc-demo-before-upgrade"
ascdemo verify-backup "$HOME/asc-demo-before-upgrade"
ascdemo stage "$HOME/asc-demo-unpack-NEXT/asc-demo-alpha"
# Stage trả release_id. Lưu cả release_id cũ (tên releases/ hoặc kết quả upgrade).
ascdemo upgrade-preflight NEW_RELEASE_ID
ascdemo upgrade NEW_RELEASE_ID --backup "$HOME/asc-demo-upgrade-verified-copy"
# Nếu cần rollback code tương thích, dừng toàn cụm lần nữa trước khi gọi:
ascdemo rollback OLD_RELEASE_ID --backup "$HOME/asc-demo-before-code-rollback"
```

Stage không đổi code đang chọn. Upgrade/rollback chỉ chấp nhận format/capabilities
chính xác, giữ Node ID/Cluster ID, token/khóa/pin/volume ID; tạo và đọc lại checksum
backup gồm toàn bộ private state, file bytes và các approved external volumes. Cần
đủ dung lượng cho bản sao backup; missing medium, source đổi, link hay thiếu chỗ
đều từ chối. Backup nằm private ngoài source/state, chứa BÍ MẬT: không đưa lên Git,
cloud công khai hay gửi nguyên thư mục cho hỗ trợ. Giữ gói/source release tương ứng.
Backup riêng trong HOME cùng điện thoại không phải disaster recovery; uninstall
Termux hoặc hỏng máy có thể mất cả backup. Owner phải giữ bản riêng an toàn theo
quy trình của mình; external DR đầy đủ thuộc Phase 3D, chưa triển khai.

Không tự restore database cũ lên volume đang có dữ liệu mới. Rollback hiện tại chỉ
đổi code tương thích sau backup mới, KHÔNG restore metadata/bytes và không downgrade
schema. Physical volume identity gắn medium gốc; khôi phục sang medium khác chưa có
migration được kiểm thử. Termux→APK, single-writer→Raft và production migration chưa
hỗ trợ. Schema tương lai không khớp phải dừng và giữ state chờ migrator đã nghiệm thu.

Nếu điện/code activation bị gián đoạn, journal PREPARED chặn runtime. Chỉ khi mọi
process đã dừng và state vẫn khớp backup, chạy `ascdemo recover-upgrade`: xác minh
backup, quay lại pointer code cũ, không restore data. Nếu bị từ chối, giữ nguyên
thư mục và nhờ review; không xóa journal/khóa hay sửa DB để ép chạy. Gói/code hỏng có
thể cần mở đúng release cũ còn nguyên vẹn; không có recovery tự động qua Internet.

## 7. Chẩn đoán đã loại bỏ bí mật

```sh
ascdemo diagnose > "$HOME/asc-demo-diagnostic.json"
```

Xem lại trước khi chia sẻ: diagnostic chỉ gồm version/mode/health/counts/dung lượng,
không xuất token/code, endpoint/IP, model profile, khóa/cert, logical filename,
đường dẫn hoặc DB/log thô. Không gửi controller.json/node.json, backup hay terminal
`pair`. Nếu validation chặn diagnose, chỉ gửi thông báo lỗi chung và checkpoint đang
sử dụng; không dump environment/state. Không có Dashboard trong gói CLI đầu tiên;
DEMO.4 được hoãn theo ưu tiên đưa engine lên điện thoại trước.
