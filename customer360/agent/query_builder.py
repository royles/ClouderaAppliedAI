"""Compile validated customer-list filters into parameterized SQL (for execution preview)."""

from __future__ import annotations

from customer360.agent.list_filters import CustomerListFilters
from customer360.api.customer_list import customer_list_where


def compile_customer_list_sql(
    filters: CustomerListFilters,
    *,
    default_segment: str,
) -> tuple[str, list[object], str]:
    """
    Returns (sql, params, plain_english).
    SQL is a COUNT query using the same WHERE as GET /api/customers.
    """
    f = filters.normalized(default_segment=default_segment)
    where_sql, params = customer_list_where(
        f.segment,
        f.q,
        policy_type_code=None,
        city=f.city,
    )
    sql = f"""
SELECT COUNT(DISTINCT c.CUSTOMER_ID)
FROM DWH_DIM_CUSTOMERS_UNIQUE c
WHERE {where_sql}
""".strip()
    parts = [f"segment={f.segment}"]
    if f.city:
        parts.append(f"city={f.city}")
    if f.q:
        parts.append(f"search={f.q!r}")
    if f.sort_by != "churn_risk":
        parts.append(f"sort={f.sort_by} {f.sort_order}")
    description = "Customer list filters: " + ", ".join(parts)
    return sql, params, description


def count_matching_customers(conn, filters: CustomerListFilters, *, default_segment: str) -> int:
    sql, params, _ = compile_customer_list_sql(filters, default_segment=default_segment)
    row = conn.execute(sql, params).fetchone()
    return int(row[0]) if row else 0
