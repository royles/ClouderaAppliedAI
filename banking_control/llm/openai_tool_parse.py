"""Parse tool calls embedded in local-model chat content (non-native OpenAI tool_calls)."""

from __future__ import annotations

import json
import re
import uuid
from typing import Any

_OPEN_THINK = "<" + "think>"
_CLOSE_THINK = "</" + "think>"

# Reasoning / chain-of-thought blocks local models often emit in the user-visible channel.
_THINKING_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        re.escape(_OPEN_THINK) + r"[\s\S]*?" + re.escape(_CLOSE_THINK),
        re.IGNORECASE,
    ),
    re.compile(r"<thinking>[\s\S]*?</thinking>", re.IGNORECASE),
    re.compile(r"<think>[\s\S]*?</think>", re.IGNORECASE),
    re.compile(r"<reasoning>[\s\S]*?</reasoning>", re.IGNORECASE),
)

_TOOL_CALL_BLOCK = re.compile(r"<tool_call>([\s\S]*?)</tool_call>", re.IGNORECASE)
_FUNCTION_XML = re.compile(
    r"<function=([a-zA-Z0-9_]+)>([\s\S]*?)</function>",
    re.IGNORECASE,
)
_PARAMETER_XML = re.compile(
    r"<parameter=([a-zA-Z0-9_]+)>\s*([\s\S]*?)\s*</parameter>",
    re.IGNORECASE,
)
_JSON_TOOL = re.compile(
    r'\{\s*"name"\s*:\s*"([a-zA-Z0-9_]+)"\s*,\s*"arguments"\s*:\s*(\{[\s\S]*?\})\s*\}',
    re.IGNORECASE,
)
_MARKDOWN_TOOL = re.compile(
    r"```(?:json|tool)?\s*(\{[\s\S]*?\})\s*```",
    re.IGNORECASE,
)


def strip_model_artifacts(text: str) -> str:
    """Remove reasoning and tool-call markup from text shown to the user."""
    from banking_control.assistant.thinking_suppress import suppress_thinking_markup

    out = suppress_thinking_markup(text)
    for pat in _THINKING_PATTERNS:
        out = pat.sub("", out)
    out = _TOOL_CALL_BLOCK.sub("", out)
    out = re.sub(r"<function=[^>]+>[\s\S]*?</function>", "", out, flags=re.IGNORECASE)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()


def _parse_xml_function_block(inner: str) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    for fn_match in _FUNCTION_XML.finditer(inner):
        name = fn_match.group(1)
        body = fn_match.group(2)
        args: dict[str, Any] = {}
        for pm in _PARAMETER_XML.finditer(body):
            key = pm.group(1)
            raw = pm.group(2).strip()
            if raw.isdigit():
                args[key] = int(raw)
            else:
                try:
                    args[key] = json.loads(raw)
                except json.JSONDecodeError:
                    args[key] = raw
        calls.append({"name": name, "arguments": args})
    return calls


def _parse_json_tool_objects(text: str) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    for m in _JSON_TOOL.finditer(text):
        name = m.group(1)
        try:
            args = json.loads(m.group(2))
        except json.JSONDecodeError:
            args = {}
        if not isinstance(args, dict):
            args = {}
        calls.append({"name": name, "arguments": args})
    for m in _MARKDOWN_TOOL.finditer(text):
        try:
            obj = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and obj.get("name"):
            args = obj.get("arguments") or obj.get("parameters") or {}
            if not isinstance(args, dict):
                args = {}
            calls.append({"name": str(obj["name"]), "arguments": args})
    return calls


def parse_tool_calls_from_content(content: str | None) -> list[dict[str, Any]]:
    """
    Return OpenAI-shaped tool_calls parsed from assistant content.
    Each item: {id, type, function: {name, arguments}}.
    """
    if not content or not content.strip():
        return []

    found: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    def add(name: str, args: dict[str, Any]) -> None:
        key = (name, json.dumps(args, sort_keys=True))
        if key in seen:
            return
        seen.add(key)
        found.append(
            {
                "id": f"call_{uuid.uuid4().hex[:12]}",
                "type": "function",
                "function": {
                    "name": name,
                    "arguments": json.dumps(args),
                },
            }
        )

    for block in _TOOL_CALL_BLOCK.findall(content):
        for item in _parse_xml_function_block(block):
            add(item["name"], item["arguments"])
        for item in _parse_json_tool_objects(block):
            add(item["name"], item["arguments"])

    for item in _parse_json_tool_objects(content):
        add(item["name"], item["arguments"])

    for fn_match in _FUNCTION_XML.finditer(content):
        if _TOOL_CALL_BLOCK.search(content):
            continue
        name = fn_match.group(1)
        body = fn_match.group(2)
        args: dict[str, Any] = {}
        for pm in _PARAMETER_XML.finditer(body):
            key = pm.group(1)
            raw = pm.group(2).strip()
            if raw.isdigit():
                args[key] = int(raw)
            else:
                try:
                    args[key] = json.loads(raw)
                except json.JSONDecodeError:
                    args[key] = raw
        add(name, args)

    return found


def content_looks_like_tool_attempt(content: str | None) -> bool:
    if not content:
        return False
    lower = content.lower()
    return (
        "<tool_call" in lower
        or "<function=" in lower
        or _OPEN_THINK.lower() in lower
        or "<redacted_thinking" in lower
    )
