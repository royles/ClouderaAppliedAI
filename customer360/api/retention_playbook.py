"""Retention playbook queue — high value-at-risk customers with suggested actions."""

from __future__ import annotations

import sqlite3

from customer360.api.segments import SEGMENT_WHERE, normalize_segment
from customer360.churn.effective_risk import effective_churn_probability_sql
from customer360.api.metrics_cache import customer_metrics_populated
from customer360.api.value_history import CUSTOMER_VALUE_SQL

_CHURN_PROB = effective_churn_probability_sql("ch")


def fetch_retention_playbook(
    conn: sqlite3.Connection,
    *,
    segment: str | None = None,
    limit: int = 25,
    offset: int = 0,
) -> dict:
    seg = normalize_segment(segment)
    segment_sql = SEGMENT_WHERE[seg]
    limit = max(1, min(int(limit), 100))
    offset = max(0, int(offset))

    churn_row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='APP_CUSTOMER_CHURN_SCORES'"
    ).fetchone()
    if not churn_row:
        return {"segment": seg, "items": [], "total": 0, "limit": limit, "offset": offset}

    if customer_metrics_populated(conn):
        value_sql = "m.CUSTOMER_VALUE"
        metrics_join = "INNER JOIN APP_CUSTOMER_METRICS m ON m.CUSTOMER_ID = c.CUSTOMER_ID"
    else:
        value_sql = f"ROUND({CUSTOMER_VALUE_SQL}, 2)"
        metrics_join = ""

    base_where = f"c.CURRENT_IND = 1 AND ({segment_sql})"

    total = conn.execute(
        f"""
        SELECT COUNT(*) FROM (
            SELECT c.CUSTOMER_ID
            FROM DWH_DIM_CUSTOMERS_UNIQUE c
            {metrics_join}
            LEFT JOIN APP_CUSTOMER_CHURN_SCORES ch ON ch.CUSTOMER_ID = c.CUSTOMER_ID
            WHERE {base_where}
              AND ({value_sql}) * ({_CHURN_PROB}) > 0
        )
        """,
    ).fetchone()[0]

    rows = conn.execute(
        f"""
        SELECT
            c.CUSTOMER_ID AS customer_id,
            c.CUSTOMER_KEY AS customer_key,
            c.CUSTOMER_NAME AS customer_name,
            c.CITY_NAME AS city_name,
            {value_sql} AS customer_value,
            ch.CHURN_PROBABILITY AS churn_probability,
            ch.CHURN_RISK_TIER AS churn_risk_tier,
            ROUND(({value_sql}) * ({_CHURN_PROB}), 2) AS value_at_risk
        FROM DWH_DIM_CUSTOMERS_UNIQUE c
        {metrics_join}
        LEFT JOIN APP_CUSTOMER_CHURN_SCORES ch ON ch.CUSTOMER_ID = c.CUSTOMER_ID
        WHERE {base_where}
          AND ({value_sql}) * ({_CHURN_PROB}) > 0
        ORDER BY value_at_risk DESC, customer_value DESC
        LIMIT ? OFFSET ?
        """,
        (limit, offset),
    ).fetchall()

    items = []
    for row in rows:
        var = float(row["value_at_risk"] or 0)
        items.append(
            {
                "customer_id": int(row["customer_id"]),
                "customer_key": row["customer_key"],
                "customer_name": row["customer_name"],
                "city_name": row["city_name"],
                "customer_value": float(row["customer_value"] or 0),
                "churn_probability": row["churn_probability"],
                "churn_risk_tier": row["churn_risk_tier"],
                "value_at_risk": var,
                "recommended_action": None,
            }
        )

    return {
        "segment": seg,
        "items": items,
        "total": int(total or 0),
        "limit": limit,
        "offset": offset,
    }
