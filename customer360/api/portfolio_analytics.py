"""Portfolio KPIs, value history, and churn-informed retention forecast."""

from __future__ import annotations

import sqlite3
from datetime import date

from customer360.api.policy_counts import policy_totals_for_segment
from customer360.api.portfolio_objectives import BOOK_WIDE_SEGMENT
from customer360.api.segments import SEGMENT_WHERE, normalize_segment
from customer360.api.value_history import CUSTOMER_VALUE_SQL, fetch_value_history
from customer360.business_kpi_targets import build_kpi_targets
from customer360.api.portfolio_objectives import fetch_objective_trends
from customer360.churn.effective_risk import BOOK_DEFAULT_CHURN_RATE, effective_churn_probability_sql
from customer360.churn.scoring import churn_scores_populated, churn_table_exists

METHODOLOGY_NOTE = (
    "Churn-aware metrics use ML scores when present; otherwise LOW/MEDIUM/HIGH tiers "
    "map to 5% / 15% / 40% 12-month lapse estimates. Value-at-risk is book-weighted "
    "(customer value × estimated lapse probability). Forward months apply monthly "
    "survival S(t)=(1−m)^t with m from the portfolio weighted churn rate (capped at 25%). "
    "Historical risk applies current scores to past book totals for trend context."
)

_CHURN_PROB_EXPR = effective_churn_probability_sql("ch")


def _segment_where(segment: str | None) -> tuple[str, list[object]]:
    seg = normalize_segment(segment)
    return f"c.CURRENT_IND = 1 AND ({SEGMENT_WHERE[seg]})", []


def _customer_metrics_ready(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='APP_CUSTOMER_METRICS'"
    ).fetchone()
    if not row:
        return False
    count = conn.execute("SELECT COUNT(*) FROM APP_CUSTOMER_METRICS").fetchone()[0]
    return int(count or 0) > 0


def _churn_table_exists(conn: sqlite3.Connection) -> bool:
    return churn_table_exists(conn)


def _finalize_churn_kpis(
    *,
    churn_ready: bool,
    scores_ready: bool,
    weighted_churn: float,
    high_risk_customers: int,
    medium_risk_customers: int,
) -> tuple[float | None, float | None]:
    """
    Retention = 1 − book-weighted estimated 12-month lapse rate.
    Returns (weighted_churn, annual_retention) or (None, None) when unscored.
    """
    if not churn_ready or not scores_ready:
        return None, None

    w = max(0.0, float(weighted_churn))
    if w <= 0 and (high_risk_customers + medium_risk_customers) > 0:
        # Scores present but lapse weight collapsed (e.g. stale cache / zero ML output).
        w = BOOK_DEFAULT_CHURN_RATE
    retention = round(1.0 - w, 4)
    return round(w, 4), retention


