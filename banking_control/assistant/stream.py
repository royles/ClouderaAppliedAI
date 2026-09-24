from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from typing import Any

from banking_control.api.sse import sse_event
from banking_control.assistant.tools import (
    bedrock_tool_definitions,
    execute_copilot_tool,
    openai_tool_definitions,
)
from banking_control.llm.admin_store import load_llm_config
from banking_control.llm.bedrock_client import invoke_bedrock_messages, stream_bedrock_chat
from banking_control.llm.errors import LLMError
from banking_control.llm.openai_compat import invoke_openai_chat, stream_openai_chat
from banking_control.llm.openai_tool_parse import (
    content_looks_like_tool_attempt,
    parse_tool_calls_from_content,
)
from banking_control.llm.router import is_llm_configured
from banking_control.assistant.response_format import (
    answer_from_tool_messages,
    postprocess_user_visible,
)
from banking_control.assistant.thinking_suppress import suppress_thinking_markup
from banking_control.assistant.router import answer_question_rules, suggest_actions
from banking_control.tools.engine import ControlToolEngine

MAX_TOOL_TURNS = 6

SYSTEM_PROMPT = """You are the Banking Control Solution assistant for an EU retail and commercial bank.
Use tools for live data: overview KPIs, control catalog, testing guides, simulated control runs, and audit events.

Grounding rules (business-critical — never violate):
- Do NOT invent workpaper IDs, board packs, customer references, or evidence filenames.
- Only cite evidence if it appears in tool JSON: inputs.evidence_refs you passed, evidence_policy.allowed_evidence_refs, or evidence_policy.warehouse_evidence_ref.
- Regulatory citations must use standards_refs (label + url) returned by tools — do not make up EUR-Lex or EBA document codes.
- Simulation outputs (status, exception_rate_pct, findings) are illustrative demo metrics — label them clearly as simulated.

When the user asks to test or simulate a control:
1. Call get_control_testing_guide and/or invoke_control_tool.
2. Present the effective_status_checklist from tool JSON as the primary "what is required for Effective" answer.
3. Use workflow_suggestions: if action is "create", offer start_control_workflow — cite artifact_ref only after that tool returns it.
4. Optionally summarize simulated_status/metrics separately under a "Simulation (demo)" heading.
5. Never list fabricated "Evidence reviewed" bullets or assume workpapers already exist.

Control codes: DOMAIN-NNN (examples: AML-001, KYC-003). If unknown_control_code, apologize and stop — do not retry invalid codes.

Tool use: call functions via the API tool mechanism only. Do not print XML, JSON tool blocks, or chain-of-thought in the user-visible reply.

Reply format: short markdown only — headings, numbered/bullet lists. No pipe tables. External regulator links as a bullet list with a one-line caution that they are third-party sites.
"""


def _rules_fallback(
    conn: sqlite3.Connection,
    engine: ControlToolEngine,
    message: str,
) -> dict[str, Any]:
    payload = answer_question_rules(conn, engine, message)
    payload.setdefault("tools_called", [])
    payload["model_id"] = None
    payload["provider"] = None
    if not is_llm_configured(conn):
        payload["answer"] = (
            payload.get("answer", "")
            + " Configure Bedrock or a local OpenAI-compatible endpoint via ⚙ Settings to enable full LLM replies."
        ).strip()
    return payload


def _execute_openai_tool_calls(
    conn: sqlite3.Connection,
    engine: ControlToolEngine,
    messages: list[dict[str, Any]],
    tool_calls: list[dict[str, Any]],
    tools_called: list[str],
) -> None:
    assistant_msg: dict[str, Any] = {
        "role": "assistant",
        "content": None,
        "tool_calls": tool_calls,
    }
    messages.append(assistant_msg)
    for tc in tool_calls:
        fn = tc.get("function") or {}
        name = fn.get("name", "")
        try:
            args = json.loads(fn.get("arguments") or "{}")
        except json.JSONDecodeError:
            args = {}
        if name:
            tools_called.append(name)
        result = execute_copilot_tool(conn, engine, name, args)
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tc.get("id", name),
                "content": result,
            }
        )


