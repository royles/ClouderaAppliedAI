#!/usr/bin/env bash
# Exit non-zero if not on the Banking Control feature branch.
set -euo pipefail
TARGET="cursor/banking-control-solution-8b7c"
CURRENT="$(git branch --show-current 2>/dev/null || true)"
if [ "$CURRENT" != "$TARGET" ]; then
  echo "Expected branch '$TARGET' but on '${CURRENT:-detached}'." >&2
  echo "Run: git checkout $TARGET" >&2
  exit 1
fi
