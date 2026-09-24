#!/usr/bin/env python3
"""CAI stage 1: install Python dependencies for Banking Control Solution."""

from __future__ import annotations

import importlib.util
import os
import subprocess
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
        "Set CDSW_PROJECT to the repository root."
    )


ROOT = _load_ensure_project_on_path()(_SCRIPT)


def main() -> None:
    req = ROOT / "requirements.txt"
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req)])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", str(ROOT)])
    print("Banking Control dependencies installed.")


if __name__ == "__main__":
    main()
