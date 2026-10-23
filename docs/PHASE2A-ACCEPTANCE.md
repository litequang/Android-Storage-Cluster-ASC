# Phase 2A — engine qualification BLOCKED (v0.7.0 not released)

Date: 2026-10-23. Accepted runtime/base remains v0.6.0 at b645e539f737c461aaa112a51f6627ef0da80d92. Initial working tree was clean on main tracking origin/main.

This is an engine-selection and integration-audit report, **not Phase 2A acceptance**. The task section 3 requires reporting unsuitable libraries and alternatives before a homegrown solution. No candidate in the evaluated set has passed ASC's complete engine gate in the available environment. No Raft algorithm, consensus mode, migration, RPC listener, elected ASC Leader or automatic failover was added. Phase 2B has not started.

## Executed evidence

- Fresh Codex Windows regression: **92 tests, OK (skipped=3), 106.154 seconds**: 89 PASS / 0 FAIL / 0 ERROR. Only the three pre-existing POSIX installer cases skipped; no TLS/storage/Catalog case skipped. This run is independent of the earlier 106.317-second v0.6 acceptance.
- Engine qualification: **6 probes: 1 PASS / 5 FAIL / 0 SKIP**, exit code **1** (rejected), against the unmodified official PySyncObj 0.3.17 sdist.
- Python 3.14.7, Windows AMD64. PySyncObj, raftos and rraft are not installed. go, rustc and cargo were not found on process PATH. wsl --list --quiet returned success with no distribution listed; no WSL instance was started or installed.
- OpenSSL for regression was supplied only in the child test process PATH from the existing Git for Windows bin directory. No system/global PATH or packages changed.
- Probe package source and damaged fixture journals existed only inside TemporaryDirectory, with SHA verification before import, no setup.py/pip execution, no network listener and no ASC private state access. The optional artifact download uses ordinary verified HTTPS, never the ASC certificate-pin bypass pattern.
- No M51, phone, production logs/database/private state, installer or production server was accessed.

Reproduction in a development PowerShell terminal:

```powershell
Set-Location E:\CODE\ASC-QuickStart
python -B tools/qualify_pysyncobj.py --download
# Above returns 1 with qualified=false; it must NOT be reported as PASS.
# Offline alternative with an already downloaded official artifact:
python -B tools/qualify_pysyncobj.py --archive C:\PRIVATE_DEV\pysyncobj-0.3.17.tar.gz

$env:PATH = "C:\Program Files\Git\usr\bin;$env:PATH"
python -B -m unittest tests.test_catalog -v
python -B -m unittest tests.test_distributed -v
python -B -m unittest discover -s tests -v
```

The actual full-suite driver was python -B with process-local PATH, sys.dont_write_bytecode=True and unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover('tests')); exit status reflected wasSuccessful(). No separate configured lint/typecheck/build pipeline exists. Probe CLI help, invalid-artifact rejection and Python AST/diff checks are checked separately; see final work report for those results.

## PySyncObj source and qualification

