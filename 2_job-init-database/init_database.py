"""CAI job: build the SQLite Customer 360 warehouse from DDS-aligned schema."""

from __future__ import annotations

import argparse
import importlib.util
import os
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
    raise RuntimeError(
        "Project root not found. cd to the repo, set CDSW_PROJECT, or run this file as "
        "python 2_job-init-database/init_database.py"
    )


_bootstrap()

from customer360.paths import default_db_path, project_root
from customer360.seed import (
    DEFAULT_SEED_CUSTOMERS,
    MAX_SEED_CUSTOMERS,
    init_database,
)


def _default_customer_count() -> int:
    raw = os.environ.get("CUSTOMER360_SEED_CUSTOMERS")
    if raw is not None and str(raw).strip() != "":
        return int(raw)
    return DEFAULT_SEED_CUSTOMERS


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help="SQLite database path (default: CUSTOMER360_DB_PATH or data/customer360.db)",
    )
    parser.add_argument(
        "--no-rebuild",
        action="store_true",
        help="Append to existing DB without deleting (schema still applied)",
    )
    parser.add_argument(
        "--customers",
        type=int,
        default=None,
        metavar="N",
        help=(
            f"Number of current customers to generate (max {MAX_SEED_CUSTOMERS}). "
            f"If omitted, uses CUSTOMER360_SEED_CUSTOMERS or {DEFAULT_SEED_CUSTOMERS}."
        ),
    )
    args = parser.parse_args()

    db_path = args.db or default_db_path()
    customer_count = (
        args.customers if args.customers is not None else _default_customer_count()
    )

    print(f"Project root: {project_root()}", flush=True)
    print(f"Initializing database at {db_path}", flush=True)
    print(f"Target customers: {customer_count}", flush=True)
    print(f"Rebuild (delete existing file): {not args.no_rebuild}", flush=True)

    init_database(
        db_path,
        rebuild=not args.no_rebuild,
        customer_count=customer_count,
    )


if __name__ == "__main__":
    main()
