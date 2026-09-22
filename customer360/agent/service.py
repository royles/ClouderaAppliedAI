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
from customer360.agent.query_builder import compile_customer_list_sql, count_matching_customers
from customer360.agent.router import answer_question_rules
from customer360.bedrock.client import BedrockError, is_bedrock_configured

logger = logging.getLogger(__name__)


def _attach_query_preview(payload: dict, filters: CustomerListFilters | None, seg: str) -> None:
    if filters is None:
        return
    sql, params, description = compile_customer_list_sql(filters, default_segment=seg)
    param_hint = ", ".join(repr(p) for p in params)
    payload["query_preview"] = f"{description}\n{sql}\n-- params: [{param_hint}]"


def answer_question(
    conn: sqlite3.Connection,
    *,
    message: str,
    segment: str | None = None,
    list_context: dict | None = None,
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

    if is_bedrock_configured() and (message or "").strip():
        try:
            payload = answer_with_bedrock(
                message=message.strip(),
                segment=seg,
                snippets=ctx["snippets"],
                list_intent=merged,
                list_context=list_ctx,
            )
            final_filters = payload.pop("_merged_list", None) or merged
            _attach_query_preview(payload, final_filters, seg)
            return payload
        except (BedrockError, ValueError) as exc:
            logger.warning("Bedrock copilot failed, using rules: %s", exc)

    payload = answer_question_rules(
        conn,
        message=message,
        segment=seg,
        merged_list=merged,
        extra_snippets=ctx["snippets"],
    )
    payload["source"] = "rules"
    payload["model_id"] = None
    _attach_query_preview(payload, merged, seg)
    return payload
