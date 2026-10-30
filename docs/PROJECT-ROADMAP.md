# ASC — Roadmap tổng và điểm tiếp tục cho AI

Cập nhật 2026-10-30. Đọc AGENTS.md và chín tài liệu bắt buộc trước, sau đó đọc
tài liệu này để chọn đúng track. Đây là bản tổng hợp hiện tại; các báo cáo nghiệm
thu bên dưới giữ bằng chứng chi tiết và giới hạn theo nền tảng. Không lấy tiêu đề
v0.4/v0.10 hoặc đoạn "future/NOT implemented" trong tài liệu lịch sử làm trạng
thái mới nhất. ASC có phiên bản Core, Controller package và APK khác nhau.

## CURRENT TASK — Dashboard đầy đủ, owner đã cài ZTE OK
Owner yêu cầu triển khai full Dashboard. Cloud phát triển source/synthetic trên
feature/dashboard-full từ PC4336ab7; ZTE runtime/state không bị truy cập hoặc đổi.
[DASHBOARD-PLAN](DASHBOARD-PLAN.md) và [DASHBOARD-PROGRESS](DASHBOARD-PROGRESS.md)
là cursor hiện tại: Node management ->owner login ->File Manager ->history/
snapshot/restore ->settings/diagnostics ->qualification/package. PC install đã OK,
không tiếp tục chẩn đoán lỗi đã giải quyết. Các mục phía dưới giữ evidence/history.

## 1. Dự án đang làm gì?

ASC biến nhiều điện thoại thành cụm lưu trữ: enrollment/identity, các volume được
owner duyệt, Global Catalog, upload/download, replica trên failure domains độc
lập, SHA-256 và fallback. LAN cần đường IP nội bộ, không cần Internet/cloud.
Không tự tạo hotspot/Wi-Fi Direct; không có mạng IP thì không truyền file được.

Tái sử dụng một Registry/Catalog/Storage Engine Python hiện có. Go sidecar phục vụ
Core quorum ở môi trường development được nghiệm thu, không tự bật trên Android.
APK Kotlin cung cấp UI/Binder/Keystore/TLS/service adapter và chạy canonical
Engine/Node, không phải một backend lưu trữ được viết lại bằng Kotlin.

Phân biệt các runtime:

- Controller pilot: single-writer runtime hiện có trong Termux hoặc Linux. APK
  hiện chưa làm Controller. Mất Controller không tự promote Node hoặc cấp ghi mới.
- Native APK: Storage Node, private state/UID riêng, không cần Termux cho Node.
- Dashboard/PWA: UI owner và File Manager dùng backend hiện có. Login bằng mã
  owner một lần ở gói043. Nhánh Dashboard mới bổ sung Owner/Viewer/password;
  chưa có ACL chia sẻ/cô lập theo từng file. Xem DASHBOARD-PROGRESS về source và gói.
- Core quorum observer: chỉ đọc. Leader flag/heartbeat/cache không cấp quyền ghi.
- Phase3D recovery staging: read-only, không được kích hoạt thành writer.
- Phase5 gateway: access plane tùy chọn trước Dashboard, không thêm Engine/authority.

## 2. Toàn bộ lộ trình và trạng thái

