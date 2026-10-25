# ZTE đang chạy Demo0.3.0 →0.4.1, giữ nguyên cụm và volume

Dành cho CHỦ DỰ ÁN tự chạy trên ZTE9045 Android11/Termux đã có Controller
192.168.100.237:8443, Storage9443, state `~/.asc-demo`, volume internal hiện hữu.
Codex không SSH/cài/đọc điện thoại. Chỉ dùng dữ liệu thử nghiệm bỏ được. Linux
synthetic đã tái hiện lỗi và có qualification riêng; ZTE/Bphone thực tế cần owner
nghiệm thu. Không dùng cho M51, production, unknown-device; không root, đổi quyền
hệ thống/SELinux/Termux:Boot hoặc chạy pkg upgrade.

**Không chạy init, join hoặc storage-init lại trên ZTE này.** Không xóa marker,
DB, khóa, identity, source cũ. Hai đường nâng cấp trực tiếp cần báo cáo nghiệm thu
0.3.0→0.4.1 và0.4.0→0.4.1 với đúng archive cũ. Chỉ dùng0.4.1 khi
[DEMO4D-ACCEPTANCE](DEMO4D-ACCEPTANCE.md) và progress tại commit tải đã đủ PASS.

## 1. Dừng foreground an toàn

Ctrl+C trong terminal Storage Node trước, Controller sau. Nếu có điện thoại khác
trong cụm, dừng chúng trước khi nâng cấp; không chạy mixed versions. Chờ mỗi terminal
trở về prompt. Không kill PID đoán mò, không xóa `.lock`. Nếu backup báo còn process
sở hữu state, quay lại đúng terminal và dừng nó. Giữ Termux và private state hiện có.

## 2. Chọn ĐÚNG prefix hiện hữu và backup bằng launcher0.3.0

Các lệnh sau là Bash/Termux, không chạy từ Cloud lên điện thoại. `set -e` dừng shell
khi một bước thất bại; mở terminal khác để chẩn đoán, không tiếp tục bỏ qua lỗi.
Nếu trước đây chọn prefix riêng (ví dụ asc-demo-alpha-0.3), THAY DEMO_CODE bằng
prefix đang có `install.json` và `bin/asc-demo`; không cài prefix mới để né state.

```bash
set -e
umask 077
DEMO_CODE="$HOME/.local/share/asc-demo"
DEMO_STATE="$HOME/.asc-demo"
test -f "$DEMO_CODE/install.json"
test -f "$DEMO_CODE/bin/asc-demo"
test -f "$DEMO_STATE/demo.json"
ascdemo() { sh "$DEMO_CODE/bin/asc-demo" --state "$DEMO_STATE" "$@"; }
ascdemo preflight
ascdemo diagnose
DEMO_BACKUPS=$(mktemp -d "$HOME/asc-demo-041-private-backups.XXXXXXXX")
DEMO_OLD_ID=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["release_id"])' "$DEMO_CODE/install.json")
printf '%s\n' "$DEMO_OLD_ID" > "$DEMO_BACKUPS/old-release-id.txt"
ascdemo backup "$DEMO_BACKUPS/before-041"
ascdemo verify-backup "$DEMO_BACKUPS/before-041"
printf 'Giữ riêng thư mục backup: %s\n' "$DEMO_BACKUPS"
```

Backup chứa bí mật, toàn bộ state/bytes và approved external volumes; không gửi
GitHub/chat/cloud công khai. Cần đủ chỗ cho backup trước nâng cấp VÀ backup mới của
activation/rollback. Backup trong cùng HOME không phải disaster recovery. Thiếu
chỗ/missing medium/checksum sai phải dừng, giữ bản cũ và dữ liệu; không dọn object.

Lưu snapshot identity bằng SHA riêng, không in token/key. Hàm này chỉ đọc state;
SQLite mở mode=ro, không tạo DB. Gọi lại sau upgrade trước khi tạo Dashboard mới.

```bash
asc_identity_snapshot() {
python3 - "$DEMO_STATE" "$1" <<'PY'
from pathlib import Path
import hashlib,json,os,sqlite3,sys
root,out=Path(sys.argv[1]),Path(sys.argv[2])
names=['demo.json','controller/controller.json','controller/server.crt','controller/server.key',
       'node/node.json','node/storage.json','node/storage.crt','node/storage.key','node/data/.asc-volume.json']
names += ['dashboard/'+n for n in ('dashboard.json','ca.crt','ca.key','server.crt','server.key') if (root/'dashboard'/n).exists()]
files={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in names}
with sqlite3.connect((root/'node/storage/manifest.sqlite3').as_uri()+'?mode=ro',uri=True) as db:
    volumes=db.execute('SELECT volume_id,node_id,kind,root,medium,quota,reserve FROM volumes ORDER BY volume_id').fetchall()
with sqlite3.connect((root/'controller/registry.sqlite3').as_uri()+'?mode=ro',uri=True) as db:
    cluster=db.execute("SELECT value FROM settings WHERE key='cluster_id'").fetchone()[0]
fd=os.open(out,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'w') as f:json.dump({'files':files,'volumes':volumes,'cluster_id':cluster},f,sort_keys=True)
print('Identity snapshot lưu riêng; không chia sẻ file này.')
PY
}
asc_identity_snapshot "$DEMO_BACKUPS/identity-before.json"
```

