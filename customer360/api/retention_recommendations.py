"""Async retention queue recommendations — rules-based best next touch per customer."""

from __future__ import annotations

import sqlite3

from customer360.api.touchpoint_actions import recommended_touchpoint_action
from customer360.insights.context import CustomerContext, load_customer_context
from customer360.insights.fallback import generate_fallback
from customer360.interactions.summary import (
    REFERENCE_DATE,
    days_since_last_interaction,
    interactions_table_exists,
)


def _interaction_counts_90d(conn: sqlite3.Connection, customer_id: int) -> tuple[int, int]:
    if not interactions_table_exists(conn):
        return 0, 0
    ref = REFERENCE_DATE.strftime("%Y-%m-%d")
    row = conn.execute(
        """
        SELECT
            SUM(CASE WHEN EVENT_TYPE = 'WEB_SEARCH'
                AND julianday(?) - julianday(EVENT_TS) <= 90 THEN 1 ELSE 0 END) AS web_search_90d,
            SUM(CASE WHEN EVENT_TYPE = 'REVIEW'
                AND julianday(?) - julianday(EVENT_TS) <= 90 THEN 1 ELSE 0 END) AS review_count_90d
        FROM APP_CUSTOMER_INTERACTION_EVENTS
        WHERE CUSTOMER_ID = ?
        """,
        (ref, ref, customer_id),
    ).fetchone()
    if not row:
        return 0, 0
    return int(row["web_search_90d"] or 0), int(row["review_count_90d"] or 0)


def _touchpoint_row(conn: sqlite3.Connection, ctx: CustomerContext) -> dict:
    summary = ctx.payload.get("interactions") or {}
    web_90, review_90 = _interaction_counts_90d(conn, ctx.customer_id)
    return {
        "churn_risk_tier": ctx.churn_tier,
        "churn_probability": ctx.churn_probability,
        "events_last_90d": int(summary.get("events_last_90d") or 0),
        "unresolved_agent_questions": int(summary.get("unresolved_agent_questions") or 0),
        "days_since_last_interaction": days_since_last_interaction(conn, ctx.customer_id),
        "web_search_90d": web_90,
        "review_count_90d": review_90,
    }


def retention_queue_recommendation(conn: sqlite3.Connection, customer_id: int) -> dict[str, str] | None:
    ctx = load_customer_context(conn, customer_id)
    if ctx is None:
        return None

    touch = recommended_touchpoint_action(_touchpoint_row(conn, ctx))
    fallback = generate_fallback(ctx.payload)
    experience = (fallback.get("experience_note") or "").strip()
    recs = fallback.get("recommendations") or []
    first_rec = (recs[0] if recs else "").strip()

    detail = experience or first_rec or touch["detail"]
    title = touch["title"]
    if first_rec and not experience:
        title = first_rec if len(first_rec) <= 120 else first_rec[:117].rstrip() + "…"

    return {
        "action_code": touch["action_code"],
        "title": title,
        "detail": detail,
    }


def fetch_retention_recommendations(
    conn: sqlite3.Connection,
    customer_ids: list[int],
) -> dict:
    seen: set[int] = set()
    items: list[dict] = []
    for raw_id in customer_ids:
        if len(items) >= 50:
            break
        try:
            cid = int(raw_id)
        except (TypeError, ValueError):
            continue
        if cid in seen:
            continue
        seen.add(cid)
        action = retention_queue_recommendation(conn, cid)
        if action is None:
            continue
        items.append({"customer_id": cid, "recommended_action": action})
    return {"recommendations": items}
