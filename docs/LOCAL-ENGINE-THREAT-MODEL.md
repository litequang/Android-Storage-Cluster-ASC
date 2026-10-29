# Phase4.1 local engine / quorum observer threat model

Assets: node/admin/IPC/private TLS keys, enrollment context, cluster/volume identity,
object bytes/retention, current authority and accurate user-facing evidence.
Actors: owner browser session, local native application grant, node machine identity,
configured Core Controllers/voters, untrusted LAN/website/app, trusted owning OS UID.
Owning privileged account can replace source/state; this is not a hostile-admin sandbox.

| Threat | Boundary / fail-closed requirement |
|---|---|
| Website/DNS rebinding drives filesystem/process | No TCP local bridge, no CORS/browser route; filesystem UDS+same UID+app grant; fixed operations/roots |
| Same-UID unauthorized app / confused deputy | Per-app random separate credential/scopes; no node/admin token accepted as app grant; request ownership/digest binding |
| Malformed/duplicate/oversized input or shell/path injection | Strict version/type/key/frame/deadline/worker limits; no arbitrary argv/env/PID/path; fixed worker argv/no shell |
| Symlink/hardlink/socket replacement | Private owner-only no-follow checked directories/files, fixed socket identity; reject suspicious state, never unlink foreign socket/lock |
| Lost ACK/crash/replayed grant duplicates node | Existing durable enrollment operation/token and receipt verification; FULL request journal before dispatch, same-ID retry and bounded permanent receipts |
| Revoked/expired code or false approval | Existing Controller validates; explicit new-code preserves operation; no bridge volume/domain approval; pending/UNKNOWN reported honestly |
| Leaked local/app/enrollment credential | No argv/env/URL/log/browser storage; private files/UDS/stdin, response whitelist, no raw source config/error dump |
| Stale Leader/partition lies about writer | Strong upstream Barrier plus current-term/identity evidence; hint alone never authority; observer always read_only/writer_authority=false |
| Core/Demo mode confusion | Explicit configured modes and server discrimination; no fallback to Demo SQL or state copying |
| Recovery staging becomes live cluster | RECOVERY_READ_ONLY rejects bridge/runtime; observer reports passive state without starting/importing; no quorum/epoch/Leader reconstruction |
| PID reuse/bridge death leaves uncontrolled service | Only actual owned child; parent-death fence before exec, no PIDfile kill; no arbitrary runtime start |
| Rollback destroys new data/identity | Separate control roots, unchanged base schemas, exact archive tests/new full backup/code-only rollback; no stale DB restore |
| Browser XSS/CSRF/admin token exposure | Existing trusted HTTPS/CA, Secure HttpOnly SameSite owner cookie/CSRF/exact origin/CSP/textContent; sanitized read-only Core views |

Android cross-UID isolation, Binder/signature permission, Keystore, SAF grants,
foreground service/notification policy, Doze/network loss/OS kill and migration are
NOT qualified by Linux. No permission elevation, shared UID assumption, root,
world-writable socket, system changes or TLS bypass is an acceptable workaround.
All source/testing is synthetic, no M51/phone/production/private real data access.
