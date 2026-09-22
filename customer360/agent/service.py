"""Orchestrate Bedrock copilot with rule-based fallback."""

from __future__ import annotations

import logging
import sqlite3

from customer360.agent.bedrock_agent import answer_with_bedrock
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
        try:
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
            return payload
        except Exception as exc:
            logger.warning("Bedrock copilot failed, using rules: %s", exc, exc_info=True)

    payload = answer_question_rules(
        conn,
        message=message,
        segment=seg,
        merged_list=merged,
        extra_snippets=ctx["snippets"],
    )
    payload["source"] = "rules"
    payload["model_id"] = None
    return payload
