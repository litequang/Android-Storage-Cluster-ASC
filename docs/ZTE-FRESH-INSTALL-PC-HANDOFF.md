# Bàn giao Codex PC — cài mới Controller trên ZTE và xử lý lỗi

## LATEST 2026-10-30 — PC chẩn đoán và cài mới thực tế

Đọc mục này trước các thông tin2026-10-29 bên dưới. Source PC bắt đầu từ fetched/
advertised feature/phase5-remote-access ca002dbcb1dfc7edbafe42c0630db1ee5126a24b.
Checkpoint riêng fix/zte-controller-fresh-install; không sửa runtime/archive/APK.

- Owner cung cấp SSH LAN của ZTE rồi bật sshd và thêm public key PC. Chỉ đúng
  ZTE9045/Android11/API30/aarch64, Termux0.118.3, Python3.14.8/OpenSSL3.6.5.
  Không USB/ADB/root/public SSH/M51. Khóa SSH PC nằm ngoài repo.
- Inspect thực tế thấy default prefix đã chọn Demo0.3.0-alpha/release ab229efb...
  và state có Controller/Node/volume,2registry nodes/0files/0jobs; runtime đều dừng.
  Đây là evidence thực tế mới, supersedes giả định fresh/partial UNKNOWN cũ.
  Không thu full private DB/config/history/logcat; chỉ field allowlist và diagnose.
- Hai thư mục asc-controller.* có archive043 đúng248278bytes/SHA6a60bd41...
  Preflight allowed=true, không thiếu dependency. Install043 vào default prefix
  tái hiện CLI exit3/generic refusal. Canonical install() giữ nguyên checks và báo
  `different active release; explicit stopped upgrade required` trước chọn code
  mới. Lệnh gây lỗi ban đầu của owner vẫn chưa được cung cấp; đây là reproducer
  PC thật cho cùng luồng cài, không suy đoán lỗi Python/OpenSSL hay package hỏng.
- Sau khi được báo existing state, owner yêu cầu: “cài đè đi, không cần quan tâm
  dữ liệu cũ”. PC giữ cả hai thư mục dưới tên mới, kiểm OS locks dừng trước rename:
  `~/.local/share/asc-demo.before-fresh-20261030-6f2cfea9` và
  `~/.asc-demo.before-fresh-20261030-6f2cfea9`. Không delete/ghi đè key/DB hoặc chạy
  upgrade03. Đây là giữ nguyên thư mục, không phải complete verified backup hay
  migration/khả năng chạy code cũ tại đường dẫn mới.
- Sau đó canonical dry-run/install/init controller/dashboard-init/dashboard-trust
  đều exit0 với exact release b423c5d8... ở prefix/state chuẩn. **Cluster và keys
  mới**, identity cũ không được adopt. Chỉ public Dashboard CA được đưa về PC;
  private key/token vẫn trên ZTE. Source/version/immutable archives giữ nguyên.
- Controller chạy foreground trong cửa sổ PC “ASC ZTE Controller” qua SSH -tt.
  Đóng/đứt session có thể dừng runtime; không tạo daemon/Boot/service. Nếu dừng,
  owner chạy lệnh foreground dưới đây trong Termux, không init lại.
- 14 kiểm tra HTTP/TLS thực từ PC vào ZTE đạt: trusted CA+IP SAN, untrusted CA denied,
  Controller correct pin+Cluster ID/wrong pin denied, HTML/mode, anonymous401,
  owner login, cookie flags, one-use denial, authenticated state, wrong-CSRF401,
  cross-Origin403, logout revocation. Không thay trust store hệ thống hoặc bỏ TLS.
  Browser tương tác/PWA/CA UX, native Node/replicas chưa thử; hiện0paired Nodes.
- Controlled SIGINT chỉ gửi sau khi xác minh exact owned Controller argv/UID/
  process-start; diagnose xác nhận dừng. Khởi động lại foreground cùng launcher:
  Controller running=true và cả9file identity/config/TLS giữ SHA giống trước dừng.
  14 HTTP checks lại PASS sau restart, 0 paired Nodes/0files. Không phải power-cut,
  Node/process-death/durability hoặc hoàn thành physical acceptance.