def _run_tool_loop_openai(
    conn: sqlite3.Connection,
    engine: ControlToolEngine,
    cfg,
    messages: list[dict[str, Any]],
) -> tuple[list[str], list[dict[str, Any]]]:
    tools_called: list[str] = []
    for _ in range(MAX_TOOL_TURNS):
        payload = invoke_openai_chat(
            system=SYSTEM_PROMPT,
            messages=messages,
            config=cfg,
            tools=openai_tool_definitions(),
        )
        choice = (payload.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        raw_content = msg.get("content") or ""
        tool_calls = list(msg.get("tool_calls") or [])
        if not tool_calls and raw_content:
            tool_calls = parse_tool_calls_from_content(str(raw_content))

        if not tool_calls:
            clean = postprocess_user_visible(str(raw_content))
            if not clean and content_looks_like_tool_attempt(str(raw_content)):
                continue
            messages.append({"role": "assistant", "content": clean})
            return tools_called, messages

        _execute_openai_tool_calls(conn, engine, messages, tool_calls, tools_called)
    return tools_called, messages


def _fallback_answer_from_tool_messages(messages: list[dict[str, Any]]) -> str:
    """When the local model cannot summarize tool JSON, format a grounded reply server-side."""
    for msg in reversed(messages):
        if msg.get("role") != "tool":
            continue
        raw = msg.get("content") or ""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(data, list) and data and isinstance(data[0], dict):
            if "event_at" in data[0] and "action" in data[0]:
                lines = ["### Recent audit activity", ""]
                for ev in data[:12]:
                    detail = str(ev.get("detail") or "")[:160]
                    lines.append(
                        f"- **{ev.get('event_at', '')}** — {ev.get('actor', '')}: "
                        f"{ev.get('action', '')} ({detail})"
                    )
                return "\n".join(lines)
        if isinstance(data, dict) and "control_health_pct" in data:
            return (
                f"Control health is **{data.get('control_health_pct')}%** effective; "
                f"**{data.get('open_exceptions', 0)}** open exceptions; "
                f"new AML alerts in overview: {data.get('alert_status', {})}."
            )
    return ""


def _summarize_after_tools_openai(
    conn: sqlite3.Connection,
    cfg,
    messages: list[dict[str, Any]],
) -> str:
    """One non-tool completion so local models produce a user-facing summary."""
    payload = invoke_openai_chat(
        system=SYSTEM_PROMPT
        + "\n\nSummarize the tool results above in clear markdown for the user. "
        "Do not show tool XML, JSON, or internal reasoning.",
        messages=messages,
        config=cfg,
        tools=None,
    )
    choice = (payload.get("choices") or [{}])[0]
    msg = choice.get("message") or {}
    return postprocess_user_visible(str(msg.get("content") or ""))


def _run_tool_loop_bedrock(
    conn: sqlite3.Connection,
    engine: ControlToolEngine,
    cfg,
    messages: list[dict[str, Any]],
) -> tuple[list[str], list[dict[str, Any]]]:
    tools_called: list[str] = []
    for _ in range(MAX_TOOL_TURNS):
        body = invoke_bedrock_messages(
            system=SYSTEM_PROMPT,
            messages=messages,
            admin=cfg,
            tools=bedrock_tool_definitions(),
        )
        content = body.get("content") or []
        stop = body.get("stop_reason")
        messages.append({"role": "assistant", "content": content})
        tool_uses = [b for b in content if b.get("type") == "tool_use"]
        if not tool_uses or stop != "tool_use":
            return tools_called, messages
        results: list[dict[str, Any]] = []
        for tu in tool_uses:
            name = tu.get("name", "")
            tools_called.append(name)
            args = tu.get("input") or {}
            results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tu.get("id"),
                    "content": execute_copilot_tool(conn, engine, name, args),
                }
            )
        messages.append({"role": "user", "content": results})
    return tools_called, messages


