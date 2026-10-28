# Phase4 — trạng thái 2026-10-28

**Đã hoàn tất gate phần mềm Linux còn thiếu. Toàn Phase4/4.2 CHƯA ACCEPTED trên Android thật.**

| Phần | Kết quả thực tế |
|---|---|
|Core decode fix|Source8c54728, original networkGC +all8Linux fault groups +guards:45targeted PASS|
|Fresh full Python|**392PASS /0SKIP /0FAIL**,1484.150s;64fault markers,314inputs không đổi|
|Fresh Go|11top-level/12nested PASS; vet/module verification và builds PASS; Windows/Android chỉ cross-build|
|Controller source mới|0.4.3-dev core-decode:139files, exact source/deterministic/secret audit PASS|
|Đúng archive upgrade|Exact0.4.2->new source:1PASS21.649s; exact e69/native-node và c831/PWA043 ->b423:2PASS51.823s, gồm pending/IDs/bytes/NEW-state code rollback|
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

Final APK5/API35 đã PASS5transport; cold boot/Package Manager đã sẵn sàng.
Cold integrated Node E2E trên35 vẫn BLOCKED ở network preflight: AP thử nghiệm
không có Internet bị Android ngắt, System UI ANR; chưa tạo Main Node identity.
Không suy ra enrollment/replica/process-death PASS từ transport. API30 proof là
x86_64 SDK NAT, không phải ARM64/phone LAN/hai miền lỗi vật lý. API26–29 NativeTLS NOT QUALIFIED dù
minSDK26. Exact direct published4->final5 chưa thử; chỉ4->interim5->final5 đã giữ
state. Không Termux→APK migration, Android voters/GC/failover hoặc writableDR.

Owner nghiệm thu theo [pilot](ANDROID-NATIVE-PILOT.md): model/SDK30+/ARM64, pin/
Cluster/pending, private probe,2phones/2domains/2replicas/SHA/fallback, restart/
Controller loss/network changes, same-signer update, FGS/Stop/Doze/OEM, Chrome
HTTPS/PWA và LAN giữ Wi-Fi khi mất Internet. Codex không truy cập phone/M51/
production để đánh PASS. Không cần chạy lại full nếu source không đổi; tiếp tục
nghiệm thu đúng platform/đường upgrade còn thiếu, không chuyển Phase5 tự động.


Latest exact043 compatibility supplement: published e69/native-node and c831/PWA
archives ->b423/core-decode upgrade +NEW-state code rollback2PASS0skip51.823s;
qualification/phase4-direct043-upgrade.json. Product/old314inputs unchanged,
full392 retained and new2tests separately targeted, not fresh full394. Any older
NOT TESTED direct043 wording above is superseded only for these exact archives.
APK direct upgrade/Android API35 Node E2E/physical-device scope remains separate.


API35 supplement: same cold sandbox boot/PM READY and exact APK5 transport5PASS
210.286s, no wipe/restore/root/source change. Node E2E still pending;0main identity
records so no retained4->5 proof. See PHASE4-API35-QUALIFICATION and transport5
receipt; previous API35 NOT TESTED wording is superseded only for this transport
scope. Physical/ARM64/Doze/OEM/PWA and full Phase4 acceptance unchanged.

Latest continuation: thêm15bài Android được yêu cầu nhưng timeout600.104s, không
có JUnit hoàn tất; **UNKNOWN/BLOCKED, không cộng PASS/FAIL/SKIP**. Chưa chạy cold
Node E2E vì network preflight chưa đạt. Emulator đã dừng, Main identity/context
vẫn chưa tạo, Wi-Fi thử nghiệm khôi phục và7image backup riêng đã xác minh hash.
SDK shutdown SIGSEGV nên chưa có clean-powerloss proof. Xem
[receipt](../qualification/phase4-api35-cold-node-blocker.json). Source/APK/signer
không đổi; không chạy lại full hoặc chuyển Phase5 để né các gate còn thiếu.


Independent upgrade setup: driver --artifact now selects fixed published4/5
bytes before initial identity;3host guards PASS0.193s, receipt
qualification/phase4-published-apk-selection.json. Only this old frozen test-driver
input changed; product/app/packages unchanged. Full392 is retained for unchanged
product, not a fresh full397. Direct published4->final5 Android upgrade remains
NOT TESTED pending actual fresh API30 sandbox; API35 blocker is preserved.


API30 direct-upgrade baseline: exact published4 FIRST install in new blank SDK
sandbox, NetworkReadiness1 +cold/retained NativeCatalog2 PASS. Real bytes/replicas/
SHA/browser/Controller-loss/identity, no intermediate main5 yet. Receipt
qualification/phase4-published4-cold-baseline.json. Actual direct4->final5 still
NOT TESTED; two logical domains on one host are not physical phone acceptance.
API35 blocked gate unchanged. Next preserve same state and normal final5 update.
