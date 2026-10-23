# ASC QuickStart 0.6.0 — Phase 1.2B: Distributed Storage & Global File Catalog

ASC có Global File Catalog do một Controller ghi, metadata replica chỉ đọc trên node, placement theo volume đã kiểm tra, queue sao chép bền vững, xác minh bytes/SHA-256 và download fallback. Chính sách single/replicated_2/replicated_3 đếm theo device domain do owner phê duyệt, không đếm hai volume cùng điện thoại thành hai bản độc lập.

Codex đã chạy lại full suite mới: **92 tests, OK (skipped=3)** trên Windows — 89 PASS, không FAIL/ERROR. Ba SKIP là installer cần Linux/Termux Bash. Mô phỏng ZTE V40/Bphone A40/Sony XZ3 dùng state/root riêng, HTTPS/pin thật và file vật lý riêng. Đây là mô phỏng trên một máy Windows, chưa phải chứng minh độ bền của nhiều điện thoại thật.

Chưa có Raft, tự bầu Controller/failover, Dashboard, Cloudflare, phần mềm mobile, SAF hay production readiness. Không truy cập M51, Android thật hoặc dữ liệu production. Phase 2 cần nhiệm vụ riêng.

**Mục 1–10 là hướng dẫn lịch sử v0.4.1; mục 11 mô tả Storage Foundation v0.5.0. Mục 12 là quy trình hiện tại v0.6.0.** Không dùng các lệnh điện thoại để triển khai trong lượt này. Giữ source cũ và private-state backup trước migration.

## 1. Chuẩn bị — chỉ ZTE và Bphone/XZ3 thử nghiệm

- Cùng Wi-Fi LAN riêng; không port-forward cổng 8443.
- Không cài, nâng cấp, chạy agent/controller hoặc thay Termux:Boot trên Samsung M51 hosting. Không yêu cầu thao tác trên M51.
- Termux thử nghiệm cần Android SDK >=24, Python >=3.9, OpenSSL và Bash. Installer không tự cài dependency hoặc chạy pkg upgrade. Nếu báo thiếu, chỉ trên điện thoại thử nghiệm đã xác nhận không phải M51: chạy thủ công `pkg install python openssl`.
- Chép source release vào Download, ví dụ `ASC-QuickStart-0.4.1`. Dùng quyền storage hiện có; nếu thực sự thiếu, chỉ trên máy thử nghiệm mới cấp quyền bằng `termux-setup-storage`.
- Không đặt ASC_HOME trong source, Download, /storage hoặc SD. Mặc định secret ở HOME riêng `~/.asc` (directory 0700, file mới 0600 trên Termux).
- Source v0.4.1 dùng main và origin GitHub ở mục 10. Giữ source v0.4 riêng trước nâng cấp; lịch sử commit v0.4.1 không tự tạo lại bản private state/source v0.4 trước đó.

```bash
cd ~/storage/downloads/ASC-QuickStart-0.4.1
bash install.sh audit
```

Thiếu model/manufacturer/SDK: chỉ audit, từ chối cài/chạy; không có cờ bỏ qua bảo vệ. Baseline nhà sản xuất nằm ở `preset`; số RAM runtime thiếu là null, không dùng thông số hãng để giả RAM đo được. `score_basis` giải thích nguồn điểm; điểm chỉ là đề xuất.

## 2. ZTE V40 — Controller mới

Nếu đã cài v0.4, dùng mục nâng cấp trước, không chạy installer để ghi đè.

```bash
cd ~/storage/downloads/ASC-QuickStart-0.4.1
bash install.sh controller
cd ~/asc-cluster
python3 -m asc.cli controller-run
```

Giữ terminal foreground. Mở terminal thứ hai trên ZTE:

```bash
cd ~/asc-cluster
python3 -m asc.cli controller-pair --ttl 600
```

Lệnh quản trị cần Controller đang chạy; đọc admin token từ file riêng, gọi HTTPS loopback với pin certificate. Kết quả có mã 12 ký tự dạng `XXXX-XXXX-XXXX`, TTL 60–1800 giây và SHA256 PIN. Mã là quyền cho phép của admin, không có bước duyệt thứ hai. Lấy IP LAN từ Android Wi-Fi Settings. Không đưa mã lên chat hoặc shell history.

## 3. Bphone / Sony XZ3 — join cùng một bộ cài

```bash
cd ~/storage/downloads/ASC-QuickStart-0.4.1
bash install.sh node --controller https://IP_ZTE:8443 --pin SHA256_PIN_ZTE --name Bphone
cd ~/asc-cluster
python3 -m asc.cli status
python3 -m asc.cli agent-run
```

