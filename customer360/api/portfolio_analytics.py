"""Portfolio KPIs, value history, and churn-informed retention forecast."""

from __future__ import annotations

import sqlite3
from datetime import date

from customer360.api.segments import SEGMENT_WHERE, normalize_segment
from customer360.api.value_history import CUSTOMER_VALUE_SQL, fetch_value_history
from customer360.business_kpi_targets import build_kpi_targets
from customer360.api.portfolio_objectives import fetch_objective_trends

METHODOLOGY_NOTE = (
    "Churn-aware metrics treat ML scores as 12-month lapse probability (common for "
    "P&C/Life retention planning). Value-at-risk is book-weighted (high-value "
    "accounts drive portfolio exposure). Forward months apply monthly survival "
    "S(t)=(1−m)^t with m from the annual weighted churn rate (capped at 25%). "
    "Historical risk applies current scores to past book totals for trend context."
)


def _segment_where(segment: str | None) -> tuple[str, list[object]]:
    seg = normalize_segment(segment)
    return f"c.CURRENT_IND = 1 AND ({SEGMENT_WHERE[seg]})", []


def _churn_table_exists(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='APP_CUSTOMER_CHURN_SCORES'"
    ).fetchone()
    return row is not None


def _fetch_kpis(conn: sqlite3.Connection, segment: str | None) -> dict:
    where_sql, params = _segment_where(segment)
    churn_join = ""
    if _churn_table_exists(conn):
        churn_join = "LEFT JOIN APP_CUSTOMER_CHURN_SCORES ch ON ch.CUSTOMER_ID = s.CUSTOMER_ID"

    row = conn.execute(
        f"""
        WITH scoped AS (
            SELECT
                c.CUSTOMER_ID,
                ROUND({CUSTOMER_VALUE_SQL}, 2) AS customer_value,
                (
                    SELECT COUNT(*)
                    FROM DWH_DIM_ALL_POLICY p
                    WHERE p.CUSTOMER_ID = CAST(c.CUSTOMER_ID AS TEXT)
                ) AS policy_count
            FROM DWH_DIM_CUSTOMERS_UNIQUE c
            WHERE {where_sql}
        )
        SELECT
            COUNT(*) AS active_customers,
            COALESCE(SUM(s.customer_value), 0) AS total_book_value,
            COALESCE(AVG(s.customer_value), 0) AS avg_customer_value,
            COALESCE(AVG(s.policy_count), 0) AS avg_policies_per_customer,
            COALESCE(SUM(s.customer_value * COALESCE(ch.CHURN_PROBABILITY, 0)), 0)
                AS value_at_risk_12m,
            COALESCE(
                SUM(s.customer_value * COALESCE(ch.CHURN_PROBABILITY, 0))
                / NULLIF(SUM(s.customer_value), 0),
                0
            ) AS weighted_churn_probability,
            COALESCE(SUM(CASE WHEN ch.CHURN_RISK_TIER = 'HIGH' THEN 1 ELSE 0 END), 0)
                AS high_risk_customers,
            COALESCE(SUM(CASE WHEN ch.CHURN_RISK_TIER = 'HIGH' THEN s.customer_value ELSE 0 END), 0)
                AS high_risk_book_value
        FROM scoped s
        {churn_join}
        """,
        params,
    ).fetchone()

    total_book = float(row["total_book_value"] or 0)
    weighted_churn = float(row["weighted_churn_probability"] or 0)
    high_risk_book = float(row["high_risk_book_value"] or 0)
    retention = None if not _churn_table_exists(conn) else round(1.0 - weighted_churn, 4)

    return {
        "active_customers": int(row["active_customers"] or 0),
        "total_book_value": round(total_book, 2),
        "avg_customer_value": round(float(row["avg_customer_value"] or 0), 2),
        "avg_policies_per_customer": round(float(row["avg_policies_per_customer"] or 0), 2),
        "weighted_churn_probability": round(weighted_churn, 4) if _churn_table_exists(conn) else None,
        "annual_retention_rate_forecast": retention,
        "value_at_risk_12m": round(float(row["value_at_risk_12m"] or 0), 2),
        "high_risk_customers": int(row["high_risk_customers"] or 0),
        "high_risk_book_pct": round(100.0 * high_risk_book / total_book, 1) if total_book > 0 else 0.0,
    }


