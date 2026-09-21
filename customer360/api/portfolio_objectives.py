"""Trend series aligned with Migdal-style strategic objectives (synthetic book)."""

from __future__ import annotations

import sqlite3

from customer360.api.segments import SEGMENT_WHERE, normalize_segment

OBJECTIVES_NOTE = (
    "Objective charts mirror Migdal Insurance & Finance strategic themes: "
    "long-term savings and AUM growth (pension & provident), retention of active "
    "policy relationships and premium momentum in general insurance, and digital "
    "customer engagement. Trends are computed from warehouse snapshots and "
    "interaction events for the selected cohort."
)


def _scope(segment: str | None) -> tuple[str, list[object]]:
    seg = normalize_segment(segment)
    return f"c.CURRENT_IND = 1 AND ({SEGMENT_WHERE[seg]})", []


def fetch_savings_aum_trend(
    conn: sqlite3.Connection,
    *,
    segment: str | None = None,
) -> list[dict]:
    where_sql, params = _scope(segment)
    rows = conn.execute(
        f"""
        WITH scoped AS (
            SELECT c.CUSTOMER_ID
            FROM DWH_DIM_CUSTOMERS_UNIQUE c
            WHERE {where_sql}
        )
        SELECT
            pit.SNAPSHOT_DATE AS period,
            SUM(pit.ACCUMULATION_TOTAL) AS accumulation_total,
            COUNT(DISTINCT pit.CUSTOMER_ID) AS active_savers,
            COUNT(DISTINCT pit.POLICY_NUM) AS savings_policies
        FROM DWH_FCT_POLICY_INVESTMENT_TRACK pit
        INNER JOIN scoped sc ON sc.CUSTOMER_ID = pit.CUSTOMER_ID
        GROUP BY pit.SNAPSHOT_DATE
        ORDER BY pit.SNAPSHOT_DATE ASC
        """,
        params,
    ).fetchall()
    return [
        {
            "period": row["period"],
            "accumulation_total": round(float(row["accumulation_total"] or 0), 2),
            "active_savers": int(row["active_savers"] or 0),
            "savings_policies": int(row["savings_policies"] or 0),
        }
        for row in rows
    ]


def fetch_premium_momentum_trend(
    conn: sqlite3.Connection,
    *,
    segment: str | None = None,
) -> list[dict]:
    """Active policy count and monthly premium base by investment snapshot month."""
    where_sql, params = _scope(segment)
    rows = conn.execute(
        f"""
        WITH scoped AS (
            SELECT c.CUSTOMER_ID
            FROM DWH_DIM_CUSTOMERS_UNIQUE c
            WHERE {where_sql}
        ),
        policy_month AS (
            SELECT
                pit.SNAPSHOT_DATE AS period,
                pol.POLICY_NUM AS policy_num,
                MAX(pol.BRUTO_MONTHLY_PREMIUM) AS monthly_premium
            FROM DWH_FCT_POLICY_INVESTMENT_TRACK pit
            INNER JOIN scoped sc ON sc.CUSTOMER_ID = pit.CUSTOMER_ID
            INNER JOIN DWH_DIM_ALL_POLICY pol
                ON pol.CUSTOMER_ID = CAST(sc.CUSTOMER_ID AS TEXT)
                AND pol.POLICY_NUM = pit.POLICY_NUM
                AND pol.IS_ACTIVE = 1
            GROUP BY pit.SNAPSHOT_DATE, pol.POLICY_NUM
        )
        SELECT
            period,
            COUNT(*) AS active_policy_count,
            COALESCE(SUM(monthly_premium), 0) AS monthly_premium_total
        FROM policy_month
        GROUP BY period
        ORDER BY period ASC
        """,
        params,
    ).fetchall()

    if rows:
        return [
            {
                "period": row["period"],
                "active_policy_count": int(row["active_policy_count"] or 0),
                "monthly_premium_total": round(float(row["monthly_premium_total"] or 0), 2),
            }
            for row in rows
        ]

    # Fallback when no investment periods: single point from current policies.
    fallback = conn.execute(
        f"""
        WITH scoped AS (
            SELECT c.CUSTOMER_ID
            FROM DWH_DIM_CUSTOMERS_UNIQUE c
            WHERE {where_sql}
        )
        SELECT
            COUNT(DISTINCT pol.POLICY_NUM) AS active_policy_count,
            COALESCE(SUM(pol.BRUTO_MONTHLY_PREMIUM), 0) AS monthly_premium_total
        FROM DWH_DIM_ALL_POLICY pol
        INNER JOIN scoped sc ON pol.CUSTOMER_ID = CAST(sc.CUSTOMER_ID AS TEXT)
        WHERE pol.IS_ACTIVE = 1
        """,
        params,
    ).fetchone()
    if fallback is None:
        return []
    return [
        {
            "period": "2025-09-30",
            "active_policy_count": int(fallback["active_policy_count"] or 0),
            "monthly_premium_total": round(float(fallback["monthly_premium_total"] or 0), 2),
        }
    ]


def fetch_engagement_trend(
    conn: sqlite3.Connection,
    *,
    segment: str | None = None,
) -> list[dict]:
    where_sql, params = _scope(segment)
    table = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='APP_CUSTOMER_INTERACTION_EVENTS'"
    ).fetchone()
    if not table:
        return []

    rows = conn.execute(
        f"""
        WITH scoped AS (
            SELECT c.CUSTOMER_ID
            FROM DWH_DIM_CUSTOMERS_UNIQUE c
            WHERE {where_sql}
        )
        SELECT
            substr(e.EVENT_TS, 1, 7) AS period,
            COUNT(*) AS interaction_events,
            SUM(
                CASE WHEN e.EVENT_TYPE IN ('WEB_SEARCH', 'REVIEW', 'AGENT_QUESTION')
                THEN 1 ELSE 0 END
            ) AS digital_touchpoints,
            SUM(CASE WHEN e.EVENT_TYPE = 'REVIEW' THEN 1 ELSE 0 END) AS review_events
        FROM APP_CUSTOMER_INTERACTION_EVENTS e
        INNER JOIN scoped sc ON sc.CUSTOMER_ID = e.CUSTOMER_ID
        GROUP BY substr(e.EVENT_TS, 1, 7)
        ORDER BY period ASC
        """,
        params,
    ).fetchall()
    return [
        {
            "period": f"{row['period']}-01",
            "interaction_events": int(row["interaction_events"] or 0),
            "digital_touchpoints": int(row["digital_touchpoints"] or 0),
            "review_events": int(row["review_events"] or 0),
        }
        for row in rows
    ]


def fetch_objective_trends(
    conn: sqlite3.Connection,
    *,
    segment: str | None = None,
) -> dict:
    return {
        "objectives_note": OBJECTIVES_NOTE,
        "savings_aum_trend": fetch_savings_aum_trend(conn, segment=segment),
        "premium_momentum_trend": fetch_premium_momentum_trend(conn, segment=segment),
        "engagement_trend": fetch_engagement_trend(conn, segment=segment),
    }
