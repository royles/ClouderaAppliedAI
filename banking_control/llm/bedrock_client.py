from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from typing import Any

from banking_control.llm.bedrock_config import (
    effective_bedrock_settings,
    resolve_client_region,
    resolve_inference_model_id,
)
from banking_control.llm.errors import LLMError

logger = logging.getLogger(__name__)


class BedrockError(LLMError):
    pass


def is_bedrock_configured(admin=None) -> bool:
    settings = effective_bedrock_settings(admin)
    if settings.has_explicit_credentials():
        return True
    try:
        import boto3
    except ImportError:
        return False
    try:
        region = resolve_client_region(settings.bedrock_region)
        session = boto3.Session(region_name=region)
        creds = session.get_credentials()
        return creds is not None and creds.access_key is not None
    except Exception:
        return False


def _session(settings):
    import boto3

    region = resolve_client_region(settings.bedrock_region)
    kwargs: dict[str, Any] = {"region_name": region}
    if settings.has_explicit_credentials():
        kwargs["aws_access_key_id"] = settings.aws_access_key_id
        kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
        if settings.aws_session_token:
            kwargs["aws_session_token"] = settings.aws_session_token
    return boto3.Session(**kwargs), region


def _anthropic_body(
    *,
    system: str,
    messages: list[dict[str, Any]],
    max_tokens: int,
    temperature: float,
    tools: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "system": [{"type": "text", "text": system}],
        "messages": messages,
        "temperature": temperature,
    }
    if tools:
        body["tools"] = tools
    return body


def stream_bedrock_chat(
    *,
    system: str,
    messages: list[dict[str, Any]],
    admin=None,
    tools: list[dict[str, Any]] | None = None,
) -> Iterator[str]:
    try:
        from botocore.exceptions import BotoCoreError, ClientError
    except ImportError as exc:
        raise BedrockError("boto3 is not installed", status_code=503) from exc

    settings = effective_bedrock_settings(admin)
    catalog_model = settings.model_id
    inference_model = resolve_inference_model_id(catalog_model, settings.bedrock_region)
    body = _anthropic_body(
        system=system,
        messages=messages,
        max_tokens=settings.max_tokens,
        temperature=settings.temperature,
        tools=tools,
    )
    session, region = _session(settings)
    client = session.client("bedrock-runtime", region_name=region)
    try:
        response = client.invoke_model_with_response_stream(
            modelId=inference_model,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "Unknown")
        msg = exc.response.get("Error", {}).get("Message", str(exc))
        raise BedrockError(f"Bedrock error ({code}): {msg}", status_code=502) from exc
    except BotoCoreError as exc:
        raise BedrockError(f"AWS connection error: {exc}", status_code=502) from exc

    for event in response.get("body", ()):
        chunk = event.get("chunk", {}).get("bytes")
        if not chunk:
            continue
        payload = json.loads(chunk)
        if payload.get("type") == "content_block_delta":
            delta = payload.get("delta") or {}
            if delta.get("type") == "text_delta" and delta.get("text"):
                yield str(delta["text"])


def invoke_bedrock_messages(
    *,
    system: str,
    messages: list[dict[str, Any]],
    admin=None,
    tools: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    try:
        from botocore.exceptions import BotoCoreError, ClientError
    except ImportError as exc:
        raise BedrockError("boto3 is not installed", status_code=503) from exc

    settings = effective_bedrock_settings(admin)
    inference_model = resolve_inference_model_id(settings.model_id, settings.bedrock_region)
    body = _anthropic_body(
        system=system,
        messages=messages,
        max_tokens=settings.max_tokens,
        temperature=settings.temperature,
        tools=tools,
    )
    session, region = _session(settings)
    client = session.client("bedrock-runtime", region_name=region)
    try:
        response = client.invoke_model(
            modelId=inference_model,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )
        return json.loads(response["body"].read())
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "Unknown")
        msg = exc.response.get("Error", {}).get("Message", str(exc))
        raise BedrockError(f"Bedrock error ({code}): {msg}", status_code=502) from exc
    except BotoCoreError as exc:
        raise BedrockError(f"AWS connection error: {exc}", status_code=502) from exc
