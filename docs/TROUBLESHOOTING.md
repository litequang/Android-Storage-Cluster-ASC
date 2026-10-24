# ASC TROUBLESHOOTING

## Phase 2B Windows development

- Metadata `invalid_snapshot` / `invalid_metadata` from a runtime: snapshots and
  deltas must keep MetadataSource's exact versioned envelope. Runtime checkpoint
  labels previously broke this contract; the response wrapper now preserves it.
  Never loosen the cache validator or recalculate a received digest to accept it.

- `controller_not_ready` / `runtime_recovering`: Follower, replay or missing
  quorum; preserve state, wait for authenticated discovery/quorum. A cached role
  cannot authorize writes.
- `stale_authority`: actual Raft term differs from the prepared activation;
  preserve stable request/job/session IDs and rediscover. Never increment a term
  in client input or reset votes to bypass this check.
- `runtime_cache_quarantined` / `invalid_runtime_projection`: stop and retain
  complete state for reviewed restore; never edit the checkpoint/document/hash.
- `attached_registry_required` / `upgrade_precondition_conflict`: runtime upgrade
  requires a stopped attached primary and exact reviewed committed metadata SHA.
  It cannot merge independent histories or replace keys/private SQL.
- Sidecar shuts down after Python dies: expected armed liveness watchdog after
  12 seconds. Restart matching complete state; never run init for recovery.
- Distributed Storage denies missing epoch/nonce/proof: provision the correct
  trusted cluster epoch and pinned bootstrap list. Never disable proof or use an
  old whole-volume grant as a fallback.
- `unmerged_controller_authority`: the original private registry is neither the
  committed primary source nor a fresh matching metadata follower. Preserve both
  histories; operator review is required. Never erase private jobs/identities or
  bypass this check to attach.
- NEEDS_REVIEW after quorum loss: a fresh exact distributed job may resume only
  when staging and final both still match. `object_requires_review` retains both
  bodies for review; never delete/rewrite an unknown copy to make retry succeed.
- Queue delayed by audit: runtime now runs due work first and limits each audit
  turn to one physical verification. Owner completion may still return PENDING;
  inspect the same persistent job until physical proof is committed.

| Symptom | Likely cause | Safe action |
|---|---|---|
| `getprop` missing on Windows/Linux | Probe is designed for Termux; other OS uses fallback | Run from Android Termux for hardware names; unknown telemetry is okay |
| `M51 PRODUCTION PROTECTED` | Hosting safeguard | Only `bash install.sh audit`; do not bypass without separate agreed deployment design |
| Termux path `~/storage/downloads` missing | Storage permission not established | `termux-setup-storage` after checking existing Termux app; Android Settings permissions |
| SD `not_tested` | Private app-specific directory absent or write probe not requested | Do not conclude card unwritable; later SAF bridge may be needed |
| `SERVER CERTIFICATE PIN MISMATCH` | Wrong controller fingerprint / MITM / regenerated controller certificate | Abort; recheck PIN via local `controller-pair`. Never disable pin verification |
| Join `invalid_or_expired_code` | Token expired/consumed/typo | Create a new `controller-pair` on controller; one-time by design |
| Agent heartbeat cannot reach controller | WLAN/IP changed, service closed, firewall, certificate mismatch | Verify LAN address and that controller-run is active; do not expose port to Internet |
| Already joined | Local identity preserved; re-run install doesn't add node | `python3 -m asc.cli status`; don't delete node.json for a retry |
| No quorum/failover yet | Raft has **not** been implemented | v0.4 only supports one controller; no production data should rely on HA claims |
| Lost `controller.json` or `node.json` | Secret/identity loss | Stop, restore private backup or controlled re-enrollment; no automated recreation/override |
| `Certificate verify` errors | Client needs exact 64-digit SHA256 PIN | Copy PIN exactly from controller; this build uses pinning instead of CA |

Never copy a live MariaDB database directory from M51 as a backup. This release does not access M51 hosting data.

## Windows v0.4.1 fixes — owner reports 40 tests OK (skipped=3)

- `FileNotFoundError: [WinError 2]` at certificate generation meant the external OpenSSL
  CLI was unavailable on PATH. Python's `ssl` module does not supply `openssl.exe`.
  `require_openssl()` now checks PATH first and raises actionable DependencyError.
  `make_cert()` invokes the resolved executable as one argv element (including paths
  with spaces), without a shell or insecure TLS fallback. If the executable disappears
  or OpenSSL fails, diagnostics stay generic; preserve partial TLS files for review.
