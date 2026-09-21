"""FastAPI application — serves REST API and built React static assets."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from customer360.api.routes import router
from customer360.paths import project_root

logger = logging.getLogger(__name__)

app = FastAPI(title="Insurance Customer 360", version="0.1.0")
app.include_router(router)


@app.exception_handler(FileNotFoundError)
async def database_missing_handler(_request: Request, exc: FileNotFoundError) -> JSONResponse:
    logger.exception("Database not available")
    return JSONResponse(
        status_code=503,
        content={"detail": str(exc)},
    )


@app.exception_handler(sqlite3.OperationalError)
async def sqlite_operational_handler(
    _request: Request, exc: sqlite3.OperationalError
) -> JSONResponse:
    message = str(exc).lower()
    if "locked" in message or "busy" in message:
        logger.warning("SQLite busy: %s", exc)
        return JSONResponse(
            status_code=503,
            content={"detail": "Database is busy; retry shortly."},
        )
    logger.exception("SQLite error")
    return JSONResponse(status_code=500, content={"detail": "Database error."})


def _frontend_dist() -> Path:
    return (project_root() / "frontend" / "dist").resolve()


def _is_api_or_docs_path(path: str) -> bool:
    normalized = path.lstrip("/")
    if normalized.startswith("api/") or normalized == "api":
        return True
    if normalized in ("docs", "redoc", "openapi.json"):
        return True
    return normalized.startswith("docs/") or normalized.startswith("redoc/")


def _spa_index_response(dist_dir: Path) -> FileResponse:
    index = dist_dir / "index.html"
    if not index.is_file():
        raise HTTPException(status_code=404, detail="UI not built")
    return FileResponse(index, media_type="text/html")


def _mount_frontend() -> None:
    dist_dir = _frontend_dist()
    if not (dist_dir / "index.html").is_file():
        @app.get("/", response_class=HTMLResponse, include_in_schema=False)
        def ui_not_built() -> str:
            return f"""<!DOCTYPE html>
<html><head><title>Customer 360 — build required</title></head>
<body style="font-family: system-ui; width: 100%; margin: 0; padding: 2rem clamp(1rem, 3vw, 3rem); line-height: 1.5; box-sizing: border-box;">
  <h1>React UI not built yet</h1>
  <p>The API is running. Build the frontend into <code>frontend/dist</code>:</p>
  <pre>%run scripts/build_frontend.py</pre>
  <p>Or from a terminal in the project root:</p>
  <pre>cd frontend && npm install && npm run build</pre>
  <p>Then restart this application.</p>
  <p>API docs: <a href="/docs">/docs</a> · Health: <a href="/api/health">/api/health</a></p>
  <p><small>Expected path: {dist_dir / "index.html"}</small></p>
</body></html>"""

        return

    assets_dir = dist_dir / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

    @app.get("/", include_in_schema=False)
    async def spa_root() -> FileResponse:
        return _spa_index_response(dist_dir)

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_client_routes(full_path: str) -> FileResponse:
        if _is_api_or_docs_path(full_path):
            raise HTTPException(status_code=404, detail="Not Found")
        candidate = dist_dir / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return _spa_index_response(dist_dir)


_mount_frontend()