def _fetch_kpis(conn: sqlite3.Connection, segment: str | None) -> dict:
    where_sql, params = _segment_where(segment)
    churn_ready = _churn_table_exists(conn)
    scores_ready = churn_scores_populated(conn) if churn_ready else False
    if churn_ready:
        churn_join = "LEFT JOIN APP_CUSTOMER_CHURN_SCORES ch ON ch.CUSTOMER_ID = s.CUSTOMER_ID"
        value_at_risk_sql = f"COALESCE(SUM(s.customer_value * ({_CHURN_PROB_EXPR})), 0)"
        weighted_churn_sql = f"""
            COALESCE(
                SUM(s.customer_value * ({_CHURN_PROB_EXPR}))
                / NULLIF(SUM(s.customer_value), 0),
                0
            )
        """
        high_risk_customers_sql = (
            "COALESCE(SUM(CASE WHEN UPPER(ch.CHURN_RISK_TIER) = 'HIGH' THEN 1 ELSE 0 END), 0)"
        )
        medium_risk_customers_sql = (
            "COALESCE(SUM(CASE WHEN UPPER(ch.CHURN_RISK_TIER) = 'MEDIUM' THEN 1 ELSE 0 END), 0)"
        )
        low_risk_customers_sql = (
            "COALESCE(SUM(CASE WHEN UPPER(ch.CHURN_RISK_TIER) = 'LOW' THEN 1 ELSE 0 END), 0)"
        )
        high_risk_book_sql = (
            "COALESCE(SUM(CASE WHEN UPPER(ch.CHURN_RISK_TIER) = 'HIGH' "
            "THEN s.customer_value ELSE 0 END), 0)"
        )
    else:
        churn_join = ""
        value_at_risk_sql = "0"
        weighted_churn_sql = "0"
        high_risk_customers_sql = "0"
        medium_risk_customers_sql = "0"
        low_risk_customers_sql = "0"
        high_risk_book_sql = "0"

    if _customer_metrics_ready(conn):
        scoped_sql = f"""
            SELECT
                c.CUSTOMER_ID,
                m.CUSTOMER_VALUE AS customer_value,
                m.POLICY_COUNT AS policy_count
            FROM DWH_DIM_CUSTOMERS_UNIQUE c
            INNER JOIN APP_CUSTOMER_METRICS m ON m.CUSTOMER_ID = c.CUSTOMER_ID
            WHERE {where_sql}
        """
    else:
        scoped_sql = f"""
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
        """

    row = conn.execute(
        f"""
        WITH scoped AS (
            {scoped_sql}
        )
        SELECT
            COUNT(*) AS active_customers,
            COALESCE(SUM(s.customer_value), 0) AS total_book_value,
            COALESCE(AVG(s.customer_value), 0) AS avg_customer_value,
            COALESCE(AVG(s.policy_count), 0) AS avg_policies_per_customer,
            {value_at_risk_sql} AS value_at_risk_12m,
            {weighted_churn_sql} AS weighted_churn_probability,
            {high_risk_customers_sql} AS high_risk_customers,
            {medium_risk_customers_sql} AS medium_risk_customers,
            {low_risk_customers_sql} AS low_risk_customers,
            {high_risk_book_sql} AS high_risk_book_value
        FROM scoped s
        {churn_join}
        """,
        params,
    ).fetchone()

    total_book = float(row["total_book_value"] or 0)
    weighted_raw = float(row["weighted_churn_probability"] or 0)
    high_risk_book = float(row["high_risk_book_value"] or 0)
    high_risk_customers = int(row["high_risk_customers"] or 0)
    medium_risk_customers = int(row["medium_risk_customers"] or 0)
    weighted_churn, retention = _finalize_churn_kpis(
        churn_ready=churn_ready,
        scores_ready=scores_ready,
        weighted_churn=weighted_raw,
        high_risk_customers=high_risk_customers,
        medium_risk_customers=medium_risk_customers,
    )
    total_policies, active_policies = policy_totals_for_segment(conn, segment)

    return {
        "active_customers": int(row["active_customers"] or 0),
        "total_policies": total_policies,
        "active_policies": active_policies,
        "total_book_value": round(total_book, 2),
        "avg_customer_value": round(float(row["avg_customer_value"] or 0), 2),
        "avg_policies_per_customer": round(float(row["avg_policies_per_customer"] or 0), 2),
        "weighted_churn_probability": weighted_churn,
        "annual_retention_rate_forecast": retention,
        "value_at_risk_12m": round(float(row["value_at_risk_12m"] or 0), 2),
        "high_risk_customers": high_risk_customers,
        "medium_risk_customers": medium_risk_customers,
        "low_risk_customers": int(row["low_risk_customers"] or 0),
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

    objectives = fetch_objective_trends(
        conn,
        segment=seg,
        prefer_materialized=(seg == BOOK_WIDE_SEGMENT),
    )

    return {
        "segment": seg,
        "kpis": kpis,
        "kpi_targets": build_kpi_targets(kpis, value_points, conn=conn),
        "value_points": value_points,
        "investment_returns": investment_returns,
        "churn_forecast": churn_forecast,
        "methodology_note": METHODOLOGY_NOTE,
        "objectives_segment": seg,
        **objectives,
    }


def apply_live_churn_metrics(conn: sqlite3.Connection, payload: dict) -> dict:
    """Recompute churn KPIs and horizon from current scores (cached charts may be stale)."""
    seg = normalize_segment(payload.get("segment"))
    value_points = payload.get("value_points") or []
    kpis = _fetch_kpis(conn, seg)

    if len(value_points) >= 2:
        first = float(value_points[0]["total_value"])
        last = float(value_points[-1]["total_value"])
        if first > 0:
            kpis["book_growth_pct"] = round(100.0 * (last - first) / first, 1)
    elif isinstance(payload.get("kpis"), dict):
        kpis["book_growth_pct"] = payload["kpis"].get("book_growth_pct")

    churn_forecast = _build_churn_forecast(
        value_points,
        weighted_churn=kpis.get("weighted_churn_probability"),
        annual_retention=kpis.get("annual_retention_rate_forecast"),
    )
    out = dict(payload)
    out["segment"] = seg
    out["kpis"] = kpis
    out["churn_forecast"] = churn_forecast
    out["methodology_note"] = METHODOLOGY_NOTE
    return out
