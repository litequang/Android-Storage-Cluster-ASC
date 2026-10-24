# Phase 3B progress and handoff

Updated: 2026-10-24 (Asia/Saigon). Target branch:
`wip/phase2a-raft-qualification`; base `0550967f57f145ff75179c20500e4aafe9c5cb31`.

## Session verification

- GitHub fetched successfully through inherited proxy; unrestricted policy enforced.
- Remote WIP and starting HEAD equal accepted Phase 3A base. No earlier Phase 3B
  commit found in available Git history. Clean tree; local WIP fast-forwarded to
  base without reset/deletion/main merge.
- Read AGENTS.md, ordered architecture/contracts/security/history and Phase 3A
  acceptance. Prior Windows 122-test PASS is historical, not a fresh Cloud result.
- Cloud Python 3.12.14; `/usr/bin/go` exists but `go version` returns
  `Go: Unknown option: version`. Investigate existing tool locations before Go
  qualification; do not install/change system environment without authorization.

## Checkpoints

| Checkpoint | Actual state / evidence |
|---|---|
| 3B.0 | PUSH VERIFIED `2b3529db0f1374b1be20fc0b2121cf21f601eef2`; remote WIP equals local commit |
| 3B.1a | PUSH VERIFIED `bdf32ac`; contract + 3 targeted tests PASS |
| 3B.1b | PUSH VERIFIED `412bb1a`; 7 contract/engine tests PASS |
| 3B.1c | PUSH VERIFIED `50f3e23`; 13 targeted tests PASS |
| 3B.2 | PUSH VERIFIED `d948762`; 38 targeted tests PASS |
| 3B.3 | PUSH VERIFIED `e24704c`; 41 targeted tests PASS |
| 3B.4 | PUSH VERIFIED `b23722a`; 54 targeted tests PASS (59.175s) |
| 3B.5a | PUSH VERIFIED `5494dce`; 37 targeted tests PASS |
| 3B.5b | 7/7 new real fault gates PASS (73.429s); 53 targeted tests PASS (2.676s); publication pending |
| Final regression / acceptance | NOT RUN; Phase 3B is NOT accepted |

3B.0 checks: `git diff --check` and local Markdown-link validation must pass before
commit. No runtime tests required for this documentation-only checkpoint.
Publication verification is reported after push and recorded in the next update.

## Next action / resume

Verify 3B.5b publication, then final acceptance gate. Source version 0.10.0.
`python -B -m unittest tests.test_node_faults -v`: **7/7 fault gates PASS,
73.429s**. `python -B -m unittest tests.test_nodes tests.test_backup.BackupStateTests tests.test_failover.RuntimeStateTests -v`:
**53 PASS, 2.676s**. AST parses all Python sources/tests; no source changes pending.

First fault attempt failed at Windows-only product entrypoint. Test-only synthetic
Linux launcher now supplies a module-local platform/profile mock; direct product
Linux refusal remains and has an explicit regression. New runtime never bypasses
guards outside tests. See PHASE3B-ACCEPTANCE.md for all intermediate findings.

Next exact commands (activate `/workspace/asc-cloud/activate.sh`):
- `python -B -m unittest discover -s tests -v`
- In consensus: `go mod verify`, `go vet ./...`, `go test -v -timeout 240s ./...`
- `CGO_ENABLED=0 go build -trimpath -buildvcs=false -o PRIVATE_OUTPUT ./cmd/asc-raft`
  for Linux AMD64 and compile-only Windows AMD64/Android ARM64.
Record actual counts/failures/skips/platform limits in PHASE3B-ACCEPTANCE.md, fix
failures without weakening tests, review tracked/staged secrets, commit/push final
report and verify remote. Do not claim Phase completion before that gate.

All checkpoints remain on WIP only; no main merge/force/GC/production/phone work.
