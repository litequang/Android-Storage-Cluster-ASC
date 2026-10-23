#!/data/data/com.termux/files/usr/bin/bash
# ASC QuickStart, idempotent for existing identities. Production M51 audit only.
set -euo pipefail
MODE="${1:-audit}"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL="$(getprop ro.product.model 2>/dev/null || true)"
BRAND="$(getprop ro.product.manufacturer 2>/dev/null || true)"
SDK="$(getprop ro.build.version.sdk 2>/dev/null || true)"
DEVICE="$(getprop ro.product.device 2>/dev/null || true)"
PRODUCT="$(getprop ro.product.name 2>/dev/null || true)"
HARDWARE="$MODEL $BRAND $DEVICE $PRODUCT"
case "${HARDWARE,,}" in
  *sm-m515*|*m51*)
    if [[ "$MODE" != "audit" ]]; then
      echo 'M51 is PRODUCTION PROTECTED. Refusing package updates, installs and service changes.' >&2
      echo 'Run bash install.sh audit only; separate authorized integration phase is required.' >&2
      exit 3
    fi
    ;;
esac
if [[ "$MODE" == 'audit' ]]; then
  echo 'ASC read-only quick audit'
  echo "Model: $MODEL"
  command -v getprop >/dev/null && getprop ro.build.version.release || true
  command -v python3 >/dev/null && (cd "$SRC" && PYTHONDONTWRITEBYTECODE=1 python3 -m asc.cli inspect) || true
  exit 0
fi
if [[ "$MODE" != 'controller' && "$MODE" != 'node' ]]; then
  echo 'Usage: bash install.sh audit|controller|node [node join arguments]' >&2; exit 2
fi
# Fail closed: missing identity must never turn a protected M51 into an install target.
if [[ -z "$MODEL" || -z "$BRAND" || "${MODEL,,}" == 'unknown' || "${BRAND,,}" == 'unknown' ||
      "${MODEL,,}" == 'null' || "${BRAND,,}" == 'null' || ! "$SDK" =~ ^[0-9]+$ ]]; then
  echo 'Device identity UNKNOWN: refusing install. Read-only audit is available; no override.' >&2
  exit 3
fi
if ((10#$SDK < 24)); then
  echo 'Android SDK below 24: install refused.' >&2; exit 3
fi
command -v pkg >/dev/null || { echo 'Requires Termux pkg'; exit 2; }
MISSING=()
command -v python3 >/dev/null || MISSING+=(python)
command -v openssl >/dev/null || MISSING+=(openssl)
if ((${#MISSING[@]})); then
  echo "Missing dependencies: ${MISSING[*]}" >&2
  echo "On a confirmed NON-M51 test phone, install manually: pkg install ${MISSING[*]}" >&2
  echo 'No packages installed or upgraded by ASC.' >&2
  exit 2
fi
DEST="$HOME/asc-cluster"
if [[ -e "$DEST" && ! -f "$DEST/asc/__init__.py" ]]; then
  echo "$DEST exists but is not ASC; refusing to overwrite" >&2; exit 3
fi
if [[ ! -e "$DEST" ]]; then
  mkdir -m 700 "$DEST"
  cp -R "$SRC/asc" "$DEST/asc"
  cp -R "$SRC/docs" "$DEST/docs"
  cp -R "$SRC/scripts" "$DEST/scripts"
  cp "$SRC/AGENTS.md" "$SRC/README-VI.md" "$DEST/"
  echo "Installed source into $DEST"
else
  echo 'ASC already exists; preserving files and identity. Upgrade via reviewed release, not reinstall.'
  if ! python3 -c 'import pathlib,sys; sys.exit(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8-sig").strip() != pathlib.Path(sys.argv[2]).read_text(encoding="utf-8-sig").strip())' "$SRC/asc/__init__.py" "$DEST/asc/__init__.py"; then
    echo 'Installed release differs. Follow README versioned-directory upgrade; no code overwritten.' >&2
    exit 3
  fi
fi
cd "$DEST"
export PYTHONDONTWRITEBYTECODE=1
case "$MODE" in
  controller) python3 -m asc.cli controller-init ;;
  node) shift; python3 -m asc.cli node-join "$@" ;;
esac
