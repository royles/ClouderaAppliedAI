"""Aggregate customer value over time (investments + coverage snapshots)."""

from __future__ import annotations

import sqlite3

from customer360.api.segments import SEGMENT_WHERE, normalize_segment


def _customer_scope_sql(segment: str, customer_id: int | None) -> tuple[str, list[object]]:
    if customer_id is not None:
        return "c.CUSTOMER_ID = ?", [customer_id]
    seg = normalize_segment(segment)
    return f"c.CURRENT_IND = 1 AND ({SEGMENT_WHERE[seg]})", []


def fetch_value_history(
    conn: sqlite3.Connection,
    *,
    segment: str | None = None,
    customer_id: int | None = None,
) -> list[dict]:
    where_sql, params = _customer_scope_sql(segment or "customers_all", customer_id)
    sql = f"""
        WITH scoped_customers AS (
            SELECT c.CUSTOMER_ID
            FROM DWH_DIM_CUSTOMERS_UNIQUE c
            WHERE {where_sql}
        ),
        investment AS (
            SELECT
                pit.SNAPSHOT_DATE AS period,
                SUM(pit.ACCUMULATION_TOTAL) AS investment_value
            FROM DWH_FCT_POLICY_INVESTMENT_TRACK pit
            INNER JOIN scoped_customers sc ON sc.CUSTOMER_ID = pit.CUSTOMER_ID
            GROUP BY pit.SNAPSHOT_DATE
        ),
        coverage AS (
            SELECT
                m.TAARICH_MAATAFIT AS period,
                SUM(
                    COALESCE(m.MBB_SCHUM_BITUACH, 0)
                    + COALESCE(m.MBB_ITRAT_CHISACHON, 0)
                    + COALESCE(m.MBB_ERECH_PIDYON, 0)
                ) AS coverage_value
            FROM FCT_MATZAV_BITUACH m
            INNER JOIN scoped_customers sc ON sc.CUSTOMER_ID = m.MS_MEVUTACH
            GROUP BY m.TAARICH_MAATAFIT
        ),
        periods AS (
            SELECT period FROM investment
            UNION
            SELECT period FROM coverage
        )
        SELECT
            p.period AS period,
            COALESCE(i.investment_value, 0) AS investment_value,
            COALESCE(cov.coverage_value, 0) AS coverage_value,
            COALESCE(i.investment_value, 0) + COALESCE(cov.coverage_value, 0) AS total_value
        FROM periods p
        LEFT JOIN investment i ON i.period = p.period
        LEFT JOIN coverage cov ON cov.period = p.period
        ORDER BY p.period ASC
    """
    rows = conn.execute(sql, params).fetchall()
    return [
        {
            "period": row["period"],
            "investment_value": round(float(row["investment_value"] or 0), 2),
            "coverage_value": round(float(row["coverage_value"] or 0), 2),
            "total_value": round(float(row["total_value"] or 0), 2),
        }
        for row in rows
    ]