Thay IP/PIN rồi nhập mã khi được hỏi (ẩn ký tự). Mỗi node dùng một mã riêng. Agent tự gửi profile; không cần nhập thông số phần cứng. PIN sai: dừng trước khi gửi mã/token, không chuyển sang HTTP hoặc bỏ xác minh.

Trên ZTE:

```bash
python3 -m asc.cli controller-nodes
python3 -m asc.cli controller-node NODE_ID
python3 -m asc.cli controller-rename NODE_ID "Bphone phong lam viec"
```

Tên 1–64 ký tự, không khoảng trắng đầu/cuối hoặc ký tự điều khiển. Output thông thường không chứa token/hash token. `status` là cache cục bộ, không chứng minh token vẫn có quyền hiện tại; trạng thái trước lần heartbeat đầu là unknown.

Chạy lại `bash install.sh node` trên cùng bản cài giữ nguyên node.json, không hỏi mã và không tạo node mới. Installer không thay source cũ; nếu phiên bản khác, dừng và yêu cầu nâng cấp rõ ràng.
Node đã enrolled và không còn pending có thể chạy lại installer khi agent đang chạy;
thao tác chỉ báo giữ nguyên identity, không start/stop thêm agent.

## 4. Start, status, stop; không chạy trùng

- Start foreground: `python3 -m asc.cli controller-run` hoặc `python3 -m asc.cli agent-run`.
- Chỉ gửi một heartbeat để kiểm tra: `python3 -m asc.cli agent-run --once` (exit khác 0 nếu thất bại).
- Status không gửi mạng: `python3 -m asc.cli status`. Trường foreground là trạng thái khóa tiến trình, bao gồm thao tác join/re-pair đang giữ khóa.
- Không đọc/xác minh được khóa: foreground trả null (unknown), không đoán tiến trình đang chạy.
- Stop: Ctrl+C tại terminal đang chạy. Không có daemon hoặc lệnh kill theo PID; không ghi startup/boot/crontab/service.
- Chạy lần thứ hai trong cùng ASC_HOME bị khóa từ chối. Khóa do OS giữ và tự nhả khi tiến trình thoát; file .lock còn lại là bình thường, không xóa nó khi tiến trình chạy.
- Script tiện dụng: `bash scripts/run-controller.sh` hoặc `bash scripts/run-agent.sh`; với release nâng cấp đặt `ASC_CODE="$HOME/asc-cluster-0.4.1"` trước khi dùng script. Agent/controller v0.4 không biết khóa mới: phải tự dừng chúng trước nâng cấp.

## 5. Revoke, rotate và re-pair

Trên ZTE, thu hồi ngay token của node:

```bash
python3 -m asc.cli controller-revoke NODE_ID
python3 -m asc.cli controller-node NODE_ID
```

Lặp revoke an toàn: không tăng version lần nữa. Node chuyển revoked/offline, heartbeat tiếp theo bị 401; agent dừng, lưu repair-required và giữ identity/snapshot. Node thường không được gọi endpoint admin. Request đã xác thực và đang xử lý trước revoke có thể đã nhận snapshot.

Để thay token của node đang active hoặc ghép lại node revoked, dừng agent bằng Ctrl+C trước. Trên ZTE:

```bash
python3 -m asc.cli controller-pair --node-id NODE_ID
```

Trên chính Bphone/XZ3 đã có node.json:

```bash
python3 -m asc.cli node-repair
python3 -m asc.cli agent-run --once
python3 -m asc.cli agent-run
```

Nhập mã targeted mới. Giữ node ID, cluster ID, tên admin; đổi token riêng, tăng token_version. Token cũ không còn dùng được sau re-pair thành công. Tạo code mới không tự vô hiệu token active; nếu nghi lộ token, revoke trước rồi tạo code. Mỗi node chỉ có một grant re-pair đang lưu; tạo grant tiếp theo thay grant cũ.

Nếu mất phản hồi mạng, chạy lại đúng node-join/node-repair: yêu cầu được lưu riêng ở enrollment_pending.json, server nhận lại cùng yêu cầu mà không thêm node hay rotate lần nữa. Retry grant đã dùng được giữ đến 24 giờ sau hạn mã, chỉ khi token hiện tại còn active và đúng yêu cầu gốc. Không có retry tự động bằng một secret khác.

Nếu **join lần đầu** bị hết hạn mã hoặc quá cửa sổ retry, ZTE cấp mã general mới bằng controller-pair; node chạy lại lệnh node-join với cùng --controller/--pin và thêm --new-code (hoặc installer node với các cờ này). Yêu cầu chờ giữ nguyên enrollment_id/token, chỉ thay mã grant; nếu join cũ đã thành công thì Controller trả lại cùng node ID. Không xóa pending để bắt đầu lại. Nếu token của thao tác cũ đã revoked/rotated, đường này bị từ chối: dùng targeted re-pair.