- On this development machine `C:\Program Files\Git\usr\bin\openssl.exe` exists but
  was not in the current PATH. See README section 8 to add the verified bin directory
  in your own PowerShell session, then run Get-Command openssl / openssl version.
  No dependency was installed and no global PATH was changed by Codex.
- TLS tests are NOT skipped when OpenSSL is missing. Lifecycle TLS setup checks the
  dependency before allocating its temp directory and registers class cleanup even
  if later setup fails. Mocked dependency tests do not replace real TLS/pin tests.
- Migration fixture `with sqlite3.connect(legacy) as db` only committed/rolled back;
  it left the connection open. Windows therefore refused temp-file deletion (WinError 32).
  The fixture now uses outer contextlib.closing plus an inner transaction, with explicit
  cursor close calls. Registry.connect already commits/rolls back and closes in finally;
  migration SQL, schema 2, IDs and token semantics are unchanged.
- Regression assertions cover closed connection/cursor objects, rollback on exception,
  and immediate rename/delete with Python references still alive, without gc.collect,
  retry sleeps, forced garbage collection or suppressed PermissionError.
- Git may report dubious ownership because local .git was created by the sandbox user.
  Use per-command `git -c safe.directory=E:/CODE/ASC-QuickStart ...` for this explicitly
  trusted workspace. Do not add wildcard trust or alter global Git config. No previous
  local repository/history existed. Main/origin were prepared for the now-authorized
  v0.4.1 publication; inspect actual git status/log to determine publication state.

The earlier owner run reported 30 tests, 3 errors, 3 skipped. The new owner run is
40 tests OK (skipped=3): only POSIX installer cases are unavailable on Windows.
Source/tests are unchanged in the subsequent docs/workflow publication update, so no
redundant rerun is required. This is an owner result, not a Codex-executed run.
Current AGENTS permits local test/typecheck/lint/build: targeted tests after code
changes, then the full applicable suite before Phase completion. Keep TLS cases active,
do not weaken tests, and report concrete blockers. Android trials remain deferred.

## Phase 1.1 (0.4.1) operator errors

These entries supersede older v0.4 instructions where behavior changed. Admin CLI
now needs a running Controller; detailed commands and rollback are in README sections 2–9.

| Symptom | Meaning | Safe action |
|---|---|---|
| M51 PRODUCTION PROTECTED / DEVICE IDENTITY UNKNOWN | Protected hardware, missing Android identity or SDK below 24 | Audit only; do not override, do not install on M51 |
| Missing dependencies | Installer made no package changes | On confirmed non-M51 test phone manually install listed Python/OpenSSL packages; never pkg upgrade for ASC |
| Installed release differs | Installer preserved old source | Stop old runtimes, back up private state, use explicit separate release directory |
| controller-pair/nodes cannot connect | Admin now uses authenticated pinned loopback HTTPS | Start controller-run in another terminal; never paste admin token into flags |
| 429 rate_limited | Join budget (8/IP,60 global/min) or auth failures (12/IP,120 global/min) | Wait 60 seconds, check credentials privately; no restart-to-bypass workflow |
| 400 bad_request / 413 payload_too_large | Invalid schema/version/text/frame or body >64KiB | Use supplied CLI; do not share raw secret-bearing requests |
| credential_rejected_repair_required, agent stopped | Revoked/rotated/invalid token; no automatic reenrollment | Keep node.json, issue targeted code on Controller, stop old agent, node-repair |
| status active but node revoked remotely | status is last observation/cache | Run agent-run --once to authenticate; cache is not present authority |
| Pending enrollment after network failure | Private retry operation retained | Repeat same node-join/node-repair; do not delete pending or start another identity |
| Initial pending code expired / retry window elapsed | Need a fresh grant while preserving operation identity | controller-pair (general), repeat node-join with original destination/PIN plus --new-code; same operation maps to same ID |
| Targeted pending grant replaced/expired | Old grant no longer authorizes re-pair | Fresh controller-pair --node-id ID, then node-repair --new-code; recovery copy retained |
| Pending operation differs | Origin/pin/cluster/target do not match saved request | Preserve state; verify correct Controller. Lost initial identity: targeted node-repair with full IDs/PIN and --new-code |
| already running or lifecycle operation in progress | OS lock held | Ctrl+C in owning terminal; do not delete .lock or kill an arbitrary PID |
| .lock file remains after exit | Normal reusable lock path | status tests the actual OS lock, not file existence |
| foreground field is null | Runtime lock state could not be read/verified | UNKNOWN; check private HOME permissions without guessing whether a process is running |
| Unsupported registry/config/profile version | Newer/incompatible schema explicitly rejected | Use matching release; do not edit version numbers to bypass validation |
| Migration cluster identity mismatch / registry missing | State inconsistent/lost | Stop, restore complete private backup; no new identity/DB over existing state |
| SD status unknown | No visible readable candidate | Not proof of no card or zero capacity; no SD root writes; SAF remains future work |
| SD probe fail | Small app-folder write/readback/fsync/delete failed | No writable-tested claim; cleanup is attempted only on its unique probe file; inspect that app folder manually if media removal prevents cleanup |
| New CLI enrollment to v0.4 Controller refused | Retry-safe enrollment requires Phase 1.1 server | Upgrade Controller first; existing v0.4 agents/tokens still heartbeat upgraded server |

