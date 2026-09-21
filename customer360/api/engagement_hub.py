"""Engagement opportunities — influence scoring and recommended next steps."""

from __future__ import annotations

import sqlite3
from typing import Any

from customer360.api.segments import SEGMENT_WHERE, normalize_segment
from customer360.interactions.summary import REFERENCE_DATE, interactions_table_exists
from customer360.metrics_refresh import customer_metrics_populated

REFERENCE_DAY = REFERENCE_DATE.strftime("%Y-%m-%d")


def _churn_table_exists(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='APP_CUSTOMER_CHURN_SCORES'"
    ).fetchone()
    return row is not None


def _book_touchpoint_summary(conn: sqlite3.Connection) -> dict[str, Any]:
    if not interactions_table_exists(conn):
        return {
            "customers_with_touchpoints_90d": 0,
            "total_touchpoints_90d": 0,
            "unresolved_agent_questions": 0,
            "digital_touchpoints_90d": 0,
            "review_events_90d": 0,
            "avg_days_since_last_touch": None,
        }

    row = conn.execute(
        f"""
        SELECT
            COUNT(DISTINCT CASE WHEN julianday(?) - julianday(EVENT_TS) <= 90
                THEN CUSTOMER_ID END) AS customers_with_touchpoints_90d,
            SUM(CASE WHEN julianday(?) - julianday(EVENT_TS) <= 90 THEN 1 ELSE 0 END)
                AS total_touchpoints_90d,
            SUM(CASE WHEN EVENT_TYPE = 'AGENT_QUESTION' AND COALESCE(RESOLVED, 1) = 0
                AND julianday(?) - julianday(EVENT_TS) <= 90 THEN 1 ELSE 0 END)
                AS unresolved_agent_questions,
            SUM(CASE WHEN EVENT_TYPE IN ('WEB_SEARCH', 'AGENT_QUESTION')
                AND julianday(?) - julianday(EVENT_TS) <= 90 THEN 1 ELSE 0 END)
                AS digital_touchpoints_90d,
            SUM(CASE WHEN EVENT_TYPE = 'REVIEW'
                AND julianday(?) - julianday(EVENT_TS) <= 90 THEN 1 ELSE 0 END)
                AS review_events_90d,
            AVG(
                CASE WHEN julianday(?) - julianday(EVENT_TS) <= 365
                THEN julianday(?) - julianday(EVENT_TS) END
            ) AS avg_days_since_last_touch
        FROM APP_CUSTOMER_INTERACTION_EVENTS
        """,
        (REFERENCE_DAY,) * 7,
    ).fetchone()

    avg_days = row["avg_days_since_last_touch"]
    return {
        "customers_with_touchpoints_90d": int(row["customers_with_touchpoints_90d"] or 0),
        "total_touchpoints_90d": int(row["total_touchpoints_90d"] or 0),
        "unresolved_agent_questions": int(row["unresolved_agent_questions"] or 0),
        "digital_touchpoints_90d": int(row["digital_touchpoints_90d"] or 0),
        "review_events_90d": int(row["review_events_90d"] or 0),
        "avg_days_since_last_touch": round(float(avg_days), 1) if avg_days is not None else None,
    }


def _influence_score(row: dict[str, Any], *, value_p90: float) -> float:
    """Higher = more worth engaging now (reachable + material value + clear lever)."""
    value = float(row.get("customer_value") or 0)
    value_norm = min(1.0, value / value_p90) if value_p90 > 0 else 0.0

    events_90 = int(row.get("events_last_90d") or 0)
    days_since = float(row.get("days_since_last_interaction") or 999)
    unresolved = int(row.get("unresolved_agent_questions") or 0)
    web_90 = int(row.get("web_search_90d") or 0)
    reviews_90 = int(row.get("review_count_90d") or 0)
    tier = (row.get("churn_risk_tier") or "").upper()
    churn_p = float(row.get("churn_probability") or 0)

    score = 0.0
    score += 32.0 * value_norm
    score += min(18.0, events_90 * 3.0)
    if 14 <= days_since <= 120:
        score += 14.0
    elif days_since < 14:
        score += 8.0
    elif 120 < days_since <= 200:
        score += 10.0
    score += min(20.0, unresolved * 10.0)
    if web_90 >= 2 and reviews_90 == 0:
        score += 8.0
    if tier == "MEDIUM":
        score += 12.0
    elif tier == "LOW":
        score += 8.0
    elif tier == "HIGH" and events_90 >= 1:
        score += 10.0
    if churn_p >= 0.25 and events_90 >= 1:
        score += 6.0
    if events_90 >= 12:
        score -= 12.0
    return round(min(100.0, max(0.0, score)), 1)


