from __future__ import annotations

import logging
import os
import re

# Uvicorn access log request line: GET / HTTP/1.1 or GET /?query HTTP/1.1
_ROOT_GET = re.compile(r'"GET /(?:\?[^\s"]*)?\s+HTTP/')


class SuppressRepeatedRootAccessFilter(logging.Filter):
    """Log the first GET / (SPA / health probe) then suppress further root hits."""

    _heartbeat_logged: bool = False

    def filter(self, record: logging.LogRecord) -> bool:
        if os.environ.get("BANKING_CONTROL_LOG_ALL_ACCESS", "").strip().lower() in (
            "1",
            "true",
            "yes",
        ):
            return True
        msg = record.getMessage()
        if not _ROOT_GET.search(msg):
            return True
        if not SuppressRepeatedRootAccessFilter._heartbeat_logged:
            SuppressRepeatedRootAccessFilter._heartbeat_logged = True
            return True
        return False
