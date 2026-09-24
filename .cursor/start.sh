#!/usr/bin/env bash
# Per-boot startup for the Cloudera Applied AI API server.
# Runs as a visible tmux terminal so logs and lifecycle stay inspectable.
set -euo pipefail

cd "$(dirname "$0")/.."

# shellcheck disable=SC1091
. .venv/bin/activate

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
