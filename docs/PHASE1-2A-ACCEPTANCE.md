# Phase 1.2A acceptance record — v0.5.0

This record covers local development fixtures only. All simulated state, certificates and bodies are under Python TemporaryDirectory, outside source and production private state.

## Reproduction (PowerShell)

```powershell
Set-Location E:\CODE\ASC-QuickStart
Get-Command openssl
openssl version
python -B -m unittest tests.test_storage -v
python -B -m unittest tests.test_storage_cluster -v
python -B -m unittest discover -s tests -v
```

If OpenSSL is already supplied by Git for Windows, add its existing directory to this terminal PATH only, for example:
```powershell
$env:PATH = "C:\Program Files\Git\usr\bin;$env:PATH"
```
Do not skip TLS tests or install/change the system automatically.

## Required scenarios

| Scenario | Evidence |
|---|---|
| Controller + ZTE V40 / Bphone A40 / Sony XZ3 | ClusterTests setup: four actual pinned loopback HTTPS endpoints, separate identities/private states/volumes |
| Streaming upload, SHA-256, immutable commit, download, restart | test_three_node_upload_download_restart_duplicate_disconnect_and_faults, all three nodes |
| Duplicate request/body/commit; conflicting logical name | engine and cluster idempotency tests |
| Network disconnect mid-write, full-body retry | synchronized WRITING state then actual client disconnect; session INTERRUPTED, retry and commit |
| Quota/full disk/fsync errors | engine reservation/physical-allocation tests, injected ENOSPC and HTTP 507 |
| Missing/replaced volume at same path | engine medium identity and cluster offline tests |
| Metadata/physical mismatch, corrupt/missing file, orphan object | engine verify/recover/inventory and cluster metadata conflict |
| Unauthorized/anonymous, node token versus user grant, wrong node/operation/pin, expiry/revoke/re-pair | cluster authorization/framing cases |
| Crash during writing and after final object copy | engine restart state injection; no implicit publication |
| Traversal, Windows junction / POSIX symlink, hardlink | engine safety tests preserve outside sentinel |
| Controlled expiry | dry-run default, explicit staging-only cleanup; final objects preserved |
| CLI owner upload/download, protected-device refusal | test_cli_owner_upload_download_and_protected_setup_refusal |
| Phase 1.1 compatibility | unchanged lifecycle assertions plus schema 0/2 -> 3 identity/code/token preservation |

## Limits of this evidence

State/fault injection is deterministic process-restart simulation; no physical power-cut, real SD controller, Doze, SAF or Android acceptance is claimed. ENOSPC is injected rather than filling a development disk. Installer cases need POSIX Bash and skip on Windows. No Raft, global file catalog, replication, backup, election or automatic failover exists.

Executed results are recorded below. The owner-supplied v0.4.1 PASS is historical and was not reused for this changed source.


## Codex execution — 2026-10-23, Windows / Python 3.14

- Final engine target: python -B -m unittest tests.test_storage -v — 16/16 PASS.
- Targeted integration/migration run before the final capability refinement: 28 tests OK; final client/CLI integration target: 12 tests OK.
- Windows oversized-body TLS regression was reproduced in the full run, fixed without changing acceptance, then its existing 413/pin test passed 5 consecutive targeted runs.
- Final full suite after all source/test edits: 61 tests run, OK (skipped=3), 22.015 seconds: 58 PASS, 0 FAIL, 0 ERROR. The three skips are exactly test_installer.InstallerTests cases requiring POSIX Bash; no TLS/storage test skipped.
- Actual four-endpoint HTTPS simulation PASS for all three nodes, including upload/download SHA, restart, duplicates, synchronized mid-stream disconnect, quota/offline/metadata conflict and unauthorized/revoked/rotated grants.
- OpenSSL was the existing C:\Program Files\Git\usr\bin\openssl.exe via process-local PATH. No dependency/system installation, production service or phone access.
- No separate lint/typecheck/build configuration exists in this standard-library project; unittest imports exercised changed Python modules. git diff --check also passed.
- Candidate tracked/untracked audit: 44 source/documentation paths; no private-key/GitHub/AWS credential patterns or sensitive runtime paths detected. Ignore-rule checks cover config/grants/keys/tokens/DB/object/staging/log/temp. Staged audit is repeated before commit.

The actual final Python -B driver body (same discovery as the reproducible CLI command above):
```python
import os, sys, unittest
os.environ['PATH'] = r'C:\Program Files\Git\usr\bin' + os.pathsep + os.environ['PATH']
sys.dont_write_bytecode = True
r = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover('tests'))
sys.exit(not r.wasSuccessful())
```

The ready-to-run CLI equivalent is python -B -m unittest discover -s tests -v with that process PATH. No source/tests changed after this final full result; subsequent edits record documentation and publish only.

Pre-commit staged-tree review completed: 44 tracked blobs inspected, 30 changed files; no sensitive runtime paths or matching private-key/GitHub/AWS credential patterns found. All Python ASTs parsed; staged git diff --check passed. Fetched origin/main matched the existing local baseline, with no divergence.
