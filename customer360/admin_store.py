"""Local SQLite store for admin configuration (control plane)."""

from __future__ import annotations

import sqlite3

from customer360.db import connect as sqlite_connect
from customer360.paths import default_db_path, project_root

ADMIN_SCHEMA = project_root() / "data" / "admin_schema.sql"

_DATA_SOURCE_MIGRATION_COLUMNS: tuple[tuple[str, str], ...] = (
    ("JDBC_URL", "TEXT"),
    ("JDBC_USER", "TEXT"),
    ("JDBC_PASSWORD", "TEXT"),
    ("ICEBERG_CATALOG", "TEXT"),
    ("ICEBERG_NAMESPACE", "TEXT"),
    ("ICEBERG_REST_URI", "TEXT"),
)


def control_db_path():
    """SQLite file that always holds admin tables and settings."""
    return default_db_path()


def _migrate_legacy_business_targets(conn: sqlite3.Connection) -> None:
    """One-time copy from deprecated single-row targets table if present."""
    legacy = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='APP_ADMIN_BUSINESS_TARGETS'"
    ).fetchone()
    if not legacy:
        return
    benchmark = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='APP_ADMIN_KPI_BENCHMARK'"
    ).fetchone()
    if not benchmark:
        return
    row = conn.execute("SELECT * FROM APP_ADMIN_BUSINESS_TARGETS WHERE ID = 1").fetchone()
    if row is None:
        return
    mapping = (
        ("total_book_value", row["TOTAL_BOOK_VALUE_TARGET"]),
        ("active_customers", row["ACTIVE_CUSTOMERS_TARGET"]),
        ("annual_retention_rate_forecast", row["RETENTION_RATE_TARGET"]),
        ("value_at_risk_12m", row["VALUE_AT_RISK_TARGET"]),
        ("avg_customer_value", row["AVG_CUSTOMER_VALUE_TARGET"]),
        ("high_risk_book_pct", row["HIGH_RISK_BOOK_PCT_TARGET"]),
        ("book_growth_pct", row["BOOK_GROWTH_PCT_TARGET"]),
    )
    for key, value in mapping:
        if value is None:
            continue
        conn.execute(
            """
            UPDATE APP_ADMIN_KPI_BENCHMARK
            SET TARGET_VALUE = ?, UPDATED_AT = COALESCE(UPDATED_AT, ?)
            WHERE KPI_KEY = ? AND (TARGET_VALUE IS NULL OR TARGET_VALUE = 0)
            """,
            (value, row["UPDATED_AT"] or "", key),
        )


def _migrate_data_source_columns(conn: sqlite3.Connection) -> None:
    rows = conn.execute("PRAGMA table_info(APP_ADMIN_DATA_SOURCE)").fetchall()
    if not rows:
        return
    existing = {row[1] for row in rows}
    for name, col_type in _DATA_SOURCE_MIGRATION_COLUMNS:
        if name not in existing:
            conn.execute(f"ALTER TABLE APP_ADMIN_DATA_SOURCE ADD COLUMN {name} {col_type}")


def ensure_admin_schema(conn: sqlite3.Connection | None = None) -> sqlite3.Connection:
    own = conn is None
    if own:
        conn = sqlite_connect(control_db_path())
    if ADMIN_SCHEMA.is_file():
        conn.executescript(ADMIN_SCHEMA.read_text(encoding="utf-8"))
        conn.commit()
    _migrate_data_source_columns(conn)
    _migrate_legacy_business_targets(conn)
    conn.commit()
    if own:
        return conn
    return conn


def admin_connect() -> sqlite3.Connection:
    conn = sqlite_connect(control_db_path())
    ensure_admin_schema(conn)
    return conn
