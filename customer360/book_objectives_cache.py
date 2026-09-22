"""Materialized book-wide strategic objective trends (fast API reads)."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from customer360.api.portfolio_objectives import (
    BOOK_WIDE_SEGMENT,
    OBJECTIVES_NOTE,
    fetch_engagement_trend,
    fetch_premium_momentum_trend,
    fetch_savings_aum_trend,
)

_SAVINGS_TABLE = "APP_BOOK_SAVINGS_AUM_TREND"
_PREMIUM_TABLE = "APP_BOOK_PREMIUM_MOMENTUM_TREND"
_ENGAGEMENT_TABLE = "APP_BOOK_ENGAGEMENT_TREND"


def book_objectives_materialized(conn: sqlite3.Connection) -> bool:
    row = conn.execute(f"SELECT COUNT(*) FROM {_SAVINGS_TABLE}").fetchone()
    return int(row[0] or 0) > 0


def load_book_objective_trends(conn: sqlite3.Connection) -> dict | None:
    """Read precomputed trends; returns None when tables are empty."""
    from customer360.metrics_refresh import ensure_metrics_schema

    ensure_metrics_schema(conn)
    if not book_objectives_materialized(conn):
        return None

    savings = conn.execute(
        f"""
        SELECT PERIOD, ACCUMULATION_TOTAL, ACTIVE_SAVERS, SAVINGS_POLICIES
        FROM {_SAVINGS_TABLE}
        ORDER BY PERIOD ASC
        """
    ).fetchall()
    premium = conn.execute(
        f"""
        SELECT PERIOD, ACTIVE_POLICY_COUNT, MONTHLY_PREMIUM_TOTAL
        FROM {_PREMIUM_TABLE}
        ORDER BY PERIOD ASC
        """
    ).fetchall()
    engagement = conn.execute(
        f"""
        SELECT
            PERIOD,
            INTERACTION_EVENTS,
            DIGITAL_TOUCHPOINTS,
            REVIEW_EVENTS,
            AVG_REVIEW_RATING
        FROM {_ENGAGEMENT_TABLE}
        ORDER BY PERIOD ASC
        """
    ).fetchall()

    return {
        "objectives_note": OBJECTIVES_NOTE,
        "savings_aum_trend": [
            {
                "period": row["PERIOD"],
                "accumulation_total": round(float(row["ACCUMULATION_TOTAL"] or 0), 2),
                "active_savers": int(row["ACTIVE_SAVERS"] or 0),
                "savings_policies": int(row["SAVINGS_POLICIES"] or 0),
            }
            for row in savings
        ],
        "premium_momentum_trend": [
            {
                "period": row["PERIOD"],
                "active_policy_count": int(row["ACTIVE_POLICY_COUNT"] or 0),
                "monthly_premium_total": round(float(row["MONTHLY_PREMIUM_TOTAL"] or 0), 2),
            }
            for row in premium
        ],
        "engagement_trend": [
            {
                "period": row["PERIOD"],
                "interaction_events": int(row["INTERACTION_EVENTS"] or 0),
                "digital_touchpoints": int(row["DIGITAL_TOUCHPOINTS"] or 0),
                "review_events": int(row["REVIEW_EVENTS"] or 0),
                "avg_review_rating": (
                    float(row["AVG_REVIEW_RATING"])
                    if row["AVG_REVIEW_RATING"] is not None
                    else None
                ),
            }
            for row in engagement
        ],
    }


def refresh_book_objective_trends(conn: sqlite3.Connection) -> dict[str, int]:
    """Recompute book-wide objective series and persist to cache tables."""
    from customer360.metrics_refresh import ensure_metrics_schema

    ensure_metrics_schema(conn)
    refreshed_at = datetime.now(timezone.utc).isoformat()
    seg = BOOK_WIDE_SEGMENT

    savings = fetch_savings_aum_trend(conn, segment=seg)
    premium = fetch_premium_momentum_trend(conn, segment=seg)
    engagement = fetch_engagement_trend(conn, segment=seg)

    conn.execute(f"DELETE FROM {_SAVINGS_TABLE}")
    conn.execute(f"DELETE FROM {_PREMIUM_TABLE}")
    conn.execute(f"DELETE FROM {_ENGAGEMENT_TABLE}")

    conn.executemany(
        f"""
        INSERT INTO {_SAVINGS_TABLE} (
            PERIOD, ACCUMULATION_TOTAL, ACTIVE_SAVERS, SAVINGS_POLICIES, REFRESHED_AT
        ) VALUES (?, ?, ?, ?, ?)
        """,
        [
            (
                row["period"],
                row["accumulation_total"],
                row["active_savers"],
                row["savings_policies"],
                refreshed_at,
            )
            for row in savings
        ],
    )
    conn.executemany(
        f"""
        INSERT INTO {_PREMIUM_TABLE} (
            PERIOD, ACTIVE_POLICY_COUNT, MONTHLY_PREMIUM_TOTAL, REFRESHED_AT
        ) VALUES (?, ?, ?, ?)
        """,
        [
            (
                row["period"],
                row["active_policy_count"],
                row["monthly_premium_total"],
                refreshed_at,
            )
            for row in premium
        ],
    )
    conn.executemany(
        f"""
        INSERT INTO {_ENGAGEMENT_TABLE} (
            PERIOD,
            INTERACTION_EVENTS,
            DIGITAL_TOUCHPOINTS,
            REVIEW_EVENTS,
            AVG_REVIEW_RATING,
            REFRESHED_AT
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                row["period"],
                row["interaction_events"],
                row["digital_touchpoints"],
                row["review_events"],
                row.get("avg_review_rating"),
                refreshed_at,
            )
            for row in engagement
        ],
    )
    conn.commit()
    return {
        "savings_periods": len(savings),
        "premium_periods": len(premium),
        "engagement_periods": len(engagement),
    }
