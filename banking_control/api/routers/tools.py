from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from banking_control.api.deps import get_plugin_manager, get_tool_engine
from banking_control.plugins.manager import PluginManager
from banking_control.tools.engine import ControlToolEngine, ToolValidationError

router = APIRouter(prefix="/api/tools", tags=["tools"])


class InvokeToolRequest(BaseModel):
    inputs: dict[str, Any] = Field(default_factory=dict)


@router.get("")
def list_control_tools(
    golden: bool = Query(False),
    engine: ControlToolEngine = Depends(get_tool_engine),
) -> dict[str, Any]:
    tools = engine.list_tools(golden_only=golden)
    return {
        "count": len(tools),
        "tools": [
            engine.describe_tool(t.control_code)
            for t in tools[:500]
        ],
    }


@router.get("/openai")
def list_openai_tools(
    golden: bool = Query(False),
    engine: ControlToolEngine = Depends(get_tool_engine),
) -> dict[str, Any]:
    tools = engine.list_tools(golden_only=golden)
    described = [engine.describe_tool(t.control_code) for t in tools[:500]]
    return {"tools": [d["openai_tool"] for d in described]}


@router.get("/meta/plugins")
def list_plugins(manager: PluginManager = Depends(get_plugin_manager)) -> dict[str, Any]:
    return {
        "schema_providers": manager.registered_schema_providers(),
        "simulators": manager.registered_simulators(),
    }


@router.get("/{control_code}")
def describe_control_tool(
    control_code: str,
    engine: ControlToolEngine = Depends(get_tool_engine),
) -> dict[str, Any]:
    try:
        return engine.describe_tool(control_code)
    except ToolValidationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{control_code}/invoke")
def invoke_control_tool(
    control_code: str,
    body: InvokeToolRequest,
    engine: ControlToolEngine = Depends(get_tool_engine),
) -> dict[str, Any]:
    try:
        return engine.invoke(control_code, body.inputs)
    except ToolValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

