"""Refresh precomputed API caches after warehouse seed or churn scoring."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from customer360.api.portfolio_analytics import fetch_portfolio_analytics
from customer360.api.segments import OVERVIEW_DOMAINS, SEGMENT_WHERE
from customer360.api.value_history import CUSTOMER_VALUE_SQL
from customer360.paths import project_root

METRICS_SCHEMA = project_root() / "data" / "metrics_schema.sql"

INVESTMENT_TRACK_COUNT_SQL = """
(
    SELECT COUNT(*)
    FROM (
        SELECT DISTINCT pit.POLICY_NUM, pit.INVESTMENT_TRACK_ID
        FROM DWH_FCT_POLICY_INVESTMENT_TRACK pit
        WHERE pit.CUSTOMER_ID = c.CUSTOMER_ID
    )
)
""".strip()


def ensure_metrics_schema(conn: sqlite3.Connection) -> None:
    if METRICS_SCHEMA.is_file():
        conn.executescript(METRICS_SCHEMA.read_text(encoding="utf-8"))
        conn.commit()


def _metrics_table_ready(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='APP_CUSTOMER_METRICS'"
    ).fetchone()
    return row is not None


def customer_metrics_populated(conn: sqlite3.Connection) -> bool:
    if not _metrics_table_ready(conn):
        return False
    row = conn.execute("SELECT COUNT(*) FROM APP_CUSTOMER_METRICS").fetchone()
    return int(row[0] or 0) > 0


def refresh_customer_metrics(conn: sqlite3.Connection) -> int:
    ensure_metrics_schema(conn)
    refreshed_at = datetime.now(timezone.utc).isoformat()
    conn.execute("DELETE FROM APP_CUSTOMER_METRICS")
    conn.execute(
        f"""
        INSERT INTO APP_CUSTOMER_METRICS (
            CUSTOMER_ID,
            POLICY_COUNT,
            INVESTMENT_TRACK_COUNT,
            CUSTOMER_VALUE,
            REFRESHED_AT
        )
        SELECT
            c.CUSTOMER_ID,
            (
                SELECT COUNT(*)
                FROM DWH_DIM_ALL_POLICY p
                WHERE p.CUSTOMER_ID = CAST(c.CUSTOMER_ID AS TEXT)
            ),
            {INVESTMENT_TRACK_COUNT_SQL},
            ROUND({CUSTOMER_VALUE_SQL}, 2),
            ?
        FROM DWH_DIM_CUSTOMERS_UNIQUE c
        WHERE c.CURRENT_IND = 1
        """,
        (refreshed_at,),
    )
    conn.commit()
    return int(conn.execute("SELECT COUNT(*) FROM APP_CUSTOMER_METRICS").fetchone()[0])


def refresh_overview_counts(conn: sqlite3.Connection) -> None:
    ensure_metrics_schema(conn)
    refreshed_at = datetime.now(timezone.utc).isoformat()
    conn.execute("DELETE FROM APP_OVERVIEW_COUNTS")
    for _label, filter_key, _description, count_sql in OVERVIEW_DOMAINS:
        row_count = int(conn.execute(count_sql).fetchone()[0])
        conn.execute(
            """
            INSERT INTO APP_OVERVIEW_COUNTS (FILTER_KEY, ROW_COUNT, REFRESHED_AT)
            VALUES (?, ?, ?)
            """,
            (filter_key, row_count, refreshed_at),
        )
    conn.commit()


def refresh_portfolio_analytics_cache(conn: sqlite3.Connection) -> int:
    from customer360.book_objectives_cache import refresh_book_objective_trends

    ensure_metrics_schema(conn)
    refresh_book_objective_trends(conn)
    refreshed_at = datetime.now(timezone.utc).isoformat()
    conn.execute("DELETE FROM APP_PORTFOLIO_ANALYTICS_CACHE")
    conn.commit()
    written = 0
    for segment in SEGMENT_WHERE:
        payload = fetch_portfolio_analytics(conn, segment=segment)
        conn.execute(
            """
            INSERT INTO APP_PORTFOLIO_ANALYTICS_CACHE (SEGMENT, PAYLOAD_JSON, REFRESHED_AT)
            VALUES (?, ?, ?)
            """,
            (segment, json.dumps(payload), refreshed_at),
        )
        written += 1
    conn.commit()
    return written


def refresh_all_api_caches(conn: sqlite3.Connection) -> dict[str, int | str]:
    """Rebuild list metrics, overview cards, and portfolio analytics caches."""
    from customer360.api.warehouse_admin import refresh_warehouse_manifest
    from customer360.churn.scoring import try_train_and_score_churn
    from customer360.paths import default_db_path

    churn_scored = try_train_and_score_churn(default_db_path())
    customers = refresh_customer_metrics(conn)
    refresh_overview_counts(conn)
    segments = refresh_portfolio_analytics_cache(conn)
    refresh_warehouse_manifest(conn, source_job="refresh_api_caches")
    return {
        "customer_metrics_rows": customers,
        "portfolio_segments_cached": segments,
        "churn_model_scored": int(churn_scored),
        "refreshed_at": datetime.now(timezone.utc).isoformat(),
    }


def portfolio_analytics_cache_ready(conn: sqlite3.Connection) -> bool:
    ensure_metrics_schema(conn)
    row = conn.execute(
        "SELECT 1 FROM APP_PORTFOLIO_ANALYTICS_CACHE WHERE SEGMENT = 'customers_all' LIMIT 1"
    ).fetchone()
    return row is not None