Nếu mã hết hạn/chưa dùng hoặc grant đã bị thay, admin tạo targeted code mới rồi node chạy `python3 -m asc.cli node-repair --new-code`. Thao tác này lưu lại pending cũ dưới tên enrollment_abandoned-*.json, không âm thầm bỏ nó.

Nếu chưa có node.json nhưng join có thể đã thành công: **không xóa pending rồi join mới**. Admin xem controller-nodes để xác định ID, tạo code targeted; trên node dùng:

```bash
python3 -m asc.cli node-repair --controller https://IP_ZTE:8443 --pin SHA256_PIN_ZTE --node-id NODE_ID --cluster-id CLUSTER_ID --new-code
```

Nếu mất cả identity và không có bản sao, cũng dùng quy trình targeted này. Không tự dò secret hoặc tự tạo node khác. Nếu mất controller.json/TLS/registry, dừng và khôi phục bản sao riêng; không chạy controller-init để tạo danh tính thay thế. Các node_before_repair-*.json, pending và bản sao là secret; không đưa vào repo/ZIP.

## 6. SD và giới hạn runtime

```bash
python3 -m asc.cli inspect
python3 -m asc.cli inspect --sd-write
```

Chỉ dùng --sd-write khi chủ động muốn thử trên máy thử nghiệm. Không đọc được SD: sd_status=unknown; tìm thấy đường dẫn: detected; chỉ write/readback/delete probe thành công mới là writable-tested. Không tạo thư mục SD root, không kiểm tra ghi trên M51 hoặc thiết bị chưa nhận diện. Writable-tested chỉ phản ánh probe nhỏ tại thời điểm đó, không chứng minh độ bền thẻ. Android Doze/OEM vẫn có thể ngắt tiến trình.

## 7. Nâng cấp v0.4, bảo toàn source và identity

Dừng Controller và mọi Agent cũ bằng Ctrl+C. Chạy trên **từng máy thử nghiệm**, với ASC_HOME mặc định. Nếu dùng ASC_HOME khác, thay đường dẫn tương ứng. Không sao lưu secret vào Download/SD/source.

```bash
umask 077
ASC_BACKUP="$HOME/asc-before-0.4.1-$(date +%Y%m%d-%H%M%S)"
mkdir -m 700 "$ASC_BACKUP"
cp -Rp "$HOME/.asc" "$ASC_BACKUP/state"
```

Chỉ copy khi mọi ASC process đã dừng: giữ cả SQLite và WAL/SHM nếu còn. Đây là bản sao trạng thái registry development đã dừng, không phải tính năng backup file NAS. Giữ đường dẫn ASC_BACKUP để rollback.

Từ thư mục source release mới, tạo thư mục code có version (không ghi đè ~/asc-cluster cũ):

```bash
cd ~/storage/downloads/ASC-QuickStart-0.4.1
if [[ ! -e "$HOME/asc-cluster-0.4.1" ]]; then
  mkdir -m 700 "$HOME/asc-cluster-0.4.1"
  cp -R asc docs scripts "$HOME/asc-cluster-0.4.1/"
  cp AGENTS.md README-VI.md "$HOME/asc-cluster-0.4.1/"
else
  echo "Thu muc release da ton tai: kiem tra, khong ghi de"
fi
cd ~/asc-cluster-0.4.1
```

Trên ZTE chạy controller-run: migration transaction cộng cột, PRAGMA user_version 0 -> 2; không đổi cluster ID/node ID/hash token/join-code v0.4. Trên node chỉ chạy agent-run, không join lại. Config v0.4 chưa có config_version vẫn đọc được, không tự viết lại token. API vẫn /api/v1; Controller mới nhận agent v0.4 (profile thiếu version là legacy). Client mới cần Controller Phase 1.1 cho ghép mới/re-pair; heartbeat identity cũ vẫn tương thích wire v0.4.

## 8. Kiểm thử local và kết quả nghiệm thu

Từ source workspace, cần Python >=3.9 và openssl trong PATH. Các bài TLS dùng loopback tạm và file tạm, không truy cập điện thoại hoặc production.

Windows PowerShell — chuẩn bị OpenSSL CLI trước khi chạy suite:

Python có module ssl không đồng nghĩa có openssl.exe. Trên máy dev này đã tìm thấy
executable đi kèm Git for Windows tại đường dẫn dưới đây; nếu máy khác dùng thư mục
khác, thay bằng thư mục bin thực sự chứa OpenSSL đã được cài trên máy đó. Không tải
binary không rõ nguồn và không thay PATH/Termux trên M51.

