"""FastAPI application — serves REST API and built React static assets."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from customer360.api.routes import router
from customer360.paths import project_root

app = FastAPI(title="Insurance Customer 360", version="0.1.0")
app.include_router(router)


def _frontend_dist() -> Path:
    return project_root() / "frontend" / "dist"


@app.on_event("startup")
def validate_frontend() -> None:
    dist = _frontend_dist()
    if not dist.is_dir():
        # API still works; UI appears after `npm run build` in frontend/
        import logging

        logging.getLogger("customer360").warning(
            "Frontend build not found at %s — run npm run build in frontend/", dist
        )


dist_dir = _frontend_dist()
if dist_dir.is_dir():
    app.mount("/", StaticFiles(directory=dist_dir, html=True), name="frontend")
