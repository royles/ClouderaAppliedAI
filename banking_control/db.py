from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    # FastAPI runs sync handlers in a thread pool; allow use across worker threads.
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _split_schema_ddl(ddl: str) -> tuple[str, str]:
    """Separate table DDL from index DDL so migrations can run in between."""
    table_parts: list[str] = []
    index_parts: list[str] = []
    for chunk in ddl.split("\n\n"):
        stripped = chunk.strip()
        if not stripped or stripped.startswith("--"):
            continue
        if stripped.upper().startswith("CREATE INDEX"):
            index_parts.append(stripped)
        else:
            table_parts.append(stripped)
    return "\n\n".join(table_parts), "\n\n".join(index_parts)


def ensure_warehouse_schema(conn: sqlite3.Connection) -> None:
    """Create warehouse tables that may be missing from older SQLite files."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS DIM_BUSINESS_UNIT (
          unit_id INTEGER PRIMARY KEY,
          unit_code TEXT NOT NULL UNIQUE,
          unit_name TEXT NOT NULL,
          region TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS DIM_CONTROL (
          control_id INTEGER PRIMARY KEY,
          control_code TEXT NOT NULL UNIQUE,
          control_name TEXT NOT NULL,
          domain TEXT NOT NULL,
          risk_tier TEXT NOT NULL CHECK (risk_tier IN ('Critical', 'High', 'Medium', 'Low')),
          owner TEXT NOT NULL,
          frequency TEXT NOT NULL,
          description TEXT NOT NULL,
          is_golden INTEGER NOT NULL DEFAULT 0,
          similarity_key TEXT,
          standards_json TEXT
        );

        CREATE TABLE IF NOT EXISTS FCT_CONTROL_ASSESSMENT (
          assessment_id INTEGER PRIMARY KEY,
          control_id INTEGER NOT NULL REFERENCES DIM_CONTROL(control_id),
          unit_id INTEGER NOT NULL REFERENCES DIM_BUSINESS_UNIT(unit_id),
          assessment_date TEXT NOT NULL,
          status TEXT NOT NULL CHECK (status IN ('Effective', 'Partially Effective', 'Ineffective', 'Not Tested')),
          tester TEXT NOT NULL,
          evidence_ref TEXT,
          notes TEXT
        );

        CREATE TABLE IF NOT EXISTS FCT_EXCEPTION (
          exception_id INTEGER PRIMARY KEY,
          control_id INTEGER NOT NULL REFERENCES DIM_CONTROL(control_id),
          unit_id INTEGER NOT NULL REFERENCES DIM_BUSINESS_UNIT(unit_id),
          opened_at TEXT NOT NULL,
          severity TEXT NOT NULL CHECK (severity IN ('Critical', 'High', 'Medium', 'Low')),
          status TEXT NOT NULL CHECK (status IN ('Open', 'In Remediation', 'Pending Validation', 'Closed')),
          title TEXT NOT NULL,
          description TEXT NOT NULL,
          assignee TEXT NOT NULL,
          due_date TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS FCT_TRANSACTION_ALERT (
          alert_id INTEGER PRIMARY KEY,
          unit_id INTEGER NOT NULL REFERENCES DIM_BUSINESS_UNIT(unit_id),
          alert_at TEXT NOT NULL,
          alert_type TEXT NOT NULL,
          amount_usd REAL NOT NULL,
          customer_ref TEXT NOT NULL,
          channel TEXT NOT NULL,
          status TEXT NOT NULL CHECK (status IN ('New', 'Under Review', 'Escalated', 'Cleared', 'SAR Filed')),
          risk_score REAL NOT NULL,
          narrative TEXT NOT NULL,
          alert_origin TEXT NOT NULL DEFAULT 'historical' CHECK (alert_origin IN ('historical', 'live'))
        );

        CREATE TABLE IF NOT EXISTS FCT_AUDIT_EVENT (
          event_id INTEGER PRIMARY KEY,
          event_at TEXT NOT NULL,
          actor TEXT NOT NULL,
          action TEXT NOT NULL,
          entity_type TEXT NOT NULL,
          entity_id TEXT NOT NULL,
          detail TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS FCT_CONTROL_WORKFLOW (
          workflow_id INTEGER PRIMARY KEY,
          control_id INTEGER NOT NULL REFERENCES DIM_CONTROL(control_id),
          workflow_type TEXT NOT NULL,
          status TEXT NOT NULL CHECK (status IN ('Draft', 'In Progress', 'Complete', 'Cancelled')),
          artifact_ref TEXT NOT NULL UNIQUE,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          metadata_json TEXT
        );

        CREATE TABLE IF NOT EXISTS FCT_CONTROL_EVIDENCE_RESOURCE (
          resource_id INTEGER PRIMARY KEY,
          control_id INTEGER NOT NULL REFERENCES DIM_CONTROL(control_id),
          resource_key TEXT NOT NULL,
          label TEXT NOT NULL,
          placeholder_ref TEXT NOT NULL,
          document_url TEXT,
          document_title TEXT,
          workflow_id INTEGER REFERENCES FCT_CONTROL_WORKFLOW(workflow_id),
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          UNIQUE(control_id, resource_key)
        );

        CREATE TABLE IF NOT EXISTS APP_OVERVIEW_SNAPSHOT (
          snapshot_key TEXT PRIMARY KEY,
          payload_json TEXT NOT NULL,
          refreshed_at TEXT NOT NULL
        );
        """
    )
    conn.commit()


