# Phase4 — trạng thái 2026-10-28

**Đã hoàn tất gate phần mềm Linux còn thiếu. Toàn Phase4/4.2 CHƯA ACCEPTED trên Android thật.**

| Phần | Kết quả thực tế |
|---|---|
|Core decode fix|Source8c54728, original networkGC +all8Linux fault groups +guards:45targeted PASS|
|Fresh full Python|**392PASS /0SKIP /0FAIL**,1484.150s;64fault markers,314inputs không đổi|
|Fresh Go|11top-level/12nested PASS; vet/module verification và builds PASS; Windows/Android chỉ cross-build|
|Controller source mới|0.4.3-dev core-decode:139files, exact source/deterministic/secret audit PASS|
|Đúng archive upgrade|Exact0.4.2->new source +pending/IDs/bytes/NEW-state rollback:1PASS21.649s; direct old0.4.3->new chưa thử|
|APK5|Giữ nguyên bản source3914/signer cũ, không rebuild vì Core Controller-only delta; Native Node không instantiate quorum Runtime|
|Android proof giữ lại|API30x86_64:28selected+foreign1/JVM17/network2/downgrade readback1 PASS trước đó; không chạy lại Android trong checkpoint này|
|Web/PWA|Dashboard login/File Manager/node/volume/replicas/upload/download/SHA/fallback; fresh full có browser/API integration PASS|
|PWA install|Actual Chromium Linux install/launch proof trước đó, web bytes không đổi; Chrome Android chưa thử|
|GitHub/checksum|Artifactd3b1a9f normal-pushed; separate GitHub clone/archive+APK SHA PASS; [receipt](../qualification/phase4-core-decode-publication.json), không phải runtime acceptance|

Core fix chỉ tái sử dụng kiểm tra cấu trúc cho2immutable inputs <=2MiB, không cache
quyền. Quorum/term/nonce, checksum/physical proof, retention/last-copy và budget10s/
250ms giữ nguyên. Các full/trial FAIL cũ được giữ trong history; đã được supersede
bởi lượt392PASS, không cộng lại thành PASS hay dùng retry/TTL thử nghiệm.

## Phần còn thiếu

APK Node không cần Termux; Controller vẫn QuickStart/Termux hoặc Linux, chưa có
Controller native. File Manager dùng web/PWA chung; chưa native file picker hay
user-password/multiuser sharing. LAN cần đường IP nội bộ; không tự tạo hotspot/
Wi-Fi Direct, PWA không offline-write/cache API/file hay điều khiển Termux.
Cloudflare/SSH/VPN/remote maintenance thuộc Phase5, chưa triển khai.

Final APK5/API35 chưa thử (cold35 BLOCKED); API30 proof là x86_64 SDK NAT, không
phải ARM64/phone LAN/hai miền lỗi vật lý. API26–29 NativeTLS NOT QUALIFIED dù
minSDK26. Exact direct published4->final5 chưa thử; chỉ4->interim5->final5 đã giữ
state. Không Termux→APK migration, Android voters/GC/failover hoặc writableDR.

Owner nghiệm thu theo [pilot](ANDROID-NATIVE-PILOT.md): model/SDK30+/ARM64, pin/
Cluster/pending, private probe,2phones/2domains/2replicas/SHA/fallback, restart/
Controller loss/network changes, same-signer update, FGS/Stop/Doze/OEM, Chrome
HTTPS/PWA và LAN giữ Wi-Fi khi mất Internet. Codex không truy cập phone/M51/
production để đánh PASS. Không cần chạy lại full nếu source không đổi; tiếp tục
nghiệm thu đúng platform/đường upgrade còn thiếu, không chuyển Phase5 tự động.
