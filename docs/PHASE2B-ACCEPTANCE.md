# Phase 2B — Controller failover: Windows development accepted, 2026-10-24

Base: `d6b540dfc989f41470eaf9c7e0a29e3abf797f24`, existing
`wip/phase2a-raft-qualification`. No phone, M51, production, Dashboard or gateway
access is authorized. Historical PySyncObj **1 PASS / 5 FAIL** is unchanged.
Phase 2A acceptance is metadata consensus; it is not Phase 2B acceptance.

## Final Windows acceptance

Codex-run `python -B -m unittest discover -s tests -v` on Python 3.13.15:
**101 tests OK, 98 PASS / 3 SKIP, 0 FAIL / 0 ERROR, 1736.964 seconds**.
All **20/20** fault scenarios below PASS in that same full regression, including
real pinned metadata snapshot/delta imports before/after takeover and after
snapshot/restart. The three skips are the unchanged Linux/Termux Bash installer
cases; no TLS, consensus or failover test is skipped. Final Go/build checks below
remain valid because their source did not change afterward.

After a client restart, one earlier full-run result could not be recovered and
was not counted as PASS. The successful rerun writes durable UTF-8 log, JSON
result and per-file SHA-256 manifest outside Git under
`%LOCALAPPDATA%\ASC-DevTools\phase2b-checks\python-full-20261024-000811.*`.
The JSON records exit 0 and identical before/after worktree fingerprints:
`1458f34ebeb5c29041b9cc28a4d365f3088d808cddabd92ff15273259e62da3b`.
That fingerprint includes then-provisional documentation; only documentation
acceptance labels/results are updated after testing. Source and tests stay frozen.
The existing Git OpenSSL directory was added only to the qualification child's
PATH; no system environment, phone or production state was changed.

### Publication review

Pre-stage review scanned all 89 source paths and the prior 80-file index. After
staging, all **89 tracked/index files** and **37 changed paths** were reviewed:
no private-key, GitHub/AWS/service-token/literal-bearer credential matches or
sensitive runtime/database/key/object paths. All 55 Python ASTs, Go formatting
and staged diff checks PASS. Ten synthetic private/runtime filenames are ignored;
no tracked path conflicts with ignore rules. AGENTS, Phase 2A acceptance and the
PySyncObj tool retain their exact starting Git blobs. Source/test hashes match
the qualified manifest; the 11 subsequent changed files are documentation only.
Publication uses the existing WIP branch with a normal commit/push, preserving
remote history and main. The resulting commit/remote verification is reported in
the completion message rather than embedding a self-referential commit hash here.

## Readiness audit before implementation

Source audit: consensus/{fsm,node}.go, asc/consensus/{adapter,projection,service}.py,
asc/store.py, asc/catalog/{schema,state,queue,grants,service,placement}.py,
asc/storage/http.py, asc/catalog/client.py, asc/cli.py and asc/server.py.

| State | Before | Evidence / required treatment before automatic activation |
|---|---|---|
| Global Catalog and event history | A | Canonical prepared projection, CAS, receipts, atomic checkpoint; preserve epoch/revision/history |
| Registry and identity | C | nodes are private SQL rows; replicate identity, current credential HASH, generation and revocation atomically; never private keys/raw bearer |
| Enrollment / re-pair / revoke | C | join_codes/enrollments private; replicate consumed-code and permanent operation routing in the same prepared transaction; only retry-safe enrollment for distributed mode |
| Grants | C | transfer_grants/storage_grants private; old grants frozen; invalidate at activation and reissue from current committed jobs, store hashes only |
| Replication queue | C | catalog_jobs/history private; replicate stable job/key/checkpoints and bounded history before physical IO |
| Idempotency | A/C | Catalog metadata receipts A; lifecycle/job routing C; retain both in the authoritative runtime document |
| Job leases | C | OS worker lock is local; bind activation to actual Raft log term, reset unfinished leases and invalidate grants on committed takeover |
| Storage policy | A/C | File policy A; approvals, domains, quotas/probes C; replicate approvals, refresh physical measurements before placement |
| Cluster configuration | A/C | Static pinned Go voters A; Python Controller endpoints C; provision an explicit pinned bootstrap allowlist, never learn trust from redirects |
| Metadata snapshots | A/C | Go snapshots preserve metadata + receipts A; runtime authorities C and must enter the same snapshot; public read-only caches never confer authority |

