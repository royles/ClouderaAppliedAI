#!/usr/bin/env python3
"""Local CLI wrapper — prefer 2_job-init-database/init_database.py on Cloudera AI."""

from __future__ import annotations

import importlib.util
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

from customer360.seed import main

if __name__ == "__main__":
    main()
