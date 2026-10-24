# Phase 3C plan / safety and continuation contract

Status: all checkpoints complete; Phase 3C ACCEPTED for Linux x86_64 isolated
synthetic qualification. Fresh 208 Python / 11 Go tests, all mandatory faults,
vet/module/build PASS on 8b679bc; see PHASE3C-ACCEPTANCE.md. Date: 2026-10-24 (Asia/Saigon).
Repository: litequang/Android-Storage-Cluster-ASC.
Only branch: `wip/phase2a-raft-qualification`.
Base: `b1b46e527826617748a8bc68795259060e12d705` (Phase 3B v0.10.0).

Read AGENTS.md and its mandatory ordered documents, then PHASE3B-PLAN,
PHASE3B-PROGRESS, PHASE3B-ACCEPTANCE, IMPLEMENTATION_PLAN, this plan and progress.
Fetch WIP every session; preserve local work and history. Never develop on/merge
main, reset existing work or force push. Stop immediately on proxy:8080 error;
keep inherited proxy/TLS. Existing Cloud tooling: source
`/workspace/asc-cloud/activate.sh` (Python 3.13.5, Go 1.27.3, existing caches).

## Publication gate after every checkpoint/subcheckpoint

Run targeted tests (and broader safety regressions when affected), fix failures,
update CODEMAP and relevant contracts/architecture/schema/security/troubleshooting/
changelog, record real checks/results/next actions in PROGRESS, review tracked AND
staged paths/blob content for secrets, commit, normal push to WIP, compare remote
ref with HEAD. No next checkpoint before successful remote verification. Hashes
are recorded in following checkpoints/final response; a commit cannot embed itself.
If push is blocked, preserve local changes and report exact blocker; a supported PR
must target WIP and is not synchronized until its commit exists on GitHub.

## Ordered checkpoints

| Checkpoint | Deliverable / required evidence |
|---|---|
| 3C.0 | This plan, durable handoff, roadmap/current authorization and data-loss risk assessment; docs/links/whitespace validation; push before source |
| 3C.1 | Explicit bounded versioned replication extension; owner replay-safe policy counts 1/2/3; durable reconciliation through existing COPY/proof jobs; under-replication stays explicit; no byte deletion |
| 3C.2 | Durable owner Drain/Rebalance, safe target/domain/capacity selection and stable copy jobs; stream checksum proof before retiring any source reference; shortage/offline/corruption keeps original bytes |
| 3C.3 | Pure full reference-graph GC planner covering every version, snapshot/trash/backup/restore, jobs/grants/transfers and retained Catalog events; conservative holds, checkpoint-bound proposal and estimates; explicit logical retirement/archive protocol before physical eligibility |
| 3C.4 | Guarded isolated-test physical GC only: default disabled, no production enable command; owner confirmation bound to plan SHA; quorum/current-term fencing; irreversible committed reservation; exact-object scope; private durable node journal; safe path/volume identity and checksum; retry/lost-ACK/crash recovery |
| 3C.5 | New actual three-Go/three-Controller/TLS fault matrix plus fresh full Python, Go uncached tests/vet/module verify/build; exact evidence in PHASE3C-ACCEPTANCE.md; final push/remote verification |

Split a/b/c (and further suffixes) when changes are too large to review. Each
split retains the same test/documentation/GitHub gate. No 3D, Dashboard, phone,
M51, production or voter/membership/quorum change. Prior 3A/3B evidence is preserved;
it is not reused as a fresh check of changed source.

## Data-safety contract and initial risk assessment