Local manifests, immutable object bytes and TLS/private IPC/admin/node secrets
remain node-local. Physical evidence must be reacquired, not inferred from a
snapshot. Unknown telemetry remains null. A restored old registry is never a
fallback writer.

## Design for unsafe state (before enabling failover)

Use the existing prepared-document CAS engine, not another consensus algorithm.
A versioned runtime envelope will carry the existing validated Catalog document
plus an explicit allowlist of SQL authority rows (hashes, not raw credentials),
an independent control revision, and the committed activation owner/term.
Existing Catalog revision semantics remain unchanged for control-only mutations.
Prepare existing business transactions against a fresh isolated in-memory SQL
projection; apply installs only validated committed bytes/checkpoints. Never
remove the original Phase 2A registry guards to run legacy writers.

Every runtime command must match its actual Raft apply term. A new Leader first
commits takeover, invalidates old grants, resets unfinished leases while retaining
session/object IDs, and verifies quorum/application before reporting write-ready.
Follower/Recovery cannot issue grants, complete jobs or do storage automation.
Loss of the Python Controller must also withdraw its sidecar's candidacy through
an authenticated local liveness watchdog; otherwise a live sidecar could keep
electing a dead Python Controller indefinitely.

Storage authority is online, pinned, per-operation and freshly checked again
before Engine visibility. The proof binds epoch/activation term/committed index,
grant hash, exact resource and fresh request identity; a supplied term or cached
Leader is never sufficient. Already authorized immutable IO may finish, but
publication requires current quorum authority. Destructive APIs remain absent.
Ambiguous staging/objects are retained and physically reverified. Execution is
at least once with stable object/session keys, not exactly once.

Discovery uses only preapproved endpoint/pin identities, bounded TTL/retries and
backoff. Local stale reads expose the exact Catalog revision and applied index.
Scores cannot change authority; keep a healthy Leader, with no score-driven
transfer until separately qualified. M51 and protected/unknown hardware are
excluded by existing runtime guards.

## Implementation history (status at each recorded run)

The provisional and failed runs in this section are preserved as history. The
final full-regression result above supersedes their pending acceptance statuses.

Implemented development paths: `asc/failover/{state,runtime,discovery,service,cli}.py`,
opt-in existing owner/Agent transports, runtime command term/owner enforcement,
and authenticated Python liveness withdrawal. Original registry guards remain
untouched. Source identifies as 0.8.0 development; this version alone does not
establish acceptance or authorize publication before the complete gate.

Preparation/validation uses deterministic disposable SQL initialization, never
sampling a clock/random source during committed projection installation. A
successful ApplyFuture already proves quorum/application: the runtime checks the
exact local receipt rather than committing redundant barriers after each write.
Each outer operation starts with a fresh Barrier; every subsequent mutation is
still CAS/actual-term checked at commit. Storage authority separately commits a
fresh nonce-bound receipt. Coalesced measured probes expire within ten seconds
and are invalidated by takeover; they are not authority or fabricated telemetry.

Private configuration (never put these files in Git):

- Runtime file schema 1: exact `schema`, absolute `home`, absolute
  `consensus_config`, numeric private/loopback `host`, and `port` 1024..65535.
  HOME contains its own `controller.json` admin credential and server TLS key.
- Agent node.json keeps its identity/token plus `cluster_id`, pinned
  `cluster_epoch`, and `controllers`: up to three preapproved
  `{node_id,origin,pin}` entries. Owner bootstrap uses distinct per-endpoint
  `token` fields instead. Do not copy owner credentials to an Agent.
