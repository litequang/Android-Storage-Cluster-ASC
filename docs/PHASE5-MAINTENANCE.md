# Phase5.3 — Bảo trì có kiểm soát qua kết nối riêng

Phạm vi đã phát triển: CLI chạy tại host của operator, cho Demo single-writer,
Linux synthetic. Không có máy chủ quản trị mới, remote shell API, SSH daemon hay
background updater. Chưa nghiệm thu SSH/VPN thật, Termux, APK hoặc production.
Không chạy các lệnh này trên điện thoại/M51 từ Codex Cloud.

## Đường kết nối và phân quyền

| Mục đích | Cơ chế | Giới hạn |
|---|---|---|
| Quản lý file | Dashboard HTTPS, owner session/CSRF | Không có shell/cập nhật code |
| Truy cập từ xa bằng browser | Adapter Access + owner session | Cloudflare thật chưa triển khai/nghiệm thu |
| Bảo trì host | Operator dùng SSH chuẩn qua mạng riêng/VPN đã duyệt | Chưa cấu hình hay thực chạy SSH trong checkpoint này |
| Bảo trì Android native | Cập nhật APK cùng signer theo contract riêng | CLI này không quản lý APK/Keystore/Termux |
| Core quorum/recovery | Runbook riêng, chưa hỗ trợ CLI này | Không đổi voter, không cấp recovery writer |

SSH tương lai phải giới hạn vào endpoint/mạng riêng, dùng tài khoản và khóa riêng
của operator, xác minh host key độc lập và ACL phù hợp. VPN không thay xác thực.
Không public SSH, không password dùng chung, không đưa shell vào Dashboard hay
Cloudflare file gateway. Không tự cài sshd, mở cổng, thay firewall hoặc Termux:Boot.
Việc triển khai kết nối thật cần task riêng; không suy ra remote access PASS từ CLI.

## Contract của CLI

Chạy từ source checkout đã xác minh, với Python phù hợp. Entry point:
`python -m asc.access.maintenance --state PRIVATE_STATE --prefix PRIVATE_CODE ...`.
Archive/APK đã công bố trước Phase5 không chứa entry point mới này; chưa phát hành
package mới. Demo device/dependency guards hiện có vẫn áp dụng. Module mới còn từ
chối Android/Termux và nền tảng chưa nghiệm thu; không có flag bypass. Fixture Linux
dùng đúng context thiết bị giả lập vốn có của test Demo, không chứng minh điện thoại.

`preflight` chỉ dùng state/prefix ĐÃ KHỞI TẠO, release ĐÃ STAGE và backup ĐÃ TẠO:

- Giữ stopped/install locks hiện có; kiểm tra state/binding/journal/schema/release.
- Verify toàn bộ backup và so với state/volume hiện tại, không chỉ kiểm tra chỗ trống.
- Trả plan format1 với action, installation/role, current/target release, backup
  SHA-256, state formats và plan SHA-256. Không có token, PIN, khóa hoặc command.
- Không tạo identity, backup, release, listener hoặc runtime.

Plan SHA là xác nhận nội dung, KHÔNG phải chữ ký, quyền SSH hay quyền writer.
Operator vẫn phải xác minh nguồn archive/checksum từ nguồn độc lập trước khi stage.
Manifest tự khớp hash không tự chứng minh nhà phát hành đáng tin cậy.

`apply` yêu cầu private plan file và xác nhận SHA rõ ràng. Nó chạy lại preflight,
rồi gọi đúng `asc.demo.upgrade.activate` hiện có với precondition bổ sung: kiểm tra
lại installation/current release và backup/state dưới CÙNG locks với activation.
Không có khoảng trống check-then-act được coi là an toàn. Nếu state/backup thay
đổi, dừng trước khi tạo activation backup hoặc đổi code pointer.

Activation vẫn tạo một backup MỚI, có readback/hash, rồi dùng journal format1 và
atomic code pointer vốn có. Không đổi database schema, không khôi phục DB, không
chạy shell hay tự khởi động dịch vụ. Luồng upgrade cũ không truyền precondition vẫn
giữ hành vi cũ. Đây không phải migration single-writer→Raft hoặc Termux→APK.

## Quy trình operator cho môi trường synthetic đã được phê duyệt

Trước hết dừng các foreground gateway/bridge/Controller/Node thuộc installation
theo cách thông thường; chờ các process do mình sở hữu thoát. Không kill PID đoán
mò. Nâng cấp có downtime, không hứa rolling-write availability. Làm từng host với
state/Node ID/volume/certificate riêng; không copy state từ host khác.

Trong terminal riêng tại host đã duyệt, từ checkout chứa module mới, đặt đúng các
đường dẫn đang có. Các placeholder bên dưới phải được thay bằng giá trị đã kiểm tra:

