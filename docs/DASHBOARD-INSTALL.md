# ASC Controller Dashboard 0.5.0-dashboard-alpha

Internal source package: `asc-controller-0.5.0-dashboard-alpha.tar.gz`.
Controller Termux/Linux single-writer, cùng Engine/Catalog hiện có. APK Storage
Node5 giữ nguyên; APK không phải Controller. Source/Linux synthetic qualification
không phải nghiệm thu Android/điện thoại/production. Xem receipt và kết quả thật
trong GitHub `docs/DASHBOARD-ACCEPTANCE.md`, `qualification/dashboard-publication.json`.
Không dùng hướng dẫn archive Demo0.3/0.4.1 lịch sử để cài gói này.

## ZTE đã có Controller0.4.3 — nâng cấp, KHÔNG init lại

Owner chạy trên ZTE hoặc qua PC đã được owner cho phép; Codex Cloud không truy
cập điện thoại. Không chạy trên M51/production. Giữ Node ID/Cluster ID/Volume ID,
PIN/keys/account/history/bytes. Không uninstall APK, copy private Termux sang APK,
format, chmod777, đổi CA/proxy hoặc bỏ qua guard. Guard từ chối ->dừng, giữ lỗi.

1. Dừng các foreground Controller/Dashboard và Termux Node thuộc ASC bằng Ctrl+C
   trong đúng terminal. APK Node dùng Stop trong app nếu cần. Không kill PID đoán
   mò, không thay Termux:Boot/hệ thống. Upgrade là stopped, chưa rolling update.
2. Terminal Termux riêng, khai báo đúng prefix/state hiện đang dùng:

```sh
umask 077
ASC_CODE="$HOME/.local/share/asc-demo"
ASC_STATE="$HOME/.asc-demo"
ascdemo() { sh "$ASC_CODE/bin/asc-demo" --state "$ASC_STATE" "$@"; }
ascdemo diagnose
ASC_BACKUPS="$HOME/asc-dashboard-backups"
mkdir -p "$ASC_BACKUPS"
ASC_RUN="$(date -u +%Y%m%dT%H%M%SZ)"
ASC_BEFORE="$ASC_BACKUPS/before-050-$ASC_RUN"
ascdemo backup "$ASC_BEFORE"
ascdemo verify-backup "$ASC_BEFORE"
```

Lệnh lỗi thì dừng; không xóa lock/state để vượt lỗi. Backup phải ở ngoài code,
state và mọi volume được backup, destination mới. Đây là backup stopped của
Controller và các volume Termux được quản lý tại máy đó; không tự backup private
APK/Keystore hay mọi remote Node, không phải external disaster recovery độc lập.

3. Tải archive +checksum từ repository chính thức, kiểm tra trước khi giải nén.
   Ưu tiên đặt `ASC_REF` bằng commit phát hành bất biến trong receipt GitHub.
   Ref nhánh dưới đây tiện dùng nhưng có thể tiến lên; checksum mismatch ->dừng.
   Dependency: Python>=3.10, OpenSSL CLI (`openssl-tool` trong Termux), curl và
   sha256sum. Chủ máy tự cài package còn thiếu; không `pkg upgrade` tự động.

```sh
ASC_REF="feature/dashboard-full"
ASC_BUNDLE="asc-controller-0.5.0-dashboard-alpha.tar.gz"
ASC_WORK="$(mktemp -d "$HOME/asc-dashboard-050.XXXXXXXX")"
cd "$ASC_WORK"
ASC_RAW="https://raw.githubusercontent.com/litequang/Android-Storage-Cluster-ASC/$ASC_REF/candidates"
curl --fail --location --proto '=https' --tlsv1.2 "$ASC_RAW/$ASC_BUNDLE" --output "$ASC_BUNDLE"
curl --fail --location --proto '=https' --tlsv1.2 "$ASC_RAW/$ASC_BUNDLE.sha256" --output "$ASC_BUNDLE.sha256"
sha256sum -c "$ASC_BUNDLE.sha256"
```

