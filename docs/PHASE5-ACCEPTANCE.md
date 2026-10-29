# Phase5 acceptance — Linux software subset ACCEPTED / overall PARTIAL

## Final5.4c — 2026-10-29

Fresh full Python: **445PASS,0FAIL/ERROR/SKIP,1690.895s**. All42Phase5 cases included,
all64required original fault markers present. Runtime started00:03:18Z and ended
00:31:29Z. Full log private work/phase5-final/python-full.log. No failed full run,
source fix, skipped assertion or deadline/fencing relaxation in this qualification.

Source26ad88e74f7379402946246cb44da0215506cc51, freeze449inputs/e98f57ca...;
all hashes and445unique test IDs identical after execution. Reports-only freeze/
platform commits457ec6a/37d7134 change no tested executable. Public exact proof:
qualification/phase5-final-source.json, phase5-platform-gates.json, phase5-final.json.
Source branch feature/phase5-remote-access, original Core/Demo/Phase4 refs preserved.

| Gate | Actual result | Scope |
|---|---|---|
| Full Python |445PASS/0skip,1690.895s | Linux x86_64/Python3.13.5, source/synthetic |
| Existing fault gates |64/64PASS | Actual TLS/process/quorum/I/O/unlink on temporary volumes only |
| Go tests |11top-level +12nested PASS | Fresh uncached Go1.27.3,23pass events |
| Go vet/modules |PASS | Actual current checkout |
| Builds |Linux/Windows/Android PASS | Windows/Android compile only, not runtime |
| Source package |Deterministic146files,127exact Python modules,0secret patterns | PRIVATE synthetic package, no release |
| Dependencies |4official wheel SHA +installed RECORD integrity and pip check PASS | Optional private env only |
| Old APK5 |Original SHA/signer/static inventory PASS | Unchanged binary; no new build/runtime/Keystore/ADB action |
| cloudflared |Official2026.10.5 SHA/offline config/rules PASS | No tunnel/account/DNS/IdP connection |

Software subset qualified: existing owner Dashboard/File Manager over private
HTTPS; separate Access JWT/owner gates over actual LOCAL TLS and synthetic connector;
actual file bytes/two logical domains/SHA/fallback; Core observer across actual
quorum partition/heal; passive recovery unchanged; owner-local stopped maintenance
with final CAS/backup/identity and NEW-state code rollback. Standard tests preserve
Core3A–3D guards/data/history. No second Engine/Catalog, authority or remote shell.
Resource context2CPU/8GiB/GOMAXPROCS2, as prior qualification;10s/250ms safety fences
and original fault assertions unchanged. No active emulator/Gradle workload.

**Overall Phase5 / production remains NOT ACCEPTED.** Live Cloudflare/Access/IdP/
DNS/tunnel/public-host browser, actual VPN/SSH/remote maintenance, independent real
hardware/LAN/ARM64/Doze/OEM/power are NOT TESTED or deferred by owner. Earlier public
hostname experiment ERR_TUNNEL_CONNECTION_FAILED remains unqualified; loopback
connector PASS never substitutes for it. Android evidence from earlier receipts
is historical on the EXACT unchanged APK, not a fresh Gradle/JVM/emulator run here.
Termux/APK/Demo/Core migration and writable DR remain unsupported/blocked. Android
Raft/voters/physical GC/failover remain locked; no production/phone/M51 access.

Historical5.4c did not publish a new source/APK release. Its existing installer can build a consistent
internal source package, but its historical allowlist omits Phase5 optional lock/
operations guides: NOT a complete Phase5 distribution. Use verified source checkout
and PHASE5-PRIVATE-ACCESS, PHASE5-CLOUDFLARE, PHASE5-MAINTENANCE for qualified local
commands/limits. Stop the gateway to return to existing LAN access; source upgrades
use NEW stopped backups and code-only rollback, never old DB restore or reinit.

Remaining work can be split: separately qualify a complete Linux access distribution
without phone access; deploy actual VPN/provider/SSH only under a reviewed owner
configuration, then execute deferred physical-device/production acceptance. No new
phase/consensus/recovery authority is authorized by software PASS.

## Historical checkpoint scopes (superseded by final source result above)

