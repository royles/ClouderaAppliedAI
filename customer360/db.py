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
    # FastAPI runs sync route handlers in a worker thread; allow this connection
    # to be opened from the dependency generator and used in the same request.
    conn = sqlite3.connect(path, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    for pragma in (
        "PRAGMA busy_timeout = 30000",
        "PRAGMA journal_mode = WAL",
        "PRAGMA synchronous = NORMAL",
        "PRAGMA cache_size = -64000",
        "PRAGMA temp_store = MEMORY",
    ):
        try:
            conn.execute(pragma)
        except sqlite3.Error:
            # Corrupt or partial files may reject tuning PRAGMAs; still allow integrity checks.
            pass
    return conn


def sqlite_table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return row is not None
