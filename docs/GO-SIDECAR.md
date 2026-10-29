# Go metadata sidecar — development contract v1

Read AGENTS.md and PHASE2A-ACCEPTANCE.md first. This is an opt-in Windows metadata
mode. Default single-writer storage remains available on unconverted registries.
Do not deploy on phones/M51 or use real user state for these commands.

## Reproduce the isolated acceptance

From `D:\CODE\ASC-QuickStart\ASC-QuickStart` in PowerShell:

```powershell
$go = "$env:LOCALAPPDATA\ASC-DevTools\go1.27.3\go\bin\go.exe"
$env:ASC_GO = $go
$env:PATH = "C:\Program Files\Git\usr\bin;$env:PATH"
Push-Location consensus
& $go mod verify
& $go vet ./...
& $go test -v -timeout 240s ./...
Pop-Location
python -B -m unittest tests.test_consensus -v
python -B -m unittest discover -s tests -v
```

Go/OpenSSL are required; failure to locate them is an error, never a consensus
SKIP. The suite provisions three private temporary voters and actual authenticated
loopback RPC plus pinned Python HTTPS. All generated keys/binaries/DBs stay out of
source. No Go dependency gets installed into the Python environment.

## Configuration and controlled bootstrap

Do not run init against a previously enrolled/lost voter. A restored voter needs
the complete reviewed state/witness/config/key backup; dynamic rejoin/rebuild is
not implemented. State loss is quarantine, never single-node reset.

1. Stop the development Controller/worker and back up its complete private state
   (DB/WAL/configs/keys) and matching source. Retain object volumes unchanged.
2. Explicitly export the existing Catalog's canonical seed to a NEW private file:
   `python -B -m asc.consensus.cli export-seed --registry PRIVATE_REGISTRY --seed NEW_PRIVATE_SEED`.
   This seed includes Catalog rows/history, not lifecycle identities/jobs/grants.
3. Provision each voter with a distinct ID, certificate/key and random IPC bearer
   (at least 32 random bytes, e.g. secrets.token_urlsafe(40)). Certificates must
   match the numeric private/loopback address SAN and permit serverAuth/clientAuth.
   Pin each exact single-certificate PEM in all three configurations. No shared
   private key or node/admin token. Keep all config/key/seed/state outside source.
4. New voter Python registries must be explicitly initialized for the SAME cluster
   identity and remain empty; `import-seed` refuses existing nonempty histories.
   It changes only the fresh metadata projection and preserves local credentials.
   Do not copy another voter's private Controller/node identity files. The primary
   attaches its existing exact projection directly. All voters need the same seed.
5. Each private JSON config has these exact fields (absolute paths on Windows):

| Field | Meaning |
|---|---|
| schema | 1 |
| cluster_id, epoch | Exact original seed identity |
| node_id | This voter's distinct static ID |
| peers | Exactly three objects with id/address/certificate (full exact public PEM) |
| state_dir | New exclusive private directory, not an existing/lost voter path |
| seed_file, seed_sha256 | Original canonical seed path and SHA-256 |
| cert_file, key_file | This voter's existing private TLS identity |
| ipc_address | Numeric loopback host:port, port 1024–65535 |
| ipc_token | Independent private random per-voter bearer, never a CLI flag |

6. Build `./cmd/asc-raft` from `consensus/` to a private path with
   `go build -trimpath -buildvcs=false -o PRIVATE_BINARY ./cmd/asc-raft`.
   Run `PRIVATE_BINARY init --config PRIVATE_CONFIG` once per new voter. This
   performs upstream offline bootstrap, writes a binding anchor and an external
   `.enrolled` witness. Partial initialization remains quarantined. Run mode never
   calls bootstrap and cannot recreate lost DB/buckets/snapshots/witnesses.
7. Run each foreground sidecar: `PRIVATE_BINARY run --config PRIVATE_CONFIG`.
   Then, on its corresponding preconfigured development Controller:
   `python -B -m asc.cli controller-run --consensus-config PRIVATE_CONFIG`.
   Attachment requires exact seed equality; mismatch refuses instead of replacing
   a real history. The API binds loopback. Explicit Windows metadata development
   is allowed; protected profiles/unknown Android never get a bypass.

These are controlled development instructions, not an automated installer or
production recovery procedure. The test fixture in `tests/test_consensus.py`
is the reproducible example of provisioning fresh isolated voters without phones.

## Commit, reads, limits and trust

IPC is authenticated loopback HTTP; peer RPC is TLS 1.3 with per-voter trust,
fingerprints and header identity binding. Raw secrets/private keys never enter
the replicated log. File metadata and digests are still private data.

Python prepares canonical document bytes outside apply. Go commits a document CAS
with cluster/epoch/request ID/intent digest/expected SHA, keeping receipts and
applied index/term in its FSM snapshots/log. Python atomically installs the latest
validated document and checkpoint/receipts. No network or generated IDs/time runs
during apply. Crash before/after ACK is retry-safe with the same intent/request ID.
The original receipt remains identical; the response's current revision may be newer.

Local reads are stale/read_only with the last exact checkpoint. A strong read
requires a fresh committed Barrier and local applied state; a follower or minority
fails, even if a cached leader hint exists. During startup replay Python can serve
its last verified stale projection; it cannot grant write authority from that cache.

Only DECLARE/POLICY metadata operations are enabled. DECLARE does not upload bytes
or create a verified replica. All old mutation/worker/registry/grant paths are
fenced; existing grants cease authorization. Physical job failover remains disabled.
No dynamic membership, disaster rebuild or automatic Controller/storage failover
is provided. Documents are bounded to 2 MiB; receipts to 4096 with no eviction.
Receipt exhaustion requires a future reviewed protocol, not manual deletion.

Raft assumes trusted non-Byzantine peers and trusted Python preparation. It does
not protect against a local administrator replacing code/state. Windows ACLs and
complete private backups are required. Physical power-loss and Android runtime
qualification remain deferred. Android cross-compilation alone is not acceptance
on Android; the executable refuses to start there.

Rollback follows DATA_MODEL: stop/isolate the whole development cluster, preserve
new state/objects, restore complete pre-attachment registry backups plus v0.6
source. Post-backup metadata is lost. Never drop guards, edit mode/index/term,
remove enrollment witnesses or re-init a lost voter to make it run.