def _add_months(period: str, months: int) -> str:
    y, m = (int(period[:4]), int(period[5:7])) if len(period) >= 7 else (date.today().year, 1)
    m += months
    while m > 12:
        m -= 12
        y += 1
    while m < 1:
        m += 12
        y -= 1
    return f"{y:04d}-{m:02d}"


def _monthly_lapse_rate(annual_weighted_churn: float) -> float:
    annual = min(max(annual_weighted_churn, 0.0), 0.25)
    if annual <= 0:
        return 0.0
    return 1.0 - (1.0 - annual) ** (1.0 / 12.0)


def _build_churn_forecast(
    value_points: list[dict],
    *,
    weighted_churn: float | None,
    annual_retention: float | None,
) -> list[dict]:
    w = weighted_churn if weighted_churn is not None else 0.12
    retention = annual_retention if annual_retention is not None else (1.0 - w)
    monthly = _monthly_lapse_rate(w)
    series: list[dict] = []

    for pt in value_points:
        total = float(pt["total_value"])
        at_risk = round(total * w, 2)
        series.append(
            {
                "period": pt["period"],
                "kind": "actual",
                "total_book_value": total,
                "value_at_risk": at_risk,
                "expected_retained_value": round(total - at_risk, 2),
                "implied_retention_rate": retention,
            }
        )

    if not value_points:
        return series

    last = value_points[-1]
    base_total = float(last["total_value"])
    last_period = str(last["period"])

    for month in range(1, 13):
        factor = (1.0 - monthly) ** month
        projected = round(base_total * factor, 2)
        at_risk = round(projected * w, 2)
        series.append(
            {
                "period": _add_months(last_period, month),
                "kind": "forecast",
                "total_book_value": projected,
                "value_at_risk": at_risk,
                "expected_retained_value": round(projected - at_risk, 2),
                "implied_retention_rate": retention,
            }
        )

    return series


def _build_investment_returns(value_points: list[dict]) -> list[dict]:
    out: list[dict] = []
    prev: float | None = None
    base: float | None = None
    for pt in value_points:
        inv = float(pt["investment_value"])
        if base is None and inv > 0:
            base = inv
        period_ret = None
        if prev is not None and prev > 0:
            period_ret = round(100.0 * (inv - prev) / prev, 2)
        cum = None
        if base and base > 0:
            cum = round(100.0 * (inv - base) / base, 2)
        out.append(
            {
                "period": pt["period"],
                "investment_balance": round(inv, 2),
                "period_return_pct": period_ret,
                "cumulative_return_pct": cum,
            }
        )
        prev = inv
    return out


def fetch_portfolio_analytics(
    conn: sqlite3.Connection,
    *,
    segment: str | None = None,
) -> dict:
    seg = normalize_segment(segment)
    value_points = fetch_value_history(conn, segment=seg)
    kpis = _fetch_kpis(conn, seg)

    book_growth_pct = None
    if len(value_points) >= 2:
        first = float(value_points[0]["total_value"])
        last = float(value_points[-1]["total_value"])
        if first > 0:
            book_growth_pct = round(100.0 * (last - first) / first, 1)
    kpis["book_growth_pct"] = book_growth_pct

    churn_forecast = _build_churn_forecast(
        value_points,
        weighted_churn=kpis.get("weighted_churn_probability"),
        annual_retention=kpis.get("annual_retention_rate_forecast"),
    )
    investment_returns = _build_investment_returns(value_points)

    objectives = fetch_objective_trends(conn)

    return {
        "segment": seg,
        "kpis": kpis,
        "kpi_targets": build_kpi_targets(kpis, value_points, conn=conn),
        "value_points": value_points,
        "investment_returns": investment_returns,
        "churn_forecast": churn_forecast,
        "methodology_note": METHODOLOGY_NOTE,
        **objectives,
    }
