# Phase4.1 acceptance — Linux synthetic foundation only

**ACCEPTED for the bounded Linux synthetic Phase4.1 scope.** Android/native/Windows
runtime and production are NOT ACCEPTED. Core3D writable disaster recovery remains
**BLOCKED / NOT ACCEPTED**. No authority/quorum reconstruction or recovery activation.

Branch `feature/phase4-1-local-engine-quorum-ui`, verified Phase4.0 baseline
b9e75779670d5565d05a324751af02e48d2538eb. Qualified source/tests/packaged guides/
archive frozen at **0a3ea839217156b69209a073f5d836ee1db4452b**. Final reporting changes documentation only;
no source/test/packaged-guide/candidate edits after this successful full run.
Normal pushes/advertised remote equality were verified before each next checkpoint.

## Published checkpoints

|Checkpoint|Source commit|Actual targeted result|
|---|---|---|
|4.1a contracts/threat model|5c26ccf92337ddf2026702a1f8310d4f07b2d689|14 PASS,0 skip/fail,20.014s|
|4.1b.1 private IPC/Quick Join|fca0c37349ec65ce62220da52f9c1e8d4b6ae632|21 PASS,0 skip/fail,94.158s|
|4.1b.2 owned lifecycle/crash|182d366a53548ab08364edb9ad23f5bf64a35ff7|19 PASS,0 skip/fail,74.287s|
|4.1c.1 Core/passive observer|fb05323708f3147cee1a8e9a4a3093ae39306d9a|28 PASS,0 skip/fail,62.475s|
|4.1c.2 shared HTTPS/browser|40fb7c788a95434387e53d04065ddf4ca7721202|15 PASS,0 skip/fail,149.641s; final browser1 PASS54.828s|
|4.1d.1 exact candidate/upgrade freeze|0a3ea839217156b69209a073f5d836ee1db4452b|38 PASS,0 skip/fail,224.827s|
|4.1d.2 full qualification/reporting|38360d1bd3261dba730e9ac7f7e9ca8772a73b40 (docs-only)|311 fresh Python +11 uncached Go PASS; gates below|

## Fresh final gates / evidence

Linux x86_64 kernel6.18.55, Python3.13.5, Go1.27.3, Node24.19.0,
Chromium154.0.8037.57/certutil/OpenSSL. Python command:
`python -B -m unittest discover -s tests -v -f`.
Started 2026-10-25T13:59:24.049377+00:00; completed 2026-10-25T14:29:25.438277+00:00.
**311 PASS,0 FAIL,0 ERROR,0 SKIP in 1801.144s**;
exit0, source fingerprint unchanged for all 191 frozen paths.
Discovery311 unique IDs, no duplicate inherited test IDs. No old full substituted.

|Fault gate inside this SAME full run|Actual result|
|---|---|
|Phase3A snapshots/versions/restore/authority/crashes|12/12 PASS|
|Phase2B actual failover/metadata consensus/fencing|20/20 PASS|
|Phase3B scoring/placement/preferences safety|7/7 PASS|
|Phase3C replication/drain/reduction/reference safety|3/3 PASS|
|Network-authorized GC security/fencing|3/3 PASS|
|Linux synthetic actual physical-unlink/TLS ACK loss/journal/replay/final-callback/quorum guards|8/8 PASS|
|Phase3D external bytes/authority/corruption/interruption/read-only recovery|9/9 PASS|
|New bridge actual UDS/peer UID/scopes/lost replies/real Engine/enrollment/lifecycle/SIGKILL|PASS|
|Core actual3-voter partition/stale Leader/quorum loss/Controller death/reconnect|PASS|
|CA-trusted Chromium/shared owner API/CSRF/XSS/read-only mode/policy3/actual transport split/heal|PASS|
|Exact old candidate upgrade/pending BOTH directions/new-state code rollback/old+new file SHA/private control|PASS|

Actual I/O uses temporary private synthetic roots only. Existing test launchers
provide isolated Core cluster fixtures; product runtime platform/GC guards remain.
Expected denial messages and injected connection errors are not test failures.
All27 original Core test files byte-identical to Core3D; no fault tests removed,
skipped or weakened. Core external/Go source unchanged; existing Core handler has
only the bounded read-only observer delegation. No whole-branch merge/history edit.

Go from consensus/: `go mod verify`, `go vet ./...`,
`go test -count=1 -v -timeout 240s ./...`: **11 tests PASS**, all exit0.
`CGO_ENABLED=0 GOOS=<linux|windows|android> GOARCH=<amd64|amd64|arm64>
go build -trimpath -buildvcs=false -o <private-output> ./cmd/asc-raft`: all PASS.
Windows/Android builds are CROSS-BUILD ONLY, not runtime or phone acceptance.

## Implemented behavior / reuse

