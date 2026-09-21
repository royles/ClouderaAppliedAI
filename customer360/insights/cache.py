"""SQLite cache for generated customer insights."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from customer360.paths import project_root

INSIGHTS_SCHEMA = project_root() / "data" / "insights_schema.sql"


def ensure_insights_table(conn: sqlite3.Connection) -> None:
    if not INSIGHTS_SCHEMA.is_file():
        return
    conn.executescript(INSIGHTS_SCHEMA.read_text(encoding="utf-8"))
    conn.commit()


def load_cached(
    conn: sqlite3.Connection,
    customer_id: int,
    context_hash: str,
) -> dict | None:
    ensure_insights_table(conn)
    row = conn.execute(
        """
        SELECT SUMMARY, PRIMARY_FOCUS, RECOMMENDATIONS, SOURCE, MODEL_ID, GENERATED_AT
        FROM APP_CUSTOMER_AI_INSIGHTS
        WHERE CUSTOMER_ID = ? AND CONTEXT_HASH = ?
        """,
        (customer_id, context_hash),
    ).fetchone()
    if row is None:
        return None
    try:
        recommendations = json.loads(row["RECOMMENDATIONS"])
    except json.JSONDecodeError:
        recommendations = []
    return {
        "summary": row["SUMMARY"],
        "primary_focus": row["PRIMARY_FOCUS"],
        "recommendations": recommendations,
        "source": row["SOURCE"],
        "model_id": row["MODEL_ID"],
        "generated_at": row["GENERATED_AT"],
    }


def save_cached(
    conn: sqlite3.Connection,
    customer_id: int,
    context_hash: str,
    *,
    summary: str,
    primary_focus: str,
    recommendations: list[str],
    source: str,
    model_id: str | None,
) -> str:
    ensure_insights_table(conn)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        """
        INSERT INTO APP_CUSTOMER_AI_INSIGHTS (
            CUSTOMER_ID, SUMMARY, PRIMARY_FOCUS, RECOMMENDATIONS,
            SOURCE, MODEL_ID, CONTEXT_HASH, GENERATED_AT
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(CUSTOMER_ID) DO UPDATE SET
            SUMMARY = excluded.SUMMARY,
            PRIMARY_FOCUS = excluded.PRIMARY_FOCUS,
            RECOMMENDATIONS = excluded.RECOMMENDATIONS,
            SOURCE = excluded.SOURCE,
            MODEL_ID = excluded.MODEL_ID,
            CONTEXT_HASH = excluded.CONTEXT_HASH,
            GENERATED_AT = excluded.GENERATED_AT
        """,
        (
            customer_id,
            summary,
            primary_focus,
            json.dumps(recommendations, ensure_ascii=False),
            source,
            model_id,
            context_hash,
            generated_at,
        ),
    )
    conn.commit()
    return generated_at
