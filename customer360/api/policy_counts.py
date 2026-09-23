"""Policy row counts scoped to overview / portfolio customer segments."""

from __future__ import annotations

import sqlite3

from customer360.api.segments import SEGMENT_WHERE, normalize_segment


def policy_totals_for_segment(
    conn: sqlite3.Connection,
    segment: str | None,
) -> tuple[int, int]:
    """Return (total_policy_rows, active_policy_rows) for customers in the segment."""
    seg = normalize_segment(segment)
    where_sql = f"c.CURRENT_IND = 1 AND ({SEGMENT_WHERE[seg]})"
    row = conn.execute(
        f"""
        WITH scoped AS (
            SELECT c.CUSTOMER_ID
            FROM DWH_DIM_CUSTOMERS_UNIQUE c
            WHERE {where_sql}
        )
        SELECT
            COUNT(*) AS total_policies,
            COALESCE(SUM(CASE WHEN p.IS_ACTIVE = 1 THEN 1 ELSE 0 END), 0) AS active_policies
        FROM DWH_DIM_ALL_POLICY p
        INNER JOIN scoped s ON p.CUSTOMER_ID = CAST(s.CUSTOMER_ID AS TEXT)
        """,
    ).fetchone()
    return int(row["total_policies"] or 0), int(row["active_policies"] or 0)
