# Phase4 — trạng thái 2026-10-27

**Native Node/PWA đã có targeted PASS. Full regression bị chặn; toàn Phase4 CHƯA ACCEPTED.**
Snapshot debug nội bộ phục vụ review/tiếp tục công việc, không phải release đã nghiệm thu.

| Phần | Kết quả thực chạy |
|---|---|
|4.0 Core/Demo +Quick Join|Linux synthetic accepted; Core3D được bảo toàn, không merge toàn Demo|
|4.1 bridge +Core quorum observer|Linux synthetic accepted, read-only|
|Native APK5|Core Engine/Agent, Keystore/TLS, Quick Join, volume, FGS/Stop, UI/observer; API30 x86_64 targeted PASS|
|Web File Manager/PWA|Owner HTTPS login, upload/download/SHA/replica/fallback; manifest/install/network-only worker; tái sử dụng backend|
|Android/JVM|28selected PASS249.012s +foreignUID1PASS0.128s; JVM17PASS; downgrade refusal/readback1PASS10.738s|
|Network|Actual browser +Native2PASS80.675s/38.373s; SDK NAT trực tiếp, không ADB reverse truyền dữ liệu|
|Web|8Dashboard/browser +3Core gateway PASS; cài/mở/gỡ PWA thực tế Chromium Linux PASS, Chrome Android chưa thử|
|Full cuối|**FAIL:184tests/1ERROR1537.737s**,313inputs unchanged; không phải384PASS|
|Blocker|GC same-job replay sau unlink/lostACK: stale_gc_proof; bounded retry FAIL1094.769s, routing trial FAIL783.307s; cả hai bản thử đã loại|
|Guard test mới|44PASS0skip14.068s sau loại trial; không thay cho network fault gate|
|Go|11top-level/12nested PASS, vet/modules/builds PASS; source Go không đổi, không chạy lại vô ích|
|Artifact mới|APK5/source được audit và lưu dạng debug review với SHA; trạng thái remote xem PHASE4-HANDOFF/receipt|

Không tăng budget GC10s/250ms, không bỏ assertions hay coi phản hồi từ chối là
thực hiện fault thành công. Mọi lần FAIL giữ trong PROGRESS/receipt; không dùng383
cũ để nghiệm thu PWA/native mới. Core GC chỉ có executor trong synthetic fixture,
vẫn khóa trong Android/runtime thường. Root cause chưa chứng minh; quan sát thấy
metadata1024events/~2.4MiB và chờ Runtime lock/authority trên môi trường2CPU.

## Sử dụng và phần còn thiếu

Node APK không cần Termux; Controller vẫn QuickStart/Termux hoặc Linux. App không
đọc/adopt state Termux. File Manager là web dùng owner code/session; chưa có native
file picker, native Controller hoặc tài khoản mật khẩu đa người dùng.

LAN cần đường IP giữa thiết bị; giao thức không phụ thuộc Internet/cloud nhưng
phone LAN/ngắt Internet chưa nghiệm thu. PWA không chạy Termux/Node, không cache
API/file/catalog hay offline-write. Cloudflare/SSH/VPN remote maintenance thuộc
Phase5, chưa triển khai.

API30 x86_64 SDK NAT chỉ là synthetic; hai logical domains trên một host không
chứng minh hai miền lỗi vật lý. Final5 trên API35 NOT TESTED (cold35 BLOCKED); APK4/
35 là proof lịch sử. ARM64 chỉ build. API26–29 NativeTLS NOT QUALIFIED dù minSDK26.
Không hỗ trợ Termux→APK migration, Android voters/GC/failover hoặc writableDR.

## Việc tiếp theo theo thứ tự

1. Điều tra GC authority/proof latency với nguyên workload; giữ mọi guard và fault.
   Chạy original targeted gate trước; không chạy full lặp lại khi gate này còn FAIL.
2. Khi targeted đạt, fresh full384 +faults; audit/package/remote checksum theo source mới.
3. Owner nghiệm thu ZTE/Bphone SDK30+/ARM64: Quick Join/pin, private probe,2phone/
   2domain/replicas/SHA/fallback, restart/mất Controller/network, app upgrade,
   notification/Stop/background/Doze/OEM, Chrome HTTPS/PWA và LAN giữ Wi-Fi mất Internet.

Codex không truy cập điện thoại/M51/production để đánh PASS các gate còn thiếu.
Hướng dẫn [PHASE4-HANDOFF](PHASE4-HANDOFF.md), [Web/PWA](PHASE4-WEB-APP.md),
[receipt blocker](../qualification/phase4-closure-gc-investigation.json).
