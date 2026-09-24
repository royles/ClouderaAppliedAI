from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from banking_control.api.deps import get_db_connection

router = APIRouter(prefix="/api", tags=["controls"])


@router.get("/controls")
def list_controls(
    domain: str | None = None,
    risk_tier: str | None = None,
    golden: bool | None = None,
    similarity_key: str | None = None,
    search: str | None = Query(None, max_length=120),
    latest_status: str | None = None,
    needs_attention: bool | None = None,
    limit: int = Query(100, le=500),
    conn: Any = Depends(get_db_connection),
) -> list[dict[str, Any]]:
    latest_status_sql = """
        (
          SELECT a.status FROM FCT_CONTROL_ASSESSMENT a
          WHERE a.control_id = c.control_id
          ORDER BY a.assessment_date DESC LIMIT 1
        )
    """
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
    if latest_status:
        clauses.append(f"COALESCE({latest_status_sql}, 'Not Tested') = ?")
        params.append(latest_status)
    if needs_attention is True:
        clauses.append(
            f"COALESCE({latest_status_sql}, 'Not Tested') != 'Effective'"
        )
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


@router.get("/controls/{control_id}")
def get_control(
    control_id: int,
    conn: Any = Depends(get_db_connection),
) -> dict[str, Any]:
    row = conn.execute(
        "SELECT * FROM DIM_CONTROL WHERE control_id = ?",
        (control_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Control not found")

    latest = conn.execute(
        """
        SELECT status FROM FCT_CONTROL_ASSESSMENT
        WHERE control_id = ?
        ORDER BY assessment_date DESC LIMIT 1
        """,
        (control_id,),
    ).fetchone()
    assessments = conn.execute(
        """
        SELECT a.assessment_id, a.assessment_date, a.status, a.tester,
               a.evidence_ref, a.notes, u.unit_code, u.unit_name
        FROM FCT_CONTROL_ASSESSMENT a
        JOIN DIM_BUSINESS_UNIT u ON u.unit_id = a.unit_id
        WHERE a.control_id = ?
        ORDER BY a.assessment_date DESC
        LIMIT 20
        """,
        (control_id,),
    ).fetchall()
    exceptions = conn.execute(
        """
        SELECT e.exception_id, e.title, e.severity, e.status, e.opened_at,
               e.due_date, e.assignee, u.unit_code
        FROM FCT_EXCEPTION e
        JOIN DIM_BUSINESS_UNIT u ON u.unit_id = e.unit_id
        WHERE e.control_id = ?
        ORDER BY e.opened_at DESC
        LIMIT 25
        """,
        (control_id,),
    ).fetchall()
    control = dict(row)
    return {
        "control": control,
        "latest_status": latest["status"] if latest else "Not Tested",
        "assessments": [dict(r) for r in assessments],
        "exceptions": [dict(r) for r in exceptions],
    }
