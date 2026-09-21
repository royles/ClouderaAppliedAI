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
    import sqlite3
    import time

    from customer360.db import connect
    from customer360.kpi_benchmarks import ensure_kpi_benchmark_catalog
    from customer360.metrics_refresh import refresh_all_api_caches
    from customer360.paths import default_db_path

    db_path = default_db_path()
    print(f"Refreshing API caches for {db_path}…", flush=True)

    last_error: sqlite3.OperationalError | None = None
    for attempt in range(5):
        try:
            conn = connect(db_path)
            try:
                ensure_kpi_benchmark_catalog(conn)
                summary = refresh_all_api_caches(conn)
            finally:
                conn.close()
            for key, value in summary.items():
                print(f"  {key}: {value}", flush=True)
            return
        except sqlite3.OperationalError as exc:
            last_error = exc
            if "locked" not in str(exc).lower():
                raise
            wait_s = 2**attempt
            print(
                f"Database busy (attempt {attempt + 1}/5), retrying in {wait_s}s…",
                flush=True,
            )
            time.sleep(wait_s)

    if last_error is not None:
        raise last_error


if __name__ == "__main__":
    main()
