#!/usr/bin/env python3
"""CAI stage: seed banking control SQLite warehouse."""

from __future__ import annotations

import importlib.util
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

from banking_control.paths import default_db_path  # noqa: E402
from banking_control.seed import init_database  # noqa: E402

if __name__ == "__main__":
    path = init_database(default_db_path(), rebuild=True)
    print(f"Seeded {path}")