Historical5.1 private gateway software subset qualified:19API/regression +1CLI +1actual
Chromium +2Core/passive read-only scoped executions PASS. Actual VPN/Tailscale,
public Cloudflare, maintenance, physical/production and final full5.4 gates are
outstanding. Hardware DEFERRED BY OWNER, not a reason to stop source development
and not evidence of PASS. See dated scopes below and PHASE5-PROGRESS.

Historical5.0 checkpoint only: source contract/route exclusions, targeted host tests. No remote runtime,
VPN, Cloudflare, SSH, phone or production acceptance. Physical-phone gates are
DEFERRED BY OWNER2026-10-28, not PASS and not unittest skips. Prior Core392/Go/fault
and Phase4 API30/API35 scoped receipts remain valid only for identical inputs.

Require5.1 actual TLS/session/CSRF/upload/two logical replicas/download SHA/fallback,
wrong pin/mode refusal, startup/Controller/gateway interruption and streaming limits.
5.2 public-edge trust and5.3 maintenance require their own source qualification.
Real ARM64/phones/LAN/independent domains/Doze/OEM/power/network switching and
production approval remain a separate combined acceptance campaign. No writerDR,
Android Raft/GC/failover, direct public node/admin ports or automatic update.

## 5.1a API/runtime scoped PASS
Fresh19targeted0skip/fail77.201s plus separately CLI1PASS7.041s. Actual trusted
TLS/session/CSRF, upload/two logical replicas/downloadSHA/offline fallback, wrong
pin/mode/CA, body/framing/route refusals, gateway/backend restart semantics and
foreground stop passed. No browser-through-gateway/Core E2E/VPN/Cloudflare/phone
claim. Prior failed fixture runs retained in PROGRESS; no checks weakened.
Source-only Linux alpha guide PHASE5-PRIVATE-ACCESS; no new archive/APK release.
Full Phase5 NOT ACCEPTED, hardware DEFERRED BY OWNER and production not qualified.

## 5.1b.1 browser scoped PASS
Actual Chromium through new gateway and verified new public CA:1PASS12.565s,
unchanged existing browser gate/PWA/mobile/XSS/session/upload/two replicas/SHA/
actual Node stop/fallback/offline refusal/reconnect/logout. Receipt
qualification/phase5-private-access.json records separate19+1+1executions and all
source hashes; not a full suite/actual VPN/phone/public-edge/Core-runtime claim.
Next Core read-only and passive recovery ingress qualification remain separate.

## 5.1b.2 Core/passive read-only ingress PASS
Two targeted tests14.866s: actual three-Go/Python Core observer through gateway,
three-island transport quorum loss and heal, owner remains read-only/no mutations;
plus actual filesystem passive backup/stage via existing MemorySource metadata
fixture, read-only mode/credentials missing/staged bytes unchanged/no writer.
Synthetic memory-source recovery is NOT live-Raft backup/DR authority proof.
Private software subset5.1 qualified in these named scopes. Actual VPN/public
Cloudflare/remote maintenance/production/phone campaign remain outstanding.

## 5.2a foundation scoped PASS
16targeted PASS0skip/fail0.066s, real ephemeral RSA/PyJWT claims/signatures and
private-mode regressions in hash-pinned optional private venv. No edge runtime/
Cloudflare-issued JWT/live provider/remote reachability acceptance yet. Official
references, dependency provenance and exact scope in PHASE5-CLOUDFLARE/PROGRESS.

## 5.2b source/loopback scoped PASS
22JWT/profile/actual edge TLS/JWKS/file cases PASS41.118s; shared gateway/Dashboard/
Chromium14PASS from initial regression (Core setup failed due wrong default go),
then explicit existing Go SDK Core/recovery2PASS67.221s. Setup error resolved,
no skip/security weakening; exact logs/initial failures in PROGRESS.
Official cloudflared2026.10.5 SHA verified, offline config/rule/catchall PASS only.
No live Cloudflare/JWT issuer/IdP/DNS/tunnel/public browser/remote reachability,
physical devices, new release or fresh full-suite acceptance. Next5.2c edge Core/
recovery and synthetic browser integration; full Phase5 NOT ACCEPTED.

