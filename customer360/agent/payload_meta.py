"""Attach LLM provider metadata to executive assistant API payloads."""

from __future__ import annotations

from customer360.llm.router import is_llm_configured
from customer360.llm_provider import get_active_provider


def attach_agent_llm_meta(
    payload: dict,
    *,
    llm_attempted: bool = False,
    fallback_reason: str | None = None,
) -> dict:
    payload.setdefault("source", "rules")
    payload["llm_provider"] = get_active_provider()
    if payload.get("source") == "rules" and (llm_attempted or is_llm_configured()):
        payload["source"] = "rules_fallback"
    if fallback_reason:
        payload["fallback_reason"] = fallback_reason
    return payload