def ensure_warehouse_indexes(conn: sqlite3.Connection) -> None:
    statements = [
        "CREATE INDEX IF NOT EXISTS idx_control_similarity ON DIM_CONTROL(similarity_key)",
        "CREATE INDEX IF NOT EXISTS idx_control_golden ON DIM_CONTROL(is_golden)",
        "CREATE INDEX IF NOT EXISTS idx_assessment_control ON FCT_CONTROL_ASSESSMENT(control_id)",
        "CREATE INDEX IF NOT EXISTS idx_exception_status ON FCT_EXCEPTION(status)",
        "CREATE INDEX IF NOT EXISTS idx_alert_status ON FCT_TRANSACTION_ALERT(status)",
        "CREATE INDEX IF NOT EXISTS idx_alert_at ON FCT_TRANSACTION_ALERT(alert_at)",
        "CREATE INDEX IF NOT EXISTS idx_audit_event_at ON FCT_AUDIT_EVENT(event_at)",
        "CREATE INDEX IF NOT EXISTS idx_workflow_control ON FCT_CONTROL_WORKFLOW(control_id)",
        "CREATE INDEX IF NOT EXISTS idx_evidence_resource_control ON FCT_CONTROL_EVIDENCE_RESOURCE(control_id)",
    ]
    for stmt in statements:
        try:
            conn.execute(stmt)
        except sqlite3.OperationalError:
            continue
    conn.commit()


def apply_schema(conn: sqlite3.Connection, schema_path: Path) -> None:
    ddl = schema_path.read_text(encoding="utf-8")
    tables_ddl, indexes_ddl = _split_schema_ddl(ddl)
    migrate_control_catalog_columns(conn)
    if tables_ddl.strip():
        conn.executescript(tables_ddl)
    ensure_warehouse_schema(conn)
    migrate_control_catalog_columns(conn)
    ensure_warehouse_indexes(conn)
    if indexes_ddl.strip():
        for stmt in indexes_ddl.split(";"):
            stmt = stmt.strip()
            if not stmt:
                continue
            try:
                conn.execute(stmt)
            except sqlite3.OperationalError:
                continue
    conn.commit()


def migrate_control_catalog_columns(conn: sqlite3.Connection) -> None:
    """Add catalog columns for existing databases created before EU expansion."""
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    if "DIM_CONTROL" not in tables:
        return

    columns = {row[1] for row in conn.execute("PRAGMA table_info(DIM_CONTROL)")}
    if "is_golden" not in columns:
        conn.execute(
            "ALTER TABLE DIM_CONTROL ADD COLUMN is_golden INTEGER NOT NULL DEFAULT 0"
        )
    if "similarity_key" not in columns:
        conn.execute("ALTER TABLE DIM_CONTROL ADD COLUMN similarity_key TEXT")
    if "standards_json" not in columns:
        conn.execute("ALTER TABLE DIM_CONTROL ADD COLUMN standards_json TEXT")
    conn.commit()


