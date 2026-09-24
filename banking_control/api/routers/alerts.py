from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from banking_control.api.deps import get_db_connection

router = APIRouter(prefix="/api", tags=["alerts"])


@router.get("/alerts")
def list_alerts(
    status: str | None = None,
    min_risk: float = Query(0.0, ge=0.0, le=1.0),
    limit: int = Query(50, le=100),
    conn: Any = Depends(get_db_connection),
) -> list[dict[str, Any]]:
    try:
        params: list[Any] = [min_risk]
        clauses = ["a.risk_score >= ?"]
        if status:
            clauses.append("a.status = ?")
            params.append(status)
        params.append(limit)
        where = "WHERE " + " AND ".join(clauses)
        rows = conn.execute(
            f"""
            SELECT a.alert_id, a.alert_at, a.alert_type, a.amount_usd, a.customer_ref,
                   a.channel, a.status, a.risk_score, u.unit_code
            FROM FCT_TRANSACTION_ALERT a
            JOIN DIM_BUSINESS_UNIT u ON u.unit_id = a.unit_id
            {where}
            ORDER BY a.risk_score DESC, a.alert_at DESC
            LIMIT ?
            """,
            params,
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
