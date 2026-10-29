# Phase4 — trạng thái 2026-10-28

**API35 Native Node synthetic vừa PASS; xem [receipt](../qualification/phase4-api35-network-native.json).**

**Cài mới trực tiếp APK5 và nâng cấp APK4→FINAL5 đã nghiệm thu trên API30 x86_64 synthetic.
Toàn Phase4/4.2 và Android thật vẫn CHƯA ACCEPTED.**

| Phần | Bằng chứng và giới hạn |
|---|---|
|Core/Linux|Source8c54728;45targeted và fresh392Python PASS0skip/all64faults trước đó; sản phẩm giữ nguyên|
|Go|11top-level/12nested, vet/modules/builds PASS trước đó; Windows/Android chỉ cross-build|
|Controller source|Core-decode0.4.3-dev139files; exact source/deterministic/secret audit +GitHub download SHA PASS|
|Source upgrade|Exact042→b423:1PASS21.649s; exact e69/native-node và c831/PWA043→b423:2PASS51.823s, giữ NEW state khi rollback|
|Công cụ nghiệm thu|Chọn đúng published4/5 bằng SHA/signer, không fallback build mới;3host guards PASS0.193s|
|Native APK4→FINAL5|**17lượt Android targeted PASS0fail/skip** trên cùng data API30, không main5 trung gian; không phải17phương thức khác nhau/full suite|
|Cài mới trực tiếp APK5|3lượt Android PASS: network0.202s, cold Node92.364s, retained36.607s; APK5 là bản đầu tiên trước identity|
|Dữ liệu sau update|UID/Keystore/App/Node/Cluster/Volume/TLS pin và6records giữ nguyên; file4 còn đọc đúng SHA sau các lần ghi5|
|Node sau update|Existing Engine/enrollment/FGS, upload256KiB/two logical replicas, HTTPS/browser/download SHA/fallback, Controller-loss503, process death PASS|
|Web/PWA|Dùng chung owner Dashboard/File Manager; Linux Chromium HTTPS/PWA proof có sẵn, Chrome Android chưa nghiệm thu|
|API35|Same exact5: network1/TLS1/cold Node1/retained1 archived PASS; actual replicas/browser/SHA/fallback/Controller loss; fresh15 TLS/context/vault/Engine PASS209.708s/all6Main hashes equal; old600s UNKNOWN giữ nguyên|
|Artifact|Giữ nguyên APK5/aec65c2c và signer bba77b68; không build/phát hành APK mới vì công cụ test thay đổi|

Chi tiết mới: [direct-upgrade receipt](../qualification/phase4-direct-published45-final.json).
Bộ17lượt gồm network1, cold/retained4 Node2, local update11, retained5 Node2,
đọc original4 sau ghi5 thêm1; có phương thức lặp lại tại các giai đoạn khác nhau.
Thêm [fresh5 receipt](../qualification/phase4-fresh-final5-api30.json):3lượt trên
userdata trống riêng. Tổng20lượt Android của hai đường, không phải20phương thức
khác nhau/full suite; không cộng15API35 UNKNOWN cũ;15fresh API35 PASS được ghi riêng trong receipt mới. Mỗi checkpoint có source/receipt
và push riêng; đọc PHASE4-2-PROGRESS.

Chỉ một trong314inputs cũ đổi: test driver chọn artifact; Core/app/dependencies/
package bytes không đổi. Ba test host mới được chạy riêng, API30 workflow thực
chạy trên cả hai APK. Giữ proof392 cho sản phẩm giống hệt, **không tuyên bố fresh
full397**. Không chạy lại Go/old faults vì không sửa sản phẩm. APK5 chứa source3914,
không chứa tối ưu Core Runtime8c; Native Node không instantiate quorum Controller.
Quorum/term/nonce/checksum/pins/last-copy/physical proof và budget10s/250ms giữ nguyên.

## Gói và cách sử dụng

- [Node APK5 internal](../android-artifacts/asc-native-node-0.4.1-internal-debug.apk)
  và [SHA-256](../android-artifacts/asc-native-node-0.4.1-internal-debug.apk.sha256).
- [Controller/PWA source](../candidates/asc-demo-alpha-0.4.3-core-decode-internal-source.tar.gz)
  và [hướng dẫn bàn giao](PHASE4-HANDOFF.md).

Node APK không cần Termux. Controller vẫn QuickStart/Termux hoặc Linux; chưa có
Controller native. File Manager/login owner-code dùng web/PWA chung, chưa native
file picker/password multiuser. LAN cần đường IP nội bộ, không tự tạo hotspot/
Wi-Fi Direct; PWA không offline-write/cache file hay điều khiển Termux.
Cloudflare/SSH/VPN/remote maintenance thuộc Phase5, chưa triển khai.

## Chưa nghiệm thu

API30 x86_64 SDK NAT +Linux peer cùng host chỉ là2miền logic, không phải LAN điện
thoại/hai miền lỗi vật lý. API35 cold/retained Node và15fresh faults nay PASS;
blocker cũ giữ làm lịch sử, xem [API35 qualification](PHASE4-API35-QUALIFICATION.md). ARM64/phones/Chrome Android/
Doze/OEM/24x7, SDK26–29 NativeTLS, Termux→APK, Foundation2→FINAL5 chưa qualified.
Direct exact published4→FINAL5 đã PASS đúng hai archive APK được chỉ rõ, không suy
ra cho mọi build gắn version4/5. Android thật phải được owner kiểm chứng riêng.

Tất cả emulator đã dừng; API35 có7offline image/32host files backup/hash-verified, all6Main hashes/UID/file SHA giữ nguyên. SDK exit-11/SIGSEGV không phải clean-powerloss PASS. Không dùng PID cũ; xác minh owner mới trước ADB. Các dataset API30 cũ giữ nguyên; private signer và mọi dữ liệu cũ giữ nguyên. Data mới
/workspace/work/phase4-direct-apk45:7image backup offline và33host files kiểm hash,
không restore. SDK shutdown yêu cầu bình thường, exit-10/SIGUSR1, chưa có bằng
chứng clean-powerloss. API35 cũ giữ riêng backup/SIGSEGV. Không dùng disk backup
SDK như tính năng export Keystore/phone backup hoặc quyền recovery writer.
Fresh5 dataset riêng: /workspace/work/phase4-fresh-final5-api30, đã dừng,7images
+32host files backup/hash-verified. Chỉ dọn2ZIP installer công khai đã cài để đủ
disk SDK; mọi công cụ cài sẵn, source/APK/signer/AVD/state cũ giữ nguyên.

Bước tiếp: owner theo [pilot](ANDROID-NATIVE-PILOT.md) trên model được phép,
SDK30+/ARM64,2phones/2domains/2replicas/SHA/fallback/restart/Controller loss,
Wi-Fi còn khi ngắt Internet, FGS/Stop/Doze/OEM và HTTPS/PWA. Codex không truy cập
phone/M51/production. API35 các gate Node/15fresh faults đã PASS; nếu mở lại dataset
chỉ --resume fixture/identity cũ sau khi xác minh live owner/default network/pin.
Không fresh init/wipe/clone hay đổi proxy/CA/validation. Không còn blocker mạng/
Node trong lượt nghiệm thu cuối này; phone/ARM64/platform gates vẫn chưa đạt.
WriterDR/Android voter/GC/failover giữ khóa.

API35 latest supersedes old network/Node blocker wording above: Node cold/retained đã PASS qua actual eth0/15 SDK NAT, không ADB relay. Main hiện đã có identity, chỉ resume cùng fixture; không init lại. Full Phase4/phone/ARM64/physical LAN vẫn NOT ACCEPTED.
