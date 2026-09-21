"""Warehouse admin metadata: tables, lineage, and data quality checks."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from customer360.bedrock.client import is_bedrock_configured
from customer360.bedrock.config import get_bedrock_settings

TABLE_CATALOG: list[dict] = [
    {
        "table_name": "DWH_DIM_CUSTOMERS_UNIQUE",
        "layer": "warehouse",
        "domain": "Customer",
        "role": "Dimension (SCD Type 2)",
        "description": "Unique customer identities with demographics, contact, and portal activity.",
        "load_job": "2_job-init-database / customer360.seed",
    },
    {
        "table_name": "DWH_DIM_ALL_POLICY",
        "layer": "warehouse",
        "domain": "Policy",
        "role": "Dimension",
        "description": "Policies linked to customers — life, health, property, pension, and savings products.",
        "load_job": "2_job-init-database / customer360.seed",
    },
    {
        "table_name": "DWH_FCT_FORECLOSURES",
        "layer": "warehouse",
        "domain": "Foreclosures",
        "role": "Fact",
        "description": "Legal encumbrance headers (ikulim) by customer and portfolio.",
        "load_job": "2_job-init-database / customer360.seed",
    },
    {
        "table_name": "DWH_FCT_FORECLOSURES_ASSETS",
        "layer": "warehouse",
        "domain": "Foreclosures",
        "role": "Fact",
        "description": "Assets located against foreclosure cases (policies or claims).",
        "load_job": "2_job-init-database / customer360.seed",
    },
    {
        "table_name": "DWH_FCT_POLICY_INVESTMENT_TRACK",
        "layer": "warehouse",
        "domain": "Investments",
        "role": "Fact (snapshot)",
        "description": "Monthly policy-level investment accumulation by track and fund.",
        "load_job": "2_job-init-database / customer360.seed",
    },
    {
        "table_name": "DWH_FCT_INVESTMENT_TRACK",
        "layer": "warehouse",
        "domain": "Market",
        "role": "Reference / market",
        "description": "Regulatory fund performance (yields, risk metrics) — not customer-specific.",
        "load_job": "2_job-init-database / customer360.seed",
    },
    {
        "table_name": "DWH_FCT_POLICY_STATUS",
        "layer": "warehouse",
        "domain": "Policy status",
        "role": "Fact (snapshot)",
        "description": "Periodic policy status, coverage amounts, surrender/savings balances by customer and policy.",
        "load_job": "2_job-init-database / customer360.seed",
    },
    {
        "table_name": "APP_CUSTOMER_INTERACTION_EVENTS",
        "layer": "application",
        "domain": "Interactions",
        "role": "Fact",
        "description": "Synthetic omnichannel events — reviews, agent questions, web searches.",
        "load_job": "2_job-init-database / customer360.seed",
    },
    {
        "table_name": "APP_CUSTOMER_CHURN_SCORES",
        "layer": "application",
        "domain": "Analytics",
        "role": "Derived",
        "description": "ML churn probability and risk tier per customer.",
        "load_job": "3_job-train-churn-model",
    },
    {
        "table_name": "APP_CUSTOMER_AI_INSIGHTS",
        "layer": "application",
        "domain": "Insights",
        "role": "Cache",
        "description": "Cached Bedrock / fallback narrative insights per customer.",
        "load_job": "On-demand (API)",
    },
    {
        "table_name": "APP_CUSTOMER_METRICS",
        "layer": "application",
        "domain": "Performance",
        "role": "Cache",
        "description": "Precomputed list metrics — value, policy count, investment tracks.",
        "load_job": "seed / scripts/refresh_api_caches.py",
    },
    {
        "table_name": "APP_OVERVIEW_COUNTS",
        "layer": "application",
        "domain": "Performance",
        "role": "Cache",
        "description": "Precomputed domain card counts for warehouse overview.",
        "load_job": "seed / scripts/refresh_api_caches.py",
    },
    {
        "table_name": "APP_PORTFOLIO_ANALYTICS_CACHE",
        "layer": "application",
        "domain": "Performance",
        "role": "Cache",
        "description": "Precomputed portfolio KPIs and chart series per cohort segment.",
        "load_job": "seed / churn train / scripts/refresh_api_caches.py",
    },
    {
        "table_name": "APP_BOOK_SAVINGS_AUM_TREND",
        "layer": "application",
        "domain": "Performance",
        "role": "Cache",
        "description": "Materialized book-wide savings/AUM objective trend.",
        "load_job": "seed / scripts/refresh_api_caches.py",
    },
    {
        "table_name": "APP_BOOK_PREMIUM_MOMENTUM_TREND",
        "layer": "application",
        "domain": "Performance",
        "role": "Cache",
        "description": "Materialized book-wide premium momentum objective trend.",
        "load_job": "seed / scripts/refresh_api_caches.py",
    },
    {
        "table_name": "APP_BOOK_ENGAGEMENT_TREND",
        "layer": "application",
        "domain": "Performance",
        "role": "Cache",
        "description": "Materialized book-wide engagement objective trend.",
        "load_job": "seed / scripts/refresh_api_caches.py",
    },
    {
        "table_name": "APP_ADMIN_KPI_BENCHMARK",
        "layer": "application",
        "domain": "Administration",
        "role": "Configuration",
        "description": "Business KPI objectives and amber thresholds for The business thermometers.",
        "load_job": "Admin UI / seed defaults",
    },
    {
        "table_name": "APP_ADMIN_DATA_SOURCE",
        "layer": "application",
        "domain": "Administration",
        "role": "Configuration",
        "description": "Warehouse backend settings (SQLite, CDW JDBC, Iceberg).",
        "load_job": "Admin UI",
    },
]

RELATIONSHIPS: list[dict] = [
    {
        "from_table": "DWH_DIM_CUSTOMERS_UNIQUE",
        "from_column": "CUSTOMER_KEY",
        "to_table": "DWH_DIM_ALL_POLICY",
        "to_column": "CUSTOMER_KEY",
        "cardinality": "1:N",
        "label": "owns policies",
    },
    {
        "from_table": "DWH_DIM_CUSTOMERS_UNIQUE",
        "from_column": "CUSTOMER_ID",
        "to_table": "DWH_FCT_FORECLOSURES",
        "to_column": "CUSTOMER_ID",
        "cardinality": "1:N",
        "label": "foreclosure cases",
    },
    {
        "from_table": "DWH_DIM_CUSTOMERS_UNIQUE",
        "from_column": "CUSTOMER_ID",
        "to_table": "DWH_FCT_POLICY_INVESTMENT_TRACK",
        "to_column": "CUSTOMER_ID",
        "cardinality": "1:N",
        "label": "investment snapshots",
    },
    {
        "from_table": "DWH_DIM_ALL_POLICY",
        "from_column": "POLICY_NUM",
        "to_table": "DWH_FCT_POLICY_INVESTMENT_TRACK",
        "to_column": "POLICY_NUM",
        "cardinality": "1:N",
        "label": "track balances",
    },
    {
        "from_table": "DWH_DIM_CUSTOMERS_UNIQUE",
        "from_column": "CUSTOMER_ID",
        "to_table": "DWH_FCT_POLICY_STATUS",
        "to_column": "CUSTOMER_ID",
        "cardinality": "1:N",
        "label": "policy status snapshots",
    },
    {
        "from_table": "DWH_FCT_FORECLOSURES",
        "from_column": "SPUROR_NUMBER",
        "to_table": "DWH_FCT_FORECLOSURES_ASSETS",
        "to_column": "SPUROR_NUMBER",
        "cardinality": "1:N",
        "label": "linked assets",
    },
    {
        "from_table": "DWH_DIM_CUSTOMERS_UNIQUE",
        "from_column": "CUSTOMER_ID",
        "to_table": "APP_CUSTOMER_INTERACTION_EVENTS",
        "to_column": "CUSTOMER_ID",
        "cardinality": "1:N",
        "label": "interactions",
    },
    {
        "from_table": "DWH_DIM_CUSTOMERS_UNIQUE",
        "from_column": "CUSTOMER_ID",
        "to_table": "APP_CUSTOMER_CHURN_SCORES",
        "to_column": "CUSTOMER_ID",
        "cardinality": "1:1",
        "label": "churn score",
    },
    {
        "from_table": "DWH_DIM_CUSTOMERS_UNIQUE",
        "from_column": "CUSTOMER_ID",
        "to_table": "APP_CUSTOMER_METRICS",
        "to_column": "CUSTOMER_ID",
        "cardinality": "1:1",
        "label": "list metrics",
    },
]

MERMAID_ER = """
erDiagram
    DWH_DIM_CUSTOMERS_UNIQUE ||--o{ DWH_DIM_ALL_POLICY : owns
    DWH_DIM_CUSTOMERS_UNIQUE ||--o{ DWH_FCT_FORECLOSURES : has
    DWH_FCT_FORECLOSURES ||--o{ DWH_FCT_FORECLOSURES_ASSETS : links
    DWH_DIM_CUSTOMERS_UNIQUE ||--o{ DWH_FCT_POLICY_INVESTMENT_TRACK : accumulates
    DWH_DIM_ALL_POLICY ||--o{ DWH_FCT_POLICY_INVESTMENT_TRACK : tracks
    DWH_DIM_CUSTOMERS_UNIQUE ||--o{ DWH_FCT_POLICY_STATUS : policy_status
    DWH_DIM_CUSTOMERS_UNIQUE ||--o{ APP_CUSTOMER_INTERACTION_EVENTS : interacts
    DWH_DIM_CUSTOMERS_UNIQUE ||--|| APP_CUSTOMER_CHURN_SCORES : scored
    DWH_DIM_CUSTOMERS_UNIQUE ||--|| APP_CUSTOMER_METRICS : metrics
    DWH_FCT_INVESTMENT_TRACK }o--|| DWH_FCT_POLICY_INVESTMENT_TRACK : fund_ref
""".strip()


def refresh_warehouse_manifest(conn: sqlite3.Connection, *, source_job: str) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS APP_WAREHOUSE_TABLE_MANIFEST (
            TABLE_NAME TEXT PRIMARY KEY,
            LAYER TEXT NOT NULL,
            DOMAIN TEXT NOT NULL,
            ROW_COUNT INTEGER NOT NULL,
            LAST_LOADED_AT TEXT NOT NULL,
            SOURCE_JOB TEXT NOT NULL
        )
        """
    )
    loaded_at = datetime.now(timezone.utc).isoformat()
    for entry in TABLE_CATALOG:
        table = entry["table_name"]
        exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
        row_count = 0
        if exists:
            row_count = int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        conn.execute(
            """
            INSERT INTO APP_WAREHOUSE_TABLE_MANIFEST (
                TABLE_NAME, LAYER, DOMAIN, ROW_COUNT, LAST_LOADED_AT, SOURCE_JOB
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(TABLE_NAME) DO UPDATE SET
                ROW_COUNT = excluded.ROW_COUNT,
                LAST_LOADED_AT = excluded.LAST_LOADED_AT,
                SOURCE_JOB = excluded.SOURCE_JOB
            """,
            (
                table,
                entry["layer"],
                entry["domain"],
                row_count,
                loaded_at,
                source_job,
            ),
        )
    conn.commit()


def _manifest_map(conn: sqlite3.Connection) -> dict[str, sqlite3.Row]:
    ready = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='APP_WAREHOUSE_TABLE_MANIFEST'"
    ).fetchone()
    if not ready:
        return {}
    rows = conn.execute(
        "SELECT TABLE_NAME, ROW_COUNT, LAST_LOADED_AT, SOURCE_JOB FROM APP_WAREHOUSE_TABLE_MANIFEST"
    ).fetchall()
    return {str(r["TABLE_NAME"]): r for r in rows}


def _quality_checks(conn: sqlite3.Connection) -> list[dict]:
    checks: list[dict] = []

    def add(
        check_id: str,
        label: str,
        status: str,
        summary: str,
        detail: str | None = None,
        metric_value: float | None = None,
    ) -> None:
        checks.append(
            {
                "id": check_id,
                "label": label,
                "status": status,
                "summary": summary,
                "detail": detail,
                "metric_value": metric_value,
            }
        )

    current = conn.execute(
        "SELECT COUNT(*) FROM DWH_DIM_CUSTOMERS_UNIQUE WHERE CURRENT_IND = 1"
    ).fetchone()[0]
    if current == 0:
        add("customers", "Current customers", "critical", "No current customers in dimension.")
        return checks

    with_email = conn.execute(
        """
        SELECT COUNT(*) FROM DWH_DIM_CUSTOMERS_UNIQUE
        WHERE CURRENT_IND = 1 AND EMAIL IS NOT NULL AND TRIM(EMAIL) != ''
        """
    ).fetchone()[0]
    email_pct = 100.0 * with_email / current
    add(
        "email_coverage",
        "Email populated",
        "ok" if email_pct >= 95 else "warn" if email_pct >= 80 else "critical",
        f"{email_pct:.1f}% of current customers have an email.",
        metric_value=round(email_pct, 1),
    )

    with_mobile = conn.execute(
        """
        SELECT COUNT(*) FROM DWH_DIM_CUSTOMERS_UNIQUE
        WHERE CURRENT_IND = 1 AND MOBILE_NO IS NOT NULL AND TRIM(MOBILE_NO) != ''
        """
    ).fetchone()[0]
    mobile_pct = 100.0 * with_mobile / current
    add(
        "mobile_coverage",
        "Mobile populated",
        "ok" if mobile_pct >= 95 else "warn",
        f"{mobile_pct:.1f}% of current customers have a mobile number.",
        metric_value=round(mobile_pct, 1),
    )

    churn_ready = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='APP_CUSTOMER_CHURN_SCORES'"
    ).fetchone()
    if churn_ready:
        scored = conn.execute("SELECT COUNT(*) FROM APP_CUSTOMER_CHURN_SCORES").fetchone()[0]
        churn_pct = 100.0 * scored / current
        add(
            "churn_coverage",
            "Churn scores present",
            "ok" if churn_pct >= 99 else "warn" if churn_pct >= 90 else "critical",
            f"{scored:,} of {current:,} current customers scored ({churn_pct:.1f}%).",
            detail="Run 3_job-train-churn-model after warehouse init.",
            metric_value=round(churn_pct, 1),
        )

    metrics_ready = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='APP_CUSTOMER_METRICS'"
    ).fetchone()
    if metrics_ready:
        metrics_rows = conn.execute("SELECT COUNT(*) FROM APP_CUSTOMER_METRICS").fetchone()[0]
        metrics_pct = 100.0 * metrics_rows / current
        add(
            "metrics_cache",
            "List metrics cache",
            "ok" if metrics_pct >= 99 else "warn",
            f"{metrics_rows:,} rows in APP_CUSTOMER_METRICS ({metrics_pct:.1f}% of current customers).",
            detail="Refresh with scripts/refresh_api_caches.py if stale.",
            metric_value=round(metrics_pct, 1),
        )

    no_policy = conn.execute(
        """
        SELECT COUNT(*)
        FROM DWH_DIM_CUSTOMERS_UNIQUE c
        WHERE c.CURRENT_IND = 1
          AND NOT EXISTS (
            SELECT 1 FROM DWH_DIM_ALL_POLICY p
            WHERE p.CUSTOMER_ID = CAST(c.CUSTOMER_ID AS TEXT)
          )
        """
    ).fetchone()[0]
    no_policy_pct = 100.0 * no_policy / current
    add(
        "policy_coverage",
        "Customers with ≥1 policy",
        "ok" if no_policy_pct <= 2 else "warn" if no_policy_pct <= 10 else "critical",
        f"{100 - no_policy_pct:.1f}% have at least one policy ({no_policy:,} without).",
        metric_value=round(100 - no_policy_pct, 1),
    )

    dup_current = conn.execute(
        """
        SELECT COUNT(*) FROM (
            SELECT CUSTOMER_ID FROM DWH_DIM_CUSTOMERS_UNIQUE
            WHERE CURRENT_IND = 1
            GROUP BY CUSTOMER_ID HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]
    add(
        "scd_uniqueness",
        "Single current row per customer ID",
        "ok" if dup_current == 0 else "critical",
        f"{dup_current} customer IDs with multiple CURRENT_IND=1 rows."
        if dup_current
        else "Each customer ID has at most one current dimension row.",
    )

    orphan_policies = conn.execute(
        """
        SELECT COUNT(*)
        FROM DWH_DIM_ALL_POLICY p
        WHERE NOT EXISTS (
            SELECT 1 FROM DWH_DIM_CUSTOMERS_UNIQUE c
            WHERE c.CURRENT_IND = 1 AND CAST(c.CUSTOMER_ID AS TEXT) = p.CUSTOMER_ID
        )
        """
    ).fetchone()[0]
    add(
        "policy_referential",
        "Policies reference current customers",
        "ok" if orphan_policies == 0 else "warn",
        f"{orphan_policies:,} policies not linked to a current customer row.",
    )

    null_inv = conn.execute(
        """
        SELECT COUNT(*) FROM DWH_FCT_POLICY_INVESTMENT_TRACK
        WHERE ACCUMULATION_TOTAL IS NULL OR ACCUMULATION_TOTAL = 0
        """
    ).fetchone()[0]
    total_inv = conn.execute("SELECT COUNT(*) FROM DWH_FCT_POLICY_INVESTMENT_TRACK").fetchone()[0]
    if total_inv:
        zero_pct = 100.0 * null_inv / total_inv
        add(
            "investment_amounts",
            "Investment snapshots with balance",
            "ok" if zero_pct <= 5 else "warn",
            f"{100 - zero_pct:.1f}% of investment snapshot rows have non-zero accumulation.",
            metric_value=round(100 - zero_pct, 1),
        )

    if churn_ready:
        high = conn.execute(
            """
            SELECT COUNT(*) FROM APP_CUSTOMER_CHURN_SCORES
            WHERE CHURN_RISK_TIER = 'HIGH'
            """
        ).fetchone()[0]
        add(
            "churn_high_tier",
            "High churn tier (informational)",
            "ok",
            f"{high:,} customers classified HIGH risk (current model).",
        )

    return checks


def _system_health_checks(conn: sqlite3.Connection, *, database_path: Path) -> list[dict]:
    from customer360.data_source import active_backend_summary
    checks: list[dict] = []

    def add(
        check_id: str,
        label: str,
        status: str,
        summary: str,
        detail: str | None = None,
    ) -> None:
        checks.append(
            {
                "id": check_id,
                "label": label,
                "status": status,
                "summary": summary,
                "detail": detail,
            }
        )

    add(
        "api",
        "Customer 360 API",
        "ok",
        "API is reachable and serving this admin request.",
        detail="Health endpoint: GET /api/health",
    )

    backend = active_backend_summary()
    backend_status = "ok" if backend["connection_ok"] else "warn"
    if backend["backend_type"] != "sqlite" and not backend["connection_ok"]:
        backend_status = "warn"
    add(
        "data_source",
        "Configured warehouse backend",
        backend_status,
        f"{backend['backend_label']}: {backend['summary']}",
        detail=backend.get("detail") or backend.get("api_routing_note"),
    )

    if not database_path.is_file():
        add(
            "database",
            "SQLite warehouse",
            "critical",
            f"Database file not found at {database_path}.",
            detail="Run 2_job-init-database or python3 -m customer360.seed.",
        )
    else:
        try:
            conn.execute("SELECT 1").fetchone()
            tables = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            ).fetchone()[0]
            add(
                "database",
                "SQLite warehouse",
                "ok",
                f"Connected; {int(tables)} tables in catalog.",
                detail=str(database_path),
            )
        except sqlite3.Error as exc:
            add(
                "database",
                "SQLite warehouse",
                "critical",
                "Database connection or query failed.",
                detail=str(exc),
            )

    settings = get_bedrock_settings()
    if is_bedrock_configured():
        add(
            "bedrock",
            "Amazon Bedrock",
            "ok",
            f"Configured for model {settings.model_id} in {settings.bedrock_region}.",
            detail="Insights and outreach drafts can use Bedrock when requested.",
        )
    else:
        add(
            "bedrock",
            "Amazon Bedrock",
            "warn",
            "Not configured — insights use local fallback rules.",
            detail=(
                "Set AWS credentials and Bedrock model environment variables "
                "(see docs/CAI_APPLICATION.md)."
            ),
        )

    churn_ready = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='APP_CUSTOMER_CHURN_SCORES'"
    ).fetchone()
    if churn_ready:
        scored = conn.execute("SELECT COUNT(*) FROM APP_CUSTOMER_CHURN_SCORES").fetchone()[0]
        if scored > 0:
            add(
                "churn_model",
                "Churn scoring",
                "ok",
                f"{scored:,} customers have churn scores.",
                detail="Populated by 3_job-train-churn-model.",
            )
        else:
            add(
                "churn_model",
                "Churn scoring",
                "warn",
                "Churn table exists but has no scores.",
                detail="Run 3_job-train-churn-model.",
            )
    else:
        add(
            "churn_model",
            "Churn scoring",
            "warn",
            "Churn scores table not present.",
            detail="Run 3_job-train-churn-model after warehouse init.",
        )

    return checks


def fetch_warehouse_admin(conn: sqlite3.Connection, *, database_path: Path) -> dict:
    manifest = _manifest_map(conn)
    tables: list[dict] = []
    warehouse_load: str | None = None

    for entry in TABLE_CATALOG:
        table = entry["table_name"]
        exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
        live_count = 0
        if exists:
            live_count = int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])

        manifest_row = manifest.get(table)
        last_loaded = manifest_row["LAST_LOADED_AT"] if manifest_row else None
        source_job = manifest_row["SOURCE_JOB"] if manifest_row else None
        if entry["layer"] == "warehouse" and last_loaded:
            if warehouse_load is None or last_loaded > warehouse_load:
                warehouse_load = last_loaded

        tables.append(
            {
                **entry,
                "row_count": live_count,
                "table_exists": bool(exists),
                "last_loaded_at": last_loaded,
                "last_source_job": source_job,
            }
        )

    db_size = database_path.stat().st_size if database_path.is_file() else 0

    return {
        "database_path": str(database_path),
        "database_size_bytes": db_size,
        "warehouse_last_loaded_at": warehouse_load,
        "tables": tables,
        "relationships": RELATIONSHIPS,
        "relationship_diagram": MERMAID_ER,
        "quality_checks": _quality_checks(conn),
        "health_checks": _system_health_checks(conn, database_path=database_path),
    }