def _recommended_action(row: dict[str, Any]) -> dict[str, str]:
    unresolved = int(row.get("unresolved_agent_questions") or 0)
    days_since = float(row.get("days_since_last_interaction") or 999)
    web_90 = int(row.get("web_search_90d") or 0)
    reviews_90 = int(row.get("review_count_90d") or 0)
    tier = (row.get("churn_risk_tier") or "").upper()
    events_90 = int(row.get("events_last_90d") or 0)

    if unresolved > 0:
        return {
            "action_code": "resolve_agent_question",
            "title": "Resolve open agent question",
            "detail": f"{unresolved} unresolved question(s) in the last 90 days — call or message while context is fresh.",
            "channel_hint": "phone",
        }
    if tier == "HIGH" and events_90 >= 1:
        return {
            "action_code": "retention_call",
            "title": "Retention call (channel is warm)",
            "detail": "High churn risk but recent touchpoints — prioritize a human retention conversation.",
            "channel_hint": "phone",
        }
    if days_since >= 90:
        return {
            "action_code": "reengagement_outreach",
            "title": "Re-engagement outreach",
            "detail": "No recent contact — send a personalized check-in (email or SMS) and offer a digital review.",
            "channel_hint": "email",
        }
    if web_90 >= 2 and reviews_90 == 0:
        return {
            "action_code": "invite_review",
            "title": "Invite feedback after digital research",
            "detail": "Customer is searching products/help online — ask for a quick review or satisfaction pulse.",
            "channel_hint": "email",
        }
    return {
        "action_code": "relationship_review",
        "title": "Schedule relationship review",
        "detail": "Stable engagement — book a proactive review to discuss coverage and savings goals.",
        "channel_hint": "phone",
    }


