"""Live warehouse snippets passed to the executive copilot model."""

from __future__ import annotations

import sqlite3

from customer360.api.segments import normalize_segment


def overview_snippet(conn: sqlite3.Connection) -> str | None:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='APP_OVERVIEW_COUNTS'"
    ).fetchone()
    if not row:
        return None
    customers = conn.execute(
        """
        SELECT ROW_COUNT FROM APP_OVERVIEW_COUNTS
        WHERE FILTER_KEY = 'customers_all' LIMIT 1
        """
    ).fetchone()
    if not customers:
        return None
    n = int(customers[0])
    return f"Current customers (overview): {n:,}."


def portfolio_snippet(conn: sqlite3.Connection, segment: str) -> str | None:
    from customer360.api.portfolio_analytics import fetch_portfolio_analytics

    try:
        payload = fetch_portfolio_analytics(conn, segment=segment)
    except Exception:
        return None
    kpis = payload.get("kpis") or {}
    book = kpis.get("total_book_value")
    risk = kpis.get("value_at_risk_12m")
    retention = kpis.get("annual_retention_rate_forecast")
    parts: list[str] = []
    if book is not None:
        parts.append(f"total_book_value_ils={float(book):,.0f}")
    if retention is not None:
        parts.append(f"retention_12m_forecast_pct={float(retention) * 100:.2f}")
    if risk is not None:
        parts.append(f"value_at_churn_risk_ils={float(risk):,.0f}")
    if not parts:
        return None
    return f"Portfolio KPIs (segment={segment}): " + ", ".join(parts) + "."


def gather_context(
    conn: sqlite3.Connection,
    *,
    message: str,
    segment: str | None,
) -> dict:
    seg = normalize_segment(segment)
    lowered = (message or "").lower()
    snippets: list[str] = []

    if any(w in lowered for w in ("how many", "count", "customers", "book size", "overview")):
        ov = overview_snippet(conn)
        if ov:
            snippets.append(ov)

    if any(
        w in lowered
        for w in (
            "kpi",
            "retention",
            "book value",
            "churn",
            "portfolio",
            "value at risk",
            "risk",
            "business",
        )
    ):
        port = portfolio_snippet(conn, seg)
        if port:
            snippets.append(port)

    if not snippets:
        ov = overview_snippet(conn)
        port = portfolio_snippet(conn, seg)
        if ov:
            snippets.append(ov)
        if port:
            snippets.append(port)

    return {"segment": seg, "snippets": snippets}
