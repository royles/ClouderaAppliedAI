#!/usr/bin/env python3
"""Build the React frontend into frontend/dist (CAI session or local dev)."""

from __future__ import annotations

import importlib.util
import shutil
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


def main() -> None:
    root = _bootstrap().resolve()
    frontend = root / "frontend"
    npm = shutil.which("npm")
    if not npm:
        raise RuntimeError(
            "npm not found on PATH. Install Node.js in the CAI runtime or run "
            "`npm run build` in frontend/ from a session that has Node."
        )
    if not frontend.is_dir():
        raise FileNotFoundError(f"Missing frontend directory: {frontend}")

    if (frontend / "package-lock.json").is_file():
        subprocess.check_call([npm, "ci"], cwd=str(frontend))
    else:
        subprocess.check_call([npm, "install"], cwd=str(frontend))
    subprocess.check_call([npm, "run", "build"], cwd=str(frontend))
    dist = frontend / "dist" / "index.html"
    if not dist.is_file():
        raise RuntimeError(f"Build finished but {dist} was not created.")
    print(f"Frontend built: {dist.parent}", flush=True)


if __name__ == "__main__":
    main()
