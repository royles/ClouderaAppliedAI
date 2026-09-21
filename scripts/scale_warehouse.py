#!/usr/bin/env python3
"""Rebuild the warehouse at scale (default 5000 customers) and score churn."""

from __future__ import annotations

import argparse
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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed SQLite warehouse with N representative customers (from synthetic DDS patterns)."
    )
    parser.add_argument(
        "--customers",
        type=int,
        default=5000,
        help="Current customers to generate (default 5000)",
    )
    parser.add_argument(
        "--skip-churn",
        action="store_true",
        help="Only rebuild warehouse; do not run churn training job",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help="Database path (default CUSTOMER360_DB_PATH)",
    )
    args = parser.parse_args()

    root = _bootstrap()
    from customer360.paths import default_db_path
    from customer360.seed import init_database

    db_path = args.db or default_db_path()
    init_database(db_path, rebuild=True, customer_count=args.customers)

    if args.skip_churn:
        print("Skipping churn training (--skip-churn).", flush=True)
        return

    train_job = root / "3_job-train-churn-model" / "train_churn.py"
    if not train_job.is_file():
        print(f"Churn job not found at {train_job}; run training manually.", flush=True)
        return

    print("Training churn model and writing APP_CUSTOMER_CHURN_SCORES…", flush=True)
    subprocess.check_call([sys.executable, str(train_job)])


if __name__ == "__main__":
    main()
