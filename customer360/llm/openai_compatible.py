"""OpenAI-compatible chat completions (vLLM, LiteLLM, Azure OpenAI-style gateways)."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from collections.abc import Iterator
from typing import Any

from customer360.llm.errors import LLMError
from customer360.llm_provider import LlmProviderConfig, load_llm_config

logger = logging.getLogger(__name__)


def _chat_completions_url(base_url: str) -> str:
    raw = base_url.strip().rstrip("/")
    if raw.endswith("/chat/completions"):
        return raw
    if raw.endswith("/v1"):
        return f"{raw}/chat/completions"
    return f"{raw}/v1/chat/completions"


def _post_chat_completion(
    *,
    url: str,
    token: str,
    body: dict[str, Any],
) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        logger.error("OpenAI-compatible HTTP %s: %s", exc.code, detail)
        status = 401 if exc.code in (401, 403) else 502
        raise LLMError(
            f"PrivateAI API error ({exc.code}): {detail or exc.reason}",
            status_code=status,
        ) from exc
    except urllib.error.URLError as exc:
        raise LLMError(f"PrivateAI connection error: {exc.reason}", status_code=502) from exc


def invoke_openai_compatible_text(
    *,
    system_prompt: str,
    user_prompt: str,
    config: LlmProviderConfig | None = None,
    json_mode: bool = False,
) -> tuple[str, str]:
    cfg = config or load_llm_config()
    token = (cfg.openai_api_token or "").strip()
    base = (cfg.openai_base_url or "").strip()
    model = (cfg.openai_model_id or "").strip()
    if not base or not model or not token:
        raise LLMError("PrivateAI provider is not fully configured", status_code=503)

    max_tokens = cfg.bedrock_max_tokens or 900
    temperature = cfg.bedrock_temperature if cfg.bedrock_temperature is not None else 0.35

    body: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    url = _chat_completions_url(base)
    payload: dict[str, Any]
    if json_mode:
        body_with_json = {**body, "response_format": {"type": "json_object"}}
        try:
            payload = _post_chat_completion(url=url, token=token, body=body_with_json)
        except LLMError as exc:
            if "response_format" in str(exc).lower() or exc.status_code == 400:
                logger.info("PrivateAI json_mode unsupported, retrying without response_format")
                payload = _post_chat_completion(url=url, token=token, body=body)
            else:
                raise
    else:
        payload = _post_chat_completion(url=url, token=token, body=body)

    choices = payload.get("choices") or []
    if not choices:
        raise LLMError("PrivateAI API returned no choices", status_code=502)
    message = choices[0].get("message") or {}
    text = message.get("content")
    if not text:
        raise LLMError("PrivateAI API returned empty content", status_code=502)
    return str(text), model


def stream_openai_compatible_text(
    *,
    system_prompt: str,
    user_prompt: str,
    config: LlmProviderConfig | None = None,
    json_mode: bool = False,
) -> Iterator[str]:
    """Yield text deltas from an OpenAI-style streaming chat completion."""
    cfg = config or load_llm_config()
    token = (cfg.openai_api_token or "").strip()
    base = (cfg.openai_base_url or "").strip()
    model = (cfg.openai_model_id or "").strip()
    if not base or not model or not token:
        raise LLMError("PrivateAI provider is not fully configured", status_code=503)

    max_tokens = cfg.bedrock_max_tokens or 900
    temperature = cfg.bedrock_temperature if cfg.bedrock_temperature is not None else 0.35

    body: dict[str, Any] = {
        "model": model,
        "stream": True,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}

    url = _chat_completions_url(base)

    def _read_stream(request_body: dict[str, Any]) -> Iterator[str]:
        request = urllib.request.Request(
            url,
            data=json.dumps(request_body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
                "Accept": "text/event-stream",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=300) as resp:
                while True:
                    line = resp.readline()
                    if not line:
                        break
                    decoded = line.decode("utf-8", errors="replace").strip()
                    if not decoded or not decoded.startswith("data:"):
                        continue
                    data = decoded[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    choices = chunk.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    piece = delta.get("content")
                    if piece:
                        yield str(piece)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            logger.error("OpenAI-compatible stream HTTP %s: %s", exc.code, detail)
            status = 401 if exc.code in (401, 403) else 502
            raise LLMError(
                f"PrivateAI API error ({exc.code}): {detail or exc.reason}",
                status_code=status,
            ) from exc
        except urllib.error.URLError as exc:
            raise LLMError(f"PrivateAI connection error: {exc.reason}", status_code=502) from exc

    try:
        yield from _read_stream(body)
    except LLMError as exc:
        if json_mode and ("response_format" in str(exc).lower() or exc.status_code == 400):
            logger.info("PrivateAI stream json_mode unsupported, retrying without response_format")
            body_no_json = {k: v for k, v in body.items() if k != "response_format"}
            yield from _read_stream(body_no_json)
        else:
            raise


def test_openai_compatible(config: LlmProviderConfig | None = None) -> dict[str, Any]:
    cfg = config or load_llm_config()
    try:
        text, model = invoke_openai_compatible_text(
            system_prompt="Reply with exactly OK.",
            user_prompt="Ping",
            config=cfg,
        )
        snippet = (text or "").strip()[:80]
        return {
            "ok": True,
            "message": f"PrivateAI endpoint responded for model {model}.",
            "detail": snippet or None,
        }
    except LLMError as exc:
        return {
            "ok": False,
            "message": str(exc),
            "detail": None,
        }