| Giai đoạn | Kết quả hiện có | Phạm vi và tài liệu |
| --- | --- | --- |
| Phase0 / Phase1.1 | Device profiling, identity, registry, one-use enrollment, credential lifecycle | Nền móng development; lịch sử trong [implementation plan](IMPLEMENTATION_PLAN.md) |
| Phase1.2A | Local volumes/identity, streaming immutable objects, SHA/recovery | Windows development; [acceptance](PHASE1-2A-ACCEPTANCE.md) |
| Phase1.2B | Global Catalog, jobs/retry/reconciliation, placement, replica/download fallback | Windows simulated nodes; [acceptance](PHASE1-2B-ACCEPTANCE.md) |
| Phase2A | Go metadata consensus, durable receipts/snapshot/replay, mTLS/quorum reads | Windows development; [acceptance](PHASE2A-ACCEPTANCE.md) |
| Phase2B | Fenced Controller/storage failover và fault gates | Windows development; [acceptance](PHASE2B-ACCEPTANCE.md). Không Android failover |
| Phase3A | Backup, Versioning & Safe Restore | DONE trong Windows development; [acceptance](PHASE3A-ACCEPTANCE.md) |
| Phase3B | Node Scoring, Telemetry/history, Preferences & Smart Placement | DONE Linux synthetic; [plan](PHASE3B-PLAN.md), [progress](PHASE3B-PROGRESS.md), [acceptance](PHASE3B-ACCEPTANCE.md) |
| Phase3C | Dynamic Replication, Reduction, Safe GC planner/executor guards | DONE Linux synthetic; [plan](PHASE3C-PLAN.md), [progress](PHASE3C-PROGRESS.md), [acceptance](PHASE3C-ACCEPTANCE.md). Physical GC khóa trong runtime thường/điện thoại |
| Phase3D | External metadata+bytes backup, anchored verify, isolated recovery staging | PARTIAL: Linux backup/verify/read-only staging accepted, writable DR BLOCKED; [plan](PHASE3D-PLAN.md), [progress](PHASE3D-PROGRESS.md), [acceptance](PHASE3D-ACCEPTANCE.md), [operations](PHASE3D-OPERATIONS.md) |
| Demo track DEMO.0–4d | Termux QuickStart, single writer/LAN/TLS, two replicas, upgrade contract, Dashboard Lite, Android-like storage fix | Riêng track, Demo0.4.1 Linux synthetic accepted; [plan](DEMO-TRACK-PLAN.md), [progress](DEMO-TRACK-PROGRESS.md), [acceptance](DEMO4D-ACCEPTANCE.md). Không whole-branch merge vào Core |
| Phase4.0 | Selective Core/Demo integration, existing Dashboard/Quick Join reuse | Linux foundation accepted; [plan](PHASE4-PLAN.md), [progress](PHASE4-PROGRESS.md), [acceptance](PHASE4-ACCEPTANCE.md) |
| Phase4.1 | Local Engine Bridge, owned lifecycle contract, Core quorum read-only UI adapter | Linux foundation accepted; [plan](PHASE4-1-PLAN.md), [progress](PHASE4-1-PROGRESS.md), [acceptance](PHASE4-1-ACCEPTANCE.md) |
| Phase4.2 | Native app/Binder/Keystore, real Engine I/O, enrollment/TLS, Storage Agent/FGS, observer, browser File Manager integration | Native Node chạy thật trên API30/35 x86_64 emulator. Overall Phase4/4.2 chưa ACCEPTED trên phone/ARM64/LAN/OEM; [plan](PHASE4-2-PLAN.md), [progress](PHASE4-2-PROGRESS.md), [acceptance](PHASE4-2-ACCEPTANCE.md), [status](PHASE4-STATUS.md), [handoff](PHASE4-HANDOFF.md) |
| Phase5 | Private gateway, Cloudflare Access source adapter, stopped local maintenance, Linux distribution và operator checker | Linux software subset accepted; full Phase5/production PARTIAL. VPN/Cloudflare/IdP/DNS/SSH live chưa nghiệm thu; [plan](PHASE5-PLAN.md), [progress](PHASE5-PROGRESS.md), [acceptance](PHASE5-ACCEPTANCE.md) |

Không cộng số tests của nhiều checkpoint thành một fresh full-suite run. Latest
Phase5 full Linux445PASS/64faults +Go/vet/modules/builds được ghi trong acceptance;
5.4e10new +28existing targeted PASS là lượt riêng. API30/35 emulator không phải
ARM64 phone; Android/Windows cross-build không phải runtime PASS. Bằng chứng Core
không có nghĩa mọi tính năng đó đều được bật hoặc có UI trong APK/Demo pilot.

## 3. Branch, code và bộ cài nên dùng

Source Dashboard hiện tại: **feature/dashboard-full**, từ PC4336ab7 sau
feature/phase5-remote-access, kế thừa Phase4
qua lịch sử tích hợp có kiểm soát. Base trước handoff này:
c2c7f531f24c73938084f5cc72b8f0838fbfe1b6. Fetch HEAD mới nhất gồm tài liệu này.
Core/Demo/Phase4 gốc giữ nguyên, không dùng main làm baseline hoặc merge cả nhánh.

| Artifact | Dành cho | Tài liệu/đường dẫn |
| --- | --- | --- |
| Controller0.4.3 core-decode internal source | Controller single-writer + Dashboard/PWA, có đường tích hợp Native Node | [PHASE4-HANDOFF](PHASE4-HANDOFF.md), [exact package](../candidates/asc-demo-alpha-0.4.3-core-decode-internal-source.tar.gz) |
| Node APK5 /0.4.1-native-node-candidate | Storage Node native; NativeTLS API30+ | [exact APK](../android-artifacts/asc-native-node-0.4.1-internal-debug.apk), [pilot](ANDROID-NATIVE-PILOT.md) |
| Linux Access0.1.0 internal | Gateway/edge/maintenance trên Linux x86_64; không phải installer Controller/Android | [package guide](PHASE5-LINUX-PACKAGE.md), [archive](../candidates/asc-linux-access-0.1.0-internal.tar.gz) |
| Demo0.4.1 cũ | Demo track/đường nâng cấp cũ đã kiểm; không phải chọn mặc định mới cho APK5 | [Demo acceptance](DEMO4D-ACCEPTANCE.md), [QuickStart lịch sử](DEMO-QUICKSTART.md) |

