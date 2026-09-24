#!/usr/bin/env python3
"""CAI stage 1: install Python dependencies for Banking Control Solution."""

from __future__ import annotations

import importlib.util
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


def main() -> None:
    req = ROOT / "requirements.txt"
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req)])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", str(ROOT)])
    print("Banking Control dependencies installed.")


if __name__ == "__main__":
    main()
