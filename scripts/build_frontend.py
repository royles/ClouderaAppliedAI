#!/usr/bin/env python3
"""Build the React frontend into frontend/dist (CAI session or local dev)."""

from __future__ import annotations

import importlib.util
import os
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
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    from customer360.node_toolchain import ensure_portable_npm, find_npm, run_npm

    frontend = root / "frontend"
    dist_index = frontend / "dist" / "index.html"
    force = os.environ.get("CUSTOMER360_FORCE_FRONTEND_REBUILD", "").lower() in (
        "1",
        "true",
        "yes",
    )

    if dist_index.is_file() and not force:
        print(
            f"Frontend already built at {dist_index}. "
            "Set CUSTOMER360_FORCE_FRONTEND_REBUILD=1 to rebuild.",
            flush=True,
        )
        return

    if not frontend.is_dir():
        raise FileNotFoundError(f"Missing frontend directory: {frontend}")

    npm = find_npm()
    if npm is None:
        print("npm not on PATH; installing portable Node.js under .tools/", flush=True)
        npm = ensure_portable_npm(root)
    else:
        print(f"Using npm: {npm}", flush=True)

    if (frontend / "package-lock.json").is_file():
        run_npm(npm, ["ci"], cwd=frontend)
    else:
        run_npm(npm, ["install"], cwd=frontend)
    run_npm(npm, ["run", "build"], cwd=frontend)

    if not dist_index.is_file():
        raise RuntimeError(f"Build finished but {dist_index} was not created.")
    print(f"Frontend built: {dist_index.parent}", flush=True)


if __name__ == "__main__":
    main()
