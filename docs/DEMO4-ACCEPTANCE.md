# ASC Demo Alpha 0.4.0 — DEMO.4 acceptance

**SOURCE-READY / ACCEPTED for Linux synthetic qualification only.**
**Android runtime, real-phone CA import/browser, microSD, Doze, power-cut, 24/7 and production: NOT TESTED / NOT QUALIFIED.**

Branch `feature/android-demo-alpha`. Date: 2026-10-25 UTC.
Frozen final implementation/tests/packaged guides: `956bf8ebb23e57b07d4ec91cefec8d89539a8327`.
Verified start `2d19eb06cee1b6bede0fbafac9d4704704c039a9`.
Core WIP `acea2aead8cfd50f8a8fc2b31e24f8f9ccaeb84c` unchanged.
Python3.13.5, Go1.27.3 linux/amd64, Chromium154.0.8037.57, local Playwright/certutil/OpenSSL.
No source/test/packaged-guide changes after final fresh full run started; only
reporting/public archive/checksum files follow. Publication commit/remote/download
receipt is recorded in DEMO-TRACK-PROGRESS after normal push.

## Actual gates

| Gate | Actual result |
|---|---|
| DEMO.4a backend | 35 targeted PASS / 0 skip,136.486s; pushed/verified 5db17aef375b5ebfd03ce680a3b0a52c3a993f99 |
| DEMO.4b frontend | 21 targeted PASS / 0 skip,105.743s incl actual trusted-CA Chromium; pushed/verified 8e4661bbccc9c6b11e451e414907d190a55a799c |
| Final0.4 targeted | **22 PASS / 0 SKIP / 0 FAIL/ERROR,119.508s** |
| All 8 Linux physical gates | **01–08 PASS**, actual network unlink/lost ACK/quorum/term/stale callback/crash/journal/whole-cluster replay/last-copy and reference protection |
| Fresh final full Python | **230 PASS / 0 SKIP / 0 FAIL/ERROR,1422.631s**; completed 2026-10-25T00:33:36.679822+00:00 |
| Exact published0.3 ->0.4 ->old0.3 code/new state | PASS in targeted and fresh full; independently 1 PASS,14.810s |
| Fresh Go `go test -count=1 -v -timeout 240s ./...` | **11 top-level PASS**, consensus20.037s/launcher0.003s; uncached |
| `go vet ./...` / `go mod verify` | PASS / all modules verified |
| LinuxAMD64 / AndroidARM64 build | PASS / cross-build PASS only; Demo does not launch sidecar; Android runtime NOT TESTED |
| Exact final archive installer | **3 PASS / 0 skip,1.697s**; rebuilt frozen source byte-identical, checksum/extraction/dry-run/install/installed-launcher/rerun/private-state retention/tamper refusal/guards |
| Public archive audit |92 regular allowlisted source/asset/guide/manifest files; no links/special entries/private state/key/token/cert/database/browser profile/node_modules/logs |
| Syntax | Changed/full packaged Python AST (BOM-aware), `sh -n scripts/demo-alpha.sh`, `node --check asc/demo/dashboard/web/app.js` PASS |
| Core preservation | Non-Demo asc/, Core tests and consensus/ unchanged against acea2ae; Core branch unchanged |

230 = 208 unchanged Core tests +14 original Demo +6 Dashboard API/session +1 real
browser +1 exact published-package upgrade. The full run includes all legacy/new
Linux physical-GC faults, Phase3A history/snapshot/backup/restore, consensus/failover,
scoring/preferences/replication, storage/installer/LAN/upgrade regressions. No fault
gate skip, fake success, TLS bypass, test weakening or timeout relaxation. Actual
physical unlinks occur ONLY within existing explicitly isolated Core test fixtures;
Dashboard and ordinary Demo runtime still issue no GC capability or delete route.

## Browser / runtime evidence

- Same Controller process/Catalog/worker and unchanged pinned Core transfer client;
  no second Catalog/database, new consensus algorithm or storage implementation.
- Separate explicit IP-SAN trusted HTTPS listener; private browser CA/leaf keys stay
  in Controller. Core/node certs/pins remain unchanged. CLI-only default retained.
- Owner-only pinned CLI issues random one-use 5min code; bounded RAM sessions 30min,
  Secure/HttpOnly/SameSite=Strict host cookie, CSRF/Host/Origin/fetch checks, bounded
  login/body/workers/one 32MiB transfer spool. No shared/default password, Core token,
  node grant/private key in browser, CORS, wildcard/public bind or HTTP fallback.
- Real Chromium uses isolated HOME/NSS with only public synthetic CA explicitly
  trusted and normal TLS validation. Untrusted profile and wrong SAN are denied.
  Auth/CSRF/Host/Origin/expiry/restart/logout/ticket scope/body bounds/traversal and
  unavailable mutation routes are tested; public CA export never overwrites.
- Actual UI upload creates two physical synthetic node/domain bodies with SHA;
  pending/received counts never imply protected. Same request key preserves Core
  durable jobs; backend rejects bad SHA and unsafe capacity/domain placement.
- Actual first replica node is stopped; UI shows degraded; downloaded saved bytes
  match SHA through existing fallback, unsafe new upload refuses without extra file.
  Browser WebCrypto checks full SHA before new download, no filesystem overwrite API.
