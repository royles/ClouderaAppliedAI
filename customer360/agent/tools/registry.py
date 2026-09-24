"""Tool registry: Bedrock schemas + validated execution."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from customer360.agent.tools.context import ToolContext

logger = logging.getLogger(__name__)

ToolFn = Callable[[ToolContext, dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: ToolFn


_REGISTRY: dict[str, ToolSpec] = {}


def register_tool(
    name: str,
    *,
    description: str,
    input_schema: dict[str, Any],
) -> Callable[[ToolFn], ToolFn]:
    def decorator(fn: ToolFn) -> ToolFn:
        _REGISTRY[name] = ToolSpec(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=fn,
        )
        return fn

    return decorator


def bedrock_tool_definitions() -> list[dict[str, Any]]:
    return [
        {
            "name": spec.name,
            "description": spec.description,
            "input_schema": spec.input_schema,
        }
        for spec in _REGISTRY.values()
    ]


def execute_tool(ctx: ToolContext, name: str, tool_input: dict[str, Any]) -> str:
    spec = _REGISTRY.get(name)
    if spec is None:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        result = spec.handler(ctx, tool_input or {})
        return json.dumps(result, default=str)
    except Exception as exc:
        logger.warning("Tool %s failed: %s", name, exc, exc_info=True)
        return json.dumps({"error": str(exc)})


def registered_tool_names() -> list[str]:
    return list(_REGISTRY.keys())
