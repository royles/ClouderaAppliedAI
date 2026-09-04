"""Serve the built React app from FastAPI (used on Cloudera AI without npm)."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


def mount_frontend(app: FastAPI) -> bool:
    """Mount frontend/dist if present. Returns True when mounted."""
    index = FRONTEND_DIST / "index.html"
    if not index.exists():
        return False

    app.mount(
        "/",
        StaticFiles(directory=str(FRONTEND_DIST), html=True),
        name="frontend",
    )
    return True