## 3. Tải đúng commit và đối chiếu SHA-256

Dùng publication commit và SHA từ báo cáo đã xác minh (không dùng main hoặc tự
đoán digest). Đây là thông tin public, không phải mã ghép/token. Các prompt dưới
đây yêu cầu dán đúng hai giá trị đó; không nhập token/key. Không pipe Internet vào sh.

```bash
command -v curl
printf 'Dán publication commit GitHub (40 hex) của0.4.1: '
read -r DEMO_PUBLIC_COMMIT
[[ "$DEMO_PUBLIC_COMMIT" =~ ^[0-9a-f]{40}$ ]]
printf 'Dán SHA-256 archive0.4.1 từ báo cáo tin cậy (64 hex): '
read -r DEMO_EXPECTED_SHA
[[ "$DEMO_EXPECTED_SHA" =~ ^[0-9a-f]{64}$ ]]
DEMO_DOWNLOAD=$(mktemp -d "$HOME/asc-demo-041-download.XXXXXXXX")
DEMO_URL="https://raw.githubusercontent.com/litequang/Android-Storage-Cluster-ASC/$DEMO_PUBLIC_COMMIT/releases"
cd "$DEMO_DOWNLOAD"
curl --fail --location --proto '=https' --tlsv1.2 "$DEMO_URL/asc-demo-alpha-0.4.1.tar.gz" -o asc-demo-alpha-0.4.1.tar.gz
curl --fail --location --proto '=https' --tlsv1.2 "$DEMO_URL/asc-demo-alpha-0.4.1.tar.gz.sha256" -o asc-demo-alpha-0.4.1.tar.gz.sha256
printf '%s  asc-demo-alpha-0.4.1.tar.gz\n' "$DEMO_EXPECTED_SHA" | sha256sum -c -
sha256sum -c asc-demo-alpha-0.4.1.tar.gz.sha256
mkdir "$DEMO_DOWNLOAD/unpacked"
tar -xzf asc-demo-alpha-0.4.1.tar.gz -C "$DEMO_DOWNLOAD/unpacked"
DEMO_NEW_SOURCE="$DEMO_DOWNLOAD/unpacked/asc-demo-alpha"
```

Nếu curl/Python/OpenSSL thiếu, giữ nguyên state và tự chuẩn bị dependency sau
review; không có auto-install/upgrade. TLS/checksum lỗi phải dừng, không dùng `-k`.

## 4. Stage / preflight / upgrade qua launcher đang có

Mọi foreground vẫn dừng. Không gọi installer mới đè prefix. Bản old launcher đã
được kiểm thử để stage/backup/activate trong tình huống '/' open bị từ chối.

```bash
sh "$DEMO_NEW_SOURCE/scripts/demo-alpha.sh" preflight
DEMO_NEW_ID=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["release_id"])' "$DEMO_NEW_SOURCE/release.json")
ascdemo stage "$DEMO_NEW_SOURCE"
ascdemo upgrade-preflight "$DEMO_NEW_ID"
ascdemo upgrade "$DEMO_NEW_ID" --backup "$DEMO_BACKUPS/activation-041"
ascdemo verify-backup "$DEMO_BACKUPS/activation-041"
ascdemo diagnose
asc_identity_snapshot "$DEMO_BACKUPS/identity-after.json"
cmp "$DEMO_BACKUPS/identity-before.json" "$DEMO_BACKUPS/identity-after.json"
```

Yêu cầu diagnose báo0.4.1-alpha; cmp không có khác biệt. Dừng nếu ID/key/PIN/volume/
medium khác hoặc compatibility từ chối; không sửa JSON/schema/marker để ép chạy.
Backup mới không restore DB cũ. Ghi lại DEMO_CODE, DEMO_BACKUPS, old/new release IDs
trong ghi chú riêng để dùng nếu mở terminal khác; đừng chia sẻ nguyên backup.

## 5. Xác nhận volume ZTE hiện hữu ghi/fsync được

Storage Node vẫn phải dừng. Controller có thể dừng hoặc đang chạy. Không tạo volume.

```bash
ascdemo storage-status > "$DEMO_BACKUPS/zte-storage-041.json"
python3 - "$DEMO_BACKUPS/zte-storage-041.json" <<'PY'
import json,sys
v=json.load(open(sys.argv[1]))['volumes']
assert len(v)==1, 'Nếu có nhiều volume: review từng volume đã duyệt, không tự chọn/khởi tạo'
x=v[0]
print({k:x[k] for k in ('node_id','volume_id','state','readable','writable','fsync_tested','last_error')})
assert x['state']=='online' and x['readable'] is True and x['writable'] is True and x['fsync_tested'] is True and x['last_error'] is None
PY
```

Probe chỉ tạo/readback/hash/fsync/xóa file tạm riêng trong staging của approved
volume. UNKNOWN/false hoặc write_denied thật vẫn là FAIL; giữ state và diagnose,
không root/chmod777/SELinux bypass. Không dùng dung lượng trống làm bằng chứng quyền ghi.

## 6. Khởi chạy Controller, Node và HTTPS Dashboard

Trên ZTE đang dừng cả Controller/Node, nếu nâng từ0.3 và CHƯA có Dashboard:

```bash
ascdemo dashboard-init --port 8444
ascdemo dashboard-trust --out "$HOME/asc-demo-dashboard-041-ca.crt"
openssl x509 -in "$HOME/asc-demo-dashboard-041-ca.crt" -noout -fingerprint -sha256
ascdemo run-controller --dashboard
```

Giữ foreground. Từ terminal ZTE khác, định nghĩa lại DEMO_CODE/DEMO_STATE/ascdemo
đúng prefix ở mục2 rồi chạy `ascdemo run-node`. Terminal owner thứ ba chạy
`ascdemo dashboard-code`; mở **https://192.168.100.237:8444** theo IP đã lưu.
Nếu IP hiện tại khác, dừng và review endpoint contract, không re-init để đổi IP.

Nếu nâng từ0.4 đã có Dashboard, giữ CA/config/port cũ; không tạo identity mới hoặc
đổi cấu hình. Export public CA sang tên MỚI nếu cần rồi chạy Controller --dashboard.
Chỉ chuyển file **public CA .crt**, đối chiếu fingerprint với ca_sha256 ngoài luồng,
owner tự trust CA trên Android/PC như QuickStart5a. Có `termux-open` thì owner có thể
`termux-open --send "$HOME/asc-demo-dashboard-041-ca.crt"` để mở share sheet, tự chọn
kênh an toàn lưu/chuyển public file. Không gửi thư mục dashboard, ca.key/server.key,
controller/node config hoặc backup. Không click qua cảnh báo TLS hay đổi sang HTTP.
Mã đăng nhập một lần nhập trong browser; không đưa mã/token/ảnh terminal vào báo cáo.

## 7. Bphone là domain thứ hai và thử file

Bphone CHƯA có Demo: tải/kiểm SHA đúng cùng gói, preflight/install theo QuickStart1;
init node/join/storage-init theo QuickStart3 trên **Bphone mới**, IP Wi-Fi riêng.
Lấy pair code MỚI bằng `ascdemo pair` trên ZTE; Bphone nhập qua prompt hidden, PIN
Controller đối chiếu ngoài luồng. Nếu Bphone đã có Demo, nâng cùng phiên bản bằng
stage/upgrade và giữ identity; không init/join lại. Không gọi các lệnh tạo node đó
trên ZTE hiện hữu. Chỉ owner thao tác điện thoại, không Codex.

Lệnh trên Bphone MỚI sau khi đã kiểm SHA và cài cùng0.4.1 (không chạy trên ZTE):

```bash
set -e
ascdemo() { sh "$HOME/.local/share/asc-demo/bin/asc-demo" "$@"; }
test ! -e "$HOME/.asc-demo/demo.json"
printf 'IPv4 Wi-Fi riêng của Bphone: '; read -r BPHONE_IP
printf 'PIN Controller ZTE đã đối chiếu ngoài luồng,64hex: '; read -r ZTE_CONTROLLER_PIN
ascdemo init --role node --host "$BPHONE_IP"
ascdemo join --controller https://192.168.100.237:8443 --pin "$ZTE_CONTROLLER_PIN" --name Bphone-demo-storage
# Nhập pair code mới qua prompt, không đưa vào flags/history/báo cáo.
ascdemo storage-init --host "$BPHONE_IP" --quota 268435456 --reserve 67108864
ascdemo storage-status
ascdemo run-node
```


Duyệt cả ZTE node/volume hiện hữu và Bphone bằng CLI QuickStart4. Lấy Node/Volume IDs
ZTE từ storage-status đã lưu, không lấy local-controller. PIN Storage ZTE từ public
certificate hiện hữu (không đọc/in private key):

