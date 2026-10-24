#!/data/data/com.termux/files/usr/bin/sh
# Owner-run entry point. Linux synthetic fixture invokes this with sh explicitly.
set -eu
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Python missing. Review Termux source; manually install python and openssl. Nothing installed.' >&2
  exit 2
fi
DEMO_SOURCE_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
export PYTHONDONTWRITEBYTECODE=1
cd "$DEMO_SOURCE_ROOT"
exec python3 -m asc.demo.cli "$@"
