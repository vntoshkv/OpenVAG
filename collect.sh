#!/usr/bin/env bash
# One-command read-only collector for the Wi-Fi and Bluetooth ELM327 adapters.
#
# Creates/uses .venv, installs the optional serial extra, then runs the
# interactive collector. All arguments are forwarded, for example:
#   ./collect.sh --no-serial
#   ./collect.sh --no-wifi --serial /dev/cu.ELM327-XXXX
#   ./collect.sh --yes
#
# macOS/Linux only. On Windows, run the same Python script after installing
# the extras manually: python -m pip install -e ".[serial]"

set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

if ! python -c "import serial" >/dev/null 2>&1; then
  echo "Installing optional serial support (first run only)..."
  python -m pip install --quiet --upgrade pip setuptools wheel
  python -m pip install --quiet -e '.[serial]'
fi

exec python scripts/collect_logs.py "$@"
