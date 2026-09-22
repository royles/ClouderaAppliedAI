"""Orchestrate Bedrock copilot with rule-based fallback."""

from __future__ import annotations

import logging
import sqlite3

from customer360.agent.bedrock_agent import _build_payload, answer_with_bedrock
from customer360.agent.llm_resilience import complete_agent_model_json
from customer360.agent.prompt import build_system_prompt, build_user_prompt
from customer360.llm.errors import LLMError
from customer360.llm_provider import get_active_provider
from customer360.agent.context import gather_context
from customer360.agent.customer_snippet import top_customers_snippet
from customer360.agent.list_filters import (
    CustomerListFilters,
    filters_from_list_context,
    merge_filters,
    parse_customer_list_intent,
    parse_refinement_intent,
)
from customer360.agent.query_builder import count_matching_customers
from customer360.agent.router import answer_question_rules
from customer360.agent.payload_meta import attach_agent_llm_meta
from customer360.llm.router import is_llm_configured

logger = logging.getLogger(__name__)


def answer_question(
    conn: sqlite3.Connection,
    *,
    message: str,
    segment: str | None = None,
    list_context: dict | None = None,
    locale: str | None = None,
) -> dict:
    ctx = gather_context(conn, message=message, segment=segment)
    seg = ctx["segment"]

    list_intent = parse_customer_list_intent(message)
    refinement = parse_refinement_intent(message)
    prior = filters_from_list_context(list_context)
    merged = merge_filters(prior, list_intent, refinement, default_segment=seg)

    if merged:
        count = count_matching_customers(conn, merged, default_segment=seg)
        ctx["snippets"].append(f"{count:,} customers match the requested list filters.")
        rank_snippet = top_customers_snippet(
            conn,
            filters=merged,
            default_segment=seg,
            limit=min(merged.page_size, 10),
        )
        if rank_snippet and rank_snippet not in ctx["snippets"]:
            ctx["snippets"].append(rank_snippet)

    if is_llm_configured() and (message or "").strip():
        fallback_reason: str | None = None
        try:
            provider = get_active_provider()
            if provider == "bedrock":
                payload = answer_with_bedrock(
                    conn=conn,
                    message=message.strip(),
                    segment=seg,
                    snippets=ctx["snippets"],
                    list_intent=merged,
                    list_context=list_context,
                    locale=locale,
                )
                payload.pop("_merged_list", None)
                return attach_agent_llm_meta(payload, llm_attempted=True)
            system_prompt = build_system_prompt(locale)
            user_prompt = build_user_prompt(
                message=message.strip(),
                segment=seg,
                snippets=ctx["snippets"],
                list_context=list_context,
                locale=locale,
            )
            parsed, _raw, model_id = complete_agent_model_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                prefer_stream=False,
            )
            source = "openai_compatible"
            payload = _build_payload(
                parsed,
                segment=seg,
                list_intent=merged,
                model_id=model_id,
                source=source,
            )
            payload.pop("_merged_list", None)
            return attach_agent_llm_meta(payload, llm_attempted=True)
        except (LLMError, ValueError, Exception) as exc:
            fallback_reason = str(exc)[:300]
            logger.warning("Executive assistant LLM failed, using rules: %s", exc, exc_info=True)

        payload = answer_question_rules(
            conn,
            message=message,
            segment=seg,
            merged_list=merged,
            extra_snippets=ctx["snippets"],
        )
        payload["model_id"] = None
        return attach_agent_llm_meta(
            payload,
            llm_attempted=True,
            fallback_reason=fallback_reason,
        )

    payload = answer_question_rules(
        conn,
        message=message,
        segment=seg,
        merged_list=merged,
        extra_snippets=ctx["snippets"],
    )
    payload["model_id"] = None
    return attach_agent_llm_meta(payload, llm_attempted=False)