```powershell
Set-Location E:\CODE\ASC-QuickStart
$ascOpenSslBin = 'C:\Program Files\Git\usr\bin'
if (-not (Test-Path -LiteralPath (Join-Path $ascOpenSslBin 'openssl.exe') -PathType Leaf)) {
    throw 'Khong tim thay openssl.exe: cai OpenSSL tren may dev va sua ascOpenSslBin theo thu muc bin thuc te.'
}
$env:Path = "$ascOpenSslBin;$env:Path"
Get-Command openssl -ErrorAction Stop
openssl version
```

Lệnh trên chỉ bổ sung PATH của phiên PowerShell hiện tại; không tự cài dependency hoặc
sửa PATH toàn hệ thống. Nếu tự thêm PATH qua Windows Environment Variables, mở lại
PowerShell/Codex để tiến trình con nhận PATH mới. Nếu executable có nhưng không chạy,
kiểm tra bộ cài/DLL và kiến trúc phù hợp. Bỏ OpenSSL khỏi PATH vẫn phải làm bài TLS báo
ERROR rõ ràng, không SKIP hoặc PASS giả. Pinning không đổi.

Sau khi OpenSSL chạy được, kiểm tra riêng hai lỗi cũ và chạy toàn bộ suite:

```powershell
Set-Location E:\CODE\ASC-QuickStart
$env:PYTHONDONTWRITEBYTECODE = '1'
python -m unittest discover -s tests -p test_identity.py -v
python -m unittest discover -s tests -p test_lifecycle.py -k test_v04_migration_keeps_every_identity_and_code -v
python -m unittest discover -s tests -p test_foundation.py -k test_lan_tls_join_heartbeat_and_certificate_pin -v
python -m unittest discover -s tests -p test_lifecycle.py -k LifecycleHTTPTests -v
python -m unittest discover -s tests -v
```

`test_identity.py` chỉ mock kiểm tra thông báo dependency và argv; các bài HTTPS/TLS
phía sau vẫn tạo certificate thật và kiểm tra pin sai. Fixture SQLite dùng closing cho
connection bên ngoài transaction, đóng cursor và thử đổi tên/xóa ngay trên Windows;
không dùng gc.collect, sleep hoặc bỏ qua lỗi cleanup.

Linux/Termux, từ source release có thư mục tests:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

Kết quả chủ dự án cung cấp ngày 2026-10-23: **40 tests, OK (skipped=3)** trên Windows. Bao gồm enrollment/lifecycle, TLS/pin, migration và khóa chạy trùng. Ba test installer được SKIP vì cần Linux/Termux; chưa tuyên bố các bài này PASS trên Linux. Lượt cập nhật workflow/xuất bản chỉ sửa docs, giữ nguyên source/test, nên dùng lại kết quả này theo chỉ dẫn chủ dự án. Không thay dependency hoặc cài WSL để chạy lại. Trong các Phase tiếp theo, Codex tự chạy test mục tiêu rồi full suite áp dụng được; các lệnh trên phục vụ việc tái hiện khi cần.

Checklist LAN hai máy — hoãn đến giai đoạn Android sau nghiệm thu end-to-end v1.0 trên Windows; không thực hiện trong lượt sửa này:

1. ZTE chạy Controller; tạo code 60 giây bằng controller-pair --ttl 60. Bphone join, agent-run --once; ID xuất hiện trong controller-nodes.
2. Ghi lại ID riêng; chạy lại installer cùng release, restart agent và reboot máy thử nghiệm rồi start thủ công. ID/số node không đổi.
3. Mở agent-run hai terminal: terminal thứ hai bị từ chối. Ctrl+C terminal đầu; status foreground.agent=false. Làm tương tự Controller.
4. Tạo code rồi chờ >60 giây: join từ XZ3 chưa enrolled báo hết hạn. Tạo code mới mới được join; code đã dùng không cho người khác dùng lại.
5. Revoke Bphone, xác nhận heartbeat 401 và repair-required; chạy revoke lần nữa. Targeted re-pair giữ ID, tăng token_version, một heartbeat mới thành công.
6. Khi node chưa enrolled, cố ý dùng PIN sai: không gửi join, không lưu identity; chạy lại với PIN đúng. Không sửa node.json để thử PIN.
7. Chạy inspect khi Android thiếu quyền: null/unknown được giữ nguyên. Không dùng model/preset thay số đo runtime.
8. Nâng cấp dữ liệu v0.4 theo mục 7; xác nhận ID/token cũ heartbeat được. Dùng suite tự động cho payload lớn, brute force và phân quyền; không thử flood LAN.
9. M51 không tham gia checklist; không cần SSH, log, DB hay thao tác production.

