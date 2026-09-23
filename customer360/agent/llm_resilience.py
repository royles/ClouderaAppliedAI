"""Retries and fallbacks for executive-assistant LLM calls."""

from __future__ import annotations

import logging
from collections.abc import Iterator

from customer360.agent.bedrock_agent import _parse_agent_json
from customer360.llm.errors import LLMError
from customer360.llm.router import invoke_text, stream_text_chunks

logger = logging.getLogger(__name__)

REPAIR_SUFFIX = (
    "\n\n---\nYour previous reply could not be parsed as JSON. "
    "Reply again with ONE JSON object only (no markdown fences, no text before or after). "
    "Required keys: answer (string), action_ids (array), open_retention_playbook (boolean). "
    "Include customer_list only when listing customers."
)


def _collect_stream(
    *,
    system_prompt: str,
    user_prompt: str,
    json_mode: bool,
) -> str:
    parts: list[str] = []
    for piece in stream_text_chunks(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        json_mode=json_mode,
    ):
        parts.append(piece)
    return "".join(parts)


def _invoke_once(
    *,
    system_prompt: str,
    user_prompt: str,
    json_mode: bool,
) -> str:
    raw, _model = invoke_text(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        json_mode=json_mode,
    )
    return raw


def _try_parse_raw(raw: str) -> dict | None:
    if not (raw or "").strip():
        return None
    try:
        return _parse_agent_json(raw)
    except (ValueError, TypeError, KeyError) as exc:
        logger.info("Agent JSON parse failed: %s", exc)
        return None


def _plaintext_fallback_payload(raw: str) -> dict | None:
    """If the model returned prose instead of JSON, still surface the text."""
    text = _strip_prose(raw)
    if len(text) < 20:
        return None
    if text.lstrip().startswith("{"):
        return None
    return {
        "answer": text[:4000],
        "action_ids": ["business"],
        "open_retention_playbook": False,
        "customer_list": None,
    }


def _strip_prose(raw: str) -> str:
    from customer360.agent.json_parse import _strip_markdown_fences

    return _strip_markdown_fences(raw).strip()


def complete_agent_model_json(
    *,
    system_prompt: str,
    user_prompt: str,
    prefer_stream: bool = True,
) -> tuple[dict, str, str]:
    """
    Returns (parsed_agent_dict, raw_text, model_id).
    Raises LLMError if the backend is unreachable; raises ValueError if all parse paths fail.
    """
    from customer360.llm_provider import get_active_provider, load_llm_config
    from customer360.bedrock.config import effective_bedrock_settings

    provider = get_active_provider()
    if provider == "openai_compatible":
        model_id = (load_llm_config().openai_model_id or "").strip() or "privateai"
    else:
        model_id = effective_bedrock_settings().model_id

    attempts: list[tuple[str, str, bool, bool]] = []
    if prefer_stream:
        attempts.append(("stream+json", user_prompt, True, True))
        attempts.append(("stream", user_prompt, True, False))
    attempts.extend(
        [
            ("invoke+json", user_prompt, False, True),
            ("invoke", user_prompt, False, False),
            ("repair+json", user_prompt + REPAIR_SUFFIX, False, True),
        ]
    )

    last_raw = ""
    last_error: Exception | None = None

    for label, prompt, use_stream, json_mode in attempts:
        try:
            if use_stream:
                last_raw = _collect_stream(
                    system_prompt=system_prompt,
                    user_prompt=prompt,
                    json_mode=json_mode,
                )
            else:
                last_raw = _invoke_once(
                    system_prompt=system_prompt,
                    user_prompt=prompt,
                    json_mode=json_mode,
                )
        except LLMError as exc:
            last_error = exc
            logger.warning("Agent LLM attempt %s failed: %s", label, exc)
            continue

        if not last_raw.strip():
            logger.warning("Agent LLM attempt %s returned empty body", label)
            continue

        parsed = _try_parse_raw(last_raw)
        if parsed is not None:
            logger.debug("Agent LLM succeeded on attempt %s", label)
            return parsed, last_raw, str(model_id)

        plain = _plaintext_fallback_payload(last_raw)
        if plain is not None:
            logger.info("Agent using plaintext fallback after attempt %s", label)
            return plain, last_raw, str(model_id)

    if last_error:
        raise LLMError(str(last_error), status_code=getattr(last_error, "status_code", 502))

    if last_raw.strip():
        raise ValueError(
            "Model returned text but not valid assistant JSON: "
            f"{last_raw.strip()[:240]}…"
        )
    raise ValueError("Model returned empty assistant response")


def stream_agent_deltas_then_parse(
    *,
    system_prompt: str,
    user_prompt: str,
) -> Iterator[tuple[str, dict | str | None]]:
    """
    Yields ("delta", str) while streaming, then ("parsed", dict) or raises.
    Falls back to complete_agent_model_json (non-stream retries) if stream parse fails.
    """
    buffer: list[str] = []
    stream_error: LLMError | None = None
    for json_mode in (True, False):
        buffer.clear()
        try:
            for piece in stream_text_chunks(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                json_mode=json_mode,
            ):
                buffer.append(piece)
                yield ("delta", piece)
        except LLMError as exc:
            stream_error = exc
            logger.warning(
                "Agent stream failed (json_mode=%s): %s",
                json_mode,
                exc,
            )
            continue
        if buffer:
            stream_error = None
            break
        logger.warning("Agent stream returned no tokens (json_mode=%s)", json_mode)

    raw = "".join(buffer)
    parsed = _try_parse_raw(raw) if raw.strip() else None
    if parsed is None and raw.strip():
        plain = _plaintext_fallback_payload(raw)
        if plain is not None:
            parsed = plain

    if parsed is not None:
        yield ("parsed", parsed)
        return

    if stream_error and not raw.strip():
        raise stream_error

    # Stream empty or unparseable — blocking retries (may not yield more deltas)
    parsed, _raw, _model = complete_agent_model_json(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        prefer_stream=False,
    )
    yield ("parsed", parsed)
