from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from banking_control.api.deps import get_db_connection

router = APIRouter(tags=["audit"])


@router.get("/api/audit-log")
def audit_log(
    limit: int = Query(30, le=100),
    conn: Any = Depends(get_db_connection),
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT event_id, event_at, actor, action, entity_type, entity_id, detail
        FROM FCT_AUDIT_EVENT
        ORDER BY event_at DESC
        LIMIT ?
        """,
        (limit,),
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