| Risk | Required control / proof |
|---|---|
| Last readable copy removed | At least policy minimum (>=1) independently approved failure domains retain freshly streamed/checksummed bytes before logical retirement; recheck immediately before destructive authorization |
| Same device masquerading as independent copies | Existing explicit physical device domains, generation/volume approval and capacity reservations remain hard gates; scores/preferences never override |
| Copy fails or ACK lost | Use existing stable COPY job/session/object IDs and independent proof; source is retained until committed completion; retries cannot create duplicate destructive work |
| Snapshot/restore/trash/history still needs object | Scan all authoritative references, not just latest heads; retain suspect/unknown data; no automatic expiry/eviction of retained history to create GC eligibility |
| Completed jobs keep physical pointers | Treat them as references too. Any future explicit terminal-job archival must preserve audit digest/identity/history and upload replay without permitting old jobs to become writers; cannot silently ignore pointers |
| New references appear between plan and unlink | Bind confirmation to exact graph/plan SHA; revalidate on commit. Commit irreversible retirement/reservation first; every apply/proof/reference path must reject reintroduction of reserved local object IDs |
| Stale Leader/minority/expired lease | Existing actual-term quorum CAS plus fresh nonce-bound online Storage authorization immediately before irreversible boundary; no cached permit/follower fallback; takeover invalidates unexecuted work/proofs |
| Crash across filesystem/SQLite/Go boundaries | Durable Controller reservation and separate private node journal before unlink; tombstone and exact size/SHA/volume/object binding make retries idempotent; ambiguous state never becomes proof of safe absence |
| Wrong path/root/media, symlink/hardlink | Existing Volume identity/no-follow safety; exact generated object ID and approved volume; rehash before removal; refuse root substitution/link/unknown identity; never arbitrary path or recursive delete |
| Test switch accidentally enables a phone | No normal CLI/config/env enable path. Physical executor requires an in-process isolated synthetic-volume capability, loopback trusted fixture, supported host checks and fresh owner/quorum authority; default absent and real Android/phone execution refused |
| Legacy migration/rollback resurrects deleted pointer | All Controllers upgrade before explicit enable; validators fail closed on new extensions. Never restore an old metadata DB over GC-mutated volumes; complete matching stopped backups must include bytes |
| State/receipt exhaustion | Keep bounded extension/jobs/journals and inherited 2 MiB/4096 receipt limits; fail closed without evicting backups, jobs or history |

A retained audit record that still contains a physical pointer remains a hold.
Plan estimates distinguish logical excess from bytes actually reclaimable now.
Snapshots/versions pin content; a replica may be detached only after sufficient
other copies are verified. An EXPIRED marker alone never authorizes physical GC.
Unknown orphan/native files remain held until provenance can be proved; no adoption
or deletion by filename/digest similarity. A GC target/journal is a retirement
record, not a new data-use reference; its object cannot reenter the live graph.

Quorum/term checks authorize the irreversible committed GC decision, and Storage
must freshly reauthorize at the final unlink boundary. Network and filesystem
operations are not one distributed transaction: a syscall already authorized at
that boundary cannot be recalled. Permanent reservations prevent newer metadata
from relying on an object once deletion has been committed. Qualification must
explicitly test paused requests, loss of quorum/term changes before the boundary,
new-reference races and crash/lost-ACK outcomes, without claiming nanosecond-atomic
failure detection or real-device power-cut durability.

## Architecture direction / compatibility

Reuse existing trusted Python preparation -> actual-term Go CAS -> atomic verified
projection and existing immutable transfer Engine. Add optional bounded versioned
replication/retirement extension; no custom Raft or dynamic voters. Explicit enable
after matching all-Controller upgrade, preserving original frozen SQL and 3A/3B.
Normal policy reduction/Drain may detach excess references but does not by itself
unlink bytes. Physical apply remains an explicit confirmed test-only path and can
be blocked even when logical reduction is safe (retained event/job/grant pins).

Keep the isolated GC executor unreachable from normal runtime/Agent setup. Fixture
capabilities are created only for fresh synthetic temporary volumes, bound to node/
volume/root identity; no flag alone can turn an existing real volume into a GC test
volume. Separate raw proof, logical retirement, eligible plan, committed deletion
reservation, authorized node execution and acknowledged completion states.

## Qualification matrix / stop conditions

Targeted units: policy 1->2->3->1 and replay/conflicts, no-quorum; duplicate domains/
unknown/free-space reservations; Drain without capacity; corrupt source/target;
all reference categories; stale plan/new pin; held last copy; path/root/link attacks;
wrong node/volume/object/size/SHA/generation/token/term; missing default capability;
node journal crash points and repeated/lost ACK; bounds/roundtrip/takeover.

Actual fixture faults: copy-before-retire, Leader/worker crash, old/minority requests,
quorum loss before unlink, paused stale permits, immutable snapshot/version restore
retention, GC retry after actual unlink/lost ACK, local journal restart and whole
cluster snapshot/replay. Full prior regression must still pass. No test is skipped,
deleted or weakened to qualify GC. If an invariant cannot be proved, leave the
feature blocked, preserve source/data and report the concrete safety blocker;
never label the Phase accepted with failing/unrun required checks.

## Rollback

Before enabling new schema, stop/isolate all development voters/Controllers/Agents
and preserve matching complete configs/keys/DB/WAL/Raft state/witnesses/manifests/
volumes and source. Physical deletion cannot be undone from metadata; rollback
requires the matching byte backup, never an old DB over current GC volumes.
Retain post-upgrade state/journals separately. No schema/term editing, reservation
removal, voter re-init, key replacement or automatic old-cluster resurrection.