Đối chiếu SHA với receipt/commit được tin cậy, không chỉ tin hai file được sửa
cùng lúc. Không tiếp tục nếu tải lỗi/checksum sai. Không `curl | sh`, `-k` hoặc HTTP.
Sau khi checksum PASS, giải nén regular files vào thư mục mới, có giới hạn:

```sh
python3 - "$ASC_BUNDLE" "$ASC_WORK/extracted" <<'PY'
import os, pathlib, shutil, sys, tarfile
archive, target = sys.argv[1], pathlib.Path(sys.argv[2])
with tarfile.open(archive) as saved:
    members = saved.getmembers()
    if not 1 <= len(members) <= 512 or sum(m.size for m in members) > 32*1024**2:
        raise SystemExit('Archive limit; STOP')
    names = set()
    for item in members:
        name = pathlib.PurePosixPath(item.name)
        if (not item.isfile() or item.name != str(name) or name.is_absolute()
            or name.parts[0] != 'asc-demo-alpha' or len(name.parts)<2
            or any(p in ('.','..','') for p in name.parts) or '\\' in item.name
            or item.name in names):
            raise SystemExit('Unsafe archive; STOP')
        names.add(item.name)
    target.mkdir(mode=0o700)  # Must be NEW; never overwrite an extraction.
    for item in members:
        path = target.joinpath(*pathlib.PurePosixPath(item.name).parts)
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with saved.extractfile(item) as source, path.open('xb') as output:
            shutil.copyfileobj(source, output, 65536)
            output.flush(); os.fsync(output.fileno())
print('Extracted; verify complete manifest next')
PY
ASC_SRC="$ASC_WORK/extracted/asc-demo-alpha"
ASC_NEW_ID="$(python3 -I -B -c 'import sys; from pathlib import Path; sys.path.insert(0,sys.argv[1]); from asc.demo.package import verify; print(verify(Path(sys.argv[1]))["release_id"])' "$ASC_SRC")"
printf '%s\n' "$ASC_NEW_ID"
ascdemo stage "$ASC_SRC"
ascdemo upgrade-preflight "$ASC_NEW_ID"
ascdemo upgrade "$ASC_NEW_ID" --backup "$ASC_BACKUPS/activation-050-$ASC_RUN"
ascdemo verify-backup "$ASC_BACKUPS/activation-050-$ASC_RUN"
ascdemo diagnose
```

Đọc PASS/compatible và kiểm tra đúng release trước mỗi bước; không nối tiếp khi
previous command lỗi. Upgrade tạo thêm backup hiện trạng dưới khóa gốc, không
migration schema, không thay identity hoặc restore DB. Không sửa source/assets
trực tiếp trong release được hash-verify. Giữ nguyên các release cũ trong prefix.

4. Khởi chạy bằng launcher hiện có:

```sh
ascdemo run-controller --dashboard
```

Terminal này foreground. Terminal thứ hai khai báo lại `ASC_CODE`, `ASC_STATE` và
hàm `ascdemo` ở bước2, rồi chạy `ascdemo dashboard-code`. Không gửi mã/cookie/token
vào chat/log công khai. Dùng URL Dashboard đã cấu hình (thường8444, khác lifecycle
8443 và Node9443). Upgrade giữ CA/IP/PIN: không dashboard-init lại để né lỗi.

Nếu browser cần public CA, export vào file MỚI bằng `ascdemo dashboard-trust --out
NEW_PUBLIC_CA_FILE`, đối chiếu public fingerprint độc lập rồi owner trust CA trên
Android/PC. Chỉ copy public CA, không `ca.key`/`server.key`; không bỏ qua TLS error.
IP/SAN đổi cần quy trình cấu hình riêng, không tự tạo identity mới.

