from __future__ import annotations

from pathlib import Path
from typing import Sequence

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from banking_control.api.routers import (
    admin_llm,
    alerts,
    assistant,
    audit,
    controls,
    core,
    exceptions,
    timeline,
    tools,
)
from banking_control.db import connect, prepare_connection
from banking_control.paths import default_db_path, default_frontend_dist_dir
from banking_control.plugins.manager import PluginManager
from banking_control.plugins.protocols import BankingControlPlugin
from banking_control.tools.engine import ControlToolEngine
from banking_control.tools.registry import ToolRegistry
from banking_control.alert_worker import TransactionAlertWorker

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
  <p>API: <a href="/api/health">/api/health</a> · <a href="/api/tools">/api/tools</a></p>
</body>
</html>"""


def create_app(
    *,
    plugin_manager: PluginManager | None = None,
    extra_plugins: Sequence[BankingControlPlugin] | None = None,
    tool_registry: ToolRegistry | None = None,
) -> FastAPI:
    """
    Application factory.

    Pass ``extra_plugins`` to register custom simulators/schema providers, or supply
    a pre-configured ``plugin_manager`` for full control.
    """
    manager = plugin_manager or PluginManager.with_builtins()
    if extra_plugins:
        for plugin in extra_plugins:
            manager.register_plugin(plugin)

    registry = tool_registry or ToolRegistry.default()
    engine = ControlToolEngine(manager, registry)

    app = FastAPI(title="Banking Control Solution", version="0.2.0")
    app.state.plugin_manager = manager
    app.state.tool_registry = registry
    app.state.tool_engine = engine

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    for module in (core, controls, exceptions, alerts, audit, timeline, tools, assistant, admin_llm):
        app.include_router(module.router)

    @app.on_event("startup")
    def _prepare_database_on_startup() -> None:
        path = default_db_path()
        if not path.is_file():
            return
        conn = connect(path)
        try:
            prepare_connection(conn)
        finally:
            conn.close()
        worker = TransactionAlertWorker(path)
        worker.start()
        app.state.alert_worker = worker

    @app.on_event("shutdown")
    def _stop_alert_worker() -> None:
        worker = getattr(app.state, "alert_worker", None)
        if worker is not None:
            worker.stop()

    _mount_frontend(app)
    return app


def _mount_frontend(app: FastAPI) -> None:
    static_dir = default_frontend_dist_dir()
    if static_dir is not None:
        assets_dir = static_dir / "assets"
        if assets_dir.is_dir():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/", include_in_schema=False, response_model=None)
    def spa_index() -> Response:
        dist = default_frontend_dist_dir()
        if dist is not None:
            return FileResponse(dist / "index.html")
        return HTMLResponse(_FALLBACK_INDEX)

    if static_dir is not None:

        @app.get("/{full_path:path}", include_in_schema=False, response_model=None)
        def spa_fallback(full_path: str) -> Response:
            if full_path.startswith("api/"):
                raise HTTPException(status_code=404)
            dist = default_frontend_dist_dir()
            if dist is None:
                return HTMLResponse(_FALLBACK_INDEX)
            candidate = dist / full_path
            if candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(static_dir / "index.html")
