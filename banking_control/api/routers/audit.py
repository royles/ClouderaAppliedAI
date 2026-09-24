from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from banking_control.api.deps import get_db_connection

router = APIRouter(tags=["audit"])


@router.get("/api/audit-log")
def audit_log(
    limit: int = Query(30, le=100),
    conn: Any = Depends(get_db_connection),
) -> list[dict[str, Any]]:
    try:
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
    finally:
        conn.close()