Malformed legacy scores are ignored for advisory ordering without rewriting saved
profiles. New malformed profiles are rejected; no score grants voter/Controller rights.

If an initial operation was already revoked/rotated, a new general code cannot recover
its authority: use a fresh targeted re-pair grant. No duplicate-registration guarantee
can identify a phone after ALL identity/pending material is lost; an admin must select
the existing node and use controlled re-pair, never blindly enroll a second identity.

Old v0.4 Controller code cannot write schema 2 and does not understand revoke. Rollback
requires the complete stopped-state backup made before upgrade, per device, plus old
source. Preserve Phase 1.1 state separately. Restoring old state may re-enable compromised
tokens; keep LAN isolated and do not claim a safe downgrade if those secrets leaked.

## Phase 1.2A storage diagnostics

| Symptom | Meaning / action |
|---|---|
| storage_root_not_empty / unsafe_storage_root | Use a new empty explicitly approved directory outside source/private manifest ancestors; never adopt a user folder or follow a junction |
| unapproved_sd_root | Root must descend from an actually detected existing Termux app folder; discovery/status proposes candidates only; SAF is unimplemented |
| volume_identity_changed | Card/root/marker differs, including a reused mount path. Preserve both media/state. Do not recreate marker, alter stored identity or bypass verification; review stopped state and restore matching media |
| volume_unavailable / VOLUME_UNAVAILABLE | Restore original root/media/permissions; unknown space is null. Restart/verify when original medium returns |
| quota_exceeded / insufficient_space (507) | Pending upload reserves staging + final copy. Retained staging and orphan objects remain charged. Keep configured free-space reserve; no automatic deletion to make room |
| upload_interrupted / INTERRUPTED | Resend full body with same session/idempotency key. No byte-range/chunk resume. Interrupted or checksum-failed body is never listed as a file |
| upload_deadline (408) / storage_busy (429) | One transfer per engine; body deadline 60 + size/rate seconds plus bounded socket read timeout. Retry after the current transfer finishes; do not increase limits blindly |
| NEEDS_REVIEW / object_conflict | Commit may have a final/partial object, or grant changed while copying. Preserve staging and final. No automatic removal/adoption; compare stopped manifest/size/hash before an explicit recovery plan |
| MISSING / CORRUPT / METADATA_CONFLICT | Startup/verify found missing bytes/hash/reference disagreement. Preserve remaining copies and manifest; do not edit paths/version to make a false success |
| forbidden (403) | Wrong node/volume/operation, expired/revoked grant or old node generation. Mint a fresh owner grant only after reviewing active identity; node token is not a user grant |
| authorization_unavailable (503) | Restore Controller reachability and correct out-of-band pin. Never disable pinning or use an offline auth bypass |
| storage already configured / existing TLS files | Preserve identity. Repeated setup does not replace config/certificates; partial initialization needs explicit recovery, not deleting keys |
| storage-status says already running | Local inspection/cleanup uses the same engine ownership lock. Stop the development Agent first, inspect, then restart; authenticated network listing remains available |

