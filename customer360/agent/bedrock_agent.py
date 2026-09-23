"""Bedrock-backed executive copilot with tool use + JSON validation."""

from __future__ import annotations

import logging

from customer360.agent.actions import actions_from_model_ids
from customer360.agent.bedrock_tool_loop import invoke_copilot_with_tools, parse_final_json
from customer360.agent.list_filters import (
    CustomerListFilters,
    filters_from_model_payload,
    merge_filters,
)
from customer360.agent.prompt import build_system_prompt, build_user_prompt
from customer360.agent.tools import ToolContext
from customer360.bedrock.client import BedrockError
from customer360.llm.router import invoke_text
from customer360.llm_provider import get_active_provider, is_llm_configured

logger = logging.getLogger(__name__)


def _parse_agent_json(text: str) -> dict:
    data = parse_final_json(text)
    answer = str(data.get("answer", "")).strip()
    if not answer:
        raise ValueError("Missing answer in copilot JSON")

    raw_ids = data.get("action_ids") or []
    action_ids = [str(x).strip() for x in raw_ids if str(x).strip()]
    open_playbook = bool(data.get("open_retention_playbook", False))
    customer_list = filters_from_model_payload(data.get("customer_list"))

    return {
        "answer": answer,
        "action_ids": action_ids[:4],
        "open_retention_playbook": open_playbook,
        "customer_list": customer_list,
    }


def _build_payload(
    parsed: dict,
    *,
    segment: str,
    list_intent: CustomerListFilters | None,
    model_id: str,
    source: str,
    tools_used: list[str] | None = None,
) -> dict:
    merged_list = merge_filters(
        list_intent,
        parsed.get("customer_list"),
        default_segment=segment,
    )
    action_ids = parsed["action_ids"]
    if merged_list and not any(
        i in action_ids for i in ("customer", "customer_top_value", "customer_churn")
    ):
        action_ids = ["customer_top_value", *action_ids]

    actions = actions_from_model_ids(
        action_ids,
        segment=segment,
        open_retention_playbook=parsed["open_retention_playbook"],
        list_filters=merged_list,
    )
    if not actions and parsed["action_ids"]:
        actions = actions_from_model_ids(
            ["business"],
            segment=segment,
            open_retention_playbook=False,
        )

    citations = [source, *parsed["action_ids"][:4]]
    if tools_used:
        citations = ["tools", *tools_used[:8], *citations]

    return {
        "answer": parsed["answer"],
        "actions": actions,
        "citations": citations,
        "source": source,
        "model_id": model_id,
        "_merged_list": merged_list,
        "tools_used": tools_used or [],
    }


def answer_with_bedrock(
    *,
    conn,
    message: str,
    segment: str,
    snippets: list[str],
    list_intent: CustomerListFilters | None = None,
    list_context: dict | None = None,
    locale: str | None = None,
) -> dict:
    """
    Returns payload with answer, actions, citations, source, model_id.
    Raises BedrockError or ValueError on failure.
    """
    if not is_llm_configured():
        raise BedrockError("LLM backend is not configured", status_code=503)

    user_prompt = build_user_prompt(
        message=message,
        segment=segment,
        snippets=snippets,
        list_context=list_context,
        locale=locale,
    )
    tool_ctx = ToolContext(
        conn=conn,
        default_segment=segment,
        list_context=list_context,
    )

    provider = get_active_provider()
    if provider == "bedrock":
        try:
            raw, model_id, tools_used = invoke_copilot_with_tools(
                user_prompt=user_prompt,
                ctx=tool_ctx,
                locale=locale,
            )
            parsed = _parse_agent_json(raw)
            parsed["customer_list"] = parsed.get("customer_list") or None
            return _build_payload(
                parsed,
                segment=segment,
                list_intent=list_intent,
                model_id=model_id,
                source="bedrock_tools" if tools_used else "bedrock",
                tools_used=tools_used,
            )
        except (BedrockError, ValueError) as tool_exc:
            logger.info("Bedrock tool path unavailable, using single-shot JSON: %s", tool_exc)

    raw, model_id = invoke_text(
        system_prompt=build_system_prompt(locale),
        user_prompt=user_prompt,
        json_mode=True,
    )
    parsed = _parse_agent_json(raw)
    source = "openai_compatible" if provider == "openai_compatible" else "bedrock"
    return _build_payload(
        parsed,
        segment=segment,
        list_intent=list_intent,
        model_id=model_id,
        source=source,
    )
