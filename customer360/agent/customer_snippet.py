"""Short ranked customer lists for copilot answers."""

from __future__ import annotations

import sqlite3

from customer360.agent.list_filters import CustomerListFilters
from customer360.api.customer_list import customer_list_where
from customer360.api.sorting import normalize_sort_by, normalize_sort_order, order_clause
from customer360.api.value_history import CUSTOMER_VALUE_SQL
from customer360.metrics_refresh import customer_metrics_populated


def top_customers_snippet(
    conn: sqlite3.Connection,
    *,
    filters: CustomerListFilters,
    default_segment: str,
    limit: int = 10,
) -> str | None:
    f = filters.normalized(default_segment=default_segment)
    limit = max(1, min(int(limit), f.page_size, 15))
    sort_by = normalize_sort_by(f.sort_by)
    sort_order = normalize_sort_order(f.sort_order, sort_by=sort_by)

    churn_ready = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='APP_CUSTOMER_CHURN_SCORES'"
    ).fetchone()
    churn_join = ""
    if churn_ready:
        churn_join = "LEFT JOIN APP_CUSTOMER_CHURN_SCORES ch ON ch.CUSTOMER_ID = c.CUSTOMER_ID"

    if customer_metrics_populated(conn):
        value_sql = "m.CUSTOMER_VALUE"
        metrics_join = "INNER JOIN APP_CUSTOMER_METRICS m ON m.CUSTOMER_ID = c.CUSTOMER_ID"
    else:
        value_sql = f"ROUND({CUSTOMER_VALUE_SQL}, 2)"
        metrics_join = ""

    where_sql, params = customer_list_where(
        f.segment,
        f.q,
        policy_type_code=f.policy_type_code,
        city=f.city,
        churn_risk_tier=f.churn_risk_tier,
    )
    order_sql = order_clause(
        sort_by,
        sort_order,
        churn_scores_available=bool(churn_ready),
    )

    rows = conn.execute(
        f"""
        SELECT
            c.CUSTOMER_NAME AS customer_name,
            c.CITY_NAME AS city_name,
            {value_sql} AS customer_value
        FROM DWH_DIM_CUSTOMERS_UNIQUE c
        {metrics_join}
        {churn_join}
        WHERE {where_sql}
        ORDER BY {order_sql}
        LIMIT ?
        """,
        [*params, limit],
    ).fetchall()

    if not rows:
        return None

    lines: list[str] = []
    for i, r in enumerate(rows, start=1):
        name = str(r["customer_name"] or "Customer")
        val = float(r["customer_value"] or 0)
        city = str(r["city_name"] or "")
        suffix = f", {city}" if city else ""
        lines.append(f"{i}. {name}{suffix} (₪{val:,.0f})")
    prefix = "Top customers"
    if f.city:
        prefix += f" in {f.city}"
    return prefix + ": " + "; ".join(lines[:limit]) + "."
