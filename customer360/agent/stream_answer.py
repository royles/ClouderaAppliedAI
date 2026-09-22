"""Streaming executive assistant (single-shot LLM path with live token deltas)."""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Iterator

from customer360.agent.bedrock_agent import _build_payload, _parse_agent_json
from customer360.agent.context import gather_context
from customer360.agent.customer_snippet import top_customers_snippet
from customer360.agent.list_filters import (
    filters_from_list_context,
    merge_filters,
    parse_customer_list_intent,
    parse_refinement_intent,
)
from customer360.agent.prompt import build_system_prompt, build_user_prompt
from customer360.agent.query_builder import count_matching_customers
from customer360.agent.router import answer_question_rules
from customer360.llm.errors import LLMError
from customer360.llm.router import is_llm_configured, stream_text_chunks
from customer360.llm_provider import get_active_provider
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
        payload["source"] = "rules"
        payload["model_id"] = None
        yield ("done", payload)
        return

    user_prompt = build_user_prompt(
        message=message.strip(),
        segment=seg,
        snippets=ctx["snippets"],
        list_context=list_context,
        locale=locale,
    )
    system_prompt = build_system_prompt(locale)

    buffer: list[str] = []
    try:
        for piece in stream_text_chunks(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_mode=False,
        ):
            buffer.append(piece)
            yield ("delta", {"text": piece})
    except LLMError as exc:
        logger.warning("Streaming agent LLM failed, using rules: %s", exc)
        payload = answer_question_rules(
            conn,
            message=message,
            segment=seg,
            merged_list=merged,
            extra_snippets=ctx["snippets"],
        )
        payload["source"] = "rules"
        payload["model_id"] = None
        yield ("done", payload)
        return

    raw = "".join(buffer)
    provider = get_active_provider()
    if provider == "openai_compatible":
        from customer360.llm_provider import load_llm_config

        model_id = (load_llm_config().openai_model_id or "").strip() or "privateai"
    else:
        model_id = effective_bedrock_settings().model_id

    try:
        parsed = _parse_agent_json(raw)
        source = "openai_compatible" if provider == "openai_compatible" else "bedrock"
        payload = _build_payload(
            parsed,
            segment=seg,
            list_intent=merged,
            model_id=str(model_id),
            source=source,
        )
        payload.pop("_merged_list", None)
        yield ("done", payload)
    except Exception as exc:
        logger.warning("Agent stream JSON parse failed: %s", exc)
        payload = answer_question_rules(
            conn,
            message=message,
            segment=seg,
            merged_list=merged,
            extra_snippets=ctx["snippets"],
        )
        payload["source"] = "rules"
        payload["model_id"] = None
        yield ("done", payload)