Local inspection: python -m asc.cli storage-status (stopped Agent) performs a tiny actual read/write/hash/fsync probe and bounded object inventory; it does not adopt orphan objects. storage-cleanup --older-than 86400 previews eligible staging; add --apply only after review. Committed files/final objects are never GC'd. Changed quota/kind on re-register conflicts; live quota editing is deferred.

For repeatable Windows checks use docs/PHASE1-2A-ACCEPTANCE.md. Missing OpenSSL executable remains an error, not a TLS skip. SQLite registry/manifest contexts close in finally, including exceptions; stop runtimes before copying/restoring private DB/WAL/volumes. Rolling schema 3 back requires the original complete stopped-state backup and matching old release, not a PRAGMA edit.

Windows TLS early rejection: a small oversized JSON body could trigger WinError 10053 while the client was still sending, hiding HTTP 413. Handler now discards at most 128 KiB within a bounded 2-second/1-second-read budget before rejecting; payload is never parsed or accepted. Larger/malicious streams are closed without unbounded draining.

write_denied: the root identity marker was readable but the write probe received access-denied/read-only. writable=false and fsync_tested=null; the Backup label is a read-only archival-source suggestion, not eligibility as a writable backup target or proof of any replicated copy.

## Phase 1.2B operator diagnostics

| Symptom | Meaning / safe action |
|---|---|
| no_eligible_storage (507) | No approved fresh writable volume meets double-copy quota/free reserve. Inspect catalog-status plus stopped Agent storage-status. Unknown measurements exclude placement; do not fabricate capacity |
| desired > verified or available / DEGRADED | Target policy is not satisfied. Inspect replica evidence/jobs. Multiple volumes or IDs on one approved device count once. No automatic deletion to force a healthy report |
| metadata_not_authorized (403) | Node is unapproved/revoked/protected or generation changed. Review identity; explicitly reapprove metadata permission after re-pair. Do not substitute admin token as node credential |
| node_not_approved / node_credential_changed | Stale generation, removed volume/permission or protected node. Preserve bytes, restore reviewed configuration and retry same job only after authorization is valid |
| RETRY / transfer_unavailable / no_verified_source | Network/volume/hash/authority prevented completion. Source and target checkpoints remain. Backoff runs automatically; no verified replica is added |
| FAILED | Default failed-attempt budget exhausted. Review job history, repair cause, then catalog-retry-job JOB_ID. Same job/key/session is retained. A spare eligible domain may repair; failed target domains are not cloned indefinitely |
| PENDING UPLOAD after interruption | Owner upload has not been physically confirmed. Repeat catalog-upload with original key/content/version/policy; request issues fresh short-lived authority. Do not invent ACK/proof or erase staging |
| Target wrote bytes but Controller restarted/offline | Job may be RUNNING/RETRY. Owned worker recovers/checks the same session/local ID, re-verifies bytes and records one replica. Do not manually add a fake replica row |
| Lost owner ACK | Reconcile can recover a committed manifest entry matching exact job principal/key/name, then still physically verifies it. Original upload retry is also idempotent |
| CORRUPT / MISSING / METADATA_CONFLICT | Preserve suspect objects and metadata. Reconcile marks discrepancy and queues replacement only from a valid readable source. If no source remains, report unavailable; no fabricated recovery |
| UNAVAILABLE / removed SD | A volume is not a readable source/target. Keep the original medium and marker. Restore it or heal to another approved physical domain; no reused-path reinitialization |
| revision_gap / resync_required | Missing/compacted history. Node keeps last verified cache and fetches a new consistent pinned snapshot. At most 1024 history revisions are retained |
| snapshot_digest_mismatch / same-checkpoint conflict / epoch or lower revision conflict | Preserve the prior cache; inspect Controller consistency/restoration plan. Do not edit revision/digest/epoch or accept a lower checkpoint blindly |
| inventory_truncated | Work/report bounds were reached. Reconcile persists per-volume offsets/rotation and continues later; output is not proof that unreported files are absent |
| uncatalogued / unreferenced objects | Standalone v0.5 file or ambiguous body lacks a global reference. Report/retain it. Automatic import/GC is not part of this phase |
| Worker already owned | Stop the owning development Controller normally. Do not delete .lock or run another independent writer |
| Long file verification times out | Job/client timeout must cover source/target multi-pass hashing and rate limits. Set reviewed controller-run --job-timeout 30..900 and --catalog-rate 65536..67108864; never disable SHA checks to finish faster |
| v0.5 Agent cannot join global placement | Global status/inventory/scoped jobs need v0.6 Agent code. Old lifecycle and standalone owner storage stay compatible. Upgrade Controller/source separately with private stopped-state backup |