```sh
ASC_MAINT_PYTHON=/path/to/qualified/python
ASC_MAINT_STATE="$HOME/.asc-demo"
ASC_MAINT_PREFIX="$HOME/.local/share/asc-demo"
ASC_MAINT_RUN="$ASC_MAINT_PREFIX/bin/asc-demo"
ASC_MAINT_TARGET_SOURCE=/path/to/verified/extracted/source
ASC_MAINT_BACKUP="$HOME/asc-maint-preflight-unique"
ASC_MAINT_ACTIVATION="$HOME/asc-maint-activation-unique"
ASC_MAINT_PLAN="$HOME/asc-maint-plan-unique.json"

# Dùng launcher CŨ. Không chạy install/init/join/storage-init lại.
sh "$ASC_MAINT_RUN" --state "$ASC_MAINT_STATE" backup "$ASC_MAINT_BACKUP"
sh "$ASC_MAINT_RUN" --state "$ASC_MAINT_STATE" verify-backup "$ASC_MAINT_BACKUP"
sh "$ASC_MAINT_RUN" --state "$ASC_MAINT_STATE" stage "$ASC_MAINT_TARGET_SOURCE"
# Lấy đúng release_id từ stage; ghi lại release_id cũ để rollback.
ASC_MAINT_TARGET=REPLACE_WITH_VERIFIED_64_LOWERCASE_RELEASE_ID
sh "$ASC_MAINT_RUN" --state "$ASC_MAINT_STATE" upgrade-preflight "$ASC_MAINT_TARGET"

# Noclobber: không ghi đè plan cũ. Chỉ đi tiếp khi lệnh trả về thành công.
(umask 077; set -C; "$ASC_MAINT_PYTHON" -m asc.access.maintenance \
  --state "$ASC_MAINT_STATE" --prefix "$ASC_MAINT_PREFIX" preflight \
  --target "$ASC_MAINT_TARGET" --backup "$ASC_MAINT_BACKUP" > "$ASC_MAINT_PLAN")
```

Xem lại plan và đối chiếu installation/current/target/backup. Lấy `plan_sha256`
từ plan đã xem vào `ASC_MAINT_CONFIRM`; không dùng digest của một plan khác.

```sh
ASC_MAINT_CONFIRM=REPLACE_WITH_REVIEWED_PLAN_SHA256
"$ASC_MAINT_PYTHON" -m asc.access.maintenance \
  --state "$ASC_MAINT_STATE" --prefix "$ASC_MAINT_PREFIX" apply \
  --plan "$ASC_MAINT_PLAN" --confirm-plan "$ASC_MAINT_CONFIRM" \
  --backup "$ASC_MAINT_BACKUP" --new-backup "$ASC_MAINT_ACTIVATION"
sh "$ASC_MAINT_RUN" --state "$ASC_MAINT_STATE" verify-backup "$ASC_MAINT_ACTIVATION"
```

Nếu `maintenance_refused`, giữ state/plan/backups/journal và kiểm tra nguyên nhân;
không xóa file, sửa journal hay tạo lại identity để lệnh chạy. Plan cũ sau khi state
đổi phải bị từ chối; tạo backup và preflight mới sau khi xác minh installation.
Không publish plan private, backup hay config thô trong bug report.

Sau khi hoàn tất từng host, khởi chạy Controller rồi Node bằng lệnh trước đây,
kiểm tra identity, TLS pin, storage read/write/fsync, node online và replica thực.
Download file cũ và file mới bằng luồng hiện có, đối chiếu SHA-256. Process đang
chạy không đủ để kết luận volume writable hoặc file có đủ replica.

## Mất ACK, gián đoạn và rollback

Nếu mất phản hồi sau thành công, chạy lại đúng `apply` với cùng plan/confirmation/
new-backup. Chỉ trả `already_applied:true` khi current pointer, journal COMPLETED,
old/new release/action/installation và backup SHA thực khớp; verify lại backup bytes
và release. Không activate lần hai, không tạo backup mới, không restore state.
Đây là chứng cứ thao tác local đã hoàn tất, không phải chứng cứ SSH/network được
nghiệm thu hoặc bảo đảm lịch sử writer/authority ngoài scope Demo.

Journal PREPARED không được coi là thành công. Runtime/retry vẫn bị khóa. Dùng
`recover-upgrade` vốn có sau kiểm tra stopped state và backup; nó chỉ chọn code cũ,
không restore DB. Nếu state khác backup, recovery phải từ chối để operator review.

Rollback bình thường: dừng runtime, tạo và verify backup MỚI của state hiện tại
(bao gồm file vừa ghi sau upgrade), tạo plan mới với `--action rollback --target`
là release cũ tương thích, rồi `apply` với một activation-backup mới khác. Không
chép backup cũ đè SQLite, volume hay credentials. Khởi động lại và kiểm tra cả file
trước/sau upgrade. Không dùng rollback code để vượt schema/identity incompatibility.

## Bằng chứng và phần còn thiếu

Test dùng Controller và hai Storage Node TLS thật trên Linux cùng host, installed
launchers, I/O/hash thật, logical failure domains. Kiểm tra plan/confirmation, CAS,
backup corruption/state change, lost local ACK retry, activation interruption và
recovery, giữ identity và file sau NEW-state code rollback. Các test upgrade cũ và
đường archive chính xác0.4.2→current source vẫn phải PASS.

Chưa nghiệm thu remote SSH/VPN, Termux runtime, cập nhật APK qua CLI, nhiều host
thật, power loss, OEM/Doze hoặc production. Không mở khóa GC/Raft/failover/writable
disaster recovery. Kết quả/commit chính xác nằm trong PHASE5-PROGRESS/ACCEPTANCE.

Pre-lock guard đã bổ sung ở5.3b: từ chối thư mục chưa đăng ký, recovery marker và
prefix chưa gắn state trước khi tạo file lock; sau đó vẫn kiểm tra lại dưới locks.
Bằng chứng cuối:8maintenance +6upgrade/tương thích PASS trong Linux synthetic.