5. Login bằng mã owner, vào Tài khoản tạo Owner/password do bạn chọn. Không có
   password mặc định. Viewer đọc toàn bộ file, chưa có ACL riêng theo thư mục.
   Ghép Bphone bằng app Node hiện có, đối chiếu endpoint/PIN/Cluster ID/mã một lần;
   Owner duyệt đúng Storage endpoint/PIN/volume và physical failure domain.
   Không tính hai Node trên cùng điện thoại là hai domain.
6. File Manager: upload file thử nhỏ <=32MiB, chờ đủ2replica thật, download so SHA,
   dừng một Node và thử fallback. Xem lịch sử/version, snapshot/restore và JSON
   chẩn đoán trong [DASHBOARD-OPERATIONS.md](DASHBOARD-OPERATIONS.md).
   Kiểm tra writable/fsync từ probe còn mới; UNKNOWN không phải0 hoặc PASS.
   Không Internet vẫn dùng được nếu các máy còn kết nối IP LAN và Controller
   online. Không tự tạo hotspot; không cần Cloudflare/Tailscale cho LAN.

## Rollback chỉ code, bảo toàn dữ liệu MỚI

Dừng ASC foreground như trước. Chọn release trước từ backup-complete.json của
backup bước2, không sửa pointer/database bằng tay. Tạo backup MỚI lúc rollback:

```sh
ASC_OLD_ID="$(python3 -I -c 'import json,sys; from pathlib import Path; print(json.loads((Path(sys.argv[1])/"backup-complete.json").read_text())["release_id"])' "$ASC_BEFORE")"
ASC_ROLLBACK_RUN="$(date -u +%Y%m%dT%H%M%SZ)"
ascdemo rollback "$ASC_OLD_ID" --backup "$ASC_BACKUPS/new-state-rollback-$ASC_ROLLBACK_RUN"
ascdemo verify-backup "$ASC_BACKUPS/new-state-rollback-$ASC_ROLLBACK_RUN"
ascdemo run-controller --dashboard
```

Old043 quay về Lite/code login; optional accounts/history/preferences vẫn giữ để
forward. File/version mới vẫn có trong Catalog và bytes, không restore DB cũ đè
lịch sử mới. Backup MỚI không hợp lệ ->rollback phải dừng. PREPARED upgrade journal
phải dùng đúng `recover-upgrade` theo lỗi thực tế; không xóa journal hoặc init lại.
Quyền Node đã approve/revoke không được hoàn tác bằng rollback source.

## Máy Controller hoàn toàn mới / giới hạn

Chỉ với state/prefix mới do owner chọn, preflight allowed và không có identity
cũ: dùng `sh "$ASC_SRC/scripts/demo-alpha.sh" preflight`, `install --dry-run`,
`install --prefix NEW_PRIVATE_PREFIX`; launcher mới `--state NEW_PRIVATE_STATE
init --role controller --host ACTUAL_PRIVATE_LAN_IP --port 8443 --name ASC-Controller`,
rồi `dashboard-init --port 8444`. Không chạy các lệnh init này trên ZTE đã cài.
Guard M51/unknown-device vẫn bắt buộc. Native Node cài APK5 riêng theo
[ANDROID-NATIVE-PILOT.md](ANDROID-NATIVE-PILOT.md), không import Termux state.

Full Dashboard ở đây là phạm vi quản trị LAN single-writer đã nêu, có giới hạn
Catalog256file/version, 32MiB/browser transfer, 16snapshot/64restore/128intent và
2MiB operator history. Không có per-file ACL/sharing, xóa vật lý/GC, remote shell/
quota/start-stop, automatic failover, production migration, external-DR Android
hoặc writable recovery. Core/quorum/recovery Dashboard giữ READ-ONLY; không đổi
mode bằng copy SQLite. Cloudflare/private gateway hiện file-only, không tự mở
management route; cấu hình/provider/điện thoại/OEM/Doze là nghiệm thu riêng.
