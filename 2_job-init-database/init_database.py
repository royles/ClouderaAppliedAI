#!/usr/bin/env python3
"""CAI stage: seed banking control SQLite warehouse."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from banking_control.paths import default_db_path  # noqa: E402
from banking_control.seed import init_database  # noqa: E402

if __name__ == "__main__":
    path = init_database(default_db_path(), rebuild=True)
    print(f"Seeded {path}")
