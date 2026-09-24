from __future__ import annotations

import logging
import os
import re

# Uvicorn access log request line: GET / HTTP/1.1 or GET /?query HTTP/1.1
_ROOT_GET = re.compile(r'"GET /(?:\?[^\s"]*)?\s+HTTP/')


def _is_live_alerts_poll(msg: str) -> bool:
    if "GET /api/alerts" not in msg:
        return False
    return "live=true" in msg and "since_id=" in msg


class SuppressRepeatedRootAccessFilter(logging.Filter):
    """Suppress noisy high-frequency access lines (SPA root, live alert polls)."""

    _root_heartbeat_logged: bool = False
    _live_poll_heartbeat_logged: bool = False

    def filter(self, record: logging.LogRecord) -> bool:
        if os.environ.get("BANKING_CONTROL_LOG_ALL_ACCESS", "").strip().lower() in (
            "1",
            "true",
            "yes",
        ):
            return True
        msg = record.getMessage()
        if _ROOT_GET.search(msg):
            if not SuppressRepeatedRootAccessFilter._root_heartbeat_logged:
                SuppressRepeatedRootAccessFilter._root_heartbeat_logged = True
                return True
            return False
        if _is_live_alerts_poll(msg):
            if not SuppressRepeatedRootAccessFilter._live_poll_heartbeat_logged:
                SuppressRepeatedRootAccessFilter._live_poll_heartbeat_logged = True
                return True
            return False
        return True
