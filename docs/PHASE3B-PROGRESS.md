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
| 3B.5b | PUSH VERIFIED `8b2e2eb`; 7/7 new faults + 53 targeted tests PASS |
| 3B.5c | PUSH VERIFIED `a1be049`; 3 consensus + 2 safety tests PASS |
| 3B.5d | Storage CLI synthetic profile fix; targeted validation/publication pending |
| Final regression / acceptance | NOT RUN; Phase 3B is NOT accepted |

3B.0 checks: `git diff --check` and local Markdown-link validation must pass before
commit. No runtime tests required for this documentation-only checkpoint.
Publication verification is reported after push and recorded in the next update.

## Next action / resume

3B.5d targeted command **6 PASS, 25.228s**:
`python -B -m unittest tests.test_storage_cluster.ClusterTests.test_cli_owner_upload_download_and_protected_setup_refusal tests.test_consensus tests.test_nodes.RuntimeSafetyTests -v`
Publish/verify 3B.5d, then run full regression on frozen source. First full run:
152 tests, 371.462s, 1 failure + 1 error (old metadata and Storage CLI fixture
Windows assumptions). Both fixtures now use permitted synthetic profiles; product
guards and existing byte/protected-setup assertions are unchanged. The metadata
no-fallback assertion is stronger. Intermediate rerun was stopped, not accepted.

Go post-checkpoint verify/vet/uncached 11 tests/builds PASS (18.100s consensus,
0.003s launcher); source/modules unchanged. Activate existing tools with
`source /workspace/asc-cloud/activate.sh`, then:
`python -B -m unittest discover -s tests -v`
Record actual complete result in acceptance/progress; no completion claim until
all checks PASS and final report is committed/pushed/verified on WIP.
