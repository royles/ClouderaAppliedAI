#!/usr/bin/env python3
"""Initialize or rebuild the banking control demo database."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from banking_control.paths import default_db_path  # noqa: E402
from banking_control.seed import init_database  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed banking control SQLite warehouse")
    parser.add_argument("--rebuild", action="store_true", help="Delete existing DB and reseed")
    parser.add_argument("--db", type=Path, default=None, help="Override database path")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()
    path = init_database(args.db or default_db_path(), rebuild=args.rebuild, seed=args.seed)
    print(f"Database ready: {path}")


if __name__ == "__main__":
    main()