- Explicit stopped development conversion:
  `python -B -m asc.failover.cli upgrade --registry PRIVATE_REGISTRY --consensus-config PRIVATE_GO_CONFIG --expected-sha256 REVIEWED_METADATA_SHA`.
  Use the current Leader's authenticated local IPC and exact source metadata.
  Same upgrade ID/intent replays its original receipt, including after lost ACK.
  It never initializes or changes Raft membership/state bindings.
- Run each corresponding Windows development Controller:
  `python -B -m asc.failover.cli run --config PRIVATE_RUNTIME_CONFIG`.
  Existing Go init/run/config remain unchanged. A configured local Storage runtime
  uses its own existing manifest/TLS/volume and node credential. Unknown Android,
  all Android runtime, and protected profiles remain refused.

Executable qualification command:
`python -B -m unittest tests.test_failover -v` with the same private Go/OpenSSL
toolchain described in GO-SIDECAR.md. The harness builds a test-only Go process
fixture with bounded authenticated transport fault injection. Production
`asc-raft` contains no fault-control endpoint or runtime partition switch.

Intermediate checks (not final acceptance): existing 8 Go tests PASS after the
initial term/watchdog edits (62.886 seconds); new actual-term FSM test PASS.
Projection/hash/private-column/revocation unit PASS. Early integration attempts
found a 20-second owner timeout and excessive duplicate barriers/probes; both
were corrected while retaining commit/fencing. A migration fault-injection test
found a changed default call signature; the default call contract was restored
and its exact targeted test passed (3.959 seconds). Earlier timed-out/incomplete
replication runs are development failures, not Phase 2B PASS. Final source and
full regression evidence must replace this provisional status before publication.

Further intermediate evidence: a real three-Go/three-Python run reached initial
election, verified replication, Python Leader withdrawal, automatic owner discovery,
post-takeover upload, old-Leader refusal and Go-mid-copy recovery with the same
session/object. It then exposed pending-upload starvation behind multi-replica
audit; qualification failed after 782.895 seconds. The fixture also exposed an
unclosed SQLite test-read connection (Windows cleanup error); it now explicitly
closes connections. These failures remain failures, not skipped acceptance gates.
The worker now prioritizes jobs and audits at most one replica/turn. A new test
relay drops an actual successful TLS commit response before retry. Targeted tests
for fresh reauthorization/matching retained bodies and unchanged legacy commit
refusal pass (3 tests, 10.747 seconds). Negative source-attachment/private-column/
discovery tests pass (3 tests, 3.859 seconds). Final qualification is still pending.

Conversion additionally verifies each frozen private registry against the initial
upgrade receipt's exact document SHA. Independent nonempty authority cannot be
silently left behind. Secrets remain local or are reissued after activation; old
whole-volume credentials are never a distributed fallback. A corrupt cache
or dead worker cannot keep an unhealthy Python Controller's voter alive forever.

At the original pre-implementation audit all twenty scenarios were NOT RUN.
The continuation results below supersede that initial status. Publication still
requires the final full regression and tracked/staged secret review.

Recovery/rollback: stop and isolate all development Controllers/voters; preserve
complete state/witnesses/configs/manifests/volumes and committed snapshots. Use
matching source and complete reviewed pre-conversion backups. Never delete
guards, witnesses, votes, tokens or unknown objects, lower a term/schema, reset a
voter, or restore an unfenced old cluster. Restoring old credentials can revive
revoked secrets, so it cannot be called automatic safe recovery.

## Windows qualification continuation