Lệnh trên máy (ASC_UNPACK là source043 đã verify, không phải gói03/Access):

```sh
cd "$ASC_UNPACK/asc-demo-alpha"
sh scripts/demo-alpha.sh preflight
sh scripts/demo-alpha.sh install --dry-run
sh scripts/demo-alpha.sh install
ASC_RUN="$HOME/.local/share/asc-demo/bin/asc-demo"
# Các lệnh init dưới đây ĐÃ chạy: không lặp để tạo identity khác.
sh "$ASC_RUN" init --role controller --host ACTUAL_ZTE_LAN_IP --name ASC-ZTE
sh "$ASC_RUN" dashboard-init --port 8444
sh "$ASC_RUN" dashboard-trust --out NEW_PUBLIC_CA_FILE
sh "$ASC_RUN" diagnose
# Resume khi runtime đã dừng, dùng cùng state/keys hiện tại:
sh "$ASC_RUN" run-controller --dashboard
# Terminal Termux riêng, owner tự lấy code; không lưu/publish code:
sh "$ASC_RUN" dashboard-code
```

PC public CA: private/zte-dashboard-ca-20261030.crt (ignored, chỉ public cert).
Đối chiếu fingerprint với dashboard-trust trước owner trust browser; không bỏ lỗi
certificate. Receipt public: qualification/zte-controller-fresh-install-20261030.json.
Không publish runtime Cluster/pin/CA, SSH private key, credentials hay state.

NEXT: owner browser trust/login thực, rồi APK5 Node và phone thứ hai/2domains,
volume writable/fsync/replicas/SHA/fallback/restart/Controller-loss/LAN-no-Internet.
Không khởi tạo lại Controller mới đã chạy. Không gán phone-wide/production PASS
cho14HTTP checks; GC/Android voters/failover/writableDR vẫn khóa.

## Lịch sử owner handoff2026-10-29 (trước actual PC inspection)

- ZTE chỉ mới cài Termux, CHƯA cài ASC trước lần thử vừa rồi. Những mô tả cũ về
  ZTE đã chạy Demo0.3/đã có volume không còn là baseline cho lượt này.
- Owner vừa báo cài Controller bị lỗi. Chưa có dòng lệnh, bước lỗi, traceback hoặc
  phiên bản thực sự đã chạy. Root cause UNKNOWN, chưa tái hiện hoặc sửa lỗi này.
- Hướng dẫn gần nhất chọn Controller0.4.3 bên dưới, nhưng chưa chứng minh owner
  đã chạy đến gói này. Không tự quy kết lỗi cho phiên bản hoặc dependency cụ thể.
- Sau lần cài lỗi có thể đã có partial code/state/identity: tình trạng hiện tại
  UNKNOWN. Kiểm tra trước khi retry; không xóa state hoặc init lại để né lỗi.
- Owner muốn Codex trên PC lấy bộ cài và hỗ trợ cài/sửa trên ZTE thử nghiệm do
  owner kiểm soát. Phiên Cloud này vẫn source-only, không truy cập điện thoại.
  Không có quyền với M51/production/điện thoại khác từ handoff này.

## Source đúng và tài liệu cần đọc

Repository: https://github.com/litequang/Android-Storage-Cluster-ASC

Nhánh source mới nhất: feature/phase5-remote-access. HEAD trước handoff:
c2c7f531f24c73938084f5cc72b8f0838fbfe1b6; đã fetch/advertised remote khớp và tree
sạch. Fetch HEAD mới nhất bao gồm tài liệu này, không reset hoặc ghi đè dirty tree.
Không dùng main hoặc merge toàn bộ Core/Demo/Phase4. Nhánh Phase4 gốc giữ0877a15.