Use catalog-status, catalog-jobs and catalog-job JOB_ID for current evidence; catalog-reconcile requests bounded scanning. catalog-run-job [JOB_ID] runs one due attempt on the owned worker. catalog-sync and catalog-local-status/files/file inspect verified metadata; local cache never becomes a writer and available-replica count is unknown offline.

The Controller defaults to one transfer and 4 MiB/s relay/readback; Agents retain their own quota/rate/one-transfer limits. An owner upload ACK may return pending when the background worker is busy; wait for verified counts rather than declaring replication from job existence.

Rollback details: DATA_MODEL and README section 12. Stop all development processes, retain current state/objects, restore the complete pre-upgrade schema-3 backup and v0.5 source together. Newer cache checkpoints intentionally refuse an older Controller. There is no automatic epoch reset or distributed recovery authority in this phase.

Catalog state/epoch missing in schema 4: stop and restore the complete reviewed stopped-state backup. Do not run initialization to create a fresh epoch over existing replicas or edit the schema version.

## Phase 2A engine qualification — blocked

- tools/qualify_pysyncobj.py --download returning exit 1 and qualified=false means the upstream candidate failed ASC safety gates. Current 0.3.17 result is one passing clean-restart probe and five failed gates; this is not a failing ASC production service and must not be relabeled PASS/SKIP.
- Missing/corrupt .meta in the isolated probe loses a prior vote and emits a second same-term vote. Never repair actual consensus state by deleting metadata or resetting term/vote. ASC has not integrated this engine; no production Raft recovery command exists.
- Exit 2 / qualification_inconclusive means download, checksum, import or probe execution failed. Preserve the error classification; verify the official artifact/network/environment instead of changing the pinned hash or installing packages automatically.
- No matching rraft-py 0.2.27 Windows CPython-3.14 wheel was published in the inspected release. go/rustc/cargo were absent from process PATH; no WSL distribution was listed. This is a development qualification blocker, not proof that Android cannot support Raft. Do not auto-install a toolchain or use phone production state to investigate.
- Existing v0.6 Controller remains single-writer with raft_enabled=false; it cannot elect a replacement or grant strong quorum reads. Metadata caches never promote themselves. Do not run independent copied Controllers against the same logical history.

Reproduce evidence and review alternatives/rollback in PHASE2A-ACCEPTANCE.md. A fresh unchanged-runtime full suite passed 92 tests (3 POSIX skips); no Phase 2A quorum/partition/snapshot acceptance has run.

## Go metadata consensus continuation

The preceding Phase 2A block is historical PySyncObj status. Current tests,
qualification and publication status: PHASE2A-ACCEPTANCE.md continuation.

| Symptom | Meaning / safe action |
|---|---|
| Go toolchain required / no executable on PATH | Set process-local ASC_GO to an official checked Go executable; no consensus test may silently skip. Portable development location is documented in GO-SIDECAR.md |
| Android build `undefined maxMapSize` | Backend transitive bbolt v1.4.1 had an upstream Android compile bug. Current module pins v1.4.3; run go mod verify, do not patch module cache or downgrade the pin |
| Sidecar refused / quarantine | Missing/corrupt/mismatched state, anchor, witness, seed, snapshot, membership or duplicate ownership. Stop; restore the complete reviewed private backup. Do not delete DB/.meta/witness or run init to recover |
| init refuses after whole directory loss | The external .enrolled witness correctly prevents known-voter reset. Rebuild/rejoin is not implemented; retain all remaining state for reviewed recovery |
| consensus_seed_mismatch / import refused | Existing metadata differs from the original canonical seed or target has history. Export a consistent stopped primary; import only to an explicitly fresh matching-cluster registry. Never merge independent nonempty epochs |
| consensus_required / SQL not authorized | Distributed registry is fenced. Use metadata API/adapter, never remove triggers or register the apply function on a normal writer |
| consensus_guards_missing / projection_quarantined | Restore complete consistent checkpoint/projection/receipt state. Do not edit index/digest/rows or recreate missing guards blindly |
| stale/recovering after Go restart | Python serves its last verified checkpoint while Go catches up. Restore quorum and wait; this cache cannot grant write authority |
| quorum_read_unavailable / commit_unconfirmed | Follower, missing quorum or interrupted commit. No success is established. Inspect authenticated status leader_id as a hint, retry SAME intent/request ID against the legitimate Leader after quorum recovers |
| request_id_conflict | Same ID used for another intent. Preserve original receipt; choose a fresh ID for a genuinely new request |
| precondition_conflict | Another committed document won the prepared SHA. This rejection is itself a durable receipt. Read current state and prepare a new request ID after inspecting the conflict |
| receipt_limit | 4096 permanent receipts reached. New requests fail; no safe automatic eviction/reset protocol exists. Preserve state; future reviewed protocol required |
| distributed_fencing_required / old grants rejected | Intentional metadata-only limit. No upload/download/job/reconcile/grant or private-registry failover. RUNNING job records remain frozen, never treated as complete |
| Android runtime refused | Cross-compiled artifact is not Android runtime acceptance. Do not install/run it on a phone in this task |

