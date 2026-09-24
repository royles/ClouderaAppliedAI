from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from banking_control.db import connect, get_overview, refresh_overview_cache
from banking_control.paths import default_db_path, default_frontend_dist_dir

app = FastAPI(title="Banking Control Solution", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _db() -> Any:
    path = default_db_path()
    if not path.is_file():
        raise HTTPException(
            status_code=503,
            detail="Database not initialized. Run scripts/init_db.py or the init-database job.",
        )
    return connect(path)


@app.get("/api/health")
def health() -> dict[str, str]:
    path = default_db_path()
    return {"status": "ok", "database": "ready" if path.is_file() else "missing"}


@app.get("/api/overview")
def overview(refresh: bool = False) -> dict[str, Any]:
    conn = _db()
    try:
        if refresh:
            return refresh_overview_cache(conn)
        return get_overview(conn)
    finally:
        conn.close()


@app.get("/api/controls")
def list_controls(
    domain: str | None = None,
    risk_tier: str | None = None,
    limit: int = Query(100, le=200),
) -> list[dict[str, Any]]:
    conn = _db()
    try:
        clauses: list[str] = []
        params: list[Any] = []
        if domain:
            clauses.append("c.domain = ?")
            params.append(domain)
        if risk_tier:
            clauses.append("c.risk_tier = ?")
            params.append(risk_tier)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        rows = conn.execute(
            f"""
            SELECT c.control_id, c.control_code, c.control_name, c.domain, c.risk_tier,
                   c.owner, c.frequency,
                   (
                     SELECT a.status FROM FCT_CONTROL_ASSESSMENT a
                     WHERE a.control_id = c.control_id
                     ORDER BY a.assessment_date DESC LIMIT 1
                   ) AS latest_status
            FROM DIM_CONTROL c
            {where}
            ORDER BY c.risk_tier, c.control_code
            LIMIT ?
            """,
            params,
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@app.get("/api/exceptions")
def list_exceptions(
    status: str | None = None,
    limit: int = Query(50, le=100),
) -> list[dict[str, Any]]:
    conn = _db()
    try:
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
    finally:
        conn.close()


@app.patch("/api/exceptions/{exception_id}")
def update_exception(exception_id: int, body: dict[str, str]) -> dict[str, Any]:
    allowed = {"Open", "In Remediation", "Pending Validation", "Closed"}
    new_status = body.get("status")
    if new_status not in allowed:
        raise HTTPException(status_code=400, detail=f"status must be one of {sorted(allowed)}")

    conn = _db()
    try:
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
    finally:
        conn.close()


@app.get("/api/alerts")
def list_alerts(
    status: str | None = None,
    min_risk: float = Query(0.0, ge=0.0, le=1.0),
    limit: int = Query(50, le=100),
) -> list[dict[str, Any]]:
    conn = _db()
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


@app.get("/api/audit-log")
def audit_log(limit: int = Query(30, le=100)) -> list[dict[str, Any]]:
    conn = _db()
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


_FALLBACK_INDEX = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Banking Control Solution</title>
  <style>
    body { font-family: system-ui, sans-serif; background: #0c1118; color: #e8eef7; margin: 2rem; }
    a { color: #3dd6c3; }
    code { background: #1a2433; padding: 0.15rem 0.4rem; border-radius: 4px; }
  </style>
</head>
<body>
  <h1>Banking Control Solution</h1>
  <p>The dashboard bundle was not found under <code>frontend/dist</code>.</p>
  <p>Check that the Git branch includes <code>frontend/dist</code>, or set
     <code>BANKING_CONTROL_FRONTEND_DIR</code> to the folder containing <code>index.html</code>.</p>
  <p>API: <a href="/api/health">/api/health</a> · <a href="/api/overview">/api/overview</a></p>
</body>
</html>"""


def _frontend_dist() -> Path | None:
    return default_frontend_dist_dir()


static_dir = _frontend_dist()
if static_dir is not None:
    assets_dir = static_dir / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


@app.get("/", include_in_schema=False, response_model=None)
def spa_index() -> Response:
    dist = _frontend_dist()
    if dist is not None:
        return FileResponse(dist / "index.html")
    return HTMLResponse(_FALLBACK_INDEX)


if static_dir is not None:

    @app.get("/{full_path:path}", include_in_schema=False, response_model=None)
    def spa_fallback(full_path: str) -> Response:
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404)
        dist = _frontend_dist()
        if dist is None:
            return HTMLResponse(_FALLBACK_INDEX)
        candidate = dist / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(dist / "index.html")