Hashes, immutable artifact commit và download links cho lượt ZTE ở
[PC handoff](ZTE-FRESH-INSTALL-PC-HANDOFF.md). Code/docs/packages đã được lưu GitHub;
private signing key/credentials/test state/AVDs/toolchains/raw logs không công bố.
Đừng tự rebuild APK với signer khác và hứa nâng cấp giữ state. Không chỉnh archive
đã phát hành; bản sửa mới cần version/manifest/checksum và nghiệm thu riêng.

## 4. ĐIỂM TIẾP TỤC NGAY — Controller ZTE đã cài mới, còn browser/Node

PC đã truy cập đúng ZTE9045/API30 qua SSH LAN owner cung cấp ngày2026-10-30.
Inspect thực tế thấy Demo0.3.0 và state Controller/Node đã tồn tại, trái với giả
định trống của handoff trước. Hai archive043 trên máy đều đúng SHA công bố.
Lệnh install043 vào prefix đang chọn03 tái hiện exit3; canonical installer báo
`different active release; explicit stopped upgrade required`. Dependency đầy đủ.

Owner sau khi được báo hiện trạng đã yêu cầu cài đè, không cần giữ dữ liệu cũ.
PC giữ nguyên hai thư mục cũ bằng rename, rồi chạy luồng cài MỚI043 ở đường dẫn
chuẩn, tạo Cluster/identity mới theo yêu cầu; không chạy hướng dẫn upgrade03,
không xóa khóa, không đổi archive/guard/source. Controller +Dashboard đã khởi tạo
và chạy foreground qua cửa sổ SSH PC.14kiểm tra TLS/pin/owner HTTP/session/CSRF
đạt trên thiết bị thật; controlled restart giữ cả9file identity/config/TLS,14HTTP
checks lại đạt. Không phải browser tương tác hay nghiệm thu Native Node.
Chi tiết/lệnh/remaining gates: [handoff cập nhật](ZTE-FRESH-INSTALL-PC-HANDOFF.md)
và [receipt](../qualification/zte-controller-fresh-install-20261030.json).

NEXT: owner trust public Dashboard CA và login bằng browser thật; sau đó ghép
Native Node/two-phone domains và kiểm replicas/SHA/fallback/Controller loss.
Cụm mới hiện0paired Storage Nodes/0files; chưa bảo vệ file hay hoàn thành Phase4.

### Lịch sử handoff2026-10-29 — superseded by actual PC inspection above

Owner xác nhận ZTE chỉ có Termux, chưa cài ASC trước lần thử. Không dùng lịch sử
"ZTE đã có Demo0.3/volume" để bắt làm upgrade. Hiện owner báo cài Controller lỗi,
nhưng chưa gửi command/output; root cause và phiên bản thực chạy UNKNOWN. Sau
thử lỗi có thể tồn tại partial state/keys: kiểm tra, không mặc định vẫn trống.

Owner chuyển sang Codex ở PC để lấy bộ cài và hỗ trợ cài/sửa trên ZTE thử nghiệm.
Cloud không truy cập phone. [PC handoff](ZTE-FRESH-INSTALL-PC-HANDOFF.md) là task
hiện tại và thứ tự tiếp tục:

1. Fetch/inspect repo và đúng ZTE owner chọn; thu đúng command/error đã làm sạch,
   model/Android/SDK/Termux/Python/OpenSSL, package checksum và trạng thái partial.
2. Phân biệt dependency/preflight/install/init/run/TLS, tái hiện rồi sửa đúng lớp.
   Dependency CLI Termux dùng openssl-tool; không đoán đó là nguyên nhân khi chưa
   có lỗi. Không mở public SSH, reset state, gỡ app hoặc bỏ guard/TLS để vượt lỗi.
3. Có Controller chạy foreground, Dashboard HTTPS tin đúng public CA và owner
   login. Đây chưa đủ bảo vệ file nếu chưa có hai Storage Nodes được duyệt.
