#!/usr/bin/env bash
# Enable repo-local hooks that keep Banking Control work on the feature branch.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
git config core.hooksPath .githooks
echo "Git hooks enabled (core.hooksPath=.githooks)."
echo "Banking Control commits must be on branch cursor/banking-control-solution-8b7c."
