from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

import banking_control
from banking_control.api.deps import get_db_connection
from banking_control.db import connect, get_overview, refresh_overview_cache
from banking_control.paths import default_db_path

router = APIRouter(tags=["core"])


@router.get("/api/health")
def health() -> dict[str, Any]:
    path = default_db_path()
    payload: dict[str, Any] = {
        "status": "ok",
        "version": banking_control.__version__,
        "database": "missing",
    }
    if not path.is_file():
        return payload

    payload["database"] = "ready"
    try:
        conn = connect(path)
        try:
            row = conn.execute("SELECT COUNT(*) AS n FROM DIM_CONTROL").fetchone()
            payload["control_count"] = int(row["n"])
            golden = conn.execute(
                "SELECT COUNT(*) AS n FROM DIM_CONTROL WHERE is_golden = 1"
            ).fetchone()
            payload["golden_count"] = int(golden["n"])
        finally:
            conn.close()
    except Exception:
        payload["database"] = "error"
    return payload


@router.get("/api/domains")
def list_domains(conn: Any = Depends(get_db_connection)) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT domain, COUNT(*) AS controls,
               SUM(CASE WHEN is_golden = 1 THEN 1 ELSE 0 END) AS golden_controls
        FROM DIM_CONTROL
        GROUP BY domain
        ORDER BY domain
        """
    ).fetchall()
    return [dict(r) for r in rows]


@router.get("/api/overview")
def overview(refresh: bool = False, conn: Any = Depends(get_db_connection)) -> dict[str, Any]:
    if refresh:
        return refresh_overview_cache(conn)
    return get_overview(conn)
