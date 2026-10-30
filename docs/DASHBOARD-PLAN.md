# Dashboard quản trị ASC — plan / owner authorization

Owner yêu cầu Dashboard đầy đủ sau khi ZTE đã cài OK. Baseline mới nhất đã fetch:
4336ab72fb2579167d61cce8466c68f59a2eff6d (PC checkpoint, exact Controller043,
14physical owner HTTPS assertions/restart). Code giống ca002db; không merge nhánh.
Nhánh triển khai riêng feature/dashboard-full xuất phát từ checkpoint đó.
Cloud chỉ source/Linux synthetic, không truy cập phone/SSH/M51 hoặc cấu hình live.

## Mục tiêu và phạm vi

Owner quản trị cụm LAN qua browser: đăng nhập thuận tiện, ghép node, duyệt storage/
physical domain, quản lý file và immutable versions, jobs, snapshot/restore, xem
sức khỏe và diagnostics. Reuse existing Controller/Catalog/Registry/Storage/API,
không backend thứ hai hoặc client nhận admin/node token. Vietnamese/mobile-first,
local assets/no CDN, không yêu cầu cloud. Browser vẫn cần HTTPS/public CA đã trust.

Chức năng single-writer Demo phải thực chạy trên sandbox có node/bytes thật.
Core quorum và recovery observer giữ READ-ONLY, không fallback sang Demo SQL,
không membership/voter/failover/GC/writableDR. Không gọi mock UI là chức năng.
App native/Termux migration/SAF/native Controller không thuộc Dashboard này.

## Checkpoints (targeted/docs/secrets/commit/push/verify mỗi phần)

0. Audit, mode/capability contract, plan/progress; lưu trước triển khai.
1. Node management: real pairing hiện có, owner-approved storage endpoint/pin/
   volumes/failure domain có confirmation và stale-generation refusal; rename/
   revoke hiện có; status/UNKNOWN, UI và API/browser/security tests.
2. Owner login/account: optional owner-managed password, server-side standard KDF,
   existing secure cookie/CSRF; one-time local bootstrap/recovery retained. No
   default/shared password/browser key storage. Explicit role capabilities; do
   not claim multiuser file ACL or sharing before implemented/tested.
3. File Manager: bounded pagination/search/folder navigation from existing logical
   paths, sorting/filter, version-aware upload without overwrite, replicas/SHA,
   durable Core retry/jobs with retry UI. No filesystem browsing/arbitrary path IO.
4. History/snapshots/restore: exact capability-aware adapter. Phase3A Backups
   currently REQUIRES Core quorum runtime; never fake term/index/Runtime for Demo.
   Review reuse of existing immutable Catalog versions/metadata snapshots and
   canonical stream/verification/replication for explicitly SINGLE-WRITER records
   in existing Registry if required. Any additive state contract must be tested
   for restart, lost ACK, references and exact043 upgrade/NEW-state rollback.
   Snapshot within cluster is NOT external DR. No physical deletion/GC. If a
   backend cannot safely support a feature, record actual blocker, never fake PASS.
5. Storage/cluster/settings/diagnostics: honest measured capacity/volumes, supported
   configuration and operation history, quotas owned by Node (no arbitrary FS or
   system/process controls), bounded redacted diagnostics. No fake remote quota
   change when Node has no authenticated configuration API.
6. Final integrated owner journey/browser/security/offline/fault +fresh applicable
   Python/Go regression, exact b423043 upgrade/identity/bytes/NEW-state rollback,
   immutable NEW source package/checksum/secret audit and GitHub download proof.
   Original043/APK5/Linux Access packages/signers unchanged. Phone/browser/Doze/
   two physical domains still distinct owner gates; no auto deployment.

Split a/b as needed, persist complete checkpoints before next. Progress records
actual results, source/remote IDs, pending work and resume commands. Do not call
full Dashboard COMPLETE until all promised applicable gates pass. Demo owner
scope does not imply arbitrary Core write UI, enterprise ACL/sharing or production.

## Audit findings / contracts

Existing Quick Join owner UI/API already creates one-use node codes and tracks
pending receipt; it is not just CLI. Missing visible approval is priority1.
CatalogService.register owns approval/credential generation/protected-node checks;
status probing follows approval using existing scoped grants. Browser supplies
only public endpoint/cert pin/volume IDs and explicit truthful physical domain.
Never infer independent phones from two volumes/Node IDs. Owner action must keep
existing credentials/bytes and reject stale state before a changed approval.

Sessions currently one-use grants/RAM owner cookie. Add account persistence only
with a versioned optional private contract; restart/logout/rotation revokes sessions.
File upload client already supports explicit immutable version; browser today uses
version1 only. Core Backups hard-binds Runtime.operation/commit, so a generic UI
call would not make it available to Demo. Existing observer must remain read-only.

Phase5 ingress currently excludes admin/pair routes intentionally. Management APIs
are direct trusted LAN Dashboard only initially; no widening remote allowlist by
default. Audit any future ingress capability separately, keep all old protections.


Checkpoint4 split after audit:4a backend/operator contract +exact043 compatibility
first, then4b UI/browser. Demo inspect_state intentionally rejects extra Registry
settings; optional private history.json1 +required-record witness preserve old043
code rollback. No new table/Engine/Catalog or fake quorum snapshot authority.
Use canonical MetadataSource, shared physical audit, stream client and durable
Core queue. Operations are owner-driven bounded steps; disconnected browser leaves
progress and exact upload intent for explicit resume, not an extra daemon queue.
