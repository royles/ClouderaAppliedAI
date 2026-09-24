from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def apply_schema(conn: sqlite3.Connection, schema_path: Path) -> None:
    ddl = schema_path.read_text(encoding="utf-8")
    conn.executescript(ddl)
    conn.commit()


def refresh_overview_cache(conn: sqlite3.Connection) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT
          COUNT(*) AS control_count,
          SUM(CASE WHEN risk_tier = 'Critical' THEN 1 ELSE 0 END) AS critical_controls
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
