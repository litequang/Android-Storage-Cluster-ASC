# Phase 3D acceptance — external data archives / recovery staging

Status: **PARTIALLY COMPLETE. External backup, anchored verification and VERIFIED
RECOVERY STAGING ACCEPTED for Linux x86_64 synthetic qualification only.**
**FULL WRITABLE DISASTER RECOVERY NOT ACCEPTED / BLOCKED.** No real-device,
Windows runtime, Android runtime or production qualification is inferred.

Branch feature/phase3d-external-dr from fetched/advertised Core WIP
acea2aead8cfd50f8a8fc2b31e24f8f9ccaeb84c. Demo remains c9c2660 unchanged.
Frozen implementation/tests: **50df5d79e1759cf5755d416d53c4bc47cc74e49b**, normal pushed/remote verified BEFORE
fresh full regression. Only reporting Markdown changed during/after successful
full; recorded source SHA256 fingerprint unchanged. Source/history/Core/Demo
preserved, no reset/force/main merge/deployment. Final reporting hash is in Git
history/final response and following publication receipt; no self-hash fiction.

## Fresh executed final gates

Existing activated Python3.13.5/Go1.27.3/OpenSSL, no system install/proxy/TLS bypass.
All below Codex-run, no old3C/Demo/owner PASS reused as current validation.

| Command / check | Actual result |
|---|---|
|python -B -m unittest discover -s tests -v|**238 PASS /0 SKIP /0 FAIL/ERROR, 1403.864s**|
|Retained3A /2B /3B faults|**12/12 +20/20 +7/7 PASS**|
|Retained3C replication /network GC authorization /Linux physical|**3/3 +3/3 +8/8 PASS**; actual original unlinks/TLS/crash/replay|
|Final targeted command below|**54 PASS /0 SKIP /0 FAIL/ERROR,66.001s**|
|New actual3D network/process matrix inside full|**9/9 groups PASS**|
|Actual recovery child exit91/normal CLI same-intent resume|PASS inside targeted and full|
|Exact original Core source schema roundtrip /compatibility|PASS, immutable baseline source actually executed|
|go test -count=1 -v -timeout 240s ./...|**11 top-level PASS**, uncached|
|go vet ./... /go mod verify|PASS /all modules verified|
|CGO_ENABLED=0 Linuxamd64 build|PASS|
|Windowsamd64 /Androidarm64 cross-build|PASS, **compile-only**, never executed|
|Python AST /operator Bash syntax /links /whitespace|108 Python PASS;3 Bash blocks bash -n PASS (not device execution); docs PASS|
|Tracked/index private-artifact/secrets audit|156 paths,0findings; repeated before final publication|

Full started **2026-10-25T05:52:00.041412+00:00**, completed **2026-10-25T06:15:24.035413+00:00**.
Private full/Go/fault/source-fingerprint logs: /workspace/work/phase3d/. Synthetic
keys/configs/stores/bytes/binaries remain outside Git; no backup/private state is
published. No source/test changes after source freeze; original208 Core cases plus
30 new3D cases =238 unique tests. New fixtures use module helpers without importing
old TestCase classes into discovery, so no duplicated tests pad counts.

```sh
source /workspace/asc-cloud/activate.sh
python -B -m unittest tests.test_external tests.test_external_verify tests.test_external_recovery tests.test_external_compatibility tests.test_external_cluster tests.test_external_faults tests.test_backup.BackupStateTests tests.test_failover.RuntimeStateTests -v
python -B -m unittest discover -s tests -v
cd consensus
go mod verify
go vet ./...
go test -count=1 -v -timeout 240s ./...
CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -trimpath -buildvcs=false -o /workspace/work/phase3d/asc-raft-linux-amd64 ./cmd/asc-raft
CGO_ENABLED=0 GOOS=windows GOARCH=amd64 go build -trimpath -buildvcs=false -o /workspace/work/phase3d/asc-raft-windows-amd64.exe ./cmd/asc-raft
CGO_ENABLED=0 GOOS=android GOARCH=arm64 go build -trimpath -buildvcs=false -o /workspace/work/phase3d/asc-raft-android-arm64 ./cmd/asc-raft
```

On another host choose approved private output paths; no toolchain installation or
runtime/device bypass is part of these commands. Go source/modules stayed identical
to baseline throughout; fresh verification/tests/builds preceded final Python full,
which also built/executed actual unchanged Go fixture binaries.

## Actual fault matrix / evidence mapping