Trước khi chia sẻ kết quả: che code, token, enrollment payload, file identity/TLS key, private backup, IP/MAC/serial và tên nhạy cảm. Có thể chia sẻ tên test, PASS/FAIL, mã HTTP/lỗi đã che và số lượng node.

## 9. Rollback v0.4

Schema 2 cộng cột nhưng code Controller v0.4 dùng INSERT không nêu cột, đồng thời không hiểu revoke. **Không chạy Controller v0.4 trực tiếp trên DB schema 2.** Dừng tất cả ASC trước rollback, giữ LAN cô lập trong lúc phục hồi.

Giữ trạng thái mới riêng, khôi phục snapshot trước nâng cấp trên từng máy tương ứng (thay ASC_BACKUP bằng đường dẫn đã lưu, không copy secret của máy khác):

```bash
ASC_BACKUP="$HOME/asc-before-0.4.1-THOI_DIEM_DA_LUU"
mv "$HOME/.asc" "$HOME/.asc-phase1.1-retained-$(date +%Y%m%d-%H%M%S)"
cp -Rp "$ASC_BACKUP/state" "$HOME/.asc"
cd ~/asc-cluster
```

Sau đó ZTE chạy controller-run v0.4; node chạy agent-run v0.4 từ source cũ. Không xóa Termux hoặc private state. Rollback mất các thay đổi registry sau bản sao; code v0.4 không thực thi revoke. Token đã thu hồi sau bản sao có thể hoạt động lại: nếu nghi lộ token, không mở mạng lại với v0.4; giữ Phase 1.1 hoặc thiết kế re-enrollment có kiểm soát. Không rollback riêng một Controller trong khi node đã đổi token mà không đồng bộ kế hoạch phục hồi.


## 10. Source sạch và xuất bản GitHub

Origin: https://github.com/litequang/Android-Storage-Cluster-ASC.git.
Chủ dự án đã xác nhận Windows 40 tests OK (skipped=3) và ủy quyền review/commit/push
v0.4.1 lên main. Codex được thực hiện các bước đó trong phạm vi được giao; không cần
xin lại quyền đã cấp. Khi network, sandbox hoặc xác thực chặn, báo blocker cụ thể,
không vượt bảo vệ. Trạng thái thực tế và hash xem bằng các lệnh kiểm tra bên dưới.

.gitignore loại private state/recovery copies, khóa TLS/SSH, DB runtime/journal,
.env/credential/token, logs/temp và archive. Vẫn giữ ASC_HOME ngoài repo. Trước mỗi
commit/push phải kiểm tra cả file đã tracked và nội dung staged; ignore không xóa file
đã tracked hoặc phát hiện mọi secret nhúng trong source. Không dùng git add -f.
Nếu từng commit secret thật, revoke/rotate rồi lập kế hoạch khắc phục lịch sử riêng;
không tự rewrite lịch sử hoặc force push.

Metadata .git có thể thuộc tài khoản sandbox. Helper sau chỉ tin workspace này cho
từng lệnh, không sửa safe.directory global và không dùng wildcard:

```powershell
Set-Location E:\CODE\ASC-QuickStart
function Invoke-AscGit {
    & git -c safe.directory=E:/CODE/ASC-QuickStart @args
    if ($LASTEXITCODE -ne 0) { throw 'Git failed: stop and inspect; do not force.' }
}
Invoke-AscGit status --short --branch
Invoke-AscGit remote -v
Invoke-AscGit ls-files
Invoke-AscGit diff --cached --name-only
Invoke-AscGit diff --cached
```

Xác minh origin fetch/push đúng URL trên và nhánh main. Đọc refs/fetch remote trước
đồng bộ; nếu đã có lịch sử thì review và tích hợp trên lịch sử đó. Không reset --hard,
clean, xóa lịch sử hoặc force để ép source local lên GitHub. Với thay đổi mã, chạy test
mục tiêu rồi full suite trước commit Phase; với docs-only, được dùng PASS source/test
không đổi và ghi rõ nguồn kết quả.

`.gitattributes` giữ LF cho *.sh khi checkout trên Windows để script vẫn đọc được bằng Bash;
không cần đổi core.autocrlf toàn hệ thống. Metadata này không sửa code/test của kết quả PASS.

Stage source rõ phạm vi, review toàn bộ staged diff và các phát hiện secret trước commit:

```powershell
Invoke-AscGit add -- .gitignore .gitattributes AGENTS.md ASC-CODEX-PHASE1-1.md CODEX-NEXT-PROMPT.md README-VI.md install.sh asc docs scripts tests
Invoke-AscGit diff --cached --name-only
Invoke-AscGit diff --cached --stat
Invoke-AscGit diff --cached
```

