"""Streaming executive assistant (single-shot LLM path with live token deltas)."""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Iterator

from customer360.agent.bedrock_agent import _build_payload
from customer360.agent.context import gather_context
from customer360.agent.customer_snippet import top_customers_snippet
from customer360.agent.list_filters import (
    filters_from_list_context,
    merge_filters,
    parse_customer_list_intent,
    parse_refinement_intent,
)
from customer360.agent.llm_resilience import stream_agent_deltas_then_parse
from customer360.agent.prompt import build_system_prompt, build_user_prompt
from customer360.agent.query_builder import count_matching_customers
from customer360.agent.router import answer_question_rules
from customer360.llm.errors import LLMError
from customer360.llm.router import is_llm_configured
from customer360.llm_provider import get_active_provider
from customer360.agent.payload_meta import attach_agent_llm_meta
from customer360.bedrock.config import effective_bedrock_settings

logger = logging.getLogger(__name__)


def _prepare_agent_context(
    conn: sqlite3.Connection,
    *,
    message: str,
    segment: str | None,
    list_context: dict | None,
) -> tuple[dict, str, object | None]:
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

    return ctx, seg, merged


def _model_id_for_provider() -> str:
    provider = get_active_provider()
    if provider == "openai_compatible":
        from customer360.llm_provider import load_llm_config

        return (load_llm_config().openai_model_id or "").strip() or "privateai"
    return effective_bedrock_settings().model_id


def stream_agent_answer(
    conn: sqlite3.Connection,
    *,
    message: str,
    segment: str | None = None,
    list_context: dict | None = None,
    locale: str | None = None,
) -> Iterator[tuple[str, dict | None]]:
    """
    Yields ("delta", {"text": "..."}) then ("done", agent_payload_dict).
    On rules-only path, yields a single ("done", ...) without deltas.
    """
    ctx, seg, merged = _prepare_agent_context(
        conn,
        message=message,
        segment=segment,
        list_context=list_context,
    )

    if not is_llm_configured() or not (message or "").strip():
        payload = answer_question_rules(
            conn,
            message=message,
            segment=seg,
            merged_list=merged,
            extra_snippets=ctx["snippets"],
        )
        yield ("done", attach_agent_llm_meta(payload, llm_attempted=False))
        return

    user_prompt = build_user_prompt(
        message=message.strip(),
        segment=seg,
        snippets=ctx["snippets"],
        list_context=list_context,
        locale=locale,
    )
    system_prompt = build_system_prompt(locale)

    fallback_reason: str | None = None
    try:
        parsed = None
        for event, data in stream_agent_deltas_then_parse(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        ):
            if event == "delta":
                yield ("delta", {"text": data})
            elif event == "parsed":
                parsed = data

        if parsed is None:
            raise ValueError("No parsed assistant response")

        provider = get_active_provider()
        source = "openai_compatible" if provider == "openai_compatible" else "bedrock"
        payload = _build_payload(
            parsed,
            segment=seg,
            list_intent=merged,
            model_id=str(_model_id_for_provider()),
            source=source,
        )
        payload.pop("_merged_list", None)
        yield ("done", attach_agent_llm_meta(payload, llm_attempted=True))
    except (LLMError, ValueError) as exc:
        fallback_reason = str(exc)[:300]
        logger.warning("Streaming agent LLM failed, using rules: %s", exc, exc_info=True)
        payload = answer_question_rules(
            conn,
            message=message,
            segment=seg,
            merged_list=merged,
            extra_snippets=ctx["snippets"],
        )
        payload["model_id"] = None
        yield (
            "done",
            attach_agent_llm_meta(
                payload,
                llm_attempted=True,
                fallback_reason=fallback_reason,
            ),
        )
