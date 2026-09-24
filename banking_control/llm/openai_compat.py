from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from typing import Any

from banking_control.llm.admin_store import LlmProviderConfig
from banking_control.llm.errors import LLMError

logger = logging.getLogger(__name__)
_RETRYABLE = frozenset({408, 429, 500, 502, 503, 504})


def _url(base: str) -> str:
    raw = base.strip().rstrip("/")
    if raw.endswith("/chat/completions"):
        return raw
    if raw.endswith("/v1"):
        return f"{raw}/chat/completions"
    return f"{raw}/v1/chat/completions"


def is_openai_configured(cfg: LlmProviderConfig) -> bool:
    return bool(
        (cfg.openai_base_url or "").strip()
        and (cfg.openai_model_id or "").strip()
        and (cfg.openai_api_token or "").strip()
    )


def stream_openai_chat(
    *,
    system: str,
    messages: list[dict[str, str]],
    config: LlmProviderConfig,
    tools: list[dict[str, Any]] | None = None,
) -> Iterator[str]:
    token = (config.openai_api_token or "").strip()
    base = (config.openai_base_url or "").strip()
    model = (config.openai_model_id or "").strip()
    if not is_openai_configured(config):
        raise LLMError("OpenAI-compatible provider is not fully configured", status_code=503)

    max_tokens = config.bedrock_max_tokens or 900
    temperature = config.bedrock_temperature if config.bedrock_temperature is not None else 0.35
    body: dict[str, Any] = {
        "model": model,
        "stream": True,
        "messages": [{"role": "system", "content": system}, *messages],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"

    payload = json.dumps(body).encode("utf-8")
    url = _url(base)
    request = urllib.request.Request(
        url,
        data=payload,
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
                if not decoded.startswith("data:"):
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
        raise LLMError(f"Local LLM HTTP {exc.code}: {detail}", status_code=502) from exc
    except urllib.error.URLError as exc:
        raise LLMError(f"Local LLM connection error: {exc.reason}", status_code=502) from exc


def invoke_openai_chat(
    *,
    system: str,
    messages: list[dict[str, str]],
    config: LlmProviderConfig,
    tools: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    token = (config.openai_api_token or "").strip()
    base = (config.openai_base_url or "").strip()
    model = (config.openai_model_id or "").strip()
    if not is_openai_configured(config):
        raise LLMError("OpenAI-compatible provider is not fully configured", status_code=503)

    max_tokens = config.bedrock_max_tokens or 900
    temperature = config.bedrock_temperature if config.bedrock_temperature is not None else 0.35
    body: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "system", "content": system}, *messages],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"

    payload = json.dumps(body).encode("utf-8")
    url = _url(base)
    last_exc: LLMError | None = None
    for attempt in range(3):
        req = urllib.request.Request(
            url,
            data=payload,
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
            last_exc = LLMError(f"Local LLM HTTP {exc.code}: {detail}", status_code=502)
            if exc.code in _RETRYABLE and attempt + 1 < 3:
                time.sleep(0.5 * (2**attempt))
                continue
            raise last_exc from exc
        except urllib.error.URLError as exc:
            last_exc = LLMError(f"Local LLM connection error: {exc.reason}", status_code=502)
            if attempt + 1 < 3:
                time.sleep(0.5 * (2**attempt))
                continue
            raise last_exc from exc
    assert last_exc
    raise last_exc
