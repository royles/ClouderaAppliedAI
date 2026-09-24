from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from banking_control.api.date_filters import append_iso_date_range
from banking_control.api.deps import get_db_connection

router = APIRouter(prefix="/api", tags=["alerts"])


@router.get("/alerts")
def list_alerts(
    status: str | None = None,
    min_risk: float = Query(0.0, ge=0.0, le=1.0),
    from_date: str | None = Query(None, description="Inclusive start date (ISO YYYY-MM-DD)"),
    to_date: str | None = Query(None, description="Inclusive end date (ISO YYYY-MM-DD)"),
    limit: int = Query(40, ge=1, le=100),
    before_id: int | None = Query(None, description="Page older alerts with alert_id less than this"),
    since_id: int | None = Query(None, description="Return alerts newer than this alert_id"),
    live: bool = Query(
        False,
        description="When true with since_id, skip date filters so live feed can prepend new alerts",
    ),
    conn: Any = Depends(get_db_connection),
) -> dict[str, Any]:
    params: list[Any] = [min_risk]
    clauses = ["a.risk_score >= ?"]
    live_feed = live and since_id is not None
    if status and not live_feed:
        clauses.append("a.status = ?")
        params.append(status)
    if not live_feed:
        append_iso_date_range(clauses, params, column="a.alert_at", from_date=from_date, to_date=to_date)

    if since_id is not None:
        clauses.append("a.alert_id > ?")
        params.append(since_id)
        order_sql = "ORDER BY a.alert_id DESC"
    elif before_id is not None:
        clauses.append("a.alert_id < ?")
        params.append(before_id)
        order_sql = "ORDER BY a.alert_id DESC"
    else:
        order_sql = "ORDER BY a.alert_at DESC, a.alert_id DESC"

    fetch_limit = limit + 1
    params.append(fetch_limit)
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    rows = conn.execute(
        f"""
        SELECT a.alert_id, a.alert_at, a.alert_type, a.amount_usd, a.customer_ref,
               a.channel, a.status, a.risk_score, u.unit_code
        FROM FCT_TRANSACTION_ALERT a
        JOIN DIM_BUSINESS_UNIT u ON u.unit_id = a.unit_id
        {where}
        {order_sql}
        LIMIT ?
        """,
        params,
    ).fetchall()
    items = [dict(r) for r in rows[:limit]]
    has_more = len(rows) > limit
    max_id = conn.execute("SELECT COALESCE(MAX(alert_id), 0) AS n FROM FCT_TRANSACTION_ALERT").fetchone()["n"]
    return {"items": items, "has_more": has_more, "max_alert_id": int(max_id)}


@router.get("/alerts/{alert_id}")
def get_alert(
    alert_id: int,
    conn: Any = Depends(get_db_connection),
) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT a.alert_id, a.alert_at, a.alert_type, a.amount_usd, a.customer_ref,
               a.channel, a.status, a.risk_score, a.narrative,
               u.unit_id, u.unit_code, u.unit_name, u.region
        FROM FCT_TRANSACTION_ALERT a
        JOIN DIM_BUSINESS_UNIT u ON u.unit_id = a.unit_id
        WHERE a.alert_id = ?
        """,
        (alert_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"alert": dict(row)}
