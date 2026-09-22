"""Trend series aligned with Migdal-style strategic objectives (synthetic book)."""

from __future__ import annotations

import sqlite3

from customer360.api.segments import SEGMENT_WHERE, normalize_segment

BOOK_WIDE_SEGMENT = "customers_all"

OBJECTIVES_NOTE_BOOK = (
    "Objective charts mirror Migdal Insurance & Finance strategic themes: "
    "long-term savings and AUM growth (pension & provident), retention of active "
    "policy relationships and premium momentum in general insurance, and digital "
    "customer engagement. Trends reflect the full active customer book."
)

OBJECTIVES_NOTE_COHORT = (
    "Strategic objective trends below use the same overview card filter as the book "
    "charts and KPIs above. Clear the card selection to return to full-book objectives."
)

# Back-compat alias for materialized cache readers.
OBJECTIVES_NOTE = OBJECTIVES_NOTE_BOOK


def objectives_note_for_segment(segment: str | None) -> str:
    seg = normalize_segment(segment)
    return OBJECTIVES_NOTE_BOOK if seg == BOOK_WIDE_SEGMENT else OBJECTIVES_NOTE_COHORT


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

    status_rows = conn.execute(
        f"""
        WITH scoped AS (
            SELECT c.CUSTOMER_ID
            FROM DWH_DIM_CUSTOMERS_UNIQUE c
            WHERE {where_sql}
        )
        SELECT
            ps.SNAPSHOT_DATE AS period,
            COUNT(DISTINCT ps.POLICY_NUM) AS active_policy_count,
            COALESCE(SUM(ps.MONTHLY_PREMIUM), 0) AS monthly_premium_total
        FROM DWH_FCT_POLICY_STATUS ps
        INNER JOIN scoped sc ON sc.CUSTOMER_ID = ps.CUSTOMER_ID
        GROUP BY ps.SNAPSHOT_DATE
        ORDER BY ps.SNAPSHOT_DATE ASC
        """,
        params,
    ).fetchall()
    if status_rows:
        return [
            {
                "period": row["period"],
                "active_policy_count": int(row["active_policy_count"] or 0),
                "monthly_premium_total": round(float(row["monthly_premium_total"] or 0), 2),
            }
            for row in status_rows
        ]

    # Fallback when no snapshot periods: single point from current policies.
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


def engagement_trend_needs_avg_refresh(trends: list[dict] | None) -> bool:
    """Cached portfolio/objective rows may predate monthly avg_review_rating."""
    if not trends:
        return True
    if not any(int(p.get("review_events") or 0) > 0 for p in trends):
        return False
    return not any(p.get("avg_review_rating") is not None for p in trends)


def ensure_engagement_review_averages(
    conn: sqlite3.Connection,
    trends: list[dict] | None,
    *,
    segment: str | None,
) -> list[dict]:
    if not engagement_trend_needs_avg_refresh(trends):
        return list(trends or [])
    return fetch_engagement_trend(conn, segment=segment)


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
            SUM(CASE WHEN e.EVENT_TYPE = 'REVIEW' THEN 1 ELSE 0 END) AS review_events,
            ROUND(
                AVG(
                    CASE
                        WHEN e.EVENT_TYPE = 'REVIEW' AND e.RATING IS NOT NULL
                        THEN e.RATING
                    END
                ),
                2,
            ) AS avg_review_rating
        FROM APP_CUSTOMER_INTERACTION_EVENTS e
        INNER JOIN scoped sc ON sc.CUSTOMER_ID = e.CUSTOMER_ID
        GROUP BY substr(e.EVENT_TS, 1, 7)
        ORDER BY period ASC
        """,
        params,
    ).fetchall()
    out: list[dict] = []
    for row in rows:
        avg = row["avg_review_rating"]
        out.append(
            {
                "period": f"{row['period']}-01",
                "interaction_events": int(row["interaction_events"] or 0),
                "digital_touchpoints": int(row["digital_touchpoints"] or 0),
                "review_events": int(row["review_events"] or 0),
                "avg_review_rating": float(avg) if avg is not None else None,
            }
        )
    return out


def fetch_objective_trends(
    conn: sqlite3.Connection,
    *,
    segment: str | None = BOOK_WIDE_SEGMENT,
    prefer_materialized: bool = True,
) -> dict:
    """Strategic trends for the requested customer segment."""
    seg = normalize_segment(segment or BOOK_WIDE_SEGMENT)
    if prefer_materialized and seg == BOOK_WIDE_SEGMENT:
        from customer360.book_objectives_cache import load_book_objective_trends

        cached = load_book_objective_trends(conn)
        if cached is not None:
            out = dict(cached)
            out["objectives_note"] = objectives_note_for_segment(seg)
            out["engagement_trend"] = ensure_engagement_review_averages(
                conn,
                out.get("engagement_trend"),
                segment=seg,
            )
            return out
    return {
        "objectives_note": objectives_note_for_segment(seg),
        "savings_aum_trend": fetch_savings_aum_trend(conn, segment=seg),
        "premium_momentum_trend": fetch_premium_momentum_trend(conn, segment=seg),
        "engagement_trend": fetch_engagement_trend(conn, segment=seg),
    }
