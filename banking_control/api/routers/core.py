from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from banking_control.api.deps import get_db_connection
from banking_control.db import get_overview, refresh_overview_cache
from banking_control.paths import default_db_path

router = APIRouter(tags=["core"])


@router.get("/api/health")
def health() -> dict[str, str]:
    path = default_db_path()
    return {"status": "ok", "database": "ready" if path.is_file() else "missing"}


@router.get("/api/overview")
def overview(refresh: bool = False, conn: Any = Depends(get_db_connection)) -> dict[str, Any]:
    if refresh:
        return refresh_overview_cache(conn)
    return get_overview(conn)
