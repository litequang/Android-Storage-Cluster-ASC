# ASC Linux Access 0.1.0 — internal test package

Gói này dành cho host Linux x86_64 có Controller/Dashboard ASC được cấu hình trước.
Không phải APK, bộ cài Termux hay release production. Python3.11+ và OpenSSL có sẵn;
qualification thực chạy trên Linux/Python3.13.5. Không cài package hệ thống, tạo SSH,
VPN, Cloudflare tunnel, Controller/Node hoặc identity backend. Các guards của ASC
vẫn áp dụng; Android/Termux không được hỗ trợ bởi gói này.

Có đủ source ASC, assets, requirements-cloudflare.txt có hash và các hướng dẫn
Phase5 private access/Cloudflare/maintenance. Bootstrap chỉ gọi ba entry point
hiện có: gateway, edge, maintenance. Không có backend/Catalog/Engine thứ hai.
Code nằm trong thư mục phiên bản bất biến; env và profile/TLS state nằm riêng.

## Kiểm tra và giải nén

Lấy đúng archive và SHA-256 từ commit/handoff GitHub đã xác minh. SHA không tự
chứng minh nhà phát hành: đối chiếu nguồn độc lập trước khi chạy bootstrap.
Archive cũ Demo/Android không phải gói này và không được ghi đè.

```sh
sha256sum -c asc-linux-access-0.1.0-internal.tar.gz.sha256
mkdir -m 700 "$HOME/asc-access-packages"
```

Dùng tools/package_access.py từ source checkout đã xác minh để cài lần đầu:

```sh
python3 -I -B tools/package_access.py unpack \
  --archive /path/to/asc-linux-access-0.1.0-internal.tar.gz \
  --sha256 REPLACE_WITH_VERIFIED_ARCHIVE_SHA256 \
  --destination "$HOME/asc-access-packages/0.1.0-internal"
```

Unpack xác minh toàn bộ archive/manifest trước khi tạo thư mục mới, từ chối link,
path traversal, duplicate entry, special file, sai hash hoặc thư mục đã tồn tại.
Không đặt code/env trong profile, volume, backup, recovery staging hay prefix Demo.
Các file được giải nén owner-only; không tự xóa bản cài dở để thử lại.

```sh
ASC_ACCESS_CODE="$HOME/asc-access-packages/0.1.0-internal"
python3 -I -B "$ASC_ACCESS_CODE/access.py" verify
```

## Môi trường riêng

Private gateway chỉ cần Python standard library/OpenSSL; tạo env mới không có pip:

```sh
python3 -I -B "$ASC_ACCESS_CODE/access.py" prepare-env \
  --destination "$HOME/asc-access-packages/env-0.1.0-private"
ASC_ACCESS_PYTHON="$HOME/asc-access-packages/env-0.1.0-private/bin/python"
```

Nếu cần adapter edge, chọn rõ --with-edge và một Python có pip hỗ trợ --python.
Bootstrap dùng venv --without-pip và pip hiện có trỏ vào env mới, require-hashes;
không nâng cấp pip hoặc cài vào Python hệ thống. Có thể dùng wheelhouse đã kiểm
chứng để cài offline; bỏ --wheelhouse mới dùng registry qua proxy/CA hiện có.

```sh
python3 -I -B "$ASC_ACCESS_CODE/access.py" prepare-env \
  --destination "$HOME/asc-access-packages/env-0.1.0-edge" --with-edge \
  --pip-python /path/to/existing/python-with-pip \
  --wheelhouse /path/to/verified/wheels
```

Không tự cài dependency khi chạy dịch vụ. Edge từ chối env chưa được chuẩn bị cho
edge hoặc version dependency không khớp lock. Receipt env gắn release ID và Python
version; không dùng env của phiên bản code khác. Lỗi prepare-env giữ env dở để
review, không fallback sang global packages hoặc bỏ hash verification.

## Khởi chạy

Làm theo PHASE5-PRIVATE-ACCESS.md để tạo profile1 mới owner-only0600 bên ngoài code.
Lấy đúng Dashboard leaf pin độc lập; không dùng Node/admin token. Chỉ init một
profile/TLS root MỚI, không init lại Controller/Node hiện có.

```sh
"$ASC_ACCESS_PYTHON" -I -B "$ASC_ACCESS_CODE/access.py" gateway \
  --root "$HOME/.asc-access-alpha" init --profile "$HOME/asc-access-profile-v1.json"
"$ASC_ACCESS_PYTHON" -I -B "$ASC_ACCESS_CODE/access.py" gateway \
  --root "$HOME/.asc-access-alpha" info
"$ASC_ACCESS_PYTHON" -I -B "$ASC_ACCESS_CODE/access.py" gateway \
  --root "$HOME/.asc-access-alpha" serve
```

Chạy foreground, Ctrl+C dừng đúng gateway đó. Browser cần CA mới được xác minh;
owner login/session/CSRF vẫn do backend quản lý. Mọi thao tác file dùng backend
ASC hiện có. Không public profile1 hoặc mở Node/admin/SSH port.

`edge` và `maintenance` gọi đúng CLI tương ứng, với nguyên guards và các tham số
trong PHASE5-CLOUDFLARE.md/PHASE5-MAINTENANCE.md. Edge yêu cầu env --with-edge và
team/audience/keys thực; render-connector không tự mở tunnel. Maintenance chỉ là
CLI source đã nghiệm thu synthetic, không phải cập nhật APK/Termux hay SSH service.
Gói không kèm cloudflared, credentials, source state, backend hay khóa mặc định.

## Nâng cấp và rollback code

1. Dừng foreground gateway cũ, đợi process thuộc mình thoát; không đoán PID.
2. Backup riêng profile/TLS root vào thư mục private MỚI, owner-only; verify hash
   từng file sau copy. Backup này chứa khóa TLS gateway, tuyệt đối không publish.
   Đây KHÔNG phải backup Controller/Node/data; dùng quy trình backend riêng cho nó.
3. Unpack archive mới vào thư mục phiên bản MỚI, tạo env MỚI; không sửa code cũ.
4. Dùng env/code mới chạy gateway/edge info trên CÙNG profile root. So sánh public
   CA fingerprint và endpoint/mode trước khi serve. Unsupported profile phải từ chối.
5. Start foreground bằng code mới; kiểm tra login, file/replica status và download
   SHA. Không suy luận writable/protected chỉ vì process đang chạy.

Rollback: dừng code mới, dùng lại code/env cũ đã giữ nguyên trên CÙNG profile root.
Không restore DB cũ, copy Node/Cluster identity hay tái tạo TLS identity. Không có
migration profile/Engine schema hoặc auto-update trong gói này. Nếu state thật
không tương thích, giữ nguyên dữ liệu và dừng để review, không ép downgrade.

Archive code và SHA sẽ được công bố chỉ sau targeted install/integration/upgrade/
rollback và secret audit PASS. Bằng chứng đầy đủ ở PHASE5-PROGRESS/ACCEPTANCE trên
GitHub. Full445 Python/64faults trước đó chỉ thuộc source runtime không đổi; tests
đóng gói mới có kết quả riêng, không cộng thành một full suite mới.

Cloudflare/IdP/DNS/public browser, VPN/SSH thật, thiết bị Android/ARM64/LAN độc lập/
Doze/OEM/power/production vẫn chưa nghiệm thu; gói internal này không thay đổi scope.
