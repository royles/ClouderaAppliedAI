"""Timestamps for warehouse, churn scores, and API caches (UI freshness strip)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from customer360.churn.scoring import churn_scores_populated, churn_table_exists
from customer360.data_source import resolve_sqlite_warehouse_path
from customer360.metrics_refresh import ensure_metrics_schema


def fetch_data_freshness(conn: sqlite3.Connection, *, database_path: Path | None = None) -> dict:
    db_path = database_path or resolve_sqlite_warehouse_path()
    ensure_metrics_schema(conn)

    warehouse_loaded_at: str | None = None
    manifest_ready = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='APP_WAREHOUSE_TABLE_MANIFEST'"
    ).fetchone()
    if manifest_ready:
        row = conn.execute(
            """
            SELECT MAX(LAST_LOADED_AT) AS ts
            FROM APP_WAREHOUSE_TABLE_MANIFEST
            WHERE LAYER = 'warehouse'
            """
        ).fetchone()
        if row and row["ts"]:
            warehouse_loaded_at = str(row["ts"])

    customer_metrics_at: str | None = None
    row = conn.execute(
        "SELECT MAX(REFRESHED_AT) AS ts FROM APP_CUSTOMER_METRICS"
    ).fetchone()
    if row and row["ts"]:
        customer_metrics_at = str(row["ts"])

    portfolio_cache_at: str | None = None
    row = conn.execute(
        "SELECT MAX(REFRESHED_AT) AS ts FROM APP_PORTFOLIO_ANALYTICS_CACHE"
    ).fetchone()
    if row and row["ts"]:
        portfolio_cache_at = str(row["ts"])

    churn_scored_at: str | None = None
    churn_customer_count = 0
    if churn_table_exists(conn) and churn_scores_populated(conn):
        row = conn.execute(
            """
            SELECT MAX(SCORED_AT) AS ts, COUNT(*) AS n
            FROM APP_CUSTOMER_CHURN_SCORES
            """
        ).fetchone()
        if row:
            churn_scored_at = str(row["ts"]) if row["ts"] else None
            churn_customer_count = int(row["n"] or 0)

    return {
        "database_path": str(db_path),
        "warehouse_loaded_at": warehouse_loaded_at,
        "customer_metrics_at": customer_metrics_at,
        "portfolio_cache_at": portfolio_cache_at,
        "churn_scored_at": churn_scored_at,
        "churn_customer_count": churn_customer_count,
    }