def fetch_engagement_opportunities(
    conn: sqlite3.Connection,
    *,
    segment: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    seg = normalize_segment(segment)
    where_sql = f"c.CURRENT_IND = 1 AND ({SEGMENT_WHERE[seg]})"

    if not interactions_table_exists(conn):
        return {
            "segment": seg,
            "book_summary": _book_touchpoint_summary(conn),
            "opportunities": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
        }

    value_expr = "m.CUSTOMER_VALUE"
    metrics_join = "INNER JOIN APP_CUSTOMER_METRICS m ON m.CUSTOMER_ID = c.CUSTOMER_ID"
    if not customer_metrics_populated(conn):
        from customer360.api.value_history import CUSTOMER_VALUE_SQL

        value_expr = f"ROUND({CUSTOMER_VALUE_SQL}, 2)"
        metrics_join = ""

    churn_join = ""
    churn_cols = "NULL AS churn_probability, NULL AS churn_risk_tier"
    if _churn_table_exists(conn):
        churn_join = "LEFT JOIN APP_CUSTOMER_CHURN_SCORES ch ON ch.CUSTOMER_ID = c.CUSTOMER_ID"
        churn_cols = "ch.CHURN_PROBABILITY AS churn_probability, ch.CHURN_RISK_TIER AS churn_risk_tier"

    ref = REFERENCE_DAY
    rows = conn.execute(
        f"""
        WITH interaction AS (
            SELECT
                CUSTOMER_ID AS customer_id,
                SUM(CASE WHEN julianday(?) - julianday(EVENT_TS) <= 90 THEN 1 ELSE 0 END)
                    AS events_last_90d,
                SUM(CASE WHEN EVENT_TYPE = 'REVIEW'
                    AND julianday(?) - julianday(EVENT_TS) <= 90 THEN 1 ELSE 0 END)
                    AS review_count_90d,
                SUM(CASE WHEN EVENT_TYPE = 'WEB_SEARCH'
                    AND julianday(?) - julianday(EVENT_TS) <= 90 THEN 1 ELSE 0 END)
                    AS web_search_90d,
                SUM(CASE WHEN EVENT_TYPE = 'AGENT_QUESTION' AND COALESCE(RESOLVED, 1) = 0
                    AND julianday(?) - julianday(EVENT_TS) <= 90 THEN 1 ELSE 0 END)
                    AS unresolved_agent_questions,
                MIN(julianday(?) - julianday(EVENT_TS)) AS days_since_last_interaction,
                MAX(EVENT_TS) AS last_event_ts
            FROM APP_CUSTOMER_INTERACTION_EVENTS
            GROUP BY CUSTOMER_ID
        )
        SELECT
            c.CUSTOMER_ID AS customer_id,
            c.CUSTOMER_KEY AS customer_key,
            c.CUSTOMER_NAME AS customer_name,
            c.CITY_NAME AS city_name,
            {value_expr} AS customer_value,
            {churn_cols},
            COALESCE(i.events_last_90d, 0) AS events_last_90d,
            COALESCE(i.review_count_90d, 0) AS review_count_90d,
            COALESCE(i.web_search_90d, 0) AS web_search_90d,
            COALESCE(i.unresolved_agent_questions, 0) AS unresolved_agent_questions,
            COALESCE(i.days_since_last_interaction, 999) AS days_since_last_interaction,
            i.last_event_ts AS last_event_ts
        FROM DWH_DIM_CUSTOMERS_UNIQUE c
        {metrics_join}
        {churn_join}
        LEFT JOIN interaction i ON i.customer_id = c.CUSTOMER_ID
        WHERE {where_sql}
        """,
        (ref, ref, ref, ref, ref),
    ).fetchall()

    values = [float(r["customer_value"] or 0) for r in rows]
    values.sort()
    value_p90 = values[int(len(values) * 0.9)] if values else 1.0

    scored: list[dict[str, Any]] = []
    for r in rows:
        base = dict(r)
        if base.get("events_last_90d", 0) == 0 and base.get("unresolved_agent_questions", 0) == 0:
            if float(base.get("days_since_last_interaction") or 999) > 200:
                continue
        influence = _influence_score(base, value_p90=value_p90)
        if influence < 25:
            continue
        action = _recommended_action(base)
        touchpoints = {
            "events_last_90d": int(base["events_last_90d"]),
            "reviews_90d": int(base["review_count_90d"]),
            "web_searches_90d": int(base["web_search_90d"]),
            "unresolved_agent_questions": int(base["unresolved_agent_questions"]),
            "days_since_last_touch": round(float(base["days_since_last_interaction"]), 0),
            "last_event_ts": base.get("last_event_ts"),
        }
        scored.append(
            {
                "customer_id": int(base["customer_id"]),
                "customer_key": base["customer_key"],
                "customer_name": base["customer_name"],
                "city_name": base.get("city_name"),
                "customer_value": round(float(base["customer_value"] or 0), 2),
                "churn_probability": base.get("churn_probability"),
                "churn_risk_tier": base.get("churn_risk_tier"),
                "influence_score": influence,
                "touchpoints": touchpoints,
                "recommended_action": action,
            }
        )

    scored.sort(key=lambda x: (-x["influence_score"], -x["customer_value"]))
    total = len(scored)
    page = scored[offset : offset + limit]

    return {
        "segment": seg,
        "book_summary": _book_touchpoint_summary(conn),
        "opportunities": page,
        "total": total,
        "limit": limit,
        "offset": offset,
    }