Actual durable sync on this Windows filesystem required election budgets larger
than subsecond in-memory fixtures. Current heartbeat/election/leader-lease values
are 3/6/2 seconds. Tests wait for quorum Barrier/application conditions instead of
asserting a fixed elected ID or disabling fsync. Go timers remain randomized.

Rollback requires stopped/isolated complete pre-attachment private backups and
matching source, retaining current metadata/objects separately. Full instructions
and exact commands: GO-SIDECAR.md and DATA_MODEL.md. No production/phone recovery
was attempted.

## Phase 3A backup/restore diagnostics

- phase3a_not_enabled: upgrade every stopped development Controller to matching
  source, preserve complete private backups, then explicit backup-enable.
- invalid_backup_projection: preserve full state; restore reviewed consistent
  backup. Never edit manifest digests, source indices or tombstones to accept it.
- snapshot_unverified_head: latest version lacks verified replica evidence; finish
  its existing upload before capture. Older versions are not silently substituted.
- copies_pending: ordinary Catalog COPY jobs have not met requested domains yet.
  Inspect existing jobs/probes/space; backup is not VERIFIED. No data is removed.
- backup_unavailable/restore_unavailable: checksum, node, quorum or transfer failed;
  checkpoints and original bytes remain. Repair cause; use same-job explicit retry
  after five failed attempts. NEEDS_REVIEW still requires exact retained hashes.
- version_not_live/version_expired: ordinary download denied by logical lifecycle.
  Restore a retained version or a retained snapshot reference into a new version.
- restore_version_reserved: an existing restore owns that logical version; use a
  different explicit upload version or complete/retry the same restore job.
- Stale backup lease/Controller failure: new Leader invalidates leases, preserves
  snapshot/reserved version/upload key and rechecks bytes. Do not reset state.
- Logical retention does not free disk space. Final immutable objects remain;
  capacity exhaustion is explicit. Physical GC requires separate qualification.
- Projection/receipt limits fail closed. No automatic history eviction exists.

Due captures with an unverified head or exhausted snapshot/job bound record a fixed
schedule last_error and retry time; existing jobs continue. Retrying a logically
expired source is refused, preserving the same restore eligibility rules.

The supplied base commit omitted `consensus/cmd/asc-raft/main.go`: the unanchored
asc-raft ignore also matched the source directory. The source launcher is now
tracked and calls the existing validated init/run APIs; no Raft module is rewritten.

## Phase 3B node insights

- phase3b_not_enabled: upgrade all stopped development Controllers, retain complete
  private backups, then owner POST nodes/enable with a stable request_id.
- UNKNOWN/low confidence: missing/stale/future/unapproved inputs or history gaps;
  inspect source times and counts. Never substitute preset RAM/readiness scores.
- node_history_limit/node_request_limit/runtime_projection_limit/receipt_limit:
  bounded state exhausted; preserve authority and existing backups. No automatic
  receipt eviction/reset. Hourly sampling reduces growth but does not remove the
  inherited Go 4096-receipt lifetime limit.
- Re-paired node: retained prior-generation history does not score the new identity.
  No history or credential is silently rewritten to manufacture continuity.
- Avoid/Drain/Protected can intentionally cause no_eligible_storage or an explicit
  replica deficit; Preferred never overrides protection/capacity/domain gates.
  Existing authorized jobs may finish; Drain does not move or delete stored bytes.
