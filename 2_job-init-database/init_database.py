"""CAI job: build the SQLite Customer 360 warehouse from DDS-aligned schema."""

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
    raise RuntimeError(
        "Project root not found. cd to the repo, set CDSW_PROJECT, or run this file as "
        "python 2_job-init-database/init_database.py"
    )


_bootstrap()

import os

from customer360.paths import default_db_path, project_root
from customer360.seed import DEFAULT_SEED_CUSTOMERS, init_database


def main() -> None:
    db_path = default_db_path()
    customer_count = int(os.environ.get("CUSTOMER360_SEED_CUSTOMERS", DEFAULT_SEED_CUSTOMERS))
    print(f"Project root: {project_root()}", flush=True)
    print(f"Initializing database at {db_path}", flush=True)
    print(f"Target customers: {customer_count}", flush=True)
    init_database(db_path, rebuild=True, customer_count=customer_count)


if __name__ == "__main__":
    main()
