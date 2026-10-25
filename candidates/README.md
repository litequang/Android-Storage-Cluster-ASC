# Phase4 source-only synthetic candidate

0.4.2-dev is a reproducible source candidate on the integration feature branch,
NOT a public Android release, Android runtime acceptance or production build.
No GitHub Release/tag is created. Core/Demo original branches/releases stay intact.
Use docs/PHASE4-ACCEPTANCE and PHASE4-PROGRESS for current qualification, exact
source commit and any remaining blockers. Do not infer PASS from this directory.
No phone installation or upgrade is performed by Codex Cloud.

Build from the qualified source (new output path required):

```sh
python -B -m asc.demo.package /approved/new/asc-demo-alpha-0.4.2-dev.tar.gz
```

Version0.4.2-dev,106 regular source/doc/asset files; no binaries, private state,
keys, credentials, backups, user bytes or logs. Manifest format1, unchanged state
formats; extra quick-join-foundation capability. Existing Core3D source is kept
inside the package but its passive recovery is never a Demo writable runtime.
SHA-256b7904a82c55e41866b374ecb42b873a6796a4f8e5e53a213f648e026467a64a3.
Release IDf550f565836b44dc582001e3adabb34e1a594441bdd52dbfff51700b7c1e19c7.
Verify SHA against the independent trusted handoff before extraction, then let
installer/stager verify every release.json file hash. Read the packaged
PHASE4-QUICK-JOIN guide before the historical Demo README instructions.
Only exact published0.4.1 ->this candidate and compatible NEW-state code rollback
are planned qualification paths; consult acceptance for actual results. Existing
historical03/04->04.1 archive regression remains separate and unchanged.