|Gate|Evidence / result|
|---|---|
|01 exact snapshot/metadata/bytes|Actual3-voter Barrier, runtime2 with3A/3B/3C extensions, two versions, snapshots/TRASH; exact metadata SHA and body SHA PASS|
|02 source changes /old backup|Real upload while export runs; original captured set/checkpoint unchanged; newer known index =>STALE, not latest-history claim PASS|
|03 quorum loss|Actual all-voter partition before final callback; actual server rejection/no COMPLETE; heal then same capture/ID resume PASS|
|04 Controller/stale Leader|Actual Python+Go kill, higher actual term takeover and resume; isolated former Controller rejects capture/check/real upload; no ghost file after heal PASS|
|05 interrupted backup/retry|Actual backup child exit91 AFTER original durable object publish, incomplete journal, normal CLI resume keeps original inode and one object perID PASS|
|06 destination full|Explicit injected ENOSPC at real streamed .part fsync, not a physically full disk claim; no COMPLETE, same-ID retry exact bytes PASS|
|07 offline/corrupt replica|Actual offline cohost/voter and corrupt bytes on a second node; third approved source supplies exact SHA, corrupt/last/pinned source bytes never deleted PASS|
|08 pending upload/bytes missing|Real Catalog upload plan/job with no sent/verified object; capture cannot COMPLETE/omit missing version PASS|
|09 total authority loss|Stop ALL Controller/Go processes; trusted completed backup still stages exact old metadata/body bytes offline; writer/credentials=false, new backup authority denied, historical completion replay safe PASS|
|Recovery interruption|Actual stage child exit91, kernel locks release, normal CLI resumes exact intent and retains completed object inode; separate exception-boundary test also PASS|
|Manifest tamper /snapshot mismatch|Actual edited canonical manifest +rehashed self-receipt still fails trusted independent anchor; metadata mismatch/future schema/native aliases/bundle ID relabel denied PASS|
|Missing/corrupt/extra object|Actual filesystem edits detected by full SHA/coverage, never VERIFIED PASS|
|Unknown/retention|Real mode000 EACCES +IO fault =>UNKNOWN/null; last valid/incomplete/unknown archives held, no delete API/executor PASS|
|Filesystem safety|Root replacement, symlinks/hardlinks, traversal, source/store overlap, unsafe permissions, wrong marker/ownership and duplicate OS owner denied; no source/foreign file overwrite PASS|
|Missing identity/authority|Malformed source/staged metadata cannot validate; no credential/config/volume-marker/registry/Raft log created; recovery remains passive PASS|
|Backward source compatibility|Exact git-archived acea2ae source validates and disposable-SQL-roundtrips new captured schema; code rollback leaves external data/state intact PASS. No old live writer or stale DB restore claim|
|Retained versions/last copy/GC|All original3A–3C faults also execute: streamed last-copy proofs, all reference holds, nonce/quorum/term/unlink boundaries and journals/replay PASS; external backup never grants GC credit|

First new matrix FAILED1test108.635s because the intended crash hook was never
reached after an early source-readiness rejection; not counted as crash evidence.
Fixture now waits for actual measured replicas, bounds same-ID retries and requires
actual hook/process death/higher term. Corrected standalone1PASS48.793s, final54
and fresh full PASS. Initial duplicate test import/umask fixture issues are recorded
in PROGRESS and corrected without weakening assertions, budgets or product guards.

## Format / authority / provider contract

Local private0700 operator-owned store format1, store.json UUID marker, working/
and completed/ UUID bundles. Canonical manifest.json binds backup UUID, capture
cluster/epoch/index/term/authority, control/Catalog revision/digest, metadata SHA,
ALL file-version descriptors (global file UUID =immutable version identity, integer
version/label/size/SHA), explicit no writer/no secrets. metadata.json is exact full
runtime2 projection, including original node/volume IDs, lifecycle/pins/jobs/history/
3A–3C evidence. It contains sensitive credential HASHES/names/profiles/endpoints;
no raw token/private key/certificate secret/config/SQLite/Raft DB is exported.
objects/<global-file-UUID>.blob stores one streaming64KiB/size/SHA-verified body per
captured version, not every redundant physical replica. Partial data is private
transaction-owned; published objects are immutable. Hash/readback/fsync plus final
fresh current quorum check precede complete.json and controlled directory publish.
Per-object no-replace links and exact .part crash recovery support same-ID retry;
corrupt published objects are retained/refused. Capture-init interruption before
complete durable manifest/metadata may need a new capture, retaining old evidence.

Coverage is conservative ALL Catalog versions, including TRASH/EXPIRED/history/
snapshot/job references. Missing pending bytes prevents COMPLETE; no partial data
omission. Native/orphan files, private staging, raw identities/keys, uncommitted
Raft proposals and external provider key escrow are out of scope. Historical jobs
and old replica pointers are evidence, not active jobs/new live physical manifests.
Source data/replicas/pins/retention/GC unchanged; only existing scoped grant/probe
bookkeeping is used. New approved source location may supply identical immutable
content after capture; original metadata point never changes.

