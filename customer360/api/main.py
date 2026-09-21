"""FastAPI application — serves REST API and built React static assets."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from customer360.api.routes import router
from customer360.paths import project_root

app = FastAPI(title="Insurance Customer 360", version="0.1.0")
app.include_router(router)


def _frontend_dist() -> Path:
    return (project_root() / "frontend" / "dist").resolve()


def _mount_frontend() -> None:
    dist_dir = _frontend_dist()
    if not (dist_dir / "index.html").is_file():
        @app.get("/", response_class=HTMLResponse, include_in_schema=False)
        def ui_not_built() -> str:
            return f"""<!DOCTYPE html>
<html><head><title>Customer 360 — build required</title></head>
<body style="font-family: system-ui; max-width: 40rem; margin: 2rem auto; line-height: 1.5;">
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

    # Register after /api routes so API paths are not shadowed by static files.
    app.mount("/", StaticFiles(directory=dist_dir, html=True), name="frontend")


_mount_frontend()
