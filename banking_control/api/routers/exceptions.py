from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from banking_control.api.deps import get_db_connection
from banking_control.db import refresh_overview_cache

router = APIRouter(prefix="/api", tags=["exceptions"])


@router.get("/exceptions")
def list_exceptions(
    status: str | None = None,
    limit: int = Query(50, le=100),
    conn: Any = Depends(get_db_connection),
) -> list[dict[str, Any]]:
    params: list[Any] = []
    where = ""
    if status:
        where = "WHERE e.status = ?"
        params.append(status)
    params.append(limit)
    rows = conn.execute(
        f"""
        SELECT e.exception_id, e.title, e.severity, e.status, e.opened_at, e.due_date,
               e.assignee, c.control_code, u.unit_code
        FROM FCT_EXCEPTION e
        JOIN DIM_CONTROL c ON c.control_id = e.control_id
        JOIN DIM_BUSINESS_UNIT u ON u.unit_id = e.unit_id
        {where}
        ORDER BY
          CASE e.severity
            WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4
          END,
          e.due_date
        LIMIT ?
        """,
        params,
    ).fetchall()
    return [dict(r) for r in rows]


@router.patch("/exceptions/{exception_id}")
def update_exception(
    exception_id: int,
    body: dict[str, str],
    conn: Any = Depends(get_db_connection),
) -> dict[str, Any]:
    allowed = {"Open", "In Remediation", "Pending Validation", "Closed"}
    new_status = body.get("status")
    if new_status not in allowed:
        raise HTTPException(status_code=400, detail=f"status must be one of {sorted(allowed)}")

    cur = conn.execute(
        "UPDATE FCT_EXCEPTION SET status = ? WHERE exception_id = ?",
        (new_status, exception_id),
    )
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Exception not found")
    conn.execute(
        """
        INSERT INTO FCT_AUDIT_EVENT (event_at, actor, action, entity_type, entity_id, detail)
        VALUES (datetime('now'), 'dashboard_user', 'Exception status updated', 'exception', ?, ?)
        """,
        (str(exception_id), f"Status set to {new_status}"),
    )
    conn.commit()
    refresh_overview_cache(conn)
    row = conn.execute(
        "SELECT * FROM FCT_EXCEPTION WHERE exception_id = ?", (exception_id,)
    ).fetchone()
    return dict(row)
