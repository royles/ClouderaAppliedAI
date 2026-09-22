"""Bedrock Messages API with Anthropic tool use for the executive copilot."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from customer360.agent.tools import ToolContext, bedrock_tool_definitions, execute_tool
from customer360.bedrock.client import (
    BedrockError,
    _anthropic_disallows_sampling,
    _build_session,
    _invoke_model,
    _normalize_model_id,
    resolve_inference_model_id,
)
from customer360.bedrock.config import get_bedrock_settings

logger = logging.getLogger(__name__)

MAX_TOOL_TURNS = 6

COPILOT_SYSTEM = """You are the executive assistant for Insurance Customer 360.
Use tools to fetch live book data before answering when the question involves counts, KPIs, rankings, filters,
freshness, retention playbook, engagement, cohort comparison, benchmarks, or navigation.
Do not invent numbers.

When you have enough information, respond with a single JSON object only (no markdown fences):
{
  "answer": "2-4 sentences for an executive",
  "action_ids": ["..."],
  "open_retention_playbook": false,
  "customer_list": { ... optional ... }
}

Use action_ids from the app catalog. Prefer prepare_customer_list_link tool output for customer_list and actions.
For retention playbook requests set open_retention_playbook true.

For portfolio or KPI questions, call get_portfolio_kpis (includes benchmark_assessments with green/amber/red).
When status is amber or red, explain using actual vs target and vs_target_summary — do not invent thresholds.
"""


def _format_body(
    *,
    messages: list[dict[str, Any]],
    system: str,
    tools: list[dict[str, Any]],
    max_tokens: int,
    temperature: float,
    model_id: str,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "system": [{"type": "text", "text": system}],
        "messages": messages,
        "tools": tools,
    }
    if not _anthropic_disallows_sampling(model_id):
        body["temperature"] = temperature
    return body


def _extract_text(content: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for block in content:
        if block.get("type") == "text":
            parts.append(str(block.get("text", "")))
    return "\n".join(parts).strip()


def _extract_tool_uses(content: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [b for b in content if b.get("type") == "tool_use"]


def invoke_copilot_with_tools(
    *,
    user_prompt: str,
    ctx: ToolContext,
) -> tuple[str, str, list[str]]:
    """
    Run tool loop; returns (final_text, model_id, tools_called_names).
    """
    try:
        from botocore.exceptions import BotoCoreError, ClientError
    except ImportError as exc:
        raise BedrockError("boto3 is not installed", status_code=503) from exc

    settings = get_bedrock_settings()
    catalog_model = settings.model_id
    ui_region = settings.bedrock_region
    inference_model = resolve_inference_model_id(catalog_model, ui_region)
    tools = bedrock_tool_definitions()
    messages: list[dict[str, Any]] = [
        {"role": "user", "content": [{"type": "text", "text": user_prompt}]},
    ]
    tools_called: list[str] = []

    session, client_region = _build_session()
    client = session.client("bedrock-runtime", region_name=client_region)

    for turn in range(MAX_TOOL_TURNS):
        body = _format_body(
            messages=messages,
            system=COPILOT_SYSTEM,
            tools=tools,
            max_tokens=settings.max_tokens,
            temperature=settings.temperature,
            model_id=catalog_model,
        )
        try:
            response_body = _invoke_model(client, inference_model, body)
        except ClientError as first_exc:
            error_code = first_exc.response.get("Error", {}).get("Code", "Unknown")
            if (
                error_code == "ValidationException"
                and inference_model != catalog_model
                and "tool" in str(first_exc).lower()
            ):
                raise BedrockError(
                    f"Model may not support tools: {first_exc}",
                    status_code=502,
                ) from first_exc
            if (
                error_code == "ValidationException"
                and inference_model != catalog_model
            ):
                inference_model = catalog_model
                response_body = _invoke_model(client, inference_model, body)
            else:
                raise

        content = response_body.get("content") or []
        stop = response_body.get("stop_reason")
        assistant_msg = {"role": "assistant", "content": content}
        messages.append(assistant_msg)

        tool_uses = _extract_tool_uses(content)
        if tool_uses and stop == "tool_use":
            tool_results: list[dict[str, Any]] = []
            for tu in tool_uses:
                name = str(tu.get("name", ""))
                tool_id = str(tu.get("id", ""))
                tool_input = tu.get("input") if isinstance(tu.get("input"), dict) else {}
                tools_called.append(name)
                result_text = execute_tool(ctx, name, tool_input)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": result_text,
                    }
                )
            messages.append({"role": "user", "content": tool_results})
            continue

        text = _extract_text(content)
        if text:
            return text, catalog_model, tools_called

        raise BedrockError("Empty model response", status_code=502)

    raise BedrockError("Tool loop exceeded max turns", status_code=502)


def parse_final_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", stripped)
        if not match:
            raise ValueError("Model did not return JSON") from None
        return json.loads(match.group(0))
