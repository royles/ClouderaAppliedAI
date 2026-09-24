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
    cols = {
        row[1]
        for row in conn.execute("PRAGMA table_info(APP_CUSTOMER_AI_INSIGHTS)").fetchall()
    }
    if "EXPERIENCE_NOTE" not in cols:
        conn.execute(
            "ALTER TABLE APP_CUSTOMER_AI_INSIGHTS ADD COLUMN EXPERIENCE_NOTE TEXT NOT NULL DEFAULT ''"
        )
    if "FALLBACK_REASON" not in cols:
        conn.execute("ALTER TABLE APP_CUSTOMER_AI_INSIGHTS ADD COLUMN FALLBACK_REASON TEXT")
    if "PREAMBLE" not in cols:
        conn.execute(
            "ALTER TABLE APP_CUSTOMER_AI_INSIGHTS ADD COLUMN PREAMBLE TEXT NOT NULL DEFAULT ''"
        )
    if "GUIDANCE" not in cols:
        conn.execute(
            "ALTER TABLE APP_CUSTOMER_AI_INSIGHTS ADD COLUMN GUIDANCE TEXT NOT NULL DEFAULT ''"
        )
    conn.commit()


def load_cached(
    conn: sqlite3.Connection,
    customer_id: int,
    context_hash: str,
) -> dict | None:
    ensure_insights_table(conn)
    row = conn.execute(
        """
        SELECT SUMMARY, PRIMARY_FOCUS, RECOMMENDATIONS, SOURCE, MODEL_ID, GENERATED_AT,
               EXPERIENCE_NOTE, FALLBACK_REASON, PREAMBLE, GUIDANCE
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
    keys = row.keys() if hasattr(row, "keys") else []
    experience_note = row["EXPERIENCE_NOTE"] if "EXPERIENCE_NOTE" in keys else ""
    fallback_reason = row["FALLBACK_REASON"] if "FALLBACK_REASON" in keys else None
    preamble = row["PREAMBLE"] if "PREAMBLE" in keys else ""
    guidance = row["GUIDANCE"] if "GUIDANCE" in keys else ""
    if not guidance and recommendations:
        guidance = " ".join(recommendations)
    return {
        "preamble": preamble or "",
        "summary": row["SUMMARY"],
        "guidance": guidance or "",
        "primary_focus": row["PRIMARY_FOCUS"],
        "recommendations": recommendations,
        "experience_note": experience_note or "",
        "source": row["SOURCE"],
        "model_id": row["MODEL_ID"],
        "generated_at": row["GENERATED_AT"],
        "fallback_reason": fallback_reason,
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
    preamble: str = "",
    guidance: str = "",
    experience_note: str = "",
    fallback_reason: str | None = None,
) -> str:
    ensure_insights_table(conn)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        """
        INSERT INTO APP_CUSTOMER_AI_INSIGHTS (
            CUSTOMER_ID, SUMMARY, PRIMARY_FOCUS, RECOMMENDATIONS,
            SOURCE, MODEL_ID, CONTEXT_HASH, GENERATED_AT,
            EXPERIENCE_NOTE, FALLBACK_REASON, PREAMBLE, GUIDANCE
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(CUSTOMER_ID) DO UPDATE SET
            SUMMARY = excluded.SUMMARY,
            PRIMARY_FOCUS = excluded.PRIMARY_FOCUS,
            RECOMMENDATIONS = excluded.RECOMMENDATIONS,
            SOURCE = excluded.SOURCE,
            MODEL_ID = excluded.MODEL_ID,
            CONTEXT_HASH = excluded.CONTEXT_HASH,
            GENERATED_AT = excluded.GENERATED_AT,
            EXPERIENCE_NOTE = excluded.EXPERIENCE_NOTE,
            FALLBACK_REASON = excluded.FALLBACK_REASON,
            PREAMBLE = excluded.PREAMBLE,
            GUIDANCE = excluded.GUIDANCE
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
            experience_note,
            fallback_reason,
            preamble,
            guidance,
        ),
    )
    conn.commit()
    return generated_at