- Linux CLI integration tests use an explicitly permitted fake hardware profile.
  Real unknown hardware remains refused; do not add a product bypass for Cloud.
- Real Python failover entrypoint is still Windows development only. Cloud fault
  suites use a synthetic test launcher with a module-local platform/profile mock;
  do not copy it into production or add a runtime bypass. A startup refusal in a
  plain Linux launch is expected. Use existing `/workspace/asc-cloud/activate.sh`
  in this Cloud environment to select Go 1.27.3/Python 3.13.5, not `/usr/bin/go`.

## Phase 3C development

- phase3c_not_enabled: matching all-Controller upgrade/private stopped backup before
  explicit owner replication/enable. No implicit schema upgrade or GC activation.
- no_independent_eligible_target: Drain can remain blocked by actual quota/domain/
  status/policy. Keep source; wait for measured fresh probes, not a fabricated ACK.
- copy_not_verified/survivor_verification_required/survivor_proof_changed:
  source is retained; finish the same COPY job and obtain current independent
  served-byte proof. A terminal FAILED job needs explicit existing retry.
- retired_object_reintroduction: preserve retirement journal and remaining copies;
  never re-adopt an old local ID/clear the fence. Use a new stable COPY job/object.
- Logical retirement frees no disk by itself. History/job/grant/snapshot pins can
  legitimately keep all retired bytes; future GC must enumerate these holds.
- gc_existing_volume_not_adopted/physical_gc_platform_locked: intentional isolated
  Linux x86 fresh-volume boundary; never create a marker/flag to convert real data.
- gc_journal_quarantined/gc_journal_conflict/gc_unknown_absence: retain complete
  state and original bytes; restore reviewed matching journal/volume backups.
  Never delete/edit the journal to claim an object was safely removed.
- gc_checksum_mismatch/gc_object_identity_changed/unsafe_gc_test_arena: preserve
  original and replacement/link targets; no recursive cleanup or identity override.
- gc_authority_budget_expired: final local work exceeded the short fresh-proof
  budget; no unlink occurred. Retry with a newly authorized same immutable intent.

- gc_execution_unconfirmed / gc_completion_unconfirmed: the remote result or its exact scope is unconfirmed; retain Controller reservation and Node journal. Retry the same gc_job_id after current quorum/proofs recover; do not mint another target, edit DONE or delete the journal.
- gc_permit_rejected / gc_permit_changed / gc_scope_rejected: expired or replaced run, changed identity/approval/endpoint or wrong exact scope. Only the explicit owner execution may renew a permit; never change term/schema/token fields manually.
- Missing/nonexistent test arena now returns unsafe_gc_test_arena consistently on Windows too. It never creates/adopts that directory or grants capability.

- Windows metadata regression initially failed its no-fallback stderr assertion because the unconfigured real PC correctly hit DEVICE IDENTITY UNKNOWN first. Synthetic launchers now supply a permitted fake profile on both platforms; do not relax the assertion or change the product hardware/config guards.

- stale_gc_proof: current references or endpoint/approval graph changed during checksum streaming. Preserve the reservation and retry the same job for new proof. Never accept a former endpoint checksum under a new pin.

- A heartbeat can legitimately stale an exact confirmed plan. Reprepare/reconfirm its new SHA; retain old plan receipts. The isolated fault harness bounds these retries and never treats a denied attempt as successful physical/lost-ACK evidence.

Linux GC qualification with a full 1024-event history can expose repeated expensive
structural checks and stale plans under CPU contention. Exact-byte structural reuse
reduces repeated work; it grants no authority. Run heavy fault matrices serially,
reprepare stale exact plans and obtain new proofs, preserving the 10s callback and
250ms local budgets. Never clear history or extend freshness limits to get PASS.
Synthetic-only pause/crash/stack controls live in tests/gc_fixture.py, not runtime
config or product endpoints.

## Demo installer preview refusal
Run `sh scripts/demo-alpha.sh preflight` for read-only dependency/device/SD status.
Missing or non-working OpenSSL/Python/pkg requires owner review/manual preparation;
no automatic installation occurs. Protected/unknown devices have no override.
Checksum, existing unmarked prefix, modified source or symlink refusal means stop
and preserve directories; do not delete identities or overwrite source. An exact
package rerun resumes a partial code install. Different releases need a later
explicit stopped upgrade, never an installer overwrite.