The independent targeted run passed **all 20 scenarios**, **4 Python tests OK**,
**887.265 seconds**, before the final source freeze/version bump. The final
v0.8.0 full Python regression subsequently ran **100 tests in 1338.406 seconds**:
**1 FAIL, 3 POSIX skips**, with the other 96 tests passing. Case 7 compared total
object counts across all volumes while unrelated background COPY jobs were still
running: counts changed from `[2, 1, 3]` to `[2, 2, 3]`. That run remains FAIL.
The harness now scopes replay checks to the exact job across all three manifests:
exactly one committed session/object, stable principal/key/session/file identity,
matching immutable bytes and SHA-256, and exactly one original UPLOAD job for the
logical file. Other files' legitimate copies no longer affect this invariant.
The corrected targeted run then passed **20/20 scenarios, 4 tests OK,
999.903 seconds**, using `python -B -m unittest tests.test_failover -v`.
The following full regression was interrupted during review, not accepted: the
runtime JSON wrapper was found to add fields to versioned metadata snapshots and
deltas, invalidating the strict cache schema/digest. Only its known isolated
unittest parent and six verified fixture children were stopped; temporary state
was retained. No unfinished suite is counted as PASS.
A new regression test reproduced the defect for both payload types before the
fix (**1 test, 3 failed assertions, 0.607 seconds**). The wrapper now preserves the
exact envelope and its captured revision, without loosening cache validation.
All **4 RuntimeStateTests PASS, 4.547 seconds** after the fix. The three-process
test now also imports real pinned metadata on all nodes before takeover, after
new-Leader upload and after snapshot/restart. Targeted qualification and the full
regression must pass again on this final source before publication.
The extended 5-test run then ended **ERROR in 900.915 seconds** at reapproval
after the repaired fake node's Python restart: bounded discovery found no current
write-ready Controller. The repaired node can itself be the current Leader. This
controlled restart now stops/restarts its full cohost with retained durable state
and waits for exactly one quorum-ready Controller before reapproval. Independent
Python-only fault cases 3/16 and all old assertions remain. Failure diagnostics
now include live Go role/term/quarantine and receipt count, without credentials.
The wrapper's safe malformed-HTTP error path is also covered before path parsing.
After these edits, **4 RuntimeStateTests PASS, 5.110 seconds**. A supplemental
stdin unittest harness using the same real three-process fixture deliberately
re-paired the **current Leader**, restarted its full cohost with retained state,
waited for quorum readiness, reapproved it, verified the old token's HTTP 401 and
successfully imported pinned metadata: **1 test PASS, 70.457 seconds**. No phone
or original private state was used. The final **101-test** regression was then
launched with `python -B -m unittest discover -s tests -v`; its durable successful
rerun and exact results are recorded above.
No failed development run is relabeled as PASS.

One intervening 239.708-second run failed post-takeover download availability.
Runtime now distinguishes authorization/quorum failures from physical evidence;
it does not downgrade a replica on permission failure. Up to three previously
UNAVAILABLE readable candidates can be reverified from actual pinned bytes on
demand before a consensus REVERIFY. Corrupt/missing/unknown bodies are not assumed
valid. Storage error labels are fixed allowlisted strings, never reflected payloads.

Actual setup: three separate Go and three Python Controller/Storage processes,
simulated ZTE V40 / Bphone A40 / Sony XZ3. Each has separate private config,
certificate, durable Bolt state, runtime cache, original guarded registry, Engine
manifest, approved fake-data volume and loopback endpoints. Physical roots are
independent directories on one Windows machine, not independently powered phones.
The test-only Go executable injects bidirectional peer partitions. The TLS relay
drops one real successful commit ACK. Neither fault endpoint is in product builds.

All scenario assertions are in
`tests.test_failover.FailoverTests.test_real_process_upload_and_controller_takeover`;
the numbered PASS markers are emitted only after their assertions pass.

| # | Required fault/behavior | Final full-regression result |
|---|---|---|
| 1 | Initial automatic quorum-confirmed election and activation | PASS |
| 2 | Real HTTPS upload and independent verified replica | PASS |
| 3 | Stop Leader; another Controller activates automatically | PASS |
| 4 | Same owner client discovers a new pinned endpoint | PASS |
| 5 | New upload completes after takeover | PASS |
| 6 | Replication resumes same job/session/object checkpoint | PASS |
| 7 | Real successful commit ACK lost; retry adds no object | PASS |
| 8 | Returning old Leader follows and refuses direct writes | PASS |
| 9 | Bidirectional 1/2 partition permits majority writes only | PASS |
| 10 | All three isolated Controllers reject writes | PASS |
| 11 | Stale reads retain exact revision/index; availability UNKNOWN | PASS |
| 12 | Revoked Agent remains rejected after Leader loss | PASS |
| 13 | Re-pair/replay keeps identity and rotates generation | PASS |
| 14 | Snapshot/all-sidecar restart retains Catalog/history/identity | PASS |
| 15 | Go killed after durable mid-copy checkpoint | PASS |
| 16 | Python killed mid-copy; watchdog withdraws voter; job recovers | PASS |
| 17 | Delayed old command and forged high term rejected | PASS |
| 18 | Physical corruption reconciled while suspect/last bytes retained | PASS |
| 19 | Old credential stays rejected; no raw secret in runtime document | PASS |
| 20 | Protected simulation refuses Controller/approval and is not a voter | PASS |

