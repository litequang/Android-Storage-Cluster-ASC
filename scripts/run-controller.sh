#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "${ASC_CODE:-$HOME/asc-cluster}"
export PYTHONDONTWRITEBYTECODE=1
exec python3 -m asc.cli controller-run