4. Cài/ghép Native Node trên máy phù hợp API30+, đo private volume/write/fsync,
   duyệt Node/volume/domain bằng owner CLI. ZTE +Bphone phải là hai thiết bị thật;
   kiểm Bphone SDK trước khi chọn Native. Termux và APK trên ZTE cùng một domain.
5. Upload nhỏ, hai replicas, download SHA, stopped-node fallback, restart giữ
   identity và Controller-loss refusal; thử mất Internet nhưng giữ Wi-Fi/IP.
   Ghi kết quả phone thật; không điền PASS bằng bằng chứng emulator cũ.

Tại handoff2026-10-29 lỗi còn UNDIAGNOSED; kết quả PC mới nhất nằm ở đầu mục4.

## 5. Backlog còn lại sau mốc cài LAN đầu tiên

- **Phase4 thực địa:** ARM64/ZTE/Bphone/phone LAN/two hardware domains, Chrome
  Android/PWA/CA UX, FGS notification/Stop/background/Doze/OEM/network changes,
  process death/update/custody và durability/power/media faults có kiểm soát.
  Owner từng hoãn để tổng nghiệm thu sau; chưa chạy không đồng nghĩa PASS.
- **App UX mở rộng:** hiện File Manager dùng web chung; native file picker,
  nhiều user/ACL/sharing, SAF/SD/USB và QR/app UX hoàn chỉnh cần checkpoint/contract
  riêng. Không coi PWA có quyền chạy Termux, ghi private key hay điều khiển FS.
- **Upgrade/migration:** giữ code tách state, Node/Cluster/Volume/keys. Chỉ công bố
  đường upgrade được exact-archive test; Termux→APK, APK Controller và
  single-writer→Raft chưa có migration được nghiệm thu.
- **Phase5 live connectivity:** chọn host Linux/endpoint và phương án private
  VPN hoặc Cloudflare/IdP/DNS owner quản lý; verify provider/owner authorization,
  HTTPS/CA/pin, file bytes và outage thực tế. [Checker](PHASE5-ACCESS-CHECK.md)
  chỉ chuẩn bị/chẩn đoán, không tự deploy hoặc chứng minh remote reachability.
- **Maintenance thật:** stopped backup/verify/stage/preflight/apply có source CLI;
  private remote access/SSH/host-key/ACL và từng loại Android update chưa có live
  acceptance. Không có public shell, auto-update hoặc remote repair mọi Node.
- **Production qualification:** chỉ sau evidence device/independent copies/
  restore/upgrade/fault/operations phù hợp và review phạm vi. Chưa production-ready.
- **Writable disaster recovery:** blocker độc lập của Phase3D; cần recovery
  authority/fencing/identity được chứng minh bằng cơ chế hỗ trợ. Không tự tạo
  epoch/quorum/Leader hoặc biến staging/backup cũ thành writer để đóng roadmap.

Không bật Android voters/Raft/automatic failover/physical GC theo backlog này.
Giữ các invariant/version/snapshot/backup/jobs/last readable copy và UNKNOWN.

## 6. Hợp đồng bàn giao cho phiên AI kế tiếp

AGENTS +roadmap tổng +progress của track +handoff task phải đủ để tiếp tục mà
không cần prompt chat. Trước sửa inspect branch/status/staged/untracked và remote;
bảo toàn dirty work. Với lỗi ZTE nên tạo nhánh fix riêng từ source mới nhất.
Sau checkpoint: targeted PASS hoặc blocker thật, cập nhật progress/CODEMAP/docs,
review tracked/staged/untracked secrets, commit, push thường, fetch và so remote
HEAD. Giữ original branches/archives/signer; không force/reset/clean/whole merge.

Khi bàn giao, ghi CURRENT TASK, qualified source/artifact, actual evidence/platform,
pending/blocker và NEXT action trong GitHub. Nếu sửa runtime, chạy regression/fault
phù hợp; không lặp full445 khi chỉ cập nhật docs hoặc source đã qualified không
đổi. Không để tình trạng thật chỉ nằm trong chat hoặc đánh dấu hoàn thành phần
chưa chạy. Roadmap này là cursor tổng; acceptance/progress riêng là bằng chứng.


Dashboard update:Node management1 and Owner/Viewer accounts2 published on
feature/dashboard-full (efe0ec4,cef9ce1). File Manager3 source now qualified
70distinct related cases; see DASHBOARD-PROGRESS for publication evidence and
remaining4snapshot/restore,5diagnostics,6upgrade/package/final gates. ZTE continues
original043Lite until owner explicitly applies a newly qualified package.
