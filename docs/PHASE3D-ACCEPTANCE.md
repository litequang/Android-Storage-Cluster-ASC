# Phase 3D acceptance

Status: **NOT ACCEPTED — implementation and fresh qualification pending.**
Branch feature/phase3d-external-dr from Core acea2ae, source/Linux synthetic scope.
Read PHASE3D-PLAN/PROGRESS for exact coverage, checkpoint and recovery contract.
No prior3A–3C or Demo test result is reused as new3D evidence.

External backup/anchored verification and isolated read-only staging are intended
scope. **Full writable disaster recovery NOT ACCEPTED:** old-cluster fencing,
upstream Raft recovery and credential restoration are not qualified. No new epoch,
quorum/Leader/bootstrap/SQLite overwrite or token resurrection is implemented.
Android/Windows runtime/real independent media/power-cut/production NOT TESTED.
Final actual commands, test matrix/counts, commits, format/operator/rollback guide
will be recorded here after they execute. Never mark an unrun gate PASS.

## Executed targeted qualification (full gate still pending)

3D.0:20 backup unitPASS0.252s;3D.1a:35PASS0.402s;3D.1b:12PASS12.663s actual
three-voter/TLS;3D.2:37PASS0.467s;3D.3:23PASS0.460s. Final3D.4a target:
**54 uniquePASS/0SKIP/0FAIL66.001s**, 30new3D +24 retained backup/runtime units.
All9 actual network/process fault groups PASS; actual recovery process death/
normal CLI resume, exact baseline source schema compatibility and security tests.
Fresh Go11/vet/module/Linux build PASS, Windows/Android cross-build PASS only.
No full3D acceptance yet; fresh238-case regression must execute to completion.
Exact commands, matrices/intermediate failures in PROGRESS; operations in
[PHASE3D-OPERATIONS.md](PHASE3D-OPERATIONS.md). No source runtime/key/schema import
exists for writer recovery. Full writable disaster recovery remains BLOCKED.
