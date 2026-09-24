#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
bash scripts/ensure_branch.sh
bash scripts/setup_git_hooks.sh
python3 -m pip install -r requirements.txt
python3 -m pip install -e .
python3 scripts/init_db.py
echo "Banking Control ready on branch $(git branch --show-current)."
