"""Ensure churn scores exist after warehouse load or cache refresh."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from customer360.db import sqlite_table_exists
from customer360.paths import default_db_path


def churn_table_exists(conn: sqlite3.Connection) -> bool:
    return sqlite_table_exists(conn, "APP_CUSTOMER_CHURN_SCORES")


def churn_scores_populated(conn: sqlite3.Connection) -> bool:
    if not churn_table_exists(conn):
        return False
    count = conn.execute("SELECT COUNT(*) FROM APP_CUSTOMER_CHURN_SCORES").fetchone()[0]
    return int(count or 0) > 0


def try_train_and_score_churn(db_path: Path | None = None) -> bool:
    """Train the churn model and write APP_CUSTOMER_CHURN_SCORES. Returns True on success."""
    db_path = db_path or default_db_path()
    try:
        from customer360.churn.model import train_and_persist

        train_and_persist(db_path)
        return True
    except Exception:
        return False
