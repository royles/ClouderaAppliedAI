#!/usr/bin/env python3
"""Launch Banking Control Solution (FastAPI + static UI)."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import uvicorn  # noqa: E402


def _load_app():
    api_path = ROOT / "4_application" / "api.py"
    spec = importlib.util.spec_from_file_location("banking_control_api", api_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load API module from {api_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.app


def _port() -> int:
    for key in ("CDSW_APP_PORT", "APP_PORT", "PORT"):
        val = os.environ.get(key)
        if val:
            return int(val)
    return 8080


def main() -> None:
    host = os.environ.get("BANKING_CONTROL_HOST", "127.0.0.1")
    uvicorn.run(
        _load_app(),
        host=host,
        port=_port(),
        reload=False,
    )


if __name__ == "__main__":
    main()
