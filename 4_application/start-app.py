#!/usr/bin/env python3
"""Launch Banking Control Solution (FastAPI + static UI)."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

_SCRIPT = globals().get("__file__")


def _load_ensure_project_on_path():
    try:
        from banking_control.cai_bootstrap import ensure_project_on_path

        return ensure_project_on_path
    except ImportError:
        pass

    seeds: list[Path] = []
    if _SCRIPT:
        seeds.append(Path(_SCRIPT).resolve().parent.parent)
    for key in ("CDSW_PROJECT", "BANKING_CONTROL_PROJECT"):
        env = os.environ.get(key)
        if env:
            seeds.append(Path(env).expanduser().resolve())
    seeds.append(Path.cwd())

    for seed in seeds:
        for root in (seed, *seed.parents):
            bootstrap = root / "banking_control" / "cai_bootstrap.py"
            if not bootstrap.is_file():
                continue
            spec = importlib.util.spec_from_file_location(
                "banking_control.cai_bootstrap", bootstrap
            )
            if spec is None or spec.loader is None:
                continue
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod.ensure_project_on_path

    raise RuntimeError(
        "Cannot locate banking_control/cai_bootstrap.py. "
        "Set CDSW_PROJECT to the repository root or run the Install dependencies task first."
    )


ROOT = _load_ensure_project_on_path()(_SCRIPT)

import uvicorn  # noqa: E402
from banking_control.api.factory import create_app  # noqa: E402


def _port() -> int:
    for key in ("CDSW_APP_PORT", "APP_PORT", "PORT"):
        val = os.environ.get(key)
        if val:
            return int(val)
    return 8080


def main() -> None:
    host = os.environ.get("BANKING_CONTROL_HOST", "127.0.0.1")
    uvicorn.run(
        create_app(),
        host=host,
        port=_port(),
        reload=False,
    )


if __name__ == "__main__":
    main()