Đọc AGENTS.md và CODEMAP/ARCHITECTURE/DECISIONS/NODE_PROTOCOL/DATA_MODEL/SECURITY/
TROUBLESHOOTING/CHANGELOG theo thứ tự bắt buộc. Tiếp đó đọc tài liệu này,
PHASE4-HANDOFF.md, PHASE4-STATUS.md, ANDROID-NATIVE-PILOT.md và PHASE5-PROGRESS.md.
Đọc các thông báo latest trước các đoạn lịch sử. Guide nâng cấp ZTE0.3 không phải
luồng cài mới hiện tại. DEMO-QUICKSTART mô tả lệnh nhưng gói0.4.1 là track cũ.

Có thể clone vào thư mục PC MỚI, chưa tồn tại:

```sh
git clone --branch feature/phase5-remote-access --single-branch https://github.com/litequang/Android-Storage-Cluster-ASC.git ASC-PC
cd ASC-PC
git status --short
git rev-parse HEAD
```

## Bộ cài đúng vai trò

Artifact commit bất biến: d3b1a9f303a03151d520154d850c407449bb69f9.
Đã tải lại byte thật và checksum qua HTTPS ở phiên bàn giao; không chỉ kiểm tra
đường dẫn build. Repo chứa artifact thường, không phải GitHub Release API.

| Vai trò | Path trong repository | SHA-256 |
| --- | --- | --- |
| Controller + Dashboard source,248278bytes | candidates/asc-demo-alpha-0.4.3-core-decode-internal-source.tar.gz | 6a60bd4180bc338d8c62eff4ef1347082a0e6c0ce36e06143ff53baa791b9d57 |
| Storage Node APK5 internal,39000831bytes | android-artifacts/asc-native-node-0.4.1-internal-debug.apk | aec65c2ca5541aab4060e19616204eef8caf4d2f0d6e7a3e27010dd819cf60f5 |

