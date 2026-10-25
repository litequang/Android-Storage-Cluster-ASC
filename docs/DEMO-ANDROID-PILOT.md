# Owner-only Android pilot record — blank / NOT TESTED

Codex must not access, SSH, install or read a real phone. This is a manual checklist
for the project owner after the exact release package has completed Linux acceptance.
Only disposable non-important files, isolated LAN and dedicated approved directories.
Never Samsung M51, production hosting, unknown-device overrides, root/format/GC,
public management ports, Termux:Boot or uncontrolled power-cut/SD removal.

Read DEMO-QUICKSTART.md first; record the package SHA and release/content ID from
DEMO4-ACCEPTANCE.md. ZTE/Bphone are the initial two-phone pilot. Sony is optional.
No Android PASS is claimed by this blank form or by a Go cross-build.

| Observation | ZTE V40 | Bphone A40 | Sony XZ3 (optional) |
|---|---|---|---|
| Actual Android SDK / Termux source/version / Python / OpenSSL | NOT TESTED | NOT TESTED | NOT TESTED |
| Exact package SHA verified / preflight allowed | NOT TESTED | NOT TESTED | NOT TESTED |
| Internal volume write/readback/identity | NOT TESTED | NOT TESTED | NOT TESTED |
| Optional approved SD app-folder / unavailable state | NOT TESTED | NOT TESTED | NOT TESTED |
| Enrollment / pinned TLS / heartbeat | NOT TESTED | NOT TESTED | NOT TESTED |
| Same-package reinstall preserves identities | NOT TESTED | NOT TESTED | NOT TESTED |
| Verified public Dashboard CA trust / HTTPS / owner login | NOT TESTED | NOT TESTED | NOT TESTED |
| Dashboard mobile UI / upload / two replicas / download SHA | NOT TESTED | NOT TESTED | NOT TESTED |
| 0.3.0 → 0.4.0 upgrade and old-code/new-state rollback | NOT TESTED | NOT TESTED | NOT TESTED |
| Foreground stop/restart retains state | NOT TESTED | NOT TESTED | NOT TESTED |
| Private stopped backup + readback verification | NOT TESTED | NOT TESTED | NOT TESTED |
| Future qualified compatible source upgrade/code rollback | NOT TESTED | NOT TESTED | NOT TESTED |

## Controlled functional gates

1. Prepare supported Termux/dependencies manually on test phones only; no installer
   package upgrades or system permission changes. If guard refuses, preserve state
   and stop. Confirm code and private state are separate; no legacy ASC_HOME adoption.
2. Start ZTE Controller plus its separately enrolled Storage Node and Bphone node.
   Approve actual pins/volume IDs with two confirmed different phone-domain labels.
3. Upload a small disposable file; retain logical file ID/key and expected SHA privately.
   Require two VERIFIED/available replicas and protected=true before declaring the
   pilot copy gate PASS. Download a NEW output and compare SHA-256.
4. Ctrl+C one Storage Node. Request replicas/reconcile: DEGRADED, survivor download
   exact SHA, new upload denied with only one eligible domain. Heartbeat offline
   display may lag by the Core freshness window; it is not an instantaneous probe.
   Restart original node and reconcile; never delete markers or substitute a volume.
5. Stop the Controller while storage agents stay running. New upload/download
   authorization must fail; no node becomes Controller. Restart the SAME Controller
   and nodes as needed, then verify old file/SHA/replicas and identity retention.
6. Stop all foreground processes. Backup each phone into a NEW private directory
   with sufficient actual free space; verify it. Reinstall the exact same package:
   keys/IDs/pins/volume markers/file bytes must remain unchanged after restart.
7. Real-phone 0.3.0 -> 0.4.0 upgrade/code rollback remains NOT TESTED. Only use
   both independently qualified packages and follow QuickStart 6a. Do not edit
   manifests/source to invent a compatible release. Linux synthetic candidate/crash evidence is not Android upgrade acceptance.
8. If optional SD is inaccessible, record UNKNOWN/unavailable and use internal.
   Do not remove active media, format, alter permissions, rewrite a marker, or test
   destructive GC. Any future removal/power-cut qualification needs a separate plan.

Record observed results and limits, not assumed PASS. If a gate fails, stop that
flow, preserve private state/releases and collect only `ascdemo diagnose` output
(after owner review). Do not publish tokens, pair codes, configs, raw logs, database,
backup, profile, network addresses or file names in a report. Full production,
Android power-cut/Doze/24x7 durability and external DR remain outside this pilot.

## Existing installer-preview prefix

Preview 0.1.0 never initialized cluster state and cannot upgrade an initialized
cluster. If its code prefix already exists, do not overwrite/delete it. From the
verified final unpacked package, select a NEW code prefix instead:

```sh
sh scripts/demo-alpha.sh install --prefix "$HOME/.local/share/asc-demo-alpha-0.4" --dry-run
sh scripts/demo-alpha.sh install --prefix "$HOME/.local/share/asc-demo-alpha-0.4"
ascdemo() { sh "$HOME/.local/share/asc-demo-alpha-0.4/bin/asc-demo" "$@"; }
```

Then follow QuickStart using this function in each terminal. Existing `.asc-demo`
state, if any, must already match the exact Demo contract; never delete/reinitialize
it to work around a refusal. The complete Core `.asc` remains untouched. Future
compatible initialized Demo upgrades use stage/upgrade with a full stopped backup,
not a fresh installer overwrite. This exception changes only source-prefix selection,
not identity or schema migration.

## DEMO.4 owner browser pilot (all NOT TESTED on phones)

Follow QuickStart 5a and 6a. Verify public CA fingerprint outside browser, then
owner imports only that CA. TLS warning/wrong IP/untrusted CA must block login.
Use one-use dashboard-code, never node/admin token. Record overview UNKNOWN handling,
node/volume details, actual small upload, distinct phones/domains and two replicas,
browser download plus independent SHA comparison. Stop a node and verify degraded
state/fallback/new-upload refusal; stop Controller and verify no new writer. Test
logout/session expiry, desktop/mobile layout and repeat after stopped compatible
upgrade/code rollback. Keep original identities and both old/new files. No public
port/tunnel or TLS exception. Linux Chromium success does not prefill any result.
