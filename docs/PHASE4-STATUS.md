# Phase4 — trạng thái bàn giao 2026-10-27

**Đã bàn giao candidate phát triển/MVP có thể tải. Toàn Phase4 CHƯA ACCEPTED.**
Không đánh đồng source/build/emulator PASS với ARM64/điện thoại/production.

| Phần | Kết quả thực tế |
|---|---|
|4.0 Core/Demo audit +selective integration +Quick Join|Linux synthetic accepted, giữ Core3D và nhánh gốc|
|4.1 local bridge +Core quorum read-only adapter|Linux synthetic accepted, không cấp writer hoặc tạo quorum|
|4.2 Node APK|Context/Keystore/TLS/enrollment/pending/Core Engine/Agent/FGS/UI/observer đã triển khai; API30 runtime và API35 retained có bằng chứng|
|Web File Manager|Có owner login/upload/download/SHA/replica/fallback; APK mở Dashboard hiện hữu, không backend/Catalog thứ hai|
|Gói và checksum|APK4 +exact source Controller đã push bằng Git và tải lại bằng clone riêng, checksum cả hai PASS|
|Full Core regression|383Python PASS0skip,64fault banners; Go11/vet/modules/builds PASS, runtime không đổi|
|API30 Android11 x86_64|Fresh enrollment/Node startup JUnit1 PASS156.88s; full retained workflow sau sửa fixture NAT PASS63.58s+33.856s;22Android117.496s+foreign1/0.124s PASS|
|API35 Android15 x86_64|Retained26+foreign1 và dữ liệu sau crash/upgrade PASS; fresh cold startup BLOCKED, log có cả system telephony ANR|

## Bằng chứng và giới hạn

[PHASE4-HANDOFF](PHASE4-HANDOFF.md) chứa gói, các đường nâng cấp thực sự đã kiểm,
Node/Controller setup và rollback giữ dữ liệu. Các JSON trong qualification giữ
hash/provenance, không chứa private signer/state. Gói Controller source0.4.3-dev
không phải APK Controller; Node APK độc lập với UID/state Termux. Native3->4 exact
upgrade qualified, Foundation2->4 direct chưa kiểm. Không migration Termux->APK.

API30 first host flow FAILED upload timeout: active wlan0 .16 khác SDK ingress .15
(radio0). Normal fixture WiFi disable chọn .15, cùng identity/context/volume; full
retry giữ state mới PASS. Không gọi đây là clean first-attempt cold E2E. SDK NAT
chuyển bytes TLS thật, ADB chỉ điều khiển;2domain trên1host không phải2hardware.
Không có proxy/CA/authority bypass, reset hay giảm assertion để đạt PASS.

Native file picker, multiuser-password accounts và PWA installability chưa có;
MVP dùng owner web File Manager. SSH/VPN/Cloudflare vẫn là Phase5 chưa triển khai.
API26–29 NativeTLS không qualified. Core3D writer recovery vẫn BLOCKED; không có
Android voters/GC/failover. Không thử phone/M51/production, không đổi Termux/Boot.

## Để đóng nghiệm thu toàn Phase4

Owner dùng dữ liệu thử không quan trọng trên điện thoại được phép, theo
ANDROID-NATIVE-PILOT. Không cài M51/production. Ghi thật PASS/FAIL/NOT TESTED:

| Gate owner | Hiện tại |
|---|---|
|Model +Android SDK thực tế; API30+ cho NativeTLS|NOT TESTED trên phone|
|ARM64 install/launch/Keystore/private probe|NOT TESTED|
|Controller endpoint/pin/Cluster +one-use join/pending|NOT TESTED trên phone|
|2điện thoại/2domain, owner approvals,2verified replicas +SHA|NOT TESTED|
|Một Node offline/fallback; Controller loss từ chối; restart giữ IDs/bytes|NOT TESTED trên phone|
|LAN giữ WiFi/IP khi Internet router bị ngắt|NOT TESTED|
|Chrome Android HTTPS CA/login/upload/download|NOT TESTED|
|FGS notification/Stop/background, Doze/OEM/network changes|NOT TESTED trên phone|
|Upgrade signer/identity/volume/bytes và compatible recovery|NOT TESTED trên phone|
|API35 fresh startup hoặc giới hạn platform được nghiệm thu rõ ràng|BLOCKED/CHƯA CHỐT|

Các mục này không thể được Codex đánh PASS khi bị cấm thao tác điện thoại. Sau
khi có bằng chứng owner mới đánh giá nghiệm thu rộng hơn; không tự chuyển Phase5
hoặc tuyên bố production-ready. Current Cloud source/artifacts và các bước tiếp
đủ ở GitHub để phiên sau tiếp tục, không cần chạy lại383gates khi runtime không đổi.
