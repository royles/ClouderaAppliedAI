from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from banking_control.api.date_filters import append_iso_date_range
from banking_control.api.deps import get_db_connection

router = APIRouter(tags=["audit"])


@router.get("/api/audit-log")
def audit_log(
    from_date: str | None = Query(None, description="Inclusive start date (ISO YYYY-MM-DD)"),
    to_date: str | None = Query(None, description="Inclusive end date (ISO YYYY-MM-DD)"),
    limit: int = Query(30, le=100),
    conn: Any = Depends(get_db_connection),
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    append_iso_date_range(clauses, params, column="event_at", from_date=from_date, to_date=to_date)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    rows = conn.execute(
        f"""
        SELECT event_id, event_at, actor, action, entity_type, entity_id, detail
        FROM FCT_AUDIT_EVENT
        {where}
        ORDER BY event_at DESC
        LIMIT ?
        """,
        params,
    ).fetchall()
    return [dict(r) for r in rows]


@router.get("/api/audit-log/{event_id}")
def get_audit_event(
    event_id: int,
    conn: Any = Depends(get_db_connection),
) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT event_id, event_at, actor, action, entity_type, entity_id, detail
        FROM FCT_AUDIT_EVENT
        WHERE event_id = ?
        """,
        (event_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Audit event not found")
    return {"event": dict(row)}
