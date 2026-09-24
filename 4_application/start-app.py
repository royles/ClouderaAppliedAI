"""CAI application entrypoint — FastAPI (uvicorn) on the platform-injected port."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path


def _bootstrap() -> Path:
    for candidate in (Path.cwd(), *Path.cwd().parents):
        path = candidate / "bootstrap_entry.py"
        if not path.is_file():
            continue
        spec = importlib.util.spec_from_file_location("bootstrap_entry", path)
        if spec is None or spec.loader is None:
            continue
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        try:
            return mod.bootstrap(__file__)
        except NameError:
            return mod.bootstrap(None)
    raise RuntimeError("Project root not found (bootstrap_entry.py).")


ROOT = _bootstrap()

from banking_control.cai_runtime import application_port  # noqa: E402

host = os.environ.get("BANKING_CONTROL_HOST", "127.0.0.1")
port = application_port()

print(f"Starting Banking Control Solution on {host}:{port}", flush=True)

log_config = ROOT / "banking_control" / "uvicorn_log.json"

subprocess.check_call(
    [
        sys.executable,
        "-m",
        "uvicorn",
        "banking_control.api.main:app",
        "--host",
        host,
        "--port",
        str(port),
        "--workers",
        "1",
        "--log-config",
        str(log_config),
    ],
    cwd=str(ROOT),
)
