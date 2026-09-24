from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from banking_control.api.deps import get_db_connection

router = APIRouter(prefix="/api", tags=["controls"])


@router.get("/controls")
def list_controls(
    domain: str | None = None,
    risk_tier: str | None = None,
    golden: bool | None = None,
    similarity_key: str | None = None,
    search: str | None = Query(None, max_length=120),
    limit: int = Query(100, le=500),
    conn: Any = Depends(get_db_connection),
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if search and search.strip():
        term = f"%{search.strip()}%"
        clauses.append(
            "(c.control_code LIKE ? OR c.control_name LIKE ? OR c.description LIKE ?)"
        )
        params.extend([term, term, term])
    if domain:
        clauses.append("c.domain = ?")
        params.append(domain)
    if risk_tier:
        clauses.append("c.risk_tier = ?")
        params.append(risk_tier)
    if golden is True:
        clauses.append("c.is_golden = 1")
    elif golden is False:
        clauses.append("c.is_golden = 0")
    if similarity_key:
        clauses.append("c.similarity_key = ?")
        params.append(similarity_key)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    rows = conn.execute(
        f"""
        SELECT c.control_id, c.control_code, c.control_name, c.domain, c.risk_tier,
               c.owner, c.frequency, c.is_golden, c.similarity_key,
               (
                 SELECT a.status FROM FCT_CONTROL_ASSESSMENT a
                 WHERE a.control_id = c.control_id
                 ORDER BY a.assessment_date DESC LIMIT 1
               ) AS latest_status
        FROM DIM_CONTROL c
        {where}
        ORDER BY c.is_golden DESC, c.risk_tier, c.control_code
        LIMIT ?
        """,
        params,
    ).fetchall()
    return [dict(r) for r in rows]