Destination logical protocol is provider independent; LocalDirectory is the ONLY
implemented qualified adapter. No pretend USB/NAS/S3/cloud acceptance. Declare all
source homes/locally mounted volumes; overlap/links refused. Remote paths cannot
be discovered by Controller; operator must accurately declare visible mounts.
Same-host temp directories simulate separation, NOT hardware disaster independence.
Required local semantics: POSIX dir_fd/no-follow/ownership/flock/hardlinks/file and
directory fsync. Trusted owning OS remains assumed; not a hostile-admin sandbox.
Store limits4096 entries/dir, inherited runtime2MiB and Go4096 receipts fail closed.
No encryption is invented; sensitive unencrypted store must remain private. Public
or untrusted providers require separately reviewed privacy/encryption/key handling.

COMPLETE is a historical transaction result. Offline VERIFIED requires separately
retained trusted manifest SHA, full schema/coverage/object readback and reports
verification time. Self-hash/list COMPLETE_UNVERIFIED is not authenticity. Known
minimum-index floor detects older history as STALE; absent newer witness means
latest history/RPO UNKNOWN. INCOMPLETE/CORRUPT/UNKNOWN never become0/healthy.
Retention is preview only, no automatic external deletion or physical GC credit.

Recovery is a NEW separate private root with RECOVERY_READ_ONLY.json immutable
backup/anchor/cluster/index-floor intent, exact metadata/manifest and portable
bodies, then READY.json after complete readback/source recheck. It creates NO live
DB/config/key/marker/voter/worker/server. Same-intent resume only. Its historical
Node/Cluster/Volume/File/version IDs are preserved without recreating identities
or silently resurrecting revoked credentials. VERIFIED_RECOVERY_STAGING never
means live storage placement or write authority. Old backup cannot overwrite an
active/nonempty state or satisfy a newer known index floor.

## Writer blocker / limits / upgrade and rollback

Full writable disaster recovery remains **NOT ACCEPTED**: ASC has no qualified
upstream-Raft lost-membership recovery integration, enforceable old-cluster fencing,
identity-key recovery/re-enrollment/rotation or writer activation procedure. Lost
latest external authority witness also prevents proving newest history/zero loss.
Do NOT forge epoch/quorum/Leader, edit SQLite/Raft logs/terms, copy old credentials
into runtime, reinitialize lost voters or launch a Controller on recovery staging.
This is a partial Phase3D delivery with explicit future writer-recovery blocker.

RPO reports captured timestamp/index versus operator's latest known required
checkpoint; no scheduled/zero-loss guarantee. Copy/verify/stage return measured
elapsed_seconds, not a real-media RTO SLA. Linux process death/fsync fault injection
is not hardware power-cut durability. Fresh Windows/Python runtime, Android runtime,
real phones/SD/USB/NAS/independent disks/Doze/production not tested. Android cross-
build is compile-only; CLI explicitly refuses Android/Termux/getprop/unqualified
platforms, and original Core runtime/GC/device guards stay intact.

[Operator CLI/backup/verify/recovery/rollback commands](PHASE3D-OPERATIONS.md).
Upgrade all stopped development Controllers coherently from matching source after
complete current private state/witness/byte backups. No base schema migration:
registry4/manifest1/runtime2/3A–3C unchanged. Code-only rollback preserves NEW current
state/bytes/external archives/staging; exact old source schema validation passed.
Never restore a stale database over newer history or erase retirement fences/
journals. No M51/real-device/production/system/Termux changes, membership change,
GC/failover enablement, Dashboard/APK/Remote Access or Demo/Core branch edit.

## Changed paths / continuation

asc/external/ (10 modules): bounded format, private local adapter/transactions,
provider protocol, owner pinned source/API, verify/inventory/retention, isolated
recovery and CLI. Existing asc/failover/service.py adds only3-line external route
delegation; existing business/consensus/Storage/3A–3C source and all original tests
remain unchanged. Six new tests/test_external*.py modules add30 cases. AGENTS,
README/README-VI, CODEMAP/architecture/ADR055–056/API/data/security/troubleshooting/
changelog/roadmap and PHASE3D plan/progress/acceptance/operations document contracts.
Only source/test additions and reporting are public; ignore rules are not the sole
secret defense. Final normal feature push and advertised ref proof follow final
tracked/index review; next action is separate operator/platform/writer qualification,
not redo3A–3C or silently enable production recovery.
