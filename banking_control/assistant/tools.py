from __future__ import annotations

import json
import sqlite3
from typing import Any

from banking_control.db import get_overview
from banking_control.tools.engine import ControlToolEngine, ToolValidationError

COPILOT_TOOL_SPECS: list[dict[str, Any]] = [
    {
        "name": "get_overview",
        "description": "Fetch control tower KPIs: health %, open exceptions, alert counts.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "list_controls",
        "description": "List catalog controls with optional filters.",
        "input_schema": {
            "type": "object",
            "properties": {
                "domain": {"type": "string"},
                "golden_only": {"type": "boolean"},
                "similarity_key": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "describe_control_tool",
        "description": "Get JSON input/output schemas for an LLM-callable control tool.",
        "input_schema": {
            "type": "object",
            "properties": {"control_code": {"type": "string"}},
            "required": ["control_code"],
            "additionalProperties": False,
        },
    },
    {
        "name": "invoke_control_tool",
        "description": "Simulate a control test (maps inputs to outputs deterministically).",
        "input_schema": {
            "type": "object",
            "properties": {
                "control_code": {"type": "string"},
                "inputs": {"type": "object"},
            },
            "required": ["control_code", "inputs"],
            "additionalProperties": False,
        },
    },
    {
        "name": "list_audit_events",
        "description": "Recent audit trail events for control and compliance activity.",
        "input_schema": {
            "type": "object",
            "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 50}},
            "additionalProperties": False,
        },
    },
]


def bedrock_tool_definitions() -> list[dict[str, Any]]:
    return [
        {
            "name": spec["name"],
            "description": spec["description"],
            "input_schema": spec["input_schema"],
        }
        for spec in COPILOT_TOOL_SPECS
    ]


def openai_tool_definitions() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": spec["name"],
                "description": spec["description"],
                "parameters": spec["input_schema"],
            },
        }
        for spec in COPILOT_TOOL_SPECS
    ]


def execute_copilot_tool(
    conn: sqlite3.Connection,
    engine: ControlToolEngine,
    name: str,
    arguments: dict[str, Any],
) -> str:
    args = arguments or {}
    if name == "get_overview":
        return json.dumps(get_overview(conn), default=str)
    if name == "list_controls":
        clauses: list[str] = []
        params: list[Any] = []
        if args.get("domain"):
            clauses.append("domain = ?")
            params.append(args["domain"])
        if args.get("golden_only"):
            clauses.append("is_golden = 1")
        if args.get("similarity_key"):
            clauses.append("similarity_key = ?")
            params.append(args["similarity_key"])
        limit = min(int(args.get("limit") or 25), 100)
        params.append(limit)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = conn.execute(
            f"""
            SELECT control_code, control_name, domain, risk_tier, is_golden, similarity_key
            FROM DIM_CONTROL {where}
            ORDER BY is_golden DESC, control_code LIMIT ?
            """,
            params,
        ).fetchall()
        return json.dumps([dict(r) for r in rows], default=str)
    if name == "describe_control_tool":
        code = str(args.get("control_code", ""))
        try:
            return json.dumps(engine.describe_tool(code), default=str)
        except ToolValidationError as exc:
            return json.dumps(
                {
                    "error": "unknown_control_code",
                    "control_code": code,
                    "message": str(exc),
                    "hint": "Tell the user you cannot run that control unless they use a valid code such as AML-001.",
                },
                default=str,
            )
    if name == "invoke_control_tool":
        code = str(args.get("control_code", ""))
        inputs = args.get("inputs") or {}
        try:
            return json.dumps(engine.invoke(code, inputs), default=str)
        except ToolValidationError as exc:
            return json.dumps(
                {
                    "error": "unknown_control_code",
                    "control_code": code,
                    "message": str(exc),
                    "hint": "Tell the user you cannot simulate that control; suggest the correct code format (e.g. AML-001).",
                },
                default=str,
            )
    if name == "list_audit_events":
        limit = min(int(args.get("limit") or 20), 50)
        rows = conn.execute(
            """
            SELECT event_at, actor, action, entity_type, entity_id, detail
            FROM FCT_AUDIT_EVENT ORDER BY event_at DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return json.dumps([dict(r) for r in rows], default=str)
    return json.dumps({"error": f"Unknown tool {name}"})
