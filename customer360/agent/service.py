"""Orchestrate Bedrock copilot with rule-based fallback."""

from __future__ import annotations

import logging
import sqlite3

from customer360.agent.bedrock_agent import answer_with_bedrock
from customer360.agent.context import gather_context
from customer360.agent.customer_snippet import top_customers_snippet
from customer360.agent.list_filters import parse_customer_list_intent
from customer360.agent.router import answer_question_rules
from customer360.bedrock.client import BedrockError, is_bedrock_configured

logger = logging.getLogger(__name__)


def answer_question(
    conn: sqlite3.Connection,
    *,
    message: str,
    segment: str | None = None,
) -> dict:
    ctx = gather_context(conn, message=message, segment=segment)
    seg = ctx["segment"]
    list_intent = parse_customer_list_intent(message)

    if list_intent:
        rank_snippet = top_customers_snippet(
            conn,
            filters=list_intent,
            default_segment=seg,
            limit=min(list_intent.page_size, 10),
        )
        if rank_snippet and rank_snippet not in ctx["snippets"]:
            ctx["snippets"].append(rank_snippet)

    if is_bedrock_configured() and (message or "").strip():
        try:
            return answer_with_bedrock(
                message=message.strip(),
                segment=seg,
                snippets=ctx["snippets"],
                list_intent=list_intent,
            )
        except (BedrockError, ValueError) as exc:
            logger.warning("Bedrock copilot failed, using rules: %s", exc)

    payload = answer_question_rules(
        conn,
        message=message,
        segment=seg,
        list_intent=list_intent,
        extra_snippets=ctx["snippets"],
    )
    payload["source"] = "rules"
    payload["model_id"] = None
    return payload