Khi kiểm tra sạch và có kết quả áp dụng được, commit bằng danh tính Git đã cấu hình.
Lệnh mẫu cho commit xuất bản v0.4.1; không lặp lại nếu commit đã tồn tại:

```powershell
Invoke-AscGit commit -m "Publish ASC v0.4.1 and update local development workflow"
Invoke-AscGit push --set-upstream origin main
Invoke-AscGit rev-parse HEAD
Invoke-AscGit ls-remote origin refs/heads/main
Invoke-AscGit status --short --branch
```

Push bình thường phải giữ lịch sử; nếu non-fast-forward thì dừng để fetch/review/tích hợp,
không dùng --force hoặc --force-with-lease. Hash remote main phải bằng commit local
định xuất bản. Không tạo workflow chạy trên production, không thao tác M51.

Lượt docs/workflow này không đổi API v1, schema 2 hoặc identity. Nếu cần đảo thay đổi
đã commit, dùng git revert trên commit phù hợp để giữ lịch sử; không sửa private state.
Rollback runtime về v0.4 vẫn theo mục 9 và cần bản sao private state trước migration.

## 11. Storage Foundation v0.5.0 — Windows trước Android

Không cần điện thoại/Termux để nghiệm thu:
```powershell
Set-Location E:\CODE\ASC-QuickStart
Get-Command openssl
openssl version
python -B -m unittest tests.test_storage -v
python -B -m unittest tests.test_storage_cluster -v
python -B -m unittest discover -s tests -v
```
Nếu OpenSSL đã có trong Git for Windows nhưng chưa ở PATH, chỉ đổi terminal hiện tại:
```powershell
$env:PATH = "C:\Program Files\Git\usr\bin;$env:PATH"
```
Suite tự tạo/xóa state/certificate/root trong TemporaryDirectory, không sửa PATH hệ thống hay cài dependency. TLS thiếu OpenSSL là ERROR. Ba installer cases vẫn cần POSIX Bash; không coi SKIP là Linux PASS. Xem ma trận lỗi và kết quả thực tế tại [PHASE1-2A-ACCEPTANCE](docs/PHASE1-2A-ACCEPTANCE.md).

Storage chỉ bật khi có storage.json. Lệnh dưới là tham khảo cho node phát triển đã enrolled hợp lệ, với ASC_HOME riêng ngoài source/shared SD; không tự tạo node.json hoặc dùng credential production. Trên Android vẫn chặn M51/thiết bị chưa nhận diện. Windows multi-node hiện được khởi tạo tự động bằng suite, không bỏ qua guard Android của controller-init/node-join.

```text
python -m asc.cli storage-init --root EMPTY_APPROVED_ROOT --quota 67108864 --reserve 67108864 --max-upload 33554432 --rate 8388608 --host 127.0.0.1 --port 9443
python -m asc.cli storage-add-volume --root ANOTHER_EMPTY_ROOT --kind directory --quota 67108864 --reserve 67108864
python -m asc.cli storage-status
python -m asc.cli agent-run
```
storage-init không có --root chọn HOME/storage-data; root phải mới/rỗng. Các kind: directory, internal, termux_sd. SD chỉ cho phép thư mục con của app folder Termux đã phát hiện, không tự cấp quyền hay format. storage-status khi Agent đã dừng thực hiện probe nhỏ, discovery và inventory; không tự đăng ký candidate. Khi Agent chạy, heartbeat gửi storage_version=1 và HTTPS storage chạy cùng vòng đời foreground. Không có storage.json giữ hành vi cũ. Bind mặc định loopback; LAN chỉ dùng địa chỉ private cụ thể và firewall phù hợp, không port-forward.

Quyền người dùng tách khỏi node token. Trên Controller phát triển đã chạy, admin xuất grant ngắn hạn vào file private:
```text
python -m asc.cli controller-storage-grant NODE_ID VOLUME_ID --operations read,list,write,verify --ttl 300 --out PRIVATE_OWNER_DIR/owner-grant.json
python -m asc.cli storage-upload SOURCE_FILE logical/file.bin --key unique_request_0001 --origin https://NODE:9443 --pin CONFIRMED_NODE_STORAGE_PIN --grant-file PRIVATE_OWNER_DIR/owner-grant.json
python -m asc.cli storage-download FILE_ID NEW_OUTPUT_FILE --origin https://NODE:9443 --pin CONFIRMED_NODE_STORAGE_PIN --grant-file PRIVATE_OWNER_DIR/owner-grant.json
```
Xác nhận riêng pin của storage node do storage-init cung cấp; pin Controller không thay thế pin này. Grant TTL 30–900 giây, chỉ ghi hash ở Controller; quyền whole-volume của owner, chưa có login/ACL đa người dùng. Mỗi thao tác gọi Controller để xác thực; mất Controller từ chối truy cập. Revoke/re-pair làm grant thế hệ cũ hết quyền. Client không ghi đè file output có sẵn; output download lỗi được giữ để kiểm tra, không coi là file đã xác minh.

