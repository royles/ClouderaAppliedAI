"""SQLite access helpers for the Customer 360 warehouse."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from customer360.paths import default_db_path


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or default_db_path()
    if not path.is_file():
        raise FileNotFoundError(
            f"Database not found at {path}. Run 2_job-init-database/init_database.py first."
        )
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn
