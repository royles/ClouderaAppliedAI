from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

import banking_control
from banking_control.api.deps import get_db_connection
from banking_control.db import connect, get_overview, refresh_overview_cache
from banking_control.llm.admin_store import load_llm_config
from banking_control.llm.bedrock_client import is_bedrock_configured
from banking_control.llm.openai_compat import is_openai_configured
from banking_control.paths import default_db_path

router = APIRouter(tags=["core"])


@router.get("/api/health")
def health() -> dict[str, Any]:
    path = default_db_path()
    payload: dict[str, Any] = {
        "status": "ok",
        "api": "ok",
        "version": banking_control.__version__,
        "database": "missing",
        "llm_link": "unknown",
        "llm_provider": None,
    }
    if not path.is_file():
        payload["llm_link"] = "offline"
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
            cfg = load_llm_config(conn)
            payload["llm_provider"] = cfg.provider_type
            llm_ready = (
                cfg.provider_type == "openai_compatible"
                and is_openai_configured(cfg)
            ) or (cfg.provider_type == "bedrock" and is_bedrock_configured(cfg))
            payload["llm_link"] = "online" if llm_ready else "offline"
        finally:
            conn.close()
    except Exception:
        payload["database"] = "error"
        payload["llm_link"] = "unknown"
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