Giới hạn: chunk 64 KiB, một transfer/engine, default 8 MiB/s, max upload mặc định 64 MiB (tối đa cấu hình 1 GiB); quota dự trữ hai bản trong lúc commit, cộng orphan/staging còn sót. Với quota mặc định 64 MiB, upload mới tối đa 32 MiB khi volume rỗng. Chưa hỗ trợ resume theo offset: gửi lại toàn bộ body với session/key cũ. Commit không thay thế logical path đã tồn tại; version hiện là 1.

```text
python -m asc.cli storage-cleanup --older-than 86400
python -m asc.cli storage-cleanup --older-than 86400 --apply
```
Dừng Agent trước lệnh local. Mặc định dry-run, --apply chỉ xóa staging đủ tuổi/trạng thái, không xóa final object hay bản đã commit. NEEDS_REVIEW/metadata conflict/orphan cần kiểm tra thủ công, không sửa marker/PRAGMA để giả hợp lệ. Chi tiết [API](docs/NODE_PROTOCOL.md), [schema](docs/DATA_MODEL.md), [lỗi](docs/TROUBLESHOOTING.md).

Nâng cấp/rollback: trước khi chạy bản mới, dừng mọi ASC development process và sao lưu đầy đủ private state (DB/WAL/SHM, config, khóa, identity) cùng các volume; giữ source b74bb594a5bff9ad0926255effed1fd41bbc1647 riêng. Registry 0/2 -> 3 additive, manifest mới schema 1. Source cũ không mở DB schema 3. Rollback dùng bản sao dừng trước migration với source tương ứng; giữ manifest/object mới riêng, không xóa file người dùng. Khôi phục backup có thể mất thay đổi và kích hoạt lại credential từng bị revoke; cô lập mạng và rà soát token. Không có downgrade tự động.

Mới chứng minh storage cục bộ trên fixture Windows; chưa chứng minh power-cut durability, Android/SD/Doze, distributed durability hay production readiness. Giữ các gate đó trước cài điện thoại. Phase 1.2B cần nhiệm vụ riêng và hợp đồng metadata/fencing/migration/fault injection.

Kết quả Codex cuối cùng (2026-10-23): **61 tests, OK (skipped=3)** — 58 PASS, không FAIL/ERROR. Ba SKIP là installer POSIX; mô phỏng ba node HTTPS đạt. Source/test đã kiểm tra bằng full suite mới; không dùng lại PASS của v0.4.1.

## 12. Global Catalog v0.6.0 — nghiệm thu Windows

Lệnh tái hiện:
```powershell
Set-Location E:\CODE\ASC-QuickStart
Get-Command openssl
python -B -m unittest tests.test_catalog -v
python -B -m unittest tests.test_distributed -v
python -B -m unittest discover -s tests -v
```
Nếu OpenSSL đã có trong Git for Windows nhưng chưa có PATH, chỉ sửa terminal hiện tại:
```powershell
$env:PATH = "C:\Program Files\Git\usr\bin;$env:PATH"
```
Không cài dependency hoặc thay môi trường hệ thống tự động. Suite tạo Controller và ba Agent bằng fixture tạm, không cần điện thoại. [Biên bản nghiệm thu](docs/PHASE1-2B-ACCEPTANCE.md) ghi ma trận lỗi, kết quả thực tế và giới hạn.

Các lệnh quản trị sau dành cho môi trường phát triển đã cấu hình identity hợp lệ, ASC_HOME riêng ngoài repo/shared storage. Windows multi-node được khởi tạo bằng suite; guard Android/M51 không bị bỏ qua. Trên Controller phát triển, owner phê duyệt pin/volume và nhãn device domain ổn định cho mỗi node:
```text
python -m asc.cli catalog-register-node NODE_ID --origin https://PRIVATE_NODE_IP:9443 --pin CONFIRMED_NODE_STORAGE_PIN --device-id PHONE_LABEL --volume-id VOLUME_ID
python -m asc.cli catalog-register-node METADATA_NODE_ID --device-id PHONE_LABEL --metadata-only
python -m asc.cli catalog-status
python -m asc.cli catalog-upload SOURCE_FILE docs/file.bin --key unique_upload_0001 --policy replicated_2 --version 1
python -m asc.cli catalog-files
python -m asc.cli catalog-file GLOBAL_FILE_ID
python -m asc.cli catalog-replicas GLOBAL_FILE_ID
python -m asc.cli catalog-download GLOBAL_FILE_ID NEW_OUTPUT_FILE
```
Không đưa token vào cờ hoặc dùng node token thay quyền owner. Admin credential chỉ tới Controller qua HTTPS có pin; Agent nhận grant hẹp, ngắn hạn. Node re-pair giữ identity nhưng phải được owner phê duyệt generation/endpoint/volume lại. Hai identity trên một điện thoại phải cùng device domain.