def migrate_alert_origin_column(conn: sqlite3.Connection) -> None:
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    if "FCT_TRANSACTION_ALERT" not in tables:
        return
    columns = {row[1] for row in conn.execute("PRAGMA table_info(FCT_TRANSACTION_ALERT)")}
    if "alert_origin" not in columns:
        conn.execute(
            """
            ALTER TABLE FCT_TRANSACTION_ALERT
            ADD COLUMN alert_origin TEXT NOT NULL DEFAULT 'historical'
            """
        )
    conn.execute(
        """
        UPDATE FCT_TRANSACTION_ALERT
        SET alert_origin = 'historical'
        WHERE alert_origin IS NULL OR alert_origin = ''
        """
    )
    conn.commit()


def prepare_connection(conn: sqlite3.Connection) -> None:
    """Apply lightweight migrations before serving API requests."""
    ensure_warehouse_schema(conn)
    migrate_control_catalog_columns(conn)
    ensure_warehouse_indexes(conn)
    from banking_control.llm.admin_store import ensure_admin_llm_schema
    from banking_control.seed import ensure_monitoring_seed_data, sync_control_catalog_metadata

    ensure_admin_llm_schema(conn)
    sync_control_catalog_metadata(conn)
    ensure_monitoring_seed_data(conn)
    migrate_alert_origin_column(conn)
    from banking_control.alert_generator import ensure_historical_alerts
    import random

    added = ensure_historical_alerts(conn, random.Random())
    if added:
        conn.commit()
        refresh_overview_cache(conn)


def refresh_overview_cache(conn: sqlite3.Connection) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT
          COUNT(*) AS control_count,
          SUM(CASE WHEN risk_tier = 'Critical' THEN 1 ELSE 0 END) AS critical_controls,
          SUM(CASE WHEN is_golden = 1 THEN 1 ELSE 0 END) AS golden_controls
        FROM DIM_CONTROL
        """
    ).fetchone()

    assessments = conn.execute(
        """
        SELECT status, COUNT(*) AS cnt
        FROM FCT_CONTROL_ASSESSMENT
        GROUP BY status
        """
    ).fetchall()
    status_counts = {r["status"]: r["cnt"] for r in assessments}

    open_exceptions = conn.execute(
        """
        SELECT COUNT(*) AS cnt FROM FCT_EXCEPTION
        WHERE status IN ('Open', 'In Remediation', 'Pending Validation')
        """
    ).fetchone()["cnt"]

    alerts = conn.execute(
        """
        SELECT status, COUNT(*) AS cnt
        FROM FCT_TRANSACTION_ALERT
        GROUP BY status
        """
    ).fetchall()
    alert_counts = {r["status"]: r["cnt"] for r in alerts}

    effective = status_counts.get("Effective", 0)
    tested = sum(status_counts.values()) - status_counts.get("Not Tested", 0)
    control_health = round(100.0 * effective / tested, 1) if tested else 0.0

    by_domain = conn.execute(
        """
        SELECT c.domain, COUNT(DISTINCT c.control_id) AS controls,
               SUM(CASE WHEN a.status = 'Ineffective' THEN 1 ELSE 0 END) AS ineffective
        FROM DIM_CONTROL c
        LEFT JOIN FCT_CONTROL_ASSESSMENT a ON a.control_id = c.control_id
        GROUP BY c.domain
        ORDER BY c.domain
        """
    ).fetchall()

    payload = {
        "control_health_pct": control_health,
        "control_count": row["control_count"],
        "critical_controls": row["critical_controls"],
        "golden_controls": row["golden_controls"] or 0,
        "assessment_status": status_counts,
        "open_exceptions": open_exceptions,
        "alert_status": alert_counts,
        "domains": [
            {
                "domain": r["domain"],
                "controls": r["controls"],
                "ineffective": r["ineffective"] or 0,
            }
            for r in by_domain
        ],
    }

    conn.execute(
        """
        INSERT INTO APP_OVERVIEW_SNAPSHOT (snapshot_key, payload_json, refreshed_at)
        VALUES ('overview', ?, datetime('now'))
        ON CONFLICT(snapshot_key) DO UPDATE SET
          payload_json = excluded.payload_json,
          refreshed_at = excluded.refreshed_at
        """,
        (json.dumps(payload),),
    )
    conn.commit()
    return payload


def get_overview(conn: sqlite3.Connection) -> dict[str, Any]:
    cached = conn.execute(
        "SELECT payload_json FROM APP_OVERVIEW_SNAPSHOT WHERE snapshot_key = 'overview'"
    ).fetchone()
    if cached:
        return json.loads(cached["payload_json"])
    return refresh_overview_cache(conn)