### State after conversion/takeover

| State | After | Actual protection/recovery |
|---|---|---|
| Catalog/history | A | Same validated Catalog, original epoch, atomic Go state/receipts and cache checkpoint |
| Registry/identity/revocation | A | Hash/generation/state in prepared CAS; never reload authority from an old private backup |
| Enrollment/re-pair | A | Code consumption, permanent operation routing and identity mutation commit together |
| Grants | A/B | Hash/scope shared; raw bearer stays local, invalidated on takeover and safely reissued |
| Queue/idempotency | A | Shared stable job/key/session/object checkpoints and history; no new physical identity on retry |
| Leases | A/B | Actual-term takeover invalidates old run IDs; retry needs a new committed lease/authority |
| Policy/approvals | A | File policy and explicit domain/endpoint/pin/volume/generation approvals shared |
| Measurements/physical proof | B | Reprobe/reverify before placement/publication; missing data remains UNKNOWN |
| Configuration | A/local trust | Static pinned Go voters bound to durable identity; Python bootstrap trust explicitly provisioned, no dynamic trust discovery |
| Snapshots | A | Entire authoritative runtime document and receipts, including authorities/jobs, survive snapshot/restart |
| Independent conflicting private authority | C / blocked | Startup rejects unmerged histories; keeps their original private rows for review |
| TLS/IPC/admin/node raw secrets | Node-local | Distinct private credentials; hashes or reissued scoped authority enable failover without key replication |

Write-ready means the full applied shared state is validated and takeover fencing
has committed. Unfinished jobs retain their known/unknown physical checkpoint and
cannot publish without current authority and independent physical verification.
Jobs run before bounded background audits. Execution is at least once plus
idempotency, not an exactly-once guarantee. No physical delete/GC exists.

### Protected writers and compatibility

Every runtime Registry/Catalog/queue/grant transaction is prepared on disposable
SQL and CAS committed in the actual Raft term before success/IO. HTTP operations
capture their activation term across the whole request/worker attempt. Go refuses
schema-2 downgrade and owner-ID mismatch. Storage checks exact job scope and a
fresh nonce-bound committed receipt over a pinned Controller, including a fresh
check before visibility. A previously authorized immutable copy can finish, but
late Catalog publication still requires the current lease/term. Unknown/mismatched
staging/final bodies are retained; matching held job bodies need fresh authority.

Existing registry 4 / manifest 1 / public metadata cache 1 remain compatible.
Private runtime cache has user_version 1 and an atomic projection/checkpoint blob;
an unreleased cache-0 can be marked 1 only after validation against live Go state.
Ordinary Registry.initialize rejects cache schema 1. Payload document schema 2,
authority_term IPC and `/cluster/v1/leader` are explicit opt-ins; old metadata-only
mode and unconverted single-writer storage remain available. Exact upgrade replay
is receipt bound; never rebootstrap to convert. Phase 2A tools/evidence are intact.

Owner `cluster-client.json` routes Catalog/admin CLI using per-endpoint credentials.
Agent heartbeat/metadata/storage use its own token with public pinned bootstrap
entries; explicit re-pair preserves that trust list/epoch and its pending operation.
Authenticated readiness is distinct from the public TLS-pinned self routing hint:
the latter can only route a rejected Agent to the real quorum-gated API so it gets
repair-required; it cannot grant access, introduce an endpoint or confer authority.