[Official PyPI 0.3.17](https://pypi.org/project/pysyncobj/0.3.17/), MIT. Download SHA-256:
8aaef68141714d556173778a51bcc4e221b6fd4c971dc1240f3ab4c0d2dfe765.
The probe pins this hash and copies only immediate Python modules into temporary private test state. No upstream implementation is vendored or patched.

The upstream [term/vote fix PR #202](https://github.com/bakwc/PySyncObj/pull/202) was merged in August 2026. Rejecting the candidate merely on older versions' missing persistence would be inaccurate: this release does persist term and vote on ordinary restart. The remaining ASC requirements still need more than that fix.

| Sampled gate | Actual observation | Result |
|---|---|---|
| Ordinary clean restart retains vote | term 7 and original peer retained | PASS |
| Missing .meta refuses participation | After removing only the closed fixture metadata file, engine starts and grants another peer a vote in term 7 | FAIL |
| Corrupt .meta refuses participation | Invalid metadata bytes are swallowed; engine starts and grants another peer a vote in term 7 | FAIL |
| Term/vote synchronization boundary | setCurrentTerm returns with zero os.fsync calls | FAIL |
| Log synchronization boundary | FileJournal.add returns with zero mapping.flush calls | FAIL |
| Default peer identity authentication | Incoming handshake accepts a configured address claim without credential with password=None | FAIL |

Root causes in the **hash-verified upstream artifact**, not ASC runtime:
- journal.MetaStorer.getMeta catches all load failures and returns an empty mapping. FileJournal defaults term/vote; SyncObj recovers term from the last log term but cannot recover the already cast vote. The deterministic probe seeds a real index-1/term-7 NO_OP plus a vote for peer A, closes it, damages only .meta, then supplies a fresh-log RequestVote from peer B at term 7 through the engine's actual transport callback. A response_vote is emitted for B.
- MetaStorer.storeMeta flushes Python buffers then moves the temporary file, without fsync. FileJournal.add updates the mapping/header without flushing before returning. These are synchronization-call observations and source inspection, **not measured physical power-cut data loss**.
- TCPTransport's default password=None handshake maps a caller-provided configured address to a peer. The optional group password is neither ASC per-voter identity nor pinned TLS. A new identity-authenticated transport is necessary. No unauthorized real-network RPC or exploit was sent.

A production wrapper/fork could address some gaps, but none is supplied or certified here. Replacing safety-critical persistence/transport, validating missing-state bootstrap and retesting snapshots/restarts would be a substantive integration decision. Existing single-writer Catalog remains unchanged while that decision is pending.

## Alternatives evaluated, not certified

| Candidate | Version/license/source checked | Suitability / blocker |
|---|---|---|
| PySyncObj | 0.3.17 / MIT / official sdist hash above | Pure Python, replicated methods, journal, snapshot and injectable transport; actual qualification failures above prohibit adopting it unchanged |
| raftos | 0.2.6 / MIT / official PyPI zip SHA-256 489449fbd3baa677fea55d8068de2c83a46d63c7db5758d79ccc8229076e3c80 | Source rewrites FileDict directly and appends log without fsync; missing files are created. Requirements pin cryptography==1.5.3 and msgpack-python==0.4.8. No qualifying snapshot/recovery/modern Windows+Termux integration established; not installed or executed |
| rraft-py / tikv raft-rs | rraft-py 0.2.27 / Apache-2.0 / official PyPI metadata and binding README | Transport/persistence remain application work. Published 0.2.27 files are one CPython-3.11 macOS-arm64 wheel and sdist, no matching Windows CPython-3.14 wheel. Rust/maturin build and Android ABI verification are unperformed; Rust tools absent from PATH |
| etcd-io/raft | v3.7.0 / Apache-2.0 / Go module metadata and upstream README | Best next investigation for deterministic Step/Tick, ReadIndex, PreVote and quorum checks. Go sidecar/binding, durable storage, authenticated transport and Windows/Android artifact validation still required; no Go executable on PATH |
| hashicorp/raft | v1.8.0 / MPL-2.0 / Go module metadata and upstream README | Alternative FSM/log/snapshot implementation; needs Go integration, a reviewed durable backend and authenticated transport. No ASC or Android acceptance performed |

Primary sources: [raftos release](https://pypi.org/project/raftos/0.2.6/), [raftos storage](https://github.com/zhebrak/raftos/blob/master/raftos/storage.py), [rraft-py](https://github.com/lablup/rraft-py), [rraft-py release](https://pypi.org/project/rraft-py/0.2.27/), [etcd raft](https://github.com/etcd-io/raft), [HashiCorp raft](https://github.com/hashicorp/raft).
Go versions were read from proxy.golang.org module @latest metadata on the report date; they are investigation candidates, not locked ASC dependencies. Latest repository READMEs are orientation, not evidence of Windows/Android certification.

Recommended next decision: evaluate an etcd/raft Go sidecar with an explicitly authorized development toolchain and reproducible Windows/Android builds. Alternative: retain Python via a separately reviewed pinned PySyncObj fork with durable journal/fail-closed bootstrap and per-voter TLS transport. Neither option is implemented; do not substitute a new homemade election algorithm. This is not a claim that every available library is unsuitable or that Android installation is impossible.

## Actual Catalog integration audit

| Current write / state | Location | Consensus preparation required |
|---|---|---|
| CREATE file, upload job | service.upload_plan -> state.Catalog.mutate CREATE | Prepare IDs, timestamp, placement and immutable request fingerprint before proposal; reserve capacity safely; publish response only after committed apply |
| POLICY | http.handle -> Catalog.mutate POLICY -> schedule | Committed deterministic policy; prevent direct endpoint bypass |
| COMPLETE replica/job | service._execute -> physical _proof -> Catalog.mutate COMPLETE | Physical work outside apply; validate fenced prepared evidence; remove dependence on nonreplicated queue/clock at voter apply |
| REPLICA_STATE | service._bad_replica -> Catalog.mutate | Commit discrepancy command; consistent timestamp/no-op behavior |
| REVERIFY | service.reconcile -> Catalog.mutate | Commit prepared verification evidence; no network during apply |
| Materialization/event/history | state._event, _new_job, _history | uid(), now(), live candidates, node rows, lease clock and job state currently differ between independent Controllers |
| Registry/lifecycle, node approval/probes/metadata ACK | store.py; service.register/refresh/metadata_ack | Unreplicated authority today; no complete Controller failover claim |
| Jobs/leases/grants/inventory cursor | queue.py; grants.py; service.py | Unreplicated runtime state; storage writes/automatic job failover must remain disabled in any future metadata-only consensus mode until distributed fencing is accepted |
| Local manifest / storage objects | storage/manifest.py, engine.py | Remain local; never replicate private identity/key or treat cache as canonical writer |

No application write is currently quorum protected. All old v0.6 paths remain single-writer, raft_enabled=false. A future consensus mode must centrally prohibit direct Catalog.mutate and every alternate writer, not add an is_leader check only to one HTTP route. No runtime consensus switch exists in this work.

## Required integration contracts (design only)

- Deterministic command v1: immutable cluster/epoch, request ID, schema, expected revision, explicit IDs/timestamp/validated payload and canonical payload digest. Preparation performs randomness/clock/placement/proof; apply uses only the committed command and replicated preconditions. Idempotency receipts bind request ID to payload/result and must survive retries, snapshots and crash.
- Persist applied index/term, request receipt and Catalog materialization/event in one transaction. Replay of an already applied entry is a no-op with identical result; conflicting index/request payload fails closed. Catalog revision maps explicitly to Catalog-changing committed entries; Raft no-ops do not fabricate file events.
- Strong reads need the engine's safe quorum read barrier/ReadIndex and local applied index at least that barrier. is_leader, last heartbeat, high term or a cached leader address is insufficient. Existing cache reads remain stale/read_only with known revision/sync time.
- Private bootstrap record binds cluster/node identity, static three-voter membership, engine/schema versions and initial imported Catalog digest. Restart requires matching state and exclusive node ownership; missing/corrupt state stops participation. No automatic single-node reset. Do not import three independently initialized epochs as one history.
- Keep public metadata schema-1 consumers compatible via an explicit consensus snapshot envelope containing cluster/membership/index/term/materialized digest, receipts and applied checkpoint. Public Catalog digest alone is not a Raft snapshot. Install atomically; verify before replacing; retain logs until durable validated snapshot/catch-up is accepted.
- Dynamic membership, learner promotion/removal, leadership transfer and quorum-loss rebuild need engine-supported operations with safety tests. Until implemented, their APIs remain unavailable. No local voter-list editing or single-node write recovery.
- Freeze physical transfer/grant automation during metadata-only leader failover until agents can reject stale side effects with quorum-established fencing. Late proof/ACK must not create a Catalog event outside committed apply. Term alone is not authority.

These contracts have no new wire endpoint, database/schema number or enabled feature yet. See ARCHITECTURE, DATA_MODEL and NODE_PROTOCOL for the preserved implemented boundaries.

## Requested Phase 2A acceptance matrix

Every item below is **NOT RUN / BLOCKED at engine selection**, not PASS or SKIP. Existing v0.6 tests and six engine probes do not cover these requirements.

| # | Required three-voter proof | Status |
|---|---|---|
| 1 | Initial one-Leader election | NOT RUN |
| 2 | Commit with 2/3 | NOT RUN |
| 3 | New Leader after Leader stop | NOT RUN |
| 4 | Old Leader returns as follower | NOT RUN |
| 5 | One voter cannot commit | NOT RUN |
| 6 | Partition 1/2 minority cannot commit | NOT RUN |
| 7 | Competing candidates cannot confirm conflicting histories | NOT RUN |
| 8 | Stale log cannot win against fresher quorum | NOT RUN |
| 9 | Committed metadata survives restart | NOT RUN |
| 10 | Duplicate command applies once | NOT RUN |
| 11 | Delay/reorder/drop preserves committed order | NOT RUN |
| 12 | Snapshot/follower catch-up preserves committed data | NOT RUN |
| 13 | Catalog API/internal writer bypass denied in consensus mode | NOT RUN |
| 14 | Follower stale read reports exact revision | NOT RUN |
| 15 | Unauthorized Raft RPC denied | NOT RUN |

## Files, publication, rollback and next gate

Added tools/qualify_pysyncobj.py and this report; updated CODEMAP, ARCHITECTURE, DECISIONS, DATA_MODEL, NODE_PROTOCOL, SECURITY, TROUBLESHOOTING, CHANGELOG, IMPLEMENTATION_PLAN and README-VI. Runtime asc/ and tests/ remain exactly at the accepted base; release stays 0.6.0 with registry 4, local manifest 1 and metadata cache 1. No runtime dependency added.

No commit, stage or push is performed because Phase 2A acceptance has not passed. Last accepted/published runtime commit remains b645e539f737c461aaa112a51f6627ef0da80d92; remote publication is not inferred for a new release. Git/secret review of this development diff is recorded in the final report.

Rollback of this investigation requires only reverting its documentation/tool changes after review. It made no migration or runtime-state change, so no database restore, credential reset or object deletion is needed. Do not use destructive git reset/clean against unrelated work. Earlier v0.6-to-v0.5 rollback remains a separate stopped-backup procedure.

Phase 2B is **not ready**. Resume Phase 2A after choosing/authorizing an engine integration route, passing engine persistence/identity/platform gates, implementing deterministic Catalog application and executing all fifteen fault cases plus the entire regression suite. No production/phone automatic failover is authorized.

Final development review: all 60 tracked files and both new files were inspected for sensitive filenames and private-key/GitHub/AWS credential patterns; no matching material found. Staging is empty. All Python ASTs parsed and git diff --check passed. Historical changelog content is preserved; asc/ and tests/ match HEAD. Probe --help exited 0; an invalid local artifact was rejected before import with qualification_inconclusive and exit 2. Existing .gitignore was reviewed and needed no change for the temporary-only probe. No commit or push occurred.
