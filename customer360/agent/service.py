"""Orchestrate Bedrock copilot with rule-based fallback."""

from __future__ import annotations

import logging
import sqlite3

from customer360.agent.bedrock_agent import answer_with_bedrock
from customer360.agent.context import gather_context
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

    if is_bedrock_configured() and (message or "").strip():
        try:
            return answer_with_bedrock(
                message=message.strip(),
                segment=seg,
                snippets=ctx["snippets"],
            )
        except (BedrockError, ValueError) as exc:
            logger.warning("Bedrock copilot failed, using rules: %s", exc)

    payload = answer_question_rules(conn, message=message, segment=seg)
    payload["source"] = "rules"
    payload["model_id"] = None
    return payload
