#!/usr/bin/env python3
"""Refresh precomputed API caches on an existing warehouse (no full reseed)."""

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


def main() -> None:
    _bootstrap()
    from customer360.db import connect
    from customer360.metrics_refresh import refresh_all_api_caches
    from customer360.paths import default_db_path

    db_path = default_db_path()
    print(f"Refreshing API caches for {db_path}…", flush=True)
    with connect(db_path) as conn:
        summary = refresh_all_api_caches(conn)
    for key, value in summary.items():
        print(f"  {key}: {value}", flush=True)


if __name__ == "__main__":
    main()