Private0700 control +0600 authenticated Linux AF_UNIX/SO_PEERCRED socket, separate
application bearer/scopes and strict version1 frames/request IDs. Read status uses
existing marked engine/volume/identity, no init/approval/write probe; write/fsync
remain null until actually measured elsewhere. Existing pinned durable Quick Join
worker retains pending operation/token and can resume lost ACK/bridge death. Full
bounded journal preserves sanitized historical receipts, not current authority.
Only configured Demo Node may be explicitly started/stopped as an OWNED child;
retained supervisor thread +Linux parent-death fence, no shell/PID/foreign kill/
Controller/Core startup/automatic restart. Crash socket cleanup only exact known
private owned receipt/inode +exclusive lock +actual refused connection.

Owner GET Core endpoint uses actual Runtime.view Barrier and stable role/term/
committed identity; never ensure_ready/takeover/commit. Existing disposable SQL
workspace/Catalog/Views reused query-only, never second persistent Catalog/Engine.
Explicit3 pinned existing Controllers/cluster/epoch/floor, no SQL/mode fallback.
Shared Dashboard Sessions/HTTPS/CA/assets have explicit Demo/Core/recovery routing,
unique gateway cookies, server-side Core GET-only enforcement and honest UNKNOWN/
OFFLINE/DEGRADED/QUORUM UNAVAILABLE/policy1/2/3/jobs/backup history. Browser receives
no node/owner/local-app credentials. Strong observation NEVER grants writer authority.
Passive recovery re-verifies anchored whole bytes/cluster/epoch/history floor each
read, RECOVERY READ-ONLY or UNKNOWN, no keys/config/runtime activation.

## Exact source candidate / compatibility

`candidates/asc-demo-alpha-0.4.3-dev.tar.gz`, **228052 bytes,
124 public files**, deterministic exact-source rebuild +inventory/SHA/
secret/private-path scan PASS. SHA-256:
`96260f1709f6a9db6cb98869fbef8fc2313feaf68a4f12da354665ad04693c04`.
Release ID `0568d5a91c32ab210fe8c39dc52be5e1862de994bf65ecd501a1e55af019e81f`.
Not a public Android release/APK or writable Core deployment package. Original
published releases and0.4.2 candidate/SHAs preserved byte-for-byte. Base formats
unchanged. Exact published0.4.2 ->0.4.3 candidate qualified; NEW-state code-only
rollback keeps old/new bytes and identities/keys/PIN/volume/pending. Historical
0.3/0.4->0.4.1 and0.4.1->0.4.2 tests remain exact and PASS separately. No claim of
untested direct paths or native/Core state migration. Old0.4.2 lacks bridge/Core UI
API and refuses unsupported commands; separate private control roots retained.

Commands, independent checksum/CA verification, staged upgrade, bridge use, owner
read-only gateway, stop, backup and code-only rollback: PHASE4-1-OPERATIONS.md.
API/IPC: LOCAL-ENGINE-BRIDGE.md, CORE-QUORUM-DASHBOARD.md. Security: LOCAL-ENGINE-
THREAT-MODEL.md. Never restore stale database over newer history/bytes. Existing
Demo backups do NOT include separate bridge/gateway roots; stopped private backup
of those credentials/journals is separate. No automatic control-root restore tool.

## Honest limits / Phase4.2

NOT TESTED: Android runtime/real media/phone TLS UX, Windows runtime, APK/Binder/
cross-UID IPC, Keystore, SAF, foreground service/notification/Doze, OS kill/reboot,
real power loss or Termux->APK migration. No adb/sdkmanager/gradle on PATH, no APK
skeleton/build/runtime claim. PWA cannot start Termux or access its private keys.
Same owning OS UID remains trusted; UDS/app grant is not a hostile-admin sandbox.
Journal256 permanent mutations; new login code requires explicit gateway restart
(revokes sessions); observer is static3-voter configuration with arbitrarily many
observed storage nodes. Source-history floor is operator minimum +RAM monotonicity,
not globally newest proof across restart. External backup unconfigured stays UNKNOWN;
historical VERIFIED status never authorizes GC. No rollback of native migration.

ANDROID-APP-CONTRACT.md specifies Phase4.2: verified SDK/emulator/toolchain,
signature/UID-authorized Binder/native foreground service, Keystore/storage provider
interfaces, network/Doze/OS-death tests, then owner-operated device qualification.
Termux->APK and single-writer->quorum migrations require separate implementation/
acceptance, not copying SQLite/keys/private folders. Android Raft/GC/failover and
Core3D writable disaster recovery stay locked/BLOCKED. No phones/M51/production/
SSH/system/Termux:Boot/root/format access performed. No automatic storage approval,
replica reduction, membership change, recovery writer or fake fencing/quorum.

## Remote receipt

Qualification/reporting38360d1bd3261dba730e9ac7f7e9ca8772a73b40 pushed normally,
advertised HEAD verified and independently fetched into a new bare repository.
All191 frozen paths and published archive/checksum matched qualified source.
Core3D/CoreWIP/Demo/Phase4.0 advertised refs remain exact baselines. Receipt
follow-ups are docs-only; current final commit is in PHASE4-1-PROGRESS/Git history.
