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

## DEMO.2 source CLI workflow (final package pending DEMO.3)

The installer preview archive above intentionally has no cluster commands. Use only
the later final qualified package for owner phone trials. The source implementation
now provides the following LAN sequence. Every terminal must define:

```sh
ascdemo() { sh "$HOME/.local/share/asc-demo/bin/asc-demo" "$@"; }
```

Choose the Controller ZTE's private Wi-Fi IP, e.g. 192.168.1.20. Use another unused
private IP for Bphone, e.g. 192.168.1.21; examples are placeholders, never public IPs.
Controller terminal:

```sh
ascdemo init --role controller --host 192.168.1.20
ascdemo run-controller
```

Leave the foreground running. In another ZTE terminal, request `ascdemo pair`.
Privately copy its origin/pin and enter the one-time code at the joining prompt:

```sh
ascdemo join --controller https://192.168.1.20:8443 --pin CONTROLLER_PIN --name ZTE-demo-storage
ascdemo storage-init --host 192.168.1.20 --quota 268435456 --reserve 67108864
ascdemo run-node
```

On Bphone after verified install:

```sh
ascdemo init --role node --host 192.168.1.21
# Obtain a NEW pair code from ZTE, then enter it at the join prompt.
ascdemo join --controller https://192.168.1.20:8443 --pin CONTROLLER_PIN --name Bphone-demo-storage
ascdemo storage-init --host 192.168.1.21 --quota 268435456 --reserve 67108864
ascdemo run-node
```

Storage setup prints volume ID, Storage pin and tested capabilities. On ZTE owner
terminal, use `ascdemo nodes` for enrolled node IDs. Approve each with its exact
volume ID/pin and a physical domain label (e.g. zte-phone / bphone-phone):

```sh
ascdemo approve --node-id NODE_ID --volume-id VOLUME_ID --origin https://192.168.1.21:9443 --pin STORAGE_PIN --domain bphone-phone
```

Repeat approval for the ZTE storage endpoint with domain zte-phone. Two volumes on
one phone must share the same label. Actual SD use is optional: only a NEW empty
subdirectory inside an already accessible Termux SD app-folder may be selected via
`storage-init --kind termux_sd --root APPROVED_EMPTY_APP_FOLDER ...`; do not use
shared media/photo folders or existing data. Internal default uses node/data only.
No SD permission changes, writes outside approval, formatting or SAF promise.

Use a small disposable file available to Termux; never important/private files:

```sh
ascdemo upload "$HOME/demo-input.txt" demo/input.txt --key unique-demo-upload-001
ascdemo files
ascdemo replicas FILE_ID
ascdemo download FILE_ID "$HOME/new-demo-output.txt"
sha256sum "$HOME/demo-input.txt" "$HOME/new-demo-output.txt"
```

Success reports protected=true only after two verified available physical domains.
Incomplete replication returns exit 4; retry the same key/file, retain state.
The output filename must be new. When one node stops, download may use the surviving
copy while Controller is up; new uploads need two eligible phones. Stop processes
with Ctrl+C in each foreground terminal; stop node agents, then Controller, before
backup/upgrade. No boot registration or automatic restart/failover is installed.