def stream_assistant_events(
    conn: sqlite3.Connection,
    engine: ControlToolEngine,
    *,
    message: str,
) -> Iterator[bytes]:
    trimmed = (message or "").strip()
    if not trimmed:
        yield sse_event("error", {"detail": "Message is required"})
        return

    cfg = load_llm_config(conn)
    provider = cfg.provider_type

    if not is_llm_configured(conn):
        yield sse_event("done", _rules_fallback(conn, engine, trimmed))
        return

    yield sse_event("meta", {"provider": provider, "status": "Running tools…"})

    try:
        tools_called: list[str] = []
        buffer: list[str] = []
        tool_result_messages: list[dict[str, Any]] = []

        if provider == "openai_compatible":
            oai_messages: list[dict[str, Any]] = [{"role": "user", "content": trimmed}]
            tools_called, oai_messages = _run_tool_loop_openai(conn, engine, cfg, oai_messages)
            tool_result_messages = oai_messages
            structured = answer_from_tool_messages(tool_result_messages, tools_called)
            yield sse_event("meta", {"status": "Streaming response…", "tools_called": tools_called})
            if structured:
                yield sse_event("meta", {"status": "Formatting grounded reply…"})
                buffer.append(structured)
                yield sse_event("delta", {"text": structured})
            else:
                last = oai_messages[-1] if oai_messages else {}
                text = ""
                if last.get("role") == "assistant" and last.get("content"):
                    text = postprocess_user_visible(str(last["content"]))
                if (not text or content_looks_like_tool_attempt(text)) and tools_called:
                    text = _summarize_after_tools_openai(conn, cfg, oai_messages)
                if text:
                    text = postprocess_user_visible(text)
                    for i in range(0, len(text), 32):
                        piece = text[i : i + 32]
                        buffer.append(piece)
                        yield sse_event("delta", {"text": piece})
                elif tools_called:
                    for piece in stream_openai_chat(
                        system=SYSTEM_PROMPT,
                        messages=oai_messages,
                        config=cfg,
                        tools=None,
                    ):
                        clean = suppress_thinking_markup(piece)
                        if clean:
                            buffer.append(clean)
                            yield sse_event("delta", {"text": clean})
                else:
                    for piece in stream_openai_chat(
                        system=SYSTEM_PROMPT,
                        messages=oai_messages,
                        config=cfg,
                    ):
                        clean = suppress_thinking_markup(piece)
                        if clean:
                            buffer.append(clean)
                            yield sse_event("delta", {"text": clean})
        else:
            bedrock_messages: list[dict[str, Any]] = [
                {"role": "user", "content": [{"type": "text", "text": trimmed}]},
            ]
            tools_called, bedrock_messages = _run_tool_loop_bedrock(
                conn, engine, cfg, bedrock_messages
            )
            yield sse_event("meta", {"status": "Streaming response…", "tools_called": tools_called})
            last_content = (bedrock_messages[-1].get("content") if bedrock_messages else []) or []
            prefilled = "\n".join(
                str(b.get("text", "")) for b in last_content if b.get("type") == "text"
            ).strip()
            if prefilled:
                for i in range(0, len(prefilled), 32):
                    piece = prefilled[i : i + 32]
                    buffer.append(piece)
                    yield sse_event("delta", {"text": piece})
            else:
                for piece in stream_bedrock_chat(
                    system=SYSTEM_PROMPT,
                    messages=bedrock_messages,
                    admin=cfg,
                ):
                    buffer.append(piece)
                    yield sse_event("delta", {"text": piece})

        structured_final = answer_from_tool_messages(tool_result_messages, tools_called)
        final_answer = structured_final or "".join(buffer)
        if not final_answer.strip() and tools_called:
            final_answer = _fallback_answer_from_tool_messages(tool_result_messages)
        if structured_final:
            visible_answer = structured_final
        else:
            visible_answer = postprocess_user_visible(final_answer)
        actions = suggest_actions(conn, trimmed, tools_called=tools_called)
        yield sse_event(
            "done",
            {
                "answer": visible_answer.strip() or "No response generated.",
                "source": provider,
                "provider": provider,
                "model_id": cfg.bedrock_model_id or cfg.openai_model_id,
                "tools_called": tools_called,
                "actions": actions,
            },
        )
    except LLMError as exc:
        yield sse_event("error", {"detail": str(exc)})
