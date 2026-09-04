"""OpenAI-compatible local inference endpoints (Ollama, vLLM, LM Studio, etc.)."""

import json
import logging
from collections.abc import Iterator
from typing import Any
from urllib.parse import urlparse

import httpx

from app.schemas import ChatMessage
from app.state import runtime_state

logger = logging.getLogger(__name__)


class LocalLLMError(Exception):
    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code


def is_local_configured() -> bool:
    return runtime_state.is_local_ready()


def normalize_chat_completions_url(endpoint: str) -> str:
    """Accept base URL or full /v1/chat/completions path."""
    url = endpoint.strip().rstrip("/")
    if not url:
        raise LocalLLMError("Local endpoint URL is not configured.", status_code=400)

    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise LocalLLMError(
            "Local endpoint must be a full URL (e.g. http://localhost:11434/v1).",
            status_code=400,
        )

    if url.endswith("/chat/completions"):
        return url
    if url.endswith("/v1"):
        return f"{url}/chat/completions"
    return f"{url}/v1/chat/completions"


def _build_messages(
    messages: list[ChatMessage],
    system_prompt: str | None,
) -> list[dict[str, str]]:
    payload: list[dict[str, str]] = []
    if system_prompt:
        payload.append({"role": "system", "content": system_prompt})
    payload.extend({"role": m.role, "content": m.content} for m in messages)
    return payload


def invoke_chat(
    messages: list[ChatMessage],
    model_id: str | None = None,
    max_tokens: int = 1024,
    temperature: float = 0.7,
    system_prompt: str | None = None,
) -> tuple[str, str, dict | None]:
    if not runtime_state.is_local_ready():
        raise LocalLLMError(
            "Local LLM is not configured. Set endpoint URL and model name.",
            status_code=503,
        )

    resolved_model = model_id or runtime_state.get_local_model_id()
    url, headers, body = _local_request(
        resolved_model, messages, max_tokens, temperature, system_prompt, stream=False
    )

    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(url, json=body, headers=headers)
    except httpx.RequestError as exc:
        logger.error("Local LLM connection error: %s", exc)
        raise LocalLLMError(f"Could not reach local endpoint: {exc}", status_code=502) from exc

    if response.status_code >= 400:
        detail = response.text[:500]
        logger.error("Local LLM HTTP %s: %s", response.status_code, detail)
        raise LocalLLMError(
            f"Local LLM error ({response.status_code}): {detail}",
            status_code=502,
        )

    data = response.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LocalLLMError("Unexpected response format from local LLM.", status_code=502) from exc

    usage = data.get("usage")
    return content, resolved_model, usage


def _local_request(
    resolved_model: str,
    messages: list[ChatMessage],
    max_tokens: int,
    temperature: float,
    system_prompt: str | None,
    stream: bool,
) -> tuple[str, dict[str, str], dict[str, Any]]:
    url = normalize_chat_completions_url(runtime_state.get_local_endpoint_url())
    headers = {"Content-Type": "application/json"}
    token = runtime_state.get_local_api_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body: dict[str, Any] = {
        "model": resolved_model,
        "messages": _build_messages(messages, system_prompt),
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": stream,
    }
    return url, headers, body


def stream_chat(
    messages: list[ChatMessage],
    model_id: str | None = None,
    max_tokens: int = 1024,
    temperature: float = 0.7,
    system_prompt: str | None = None,
) -> Iterator[str]:
    if not runtime_state.is_local_ready():
        raise LocalLLMError(
            "Local LLM is not configured. Set endpoint URL and model name.",
            status_code=503,
        )

    resolved_model = model_id or runtime_state.get_local_model_id()
    url, headers, body = _local_request(
        resolved_model, messages, max_tokens, temperature, system_prompt, stream=True
    )

    try:
        with httpx.Client(timeout=120.0) as client:
            with client.stream("POST", url, json=body, headers=headers) as response:
                if response.status_code >= 400:
                    detail = response.read().decode()[:500]
                    raise LocalLLMError(
                        f"Local LLM error ({response.status_code}): {detail}",
                        status_code=502,
                    )

                for line in response.iter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    payload = line[5:].strip()
                    if payload == "[DONE]":
                        break
                    try:
                        data = json.loads(payload)
                    except json.JSONDecodeError:
                        continue
                    choices = data.get("choices", [])
                    if not choices:
                        continue
                    delta = choices[0].get("delta", {})
                    content = delta.get("content")
                    if content:
                        yield content
    except httpx.RequestError as exc:
        logger.error("Local LLM stream error: %s", exc)
        raise LocalLLMError(f"Could not reach local endpoint: {exc}", status_code=502) from exc