[Controller archive](https://raw.githubusercontent.com/litequang/Android-Storage-Cluster-ASC/d3b1a9f303a03151d520154d850c407449bb69f9/candidates/asc-demo-alpha-0.4.3-core-decode-internal-source.tar.gz)
và [.sha256](https://raw.githubusercontent.com/litequang/Android-Storage-Cluster-ASC/d3b1a9f303a03151d520154d850c407449bb69f9/candidates/asc-demo-alpha-0.4.3-core-decode-internal-source.tar.gz.sha256).

[Node APK](https://raw.githubusercontent.com/litequang/Android-Storage-Cluster-ASC/d3b1a9f303a03151d520154d850c407449bb69f9/android-artifacts/asc-native-node-0.4.1-internal-debug.apk)
và [.sha256](https://raw.githubusercontent.com/litequang/Android-Storage-Cluster-ASC/d3b1a9f303a03151d520154d850c407449bb69f9/android-artifacts/asc-native-node-0.4.1-internal-debug.apk.sha256).

Controller release ID b423c5d8e811876ae71a9e0ad41c6ba46acc5b4056b408a8e125875aabcf2aca.
Giải nén vào thư mục MỚI; root archive là asc-demo-alpha. Không ghi đè bộ cài cũ.
Gói Linux Access0.1.0 là access gateway cho Linux, KHÔNG phải bộ cài Controller
Termux. Không trộn Node APK mới với Controller Demo0.4.1 và coi như đã qualified.

APK application ID org.asc.foundation,versionCode5. NativeTLS cần API30+ dù minSDK
package26. Xác minh Android/SDK/model thật trước thử. Public signer SHA256:
bba77b68e43ecfe885705442d2224977208bf77a397c216393c26fc151a6bc30.
Private signer không nằm GitHub. Không build signer khác rồi tuyên bố in-place
upgrade; giữ original APK/state khi đã cài. Mã nguồn Python/Controller có thể sửa
trước, không cần rebuild APK chỉ để chẩn đoán Controller.

## Quy trình PC tiếp tục

1. Xác định đúng ZTE owner chọn và khả năng điều khiển thực tế. Không giả định
   adb shell có UID/quyền đọc private Termux. Chạy trong terminal Termux hoặc kênh
   owner đã thiết lập đúng quyền. Không mở public SSH, root hoặc đổi SELinux/quyền.
2. Thu đúng lệnh bị lỗi và output đã loại bí mật, Android/model/SDK, nguồn Termux,
   python3 --version, openssl version. Không thu cả private DB/config/full logcat.
   Cài dependency khi cần bằng lệnh owner chạy có kiểm soát; không pkg upgrade.
   Termux CLI OpenSSL thuộc package openssl-tool, không chỉ thư viện openssl.
3. Kiểm tra bộ cài/checksum, prefix ~/.local/share/asc-demo và state ~/.asc-demo
   có partial data không trước retry. Không rm/reset/clear data/recreate identity.
   Giữ lại báo lỗi trước khi sửa, phân biệt dependency/preflight/install/init/run.
4. Với cài mới thật sự và preflight allowed: sh scripts/demo-alpha.sh preflight;
   install --dry-run; install. Launcher là
   sh "$HOME/.local/share/asc-demo/bin/asc-demo" COMMAND. init --role controller
   --host ACTUAL_ZTE_LAN_IP --name ASC-ZTE chỉ chạy khi chưa khởi tạo identity.
   Không dùng IP192.168.100.237 cũ nếu hiện tại khác. Giữ IP ổn định sau init.
5. Khi chưa có Dashboard và Controller/Node đều dừng: dashboard-init --port 8444;
   dashboard-trust --out NEW_PUBLIC_CA_FILE; đối
   chiếu fingerprint public CA, owner trust trong browser. Chạy run-controller
   --dashboard foreground. Terminal owner riêng lấy dashboard-code. Không dùng
   -k/HTTP hoặc copy private key để né lỗi. Xem PHASE4-HANDOFF cho luồng Node APK.
6. Sửa đúng lớp gây lỗi; tái hiện bằng targeted test nếu là source bug. Tạo nhánh
   sửa riêng từ source mới nhất, ví dụ fix/zte-controller-install. Giữ các guards,
   định dạng/IDs và tests cũ; không rebuild hoặc ghi đè archive đã công bố. Gói sửa
   mới cần version/checksum/manifest rõ ràng và package audit. Ghi output thực chạy,
   test PASS/FAIL/BLOCKED, commit/push/fetch/remote verification và bước resume.

Controller native trong APK chưa có. ZTE Termux làm Controller; APK làm Storage
Node, không cần Termux cho chính Node. APK/Termux khác UID/state, không copy/adopt
keys/database/volume. Hai Node trên cùng ZTE vẫn một failure domain; cần điện
thoại thứ hai thật sự để đạt hai domain/replicas. Bphone SDK còn cần xác minh.

## Gate sau khi sửa và giới hạn bằng chứng

Controller start, trusted Dashboard HTTPS/owner login, native enrollment với đúng
PIN/Cluster ID, owner phê duyệt node/volume/domain, actual writable/fsync/two-phone
replicas/upload/download SHA/fallback/restart/Controller loss và LAN còn khi ngắt
Internet. Ghi riêng từng kết quả phone thực chạy; không suy ra từ emulator PASS.
Không có physical Android acceptance cho lượt ZTE này. WritableDR, Android Raft/
membership/failover/GC vẫn khóa. Không cần Cloudflare/VPN để chạy LAN.

Source/Linux synthetic trước đó: full445 và riêng5.4e38targeted PASS. Không rerun
full chỉ để đọc handoff; nếu sửa runtime thì chạy targeted/regression phù hợp và
các safety gates liên quan. Private toolchains/raw logs/keys/signer/AVD không công
bố GitHub; đó không phải mã nguồn bị thiếu. Lỗi cài ZTE vẫn UNDIAGNOSED đến khi
PC/owner thu được lỗi thực tế. Handoff này chỉ sửa docs, không chứa bug fix/runtime.