```bash
openssl x509 -in "$HOME/.asc-demo/node/storage.crt" -outform DER | sha256sum
```

Dùng đúng Node ID/Volume ID/PIN và `--origin https://192.168.100.237:9443`;
`--domain zte-phone` và Bphone `--domain bphone-phone`. Hai volume/Node IDs trên
cùng một điện thoại phải cùng domain. Duyệt node vẫn ở CLI, không Dashboard.

Trên terminal owner ZTE, dùng ascdemo/prefix cũ ở mục2. `ascdemo nodes` cho IDs;
nhập đúng IDs/volume/PIN đã kiểm, không dùng local-controller. Các giá trị dưới đây
là định danh/fingerprint public, KHÔNG phải token/code/key:

```bash
ascdemo nodes
printf 'Node ID Storage ZTE hiện hữu: '; read -r ZTE_NODE_ID
printf 'Volume ID internal ZTE hiện hữu: '; read -r ZTE_VOLUME_ID
ZTE_STORAGE_PIN=$(openssl x509 -in "$HOME/.asc-demo/node/storage.crt" -outform DER | sha256sum | cut -d' ' -f1)
printf 'IPv4 Wi-Fi Bphone: '; read -r BPHONE_IP
printf 'Node ID Storage Bphone: '; read -r BPHONE_NODE_ID
printf 'Volume ID Bphone: '; read -r BPHONE_VOLUME_ID
printf 'PIN Storage Bphone đã đối chiếu ngoài luồng,64hex: '; read -r BPHONE_STORAGE_PIN
ascdemo approve --node-id "$ZTE_NODE_ID" --volume-id "$ZTE_VOLUME_ID" --origin https://192.168.100.237:9443 --pin "$ZTE_STORAGE_PIN" --domain zte-phone
ascdemo approve --node-id "$BPHONE_NODE_ID" --volume-id "$BPHONE_VOLUME_ID" --origin "https://$BPHONE_IP:9443" --pin "$BPHONE_STORAGE_PIN" --domain bphone-phone
```

Trong Dashboard: chọn file nhỏ bỏ được, tên MỚI, Upload; đợi **Đủ hai bản sao**,
xem hai node/volume/domain trong Bản sao & SHA, Download và so SHA. Giới hạn32MiB.
Hoặc dùng QuickStart5 CLI. Giữ file gốc/key nếu pending; không đổi key để bỏ job.
Ctrl+C một Node: refresh báo degraded, download phải đúng SHA từ survivor, upload
mới thiếu hai domain bị từ chối. Restart CHÍNH node cũ, refresh/replicas phải trở
lại hai bản sao. Mất Controller thì không ghi mới, không failover. Không test GC.

## 8. Rollback code với backup MỚI, giữ mọi byte mới

Dừng toàn cụm như mục1. Chọn đúng prefix và thư mục private backup đã ghi lại.
KHÔNG restore before-041/DB cũ. Source0.3/0.4 tương thích format nhưng chứa lỗi
Android ban đầu: rollback có thể quay lại write_denied và không phục vụ storage
được trên ZTE này. Đây là rollback giữ dữ liệu/identity, không sửa lỗi Android;
ưu tiên giữ service dừng để review nếu cần quay code cũ.

```bash
DEMO_OLD_ID=$(cat "$DEMO_BACKUPS/old-release-id.txt")
ascdemo rollback "$DEMO_OLD_ID" --backup "$DEMO_BACKUPS/new-state-before-code-rollback"
ascdemo verify-backup "$DEMO_BACKUPS/new-state-before-code-rollback"
ascdemo diagnose
```

Nếu chủ động chạy0.3 CLI-only: `ascdemo run-controller` KHÔNG `--dashboard`, giữ
thư mục CA/bytes mới. Không xóa marker/identity vì old runtime lại báo lỗi. Không
hạ schema hoặc thay volume. Muốn quay lại0.4.1 phải stop-all, preflight/upgrade về
DEMO_NEW_ID với thư mục backup MỚI khác; không dùng lại đường dẫn backup đã có.

## 9. Bằng chứng owner cần ghi

Bản gói/SHA/phiên bản Termux/Python/Android; snapshot identity cmp không đổi;
writable/fsync/state/error thực; CA/IP SAN trusted HTTPS; hai điện thoại/domain,
file hai replica/SHA và fallback/restart; Controller loss; upgrade/rollback giữ
file cũ/mới. Chỉ chia sẻ diagnose/lỗi cố định đã xem lại, không secret/code/profile/
raw logs/HAR/database/backup. Linux synthetic PASS không điền thay bất kỳ gate
Android/SD/Doze/power-cut/production nào. Chưa đạt thì ghi FAIL/BLOCKED, giữ dữ liệu.