### Final Go/build checks (source unchanged afterward)

- `go test -v -timeout 240s ./...`: **9 top-level PASS**, 12 stable-state
  subcases PASS, 0 FAIL/SKIP, **69.972 seconds**.
- `go vet ./...`: exit 0. `go mod verify`: all modules verified.
- Windows build PASS; PE/AMD64 machine verified. SHA-256:
  `cba92f501883eca704391c59aca1c34df215dfe14723d8e37c4aa87703702d35`.
- Android ARM64 cross-build PASS; ELF64/AArch64 machine verified, CGO disabled.
  SHA-256: `e5ef737908710942749a604b3bbd1e6e8e556fbc9d0acdaeaba3115a4285367e`.
- Build command: `go build -trimpath -buildvcs=false -o PRIVATE_OUTPUT ./cmd/asc-raft`;
  Android child environment `GOOS=android GOARCH=arm64 CGO_ENABLED=0`.
  Outputs remain in `%LOCALAPPDATA%\ASC-DevTools\phase2b-build`, outside Git.
- Android/Termux runtime **NOT RUN / refused**, not PASS. No phone/M51 access.
  No C compiler is available for `-race`; actual concurrent fault tests and vet
  ran. This is not Android, SD/Doze, physical power-cut or production acceptance.
- AST parsing all 55 Python files with UTF-8 BOM handling PASS; git diff --check
  PASS. PySyncObj probe Git blob equals starting HEAD; **1 PASS / 5 FAIL** retained.

### Remaining limits and rollback

Static three-voter Windows development only; no dynamic membership, quorum-loss
rebuild, hot trust/certificate rotation or planned score-driven transfer. Retain a
healthy Leader; measured hardware/thermal/network preferences are UNKNOWN when
unavailable, and advisory CPU scores never confer authority. A dead/unhealthy
Python runtime withdraws its sidecar through the armed 12-second watchdog.
Configured pins/owner credentials must be provisioned on each endpoint/client;
the runtime never learns trust from arbitrary redirects. Default unconverted
registries remain single-Controller. Independent private histories stay blocked.
Full-body retries, 2 MiB document / 4096 permanent receipt / bounded queue/history
limits remain; exhaustion fails closed, with no unsafe eviction/reset. Windows
directories simulate domains; they do not prove hardware/disaster independence.

Rollback requires stopping/isolating every Controller/voter/client writer, keeping
all current state/configs/witnesses/manifests/volumes, and restoring complete
reviewed **pre-Phase-2B** Go+Python state with matching Phase 2A source. This loses
later runtime/catalog/revocation changes and can revive old credentials; review
credentials in isolation. Old metadata-only source cannot consume a schema-2
runtime snapshot. Do not drop guards, replace an epoch, edit a vote, delete an
unknown body or run init as recovery. No rollback/deployment touched real state.

### Change inventory

- New opt-in package: `asc/failover/{__init__,cli,discovery,runtime,service,state}.py`.
- Existing integration: `asc/{__init__,cli,client,store}.py`,
  `asc/catalog/{cli,client,metadata,schema,service}.py`,
  `asc/consensus/client.py`, `asc/storage/{client,engine,http}.py`.
- Go: `consensus/{fsm,node}.go`, `fsm_test.go`, new test-only
  `runtime_fixture_test.go`. Dependency pins and the election engine are unchanged.
- Qualification: new `tests/test_failover.py`, extended `tests/test_storage.py`.
- Documentation: README-VI, CODEMAP, ARCHITECTURE, DECISIONS, DATA_MODEL,
  NODE_PROTOCOL, SECURITY, TROUBLESHOOTING, CHANGELOG, IMPLEMENTATION_PLAN and this
  report. `.gitignore` adds private bootstrap/runtime configuration exclusions.
- `AGENTS.md`, `docs/PHASE2A-ACCEPTANCE.md` and
  `tools/qualify_pysyncobj.py` are preserved unchanged.
