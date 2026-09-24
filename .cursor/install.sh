#!/usr/bin/env bash
# Idempotent environment bootstrap for the Cloudera Applied AI service.
# Safe to run repeatedly and against cached/snapshotted state.
set -euo pipefail

cd "$(dirname "$0")/.."

# The Cursor default image ships Python 3.12 but not the venv module.
# Ensure it is present (no-op when already installed, e.g. from a snapshot).
if ! python3 -c 'import ensurepip' >/dev/null 2>&1; then
  echo "Installing python3-venv..."
  sudo apt-get update
  sudo apt-get install -y --no-install-recommends python3-venv
fi

# Create or reuse the virtual environment.
python3 -m venv .venv
# shellcheck disable=SC1091
. .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Train and persist the model so the API can serve predictions immediately.
python -m scripts.train

echo "Install complete. Activate with: source .venv/bin/activate"
