"""Shared checks for precomputed APP_CUSTOMER_METRICS cache."""

from __future__ import annotations

import sqlite3

from customer360.db import sqlite_table_exists


def customer_metrics_populated(conn: sqlite3.Connection) -> bool:
    if not sqlite_table_exists(conn, "APP_CUSTOMER_METRICS"):
        return False
    row = conn.execute("SELECT COUNT(*) FROM APP_CUSTOMER_METRICS").fetchone()
    return int(row[0] or 0) > 0
