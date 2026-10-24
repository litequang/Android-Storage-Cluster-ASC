# ASC Demo Alpha — installer preview (DEMO.1)

This source-only preview installs immutable code. LAN cluster and upgrade commands
are not delivered yet. Android runtime is NOT TESTED; Linux fake-getprop tests do
not qualify real phones. Use only disposable files. No production/M51/unknown phone,
root, formatting, Termux:Boot, automatic packages, public ports, Raft or GC.

Owner preparation: obtain current supported Termux from its official distribution,
review it, then manually prepare Python >=3.10 and OpenSSL. Installer never runs
`pkg install` or `pkg upgrade`. Do not uninstall/replace an existing Termux or ASC.
ZTE V40 / Bphone A40 / Sony XZ3 trials are performed by the owner, never by Codex.

Download the archive and adjacent `.sha256` from the same verified Demo commit.
Before extraction run `sha256sum -c <archive>.sha256` and compare the expected digest
with the published checkpoint. Extract into a NEW empty source directory; do not
extract into an existing installation or private state. Do not pipe Internet scripts
into a shell. Inside the extracted `asc-demo-alpha` folder:

```sh
sh scripts/demo-alpha.sh preflight
sh scripts/demo-alpha.sh install --dry-run
sh scripts/demo-alpha.sh install
sh "$HOME/.local/share/asc-demo/bin/asc-demo" preflight
```

Preflight is read-only: internal/SD space is measured, never treated as proof of write
access; SD app-folder candidates may be missing/unavailable. No probe writes occur
until a later explicitly approved storage setup. M51/unknown identity/SDK<24 or missing
dependencies deny installation. No override exists. A rerun with identical package
verifies installed bytes and preserves state; another release requires a later
explicit stopped upgrade workflow. Do not alter installed release files.

Code: `~/.local/share/asc-demo/releases/<release_id>`; no private identity is created
by installation. Future Demo state uses a separate `~/.asc-demo` directory and is
never implicitly adopted from `~/.asc`. For rollback at this preview stage, simply
stop using the launcher; preserve all directories for review. No downgrade, schema
migration, Termux-to-APK or single-writer-to-Raft migration is implemented.

An interrupted source install may be retried with the exact same checked archive.
If integrity/path/state checks refuse, retain the directory and seek review rather
than deleting keys or overwriting it. No phones or production data were used by
Cloud qualification. This preview is not the final QuickStart Package.