## 5.2c synthetic connector/browser and edge read-only scoped PASS
Fresh6PASS0skip/fail55.833s: actual edge connector/browser1/Core1/passive recovery1
and original private equivalents3. No product source change sincebf04868; real
TLS/RSA/owner/Engine bytes/pinning and all original assertions remain. See guide/
receipt for exact key-transport and recovery fixture scope.
Reserved public-host browser experiment failed ERR_TUNNEL_CONNECTION_FAILED;
proxy/CA/policy untouched, test changed to explicitly local synthetic connector.
Therefore no live provider/IdP/public-DNS/Cloudflare/tunnel acceptance is inferred.
Next5.3 maintenance and5.4fresh final gates. Full Phase5 NOT ACCEPTED, phone gates
deferred and writableDR/Android voter/GC/failover locked; no new release/APK.

## 5.3 private maintenance source/synthetic scoped PASS
7fresh maintenance cases PASS39.055s,5original upgrade regressions PASS (initial
selector run additionally had one loader-name error), corrected exact0.4.2->CURRENT
source/NEW-state rollback1PASS24.651s.13scoped cases, no full-regression claim.
Actual installed TLS/file I/O/identity/Controller+Node upgrade and local ACK retry,
new writes/code-only rollback, interruption/recovery, stale/CAS/backup/guard refusal.
No journal/DB formats changed or original tests weakened. No real SSH/VPN/phone/
Termux/APK/Core maintenance, release or production acceptance. Full Phase5 remains
NOT ACCEPTED pending5.4fresh gates and external/physical scope; see owner guide.

5.3 final clean regression command (corrected selector)6PASS0skip/fail59.551s.
Together with7targeted PASS39.055s this supersedes the initial selector-error run
for final qualification;13distinct cases, no double counting. No full-suite claim.

5.3b final-current-source:8maintenance PASS49.868s +6original upgrade/fault/exact
current-source compatibility PASS59.793s,0skip/fail. Reproduced prior extra lock on
unmarked state1FAIL4.892s and fixed pre-lock marker/binding validation; synthetic
unmarked/recovery-marker/unbound paths remain untouched.14distinct final cases,
not cumulative with earlier passes. Full5.4/real connectivity/phone gates pending.

## Separate distribution5.4d.2 — Linux internal candidate
Dedicated Linux Access0.1.0-internal closes the historical missing-guides/lock gap.
8package cases PASS7.349s, shipped wrapper lifecycle1 and nested original42access
cases PASS in208.918s integration driver (nested42=191.963s).51leaf executions,
0skip/fail; prior445full reused only identical runtime/legacy test bytes, not new
full496. Exact shipped candidate146files/127runtime modules/8guides+README/lock,
SHA d6f751d7bd93f3f438bec1c983b05b133b209870fe164cf7ea4bcf9e268e10d9,
private state/credentials0findings. Candidate byte-identical to active installed
regression archive; manifest/source members checked. See distribution receipt/
latest progress for normal push and REQUIRED fresh remote-download verification.
No new APK, live Cloudflare/SSH/VPN/provider, phone/production or migration scope.

Distribution publication verified at artifactfd5ca25213c680ea212636b292db1d20450220f7:
normal push/fetch/advertised HEAD match, fresh HTTPS download archive +checksum
byte-equal, SHA d6f751d7bd93f3f438bec1c983b05b133b209870fe164cf7ea4bcf9e268e10d9.
Downloaded bundle's actual safe unpack/env/verify and exact source rebuild PASS.
Linux INTERNAL DISTRIBUTION accepted in that scope; overall/live/device/production
Phase5 scope unchanged. No new APK or public management/service configuration.


## Separate source checkpoint5.4e — operator-local diagnostic qualified
10new checker cases PASS31.660s plus28unchanged access regression PASS85.849s,
38distinct cases/0skip/fail. Initial1FAIL/1ERROR fixed in new checker only; see
PROGRESS/qualification/phase5-access-check.json. Actual loopback TLS with existing
Controller/Dashboard/Storage Nodes; no live provider/JWT issuer call by checker.
Offline no-write/no-network, pin/mode/key/CA/path/permission/service-loss and
negative anonymous-gate/malformed-mode refusals. This is source-only tooling, not
a new artifact/full suite/Go/Android qualification or deployment approval. Existing
runtime and published0.1.0 bytes unchanged. Phase5 overall remains PARTIAL; VPN/
SSH/Cloudflare/IdP/DNS/phone/hardware/production and writableDR not accepted.
