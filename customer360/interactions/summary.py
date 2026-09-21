"""Aggregate interaction events for API, churn features, and Bedrock context."""

from __future__ import annotations

import sqlite3
from datetime import datetime

REFERENCE_DATE = datetime(2025, 9, 15)


def interactions_table_exists(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='APP_CUSTOMER_INTERACTION_EVENTS'"
    ).fetchone()
    return row is not None


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value[:19], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def load_interaction_bundle(conn: sqlite3.Connection, customer_id: int, *, limit: int = 25) -> dict:
    if not interactions_table_exists(conn):
        return {
            "events": [],
            "summary": {
                "total_events": 0,
                "events_last_90d": 0,
                "avg_review_rating": None,
                "unresolved_agent_questions": 0,
                "help_search_share": None,
                "last_event_ts": None,
                "recent_highlights": [],
            },
        }

    events = conn.execute(
        """
        SELECT
            EVENT_ID AS event_id,
            EVENT_TYPE AS event_type,
            EVENT_TS AS event_ts,
            CHANNEL AS channel,
            TOPIC AS topic,
            QUERY_OR_TITLE AS query_or_title,
            RATING AS rating,
            SENTIMENT AS sentiment,
            RESOLVED AS resolved,
            DETAIL AS detail
        FROM APP_CUSTOMER_INTERACTION_EVENTS
        WHERE CUSTOMER_ID = ?
        ORDER BY EVENT_TS DESC
        LIMIT ?
        """,
        (customer_id, limit),
    ).fetchall()

    agg = conn.execute(
        """
        SELECT
            COUNT(*) AS total_events,
            SUM(CASE WHEN julianday(?) - julianday(EVENT_TS) <= 90 THEN 1 ELSE 0 END) AS events_last_90d,
            AVG(CASE WHEN EVENT_TYPE = 'REVIEW' AND julianday(?) - julianday(EVENT_TS) <= 90
                THEN RATING END) AS avg_review_rating_90d,
            SUM(CASE WHEN EVENT_TYPE = 'AGENT_QUESTION' AND COALESCE(RESOLVED, 1) = 0
                AND julianday(?) - julianday(EVENT_TS) <= 90 THEN 1 ELSE 0 END) AS unresolved_agent_90d,
            SUM(CASE WHEN EVENT_TYPE = 'WEB_SEARCH' AND julianday(?) - julianday(EVENT_TS) <= 90
                THEN 1 ELSE 0 END) AS web_search_90d,
            SUM(CASE WHEN EVENT_TYPE = 'WEB_SEARCH' AND TOPIC = 'help_center'
                AND julianday(?) - julianday(EVENT_TS) <= 90 THEN 1 ELSE 0 END) AS help_search_90d,
            MAX(EVENT_TS) AS last_event_ts
        FROM APP_CUSTOMER_INTERACTION_EVENTS
        WHERE CUSTOMER_ID = ?
        """,
        (
            REFERENCE_DATE.strftime("%Y-%m-%d"),
            REFERENCE_DATE.strftime("%Y-%m-%d"),
            REFERENCE_DATE.strftime("%Y-%m-%d"),
            REFERENCE_DATE.strftime("%Y-%m-%d"),
            REFERENCE_DATE.strftime("%Y-%m-%d"),
            customer_id,
        ),
    ).fetchone()

    web_90 = int(agg["web_search_90d"] or 0)
    help_90 = int(agg["help_search_90d"] or 0)
    help_share = round(help_90 / web_90, 3) if web_90 else None

    highlights: list[str] = []
    for row in events[:8]:
        etype = row["event_type"]
        title = row["query_or_title"] or "Interaction"
        if etype == "REVIEW" and row["rating"] is not None:
            highlights.append(f"Review ({row['rating']}/5): {title}")
        elif etype == "AGENT_QUESTION":
            status = "open" if row["resolved"] == 0 else "resolved"
            highlights.append(f"Agent question ({status}): {title}")
        elif etype == "WEB_SEARCH":
            kind = "Help" if row["topic"] == "help_center" else "Product"
            highlights.append(f"{kind} search: {title}")
        if len(highlights) >= 4:
            break

    avg_rating = agg["avg_review_rating_90d"]
    summary = {
        "total_events": int(agg["total_events"] or 0),
        "events_last_90d": int(agg["events_last_90d"] or 0),
        "avg_review_rating": round(float(avg_rating), 2) if avg_rating is not None else None,
        "unresolved_agent_questions": int(agg["unresolved_agent_90d"] or 0),
        "help_search_share": help_share,
        "last_event_ts": agg["last_event_ts"],
        "recent_highlights": highlights,
    }

    event_dicts = []
    for row in events:
        resolved = row["resolved"]
        event_dicts.append(
            {
                "event_id": row["event_id"],
                "event_type": row["event_type"],
                "event_ts": row["event_ts"],
                "channel": row["channel"],
                "topic": row["topic"],
                "query_or_title": row["query_or_title"],
                "rating": row["rating"],
                "sentiment": row["sentiment"],
                "resolved": None if resolved is None else bool(resolved),
                "detail": row["detail"],
            }
        )

    return {"events": event_dicts, "summary": summary}


def days_since_last_interaction(conn: sqlite3.Connection, customer_id: int) -> float:
    if not interactions_table_exists(conn):
        return 999.0
    row = conn.execute(
        """
        SELECT MAX(EVENT_TS) AS last_ts
        FROM APP_CUSTOMER_INTERACTION_EVENTS
        WHERE CUSTOMER_ID = ?
        """,
        (customer_id,),
    ).fetchone()
    last_dt = _parse_ts(row["last_ts"] if row else None)
    if not last_dt:
        return 999.0
    return max(0.0, float((REFERENCE_DATE - last_dt).days))
