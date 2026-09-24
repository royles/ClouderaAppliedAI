"""Feature flags for the executive agent."""

from __future__ import annotations

import os


def agent_enabled() -> bool:
    raw = os.environ.get("CUSTOMER360_AGENT_ENABLED", "true").strip().lower()
    return raw not in ("0", "false", "no", "off")