Worker chạy cùng controller-run, mặc định một transfer, 4 MiB/s và lease 300 giây:
```text
python -m asc.cli controller-run --catalog-rate 4194304 --job-timeout 300
python -m asc.cli catalog-jobs
python -m asc.cli catalog-job JOB_ID
python -m asc.cli catalog-run-job JOB_ID
python -m asc.cli catalog-retry-job JOB_ID
python -m asc.cli catalog-reconcile
python -m asc.cli catalog-policy GLOBAL_FILE_ID --policy replicated_3
```
RUNNING lỗi được retry với backoff, tối đa năm lần trước FAILED; owner xem nguyên nhân rồi retry cùng job. File/session/key không đổi do retry. PENDING owner upload chờ hoàn tất/resume; dùng lại original key/content/version/policy để cấp grant mới. ACK chưa đủ làm replica hợp lệ: Controller xác minh cả bytes được phục vụ. Khi worker bận, ACK có thể trả pending; theo dõi verified/available counts.

Agent heartbeat tự sync metadata khi Controller bật tính năng và node được duyệt. Có thể yêu cầu/tra cứu:
```text
python -m asc.cli catalog-sync
python -m asc.cli catalog-local-status
python -m asc.cli catalog-local-files
python -m asc.cli catalog-local-file GLOBAL_FILE_ID
```
Cache offline giữ bản cuối đã xác minh, luôn đánh dấu stale/read_only; không xác nhận global write hoặc tự nhận quyền Controller. Khi thiếu log, node lấy snapshot có kiểm tra cluster/epoch/revision/digest. Không chấp nhận checkpoint lùi hoặc snapshot khác nội dung tại cùng checkpoint.

desired/verified/available là ba số khác nhau. Chỉ bản vật lý được xác minh mới có evidence VERIFIED; available còn phụ thuộc trạng thái identity/volume gần nhất. Không đủ node/quota -> DEGRADED, không báo đã bảo vệ đủ. Nếu Controller offline, vẫn đọc metadata cache cục bộ; API file tiếp tục cần Controller xác thực.

Giới hạn: dữ liệu hiện relay qua Controller theo chunk 64 KiB và có thêm readback/hash; chưa hỗ trợ offset/chunk resume hoặc direct peer pull. Catalog tối đa 256 immutable versions, 16 approved nodes, 2048 jobs; lịch sử metadata giữ 1024 revisions. Reconcile quay vòng tối đa 16 trang inventory/200 record và 8 physical proof mỗi lượt; báo cáo diagnostic có giới hạn, cursor được lưu qua restart. Không có object GC, tự xóa excess replica hoặc tự import file standalone v0.5; file lạ/bản nghi vấn được báo và giữ nguyên. Unknown load/stability vẫn null.

Migration: Controller registry 0/2/3 -> 4 additive; local manifest vẫn 1, cache metadata mới 1. Controller mới giữ lifecycle/owner grants cũ; global jobs cần Agent v0.6. Giữ API [NODE_PROTOCOL](docs/NODE_PROTOCOL.md), schema [DATA_MODEL](docs/DATA_MODEL.md), [CODEMAP](docs/CODEMAP.md) và lỗi [TROUBLESHOOTING](docs/TROUBLESHOOTING.md) làm nguồn chuẩn.

Rollback: dừng toàn bộ ASC development, lưu riêng state/object hiện tại, phục hồi bản sao private state đầy đủ trước nâng cấp cùng source v0.5.0 tại f70b095b8f2ec507baaea5a4bdb3d03667209f94. Không chạy v0.5 Controller trên registry 4 hoặc sửa PRAGMA. Giữ manifest/volume/object mới; không xóa chúng để downgrade. Restore có thể mất thay đổi catalog và kích hoạt lại credential cũ; cô lập môi trường và rà soát quyền. Cache đi trước Controller được phục hồi sẽ từ chối checkpoint lùi; không ép reset epoch.

Gate Phase 1.2B đã đạt trên Windows. Trước Phase 2 cần thiết kế deterministic prepared commands, Raft/fencing/membership/epoch recovery và acceptance partition/quorum. Chưa triển khai Phase 2, Linux/Termux installer, Android/SD/Doze hoặc power-cut acceptance.
