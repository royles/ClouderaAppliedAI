from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request

from banking_control.db import connect, prepare_connection
from banking_control.paths import default_db_path
from banking_control.plugins.manager import PluginManager
from banking_control.tools.engine import ControlToolEngine


def get_plugin_manager(request: Request) -> PluginManager:
    manager = getattr(request.app.state, "plugin_manager", None)
    if manager is None:
        raise HTTPException(status_code=503, detail="Plugin manager not initialized")
    return manager


def get_tool_engine(request: Request) -> ControlToolEngine:
    engine = getattr(request.app.state, "tool_engine", None)
    if engine is None:
        raise HTTPException(status_code=503, detail="Tool engine not initialized")
    return engine


def get_db_connection() -> Any:
    path = default_db_path()
    if not path.is_file():
        raise HTTPException(
            status_code=503,
            detail="Database not initialized. Run scripts/init_db.py or the init-database job.",
        )
    conn = connect(path)
    prepare_connection(conn)
    return conn