- Literal HTML filename cannot execute/no injected IMG; dynamic content uses text
  nodes. No external requests or page errors. Reviewed 1280px and 390px screenshots,
  no mobile horizontal overflow. Browser network loss sets cache UNKNOWN and disables
  upload/download; reconnect works. Physical missing-volume/Controller-loss cases
  also run in original unchanged Demo tests, no failover or new leader appears.
- Overview/node/volume/file/replica views retain UNKNOWN for missing/stale metrics;
  unobserved approved volume IDs remain visible. Shared-domain available capacity
  is conservative, two volumes/identities on one phone never prove two domains.
  Node approval/failure-domain confirmation remains owner CLI only.

## Exact compatibility and rollback

The test uses exact published0.3 archive SHA
`3bf81c5d94891fa064e2f05f99d60d620b4c5db71c87bb2ee6c89ac72b9a445a`.
Old installed code creates/populates cluster/two nodes, stages/verifies/activates0.4
using NEW complete stopped backups. Trusted Dashboard reads old bytes;0.4 writes a
second file. Another NEW full backup precedes code-only rollback; old immutable0.3
runs against actual new state and downloads BOTH files with exact SHA. Node/Cluster/
installation/volume IDs, tokens/pins/keys/certs/base formats unchanged; Dashboard
keys retained and backed up. Base STATE_FORMATS demo1/registry4/manifest1/metadata1/
config1/wire1 unchanged. Old0.3 CLI ignores optional Dashboard folder; no DB restore,
identity recreation, schema downgrade or migration claim. Existing future-schema,
interrupted activation/journal and linked-lock safety tests remain PASS.

Rollback: stop entire cluster, make/verify NEW complete private state+approved-volume
backup on each phone, select preserved compatible0.3 release via `rollback`, restart
without `--dashboard`; keep optional browser identity and all old/new bytes. For
CLI-only0.4 simply stop Controller and restart without flag. Never restore stale
metadata, overwrite release/source, remove marker/journal or recreate identity.

## Public QuickStart package

- `releases/asc-demo-alpha-0.4.0.tar.gz`, 168292bytes,92members.
- SHA-256 `b9e186589bb4f5c698c7df2250f94ec32ce1e6e2acb41cf3923ade9e706a29f1`; adjacent `.sha256` file.
- Content/release ID `84849e9f1c269db1168d3adfa4f71fc0f720f92c5da63143c6d00811b9590277`.
- Old0.3 archive/checksum kept intact. Deterministic final rebuild and per-file
  manifest hashes bind source/assets/guides; installed launcher verifies every file.
- Source-only, no runtime state/binaries/CA private material/dependency download.
  README duplicates tested owner guide; actual Android/PC CA-install UX is manual.

Owner usage: DEMO-QUICKSTART sections1–5 for install/controller/nodes/approval,
5a for public-CA fingerprint/trust/HTTPS/one-use login/browser file+SHA workflow,
6/6a for stopped0.3 upgrade/new-backup/code rollback; section7 safe diagnostics.
Before using a published package verify SHA from trusted commit. Android checklist
stays entirely NOT TESTED in DEMO-ANDROID-PILOT; owner alone tries ZTE/Bphone/XZ3.

## Changed files / limits

New `asc/demo/dashboard/` auth/TLS/views/HTTP/runtime and three local web assets;
Demo lan/cli/state/package/version integrations; tests/test_demo_dashboard.py,
test_demo_dashboard_browser.py, tests/browser/demo_dashboard.cjs and
 test_demo_release_upgrade.py; ordered-contract/CODEMAP/security/protocol/schema/
troubleshooting/changelog/plan/progress/acceptance/QuickStart/pilot/README docs.
Public0.4 archive/checksum and narrow .gitignore exception follow full PASS.
No Core source/test/Go guard or Core branch changes.

Default browser limit32MiB, one transfer at a time, first256files preview with
UNKNOWN truncated totals, volatile sessions, fixed IP SAN/explicit manual CA trust,
node approval via CLI, owner-confirmed domains without hardware attestation.
No PWA/offline write/background sync, native APK, auto-update, automatic failover,
Raft activation/migration, physical GC/reduction, Phase3D or production claim.
Browser network simulation and Linux synthetic domains do not qualify actual
independent hardware/power failures. Real Android/Chrome/Termux/SD/Doze/power-cut,
PC/Android manual certificate trust and production remain separate owner acceptance.

## Reproduction

```sh
source /workspace/asc-cloud/activate.sh
python -B -m unittest tests.test_demo_dashboard tests.test_demo_dashboard_browser tests.test_demo_release_upgrade tests.test_demo_installer tests.test_demo_lan tests.test_demo_upgrade -v
python -B -m unittest discover -s tests -v
cd consensus
go test -count=1 -v -timeout 240s ./...
go vet ./...
go mod verify
CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -trimpath -buildvcs=false -o /PRIVATE_TEST_BUILD/asc-raft-linux-amd64 ./cmd/asc-raft
CGO_ENABLED=0 GOOS=android GOARCH=arm64 go build -trimpath -buildvcs=false -o /PRIVATE_TEST_BUILD/asc-raft-android-arm64 ./cmd/asc-raft
```

Use an existing private build directory. Browser gate requires local Node Playwright,
Chromium and certutil; missing tools FAIL explicitly, never skip/bypass TLS.
Cloud tests do not install/change system packages/trust/phones. Full logs/builds/
profiles/state remain private test artifacts; only sanitized results are published.
