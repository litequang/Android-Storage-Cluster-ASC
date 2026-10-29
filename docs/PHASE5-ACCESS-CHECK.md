# Kiểm tra Access trước khi triển khai — source checkpoint 5.4e

Công cụ chạy cục bộ trên host Linux thử nghiệm, dùng profile gateway đã tồn tại.
Không cài dịch vụ, tạo profile/identity, mở listener, đăng nhập, tạo mã owner hay
chạy SSH/tunnel. Không phải Android/Termux installer. Không sửa state/backend/mạng.

## Chạy từ source đã xác minh

Dùng checkout feature/phase5-remote-access có tools/check_access.py.
Private profile1 dùng Python3.11+ và OpenSSL có sẵn. Edge profile2 cần môi trường
riêng với dependencies đúng requirements-cloudflare.txt; công cụ không tự cài.

```sh
# Offline: profile, private paths/quyền, CA/IP SAN và certificate/key hiện có.
python3 -I -B tools/check_access.py --root "$HOME/.asc-access-alpha"

# Probe backend đã cấu hình, chỉ khi owner được phép kết nối tới endpoint đó.
python3 -I -B tools/check_access.py --root "$HOME/.asc-access-alpha" --probe-upstream

# Sau khi tự khởi chạy gateway: kiểm tra cả backend và listener.
python3 -I -B tools/check_access.py --root "$HOME/.asc-access-alpha" \
  --probe-upstream --probe-listener
```

Edge: dùng Python của private edge environment và root edge hiện có. Chỉ probe
loopback đã cấu hình, không gọi public hostname/issuer; không cần JWT/token/khóa
trên command line. Mặc định không kết nối mạng và không tạo lock/journal/file.
Công cụ **source-only**, chưa nằm trong archive Linux Access0.1.0. Không chép vào
bundle bất biến hoặc sửa manifest/archive/checksum cũ. Không có release/APK mới.

## Đọc kết quả

JSON format1 stdout; exit0 khi các check đã chạy đạt, exit1 khi BLOCKED, exit2 khi
command sai. Không phản chiếu raw exception, private path, profile/pin hay response.

| Check | Bằng chứng |
| --- | --- |
| profile | Loader hiện có chấp nhận profile1/2, private path/quyền, CA/IP SAN |
| tls_identity | Certificate và private leaf key khớp, không tạo mới |
| upstream_mode | Khi yêu cầu: pinned HTTPS GET /api/mode khớp mode/read_only |
| listener_mode | Private: CA + hostname + đúng leaf, GET mode khớp |
| anonymous_gate | Private: GET state không cookie bị401 login_required; edge: không assertion bị403 edge_access_denied |

NOT_REQUESTED nghĩa là chưa probe. Edge listener_mode luôn UNKNOWN vì không vượt
Access để đọc mode. anonymous_gate VERIFIED chỉ chứng minh request ẩn danh đó bị
chặn, không chứng minh owner login/JWKS/IdP/provider policy. Các check độc lập;
một bên đạt không bù cho bên khác lỗi.

CHECKS_PASSED chỉ là kết quả những check đã chạy tại thời điểm chạy. Offline vẫn
có thể trả CHECKS_PASSED dù chưa có dịch vụ. Không phải deployment approval/sức
khỏe toàn cụm: writer_authority luôn false; quorum_status/remote_reachability/
vpn_membership UNKNOWN; authenticated_access NOT_TESTED;
live_deployment_accepted false. Mode/Leader/heartbeat không cấp writer authority.

Sai mode/pin/TLS/quyền/missing state/offline trả BLOCKED, không tái tạo certificate,
thử endpoint khác, khởi chạy recovery staging hoặc bỏ TLS. Probes chỉ GET cố định,
không redirect, socket timeout6s; listener response tối đa8KiB/framing rõ ràng.
Upstream dùng client hiện có/tối đa2MiB. Không cam kết tổng thời gian6s: OpenSSL
loader có timeout riêng30s. GET ẩn danh có thể tiêu thụ rate-limit; tránh chạy dồn.

## Bằng chứng, bước tiếp và rollback

tests/test_access_check.py dùng TLS/I/O loopback thật với Controller/Dashboard và
hai Storage Nodes fixture hiện có. Edge dùng local HTTPS JWKS/real RS256 của test
cũ; checker không gọi issuer/lấy token. Negative TLS fixture cố tình trả sai
boolean mode và cho đọc anonymous, để chứng minh checker từ chối.

Linux synthetic không chứng minh VPN/Cloudflare public DNS/IdP/SSH/điện thoại thật.
Live acceptance cần owner cung cấp host Linux thử nghiệm, lựa chọn private VPN
hoặc Cloudflare, hostname/endpoint và cấu hình quyền đã review. Không gửi secrets.
Không thay account/DNS/tunnel trong checkpoint này; phone acceptance vẫn hoãn.

Rollback: ngừng dùng checker. Không có state/journal/schema mới, không restore DB
cũ. Gateway0.1.0, Node/Cluster/Volume identity và signer/AVD đều giữ nguyên.
