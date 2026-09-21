"""CAI application entrypoint — FastAPI (uvicorn) on the platform-injected port."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


def _bootstrap() -> None:
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
            mod.bootstrap(__file__)
        except NameError:
            mod.bootstrap(None)
        return
    raise RuntimeError("Project root not found (bootstrap_entry.py).")


_bootstrap()

from customer360.cai_runtime import application_port

port = application_port()

print(f"Starting Customer 360 API on 127.0.0.1:{port}", flush=True)

subprocess.check_call(
    [
        sys.executable,
        "-m",
        "uvicorn",
        "customer360.api.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--workers",
        "1",
    ]
)
