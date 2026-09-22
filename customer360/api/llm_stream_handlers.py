"""SSE generators for streaming LLM-backed API responses."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator

from customer360.actions.bedrock_draft import (
    ACTION_DRAFT_SYSTEM,
    _parse_draft_json,
)
from customer360.actions.draft import build_action_draft
from customer360.agent.stream_answer import stream_agent_answer
from customer360.insights.action_meta import experience_note_actionable, insight_action_meta
import json
from customer360.api.sse import sse_event
from customer360.insights.context import load_customer_context
from customer360.insights.parse import parse_insight_json
from customer360.insights.prompt import SYSTEM_PROMPT, build_user_prompt
from customer360.insights.service import _align_focus_with_churn, _generated_at_stamp, get_customer_insights
from customer360.insights.fallback import generate_fallback
from customer360.llm.errors import LLMError
from customer360.llm.router import is_llm_configured, stream_text_chunks
from customer360.llm_provider import get_active_provider
from customer360.bedrock.config import effective_bedrock_settings
from customer360.actions.draft import classify_recommendation, channel_for_action_kind
from customer360.llm_provider import user_facing_brand, get_active_provider as active_provider


def stream_agent_ask_events(
    conn: sqlite3.Connection,
    *,
    message: str,
    segment: str | None,
    list_context: dict | None,
    locale: str | None,
) -> Iterator[bytes]:
    try:
        for kind, payload in stream_agent_answer(
            conn,
            message=message,
            segment=segment,
            list_context=list_context,
            locale=locale,
        ):
            if kind == "delta" and payload:
                yield sse_event("delta", payload)
            elif kind == "done" and payload:
                yield sse_event("done", payload)
    except Exception as exc:
        yield sse_event("error", {"detail": str(exc)})


def stream_insights_events(
    conn: sqlite3.Connection,
    customer_id: int,
    *,
    refresh: bool,
) -> Iterator[bytes]:
    del refresh
    ctx = load_customer_context(conn, customer_id)
    if ctx is None:
        yield sse_event("error", {"detail": "Customer not found"})
        return

    llm_ready = is_llm_configured()
    if not llm_ready:
        result = get_customer_insights(conn, customer_id, refresh=True)
        if result:
            result["recommendation_actions"] = [
                insight_action_meta(text) for text in result.get("recommendations", [])
            ]
            note = result.get("experience_note") or ""
            result["experience_note_actionable"] = experience_note_actionable(note)
            yield sse_event("done", result)
        return

    buffer: list[str] = []
    try:
        for piece in stream_text_chunks(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=build_user_prompt(ctx.payload, ctx.churn_tier),
            json_mode=True,
        ):
            buffer.append(piece)
            yield sse_event("delta", {"text": piece})
        raw = "".join(buffer)
        parsed = _align_focus_with_churn(parse_insight_json(raw), ctx.churn_tier)
        provider = get_active_provider()
        source = "openai_compatible" if provider == "openai_compatible" else "bedrock"
        if provider == "openai_compatible":
            from customer360.llm_provider import load_llm_config

            model_id = (load_llm_config().openai_model_id or "").strip() or None
        else:
            model_id = effective_bedrock_settings().model_id

        result = {
            "preamble": parsed.get("preamble", ""),
            "summary": parsed["summary"],
            "guidance": parsed.get("guidance", ""),
            "primary_focus": parsed["primary_focus"],
            "recommendations": parsed["recommendations"],
            "experience_note": parsed.get("experience_note", ""),
            "source": source,
            "model_id": model_id,
            "generated_at": _generated_at_stamp(),
            "bedrock_configured": llm_ready,
            "fallback_reason": None,
            "cached": False,
        }
        result["recommendation_actions"] = [
            insight_action_meta(text) for text in result.get("recommendations", [])
        ]
        result["experience_note_actionable"] = experience_note_actionable(
            result.get("experience_note") or ""
        )
        yield sse_event("done", result)
    except (LLMError, ValueError) as exc:
        parsed = generate_fallback(ctx.payload)
        result = {
            "preamble": parsed.get("preamble", ""),
            "summary": parsed["summary"],
            "guidance": parsed.get("guidance", ""),
            "primary_focus": parsed["primary_focus"],
            "recommendations": parsed["recommendations"],
            "experience_note": parsed.get("experience_note", ""),
            "source": "fallback",
            "model_id": None,
            "generated_at": _generated_at_stamp(),
            "bedrock_configured": llm_ready,
            "fallback_reason": str(exc),
            "cached": False,
        }
        result["recommendation_actions"] = [
            insight_action_meta(text) for text in result.get("recommendations", [])
        ]
        result["experience_note_actionable"] = experience_note_actionable(
            result.get("experience_note") or ""
        )
        yield sse_event("done", result)


def stream_action_draft_events(
    conn: sqlite3.Connection,
    customer_id: int,
    *,
    recommendation: str,
    source: str,
) -> Iterator[bytes]:
    ctx = load_customer_context(conn, customer_id)
    if ctx is None:
        yield sse_event("error", {"detail": "Customer not found"})
        return

    action_kind = classify_recommendation(recommendation)
    if source == "experience_note" and not action_kind:
        action_kind = classify_recommendation(recommendation) or (
            "email_with_callback" if "email" in recommendation.lower() else "call_script"
        )

    if not action_kind or not is_llm_configured():
        draft = build_action_draft(
            conn, customer_id, recommendation, source=source
        )
        yield sse_event("done", draft)
        return

    expected_channel = channel_for_action_kind(action_kind)
    email_row = conn.execute(
        "SELECT CUSTOMER_NAME, EMAIL, MOBILE_NO FROM DWH_DIM_CUSTOMERS_UNIQUE "
        "WHERE CURRENT_IND = 1 AND CUSTOMER_ID = ?",
        (customer_id,),
    ).fetchone()
    name = ctx.payload.get("customer_name") or "Customer"
    email = None
    phone = None
    if email_row is not None:
        keys = email_row.keys() if hasattr(email_row, "keys") else []
        if "CUSTOMER_NAME" in keys and email_row["CUSTOMER_NAME"]:
            name = email_row["CUSTOMER_NAME"]
        email = email_row["EMAIL"] if "EMAIL" in keys else None
        phone = email_row["MOBILE_NO"] if "MOBILE_NO" in keys else None
    provider = active_provider()
    brand = user_facing_brand(provider)
    channel_labels = {
        "email": f"Draft email ({brand})",
        "sms": f"Draft SMS ({brand})",
        "call": f"Call script ({brand})",
    }
    yield sse_event(
        "meta",
        {
            "actionable": True,
            "action_kind": action_kind,
            "channel": expected_channel,
            "recipient_name": name,
            "recipient_email": email,
            "recipient_phone": phone,
            "preview_label": channel_labels.get(expected_channel, f"Draft ({brand})"),
        },
    )

    user_prompt = (
        f"Customer ID: {customer_id}\n"
        f"Action type: {action_kind}\n"
        f"Required channel: {expected_channel}\n"
        f"Insight recommendation to execute:\n{recommendation}\n\n"
        "Customer data (JSON):\n"
        f"{json.dumps(ctx.payload, ensure_ascii=False, indent=2)}"
    )

    buffer: list[str] = []
    try:
        for piece in stream_text_chunks(
            system_prompt=ACTION_DRAFT_SYSTEM,
            user_prompt=user_prompt,
            json_mode=True,
        ):
            buffer.append(piece)
            yield sse_event("delta", {"text": piece})
        raw = "".join(buffer)
        parsed = _parse_draft_json(raw)
        if parsed["channel"] != expected_channel:
            parsed["channel"] = expected_channel
        provider = active_provider()
        if provider == "openai_compatible":
            from customer360.llm_provider import load_llm_config

            model_id = (load_llm_config().openai_model_id or "").strip() or "privateai"
        else:
            model_id = effective_bedrock_settings().model_id
        draft_source = "openai_compatible" if provider == "openai_compatible" else "bedrock"
        yield sse_event(
            "done",
            {
                "actionable": True,
                "action_kind": action_kind,
                "channel": parsed["channel"],
                "preview_label": channel_labels.get(parsed["channel"], f"Draft ({brand})"),
                "recommendation": recommendation,
                "subject": parsed.get("subject"),
                "body": parsed["body"],
                "recipient_name": name,
                "recipient_email": email,
                "recipient_phone": phone,
                "content_source": draft_source,
                "model_id": model_id,
            },
        )
    except (LLMError, ValueError) as exc:
        yield sse_event(
            "done",
            {
                "actionable": False,
                "recommendation": recommendation,
                "action_kind": action_kind,
                "message": f"LLM could not generate this draft: {exc}",
                "content_source": "bedrock_error",
                "generation_error": str(exc),
            },
        )
