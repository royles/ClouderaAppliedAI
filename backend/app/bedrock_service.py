"""AWS Bedrock integration. Credentials are never logged or returned to clients."""

import json
import logging
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import get_settings
from app.schemas import ChatMessage
from app.state import runtime_state

logger = logging.getLogger(__name__)


class BedrockError(Exception):
    """Raised when Bedrock invocation fails."""

    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code


def _credential_source() -> str:
    settings = get_settings()
    if settings.has_explicit_credentials():
        return "environment_variables"
    return "iam_role_or_default_chain"


def is_aws_configured() -> bool:
    """True if explicit env credentials exist or default credential chain is available."""
    settings = get_settings()
    if settings.has_explicit_credentials():
        return True
    try:
        session = boto3.Session(region_name=runtime_state.get_region())
        credentials = session.get_credentials()
        return credentials is not None and credentials.access_key is not None
    except Exception:
        return False


def _build_session() -> boto3.Session:
    settings = get_settings()
    kwargs: dict[str, Any] = {"region_name": runtime_state.get_region()}
    if settings.has_explicit_credentials():
        kwargs["aws_access_key_id"] = settings.aws_access_key_id
        kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
        if settings.aws_session_token:
            kwargs["aws_session_token"] = settings.aws_session_token
    return boto3.Session(**kwargs)


def _get_client() -> Any:
    session = _build_session()
    return session.client("bedrock-runtime")


def _format_anthropic(
    messages: list[ChatMessage],
    max_tokens: int,
    temperature: float,
    system_prompt: str | None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": m.role, "content": m.content} for m in messages],
    }
    if system_prompt:
        body["system"] = system_prompt
    return body


def _format_amazon_titan(
    messages: list[ChatMessage],
    max_tokens: int,
    temperature: float,
) -> dict[str, Any]:
    # Titan expects a single prompt string.
    parts: list[str] = []
    for msg in messages:
        prefix = "User: " if msg.role == "user" else "Assistant: "
        parts.append(f"{prefix}{msg.content}")
    parts.append("Assistant: ")
    return {
        "inputText": "\n".join(parts),
        "textGenerationConfig": {
            "maxTokenCount": max_tokens,
            "temperature": temperature,
            "topP": 0.9,
        },
    }


def _format_meta_llama(
    messages: list[ChatMessage],
    max_tokens: int,
    temperature: float,
) -> dict[str, Any]:
    prompt_parts: list[str] = ["<s>"]
    for msg in messages:
        if msg.role == "user":
            prompt_parts.append(f"[INST] {msg.content} [/INST]")
        else:
            prompt_parts.append(msg.content)
    return {
        "prompt": "".join(prompt_parts),
        "max_gen_len": max_tokens,
        "temperature": temperature,
        "top_p": 0.9,
    }


def _format_mistral(
    messages: list[ChatMessage],
    max_tokens: int,
    temperature: float,
) -> dict[str, Any]:
    prompt_parts: list[str] = ["<s>"]
    for msg in messages:
        if msg.role == "user":
            prompt_parts.append(f"[INST] {msg.content} [/INST]")
        else:
            prompt_parts.append(msg.content)
    return {
        "prompt": "".join(prompt_parts),
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": 0.9,
    }


def _build_request_body(
    model_id: str,
    messages: list[ChatMessage],
    max_tokens: int,
    temperature: float,
    system_prompt: str | None,
) -> dict[str, Any]:
    if model_id.startswith("anthropic."):
        return _format_anthropic(messages, max_tokens, temperature, system_prompt)
    if model_id.startswith("amazon.titan"):
        return _format_amazon_titan(messages, max_tokens, temperature)
    if model_id.startswith("meta."):
        return _format_meta_llama(messages, max_tokens, temperature)
    if model_id.startswith("mistral."):
        return _format_mistral(messages, max_tokens, temperature)
    # Fallback: try Anthropic format for unknown models.
    return _format_anthropic(messages, max_tokens, temperature, system_prompt)


def _parse_response(model_id: str, response_body: dict[str, Any]) -> tuple[str, dict | None]:
    usage: dict | None = None

    if model_id.startswith("anthropic."):
        content = response_body.get("content", [])
        text = content[0].get("text", "") if content else ""
        if "usage" in response_body:
            usage = response_body["usage"]
        return text, usage

    if model_id.startswith("amazon.titan"):
        results = response_body.get("results", [])
        text = results[0].get("outputText", "") if results else ""
        return text, usage

    if model_id.startswith("meta."):
        return response_body.get("generation", ""), usage

    if model_id.startswith("mistral."):
        outputs = response_body.get("outputs", [])
        text = outputs[0].get("text", "") if outputs else ""
        return text, usage

    # Generic fallback
    return json.dumps(response_body), usage


def invoke_chat(
    messages: list[ChatMessage],
    model_id: str | None = None,
    max_tokens: int = 1024,
    temperature: float = 0.7,
    system_prompt: str | None = None,
) -> tuple[str, str, dict | None]:
    """
    Invoke Bedrock and return (content, model_id, usage).
    Raises BedrockError on failure.
    """
    resolved_model = model_id or runtime_state.get_model_id()
    body = _build_request_body(
        resolved_model, messages, max_tokens, temperature, system_prompt
    )

    try:
        client = _get_client()
        response = client.invoke_model(
            modelId=resolved_model,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )
        response_body = json.loads(response["body"].read())
        text, usage = _parse_response(resolved_model, response_body)
        return text, resolved_model, usage
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "Unknown")
        error_msg = exc.response.get("Error", {}).get("Message", str(exc))
        logger.error("Bedrock ClientError [%s]: %s", error_code, error_msg)
        status = 403 if error_code in ("AccessDeniedException", "UnauthorizedException") else 502
        raise BedrockError(f"Bedrock error ({error_code}): {error_msg}", status_code=status) from exc
    except BotoCoreError as exc:
        logger.error("BotoCoreError: %s", exc)
        raise BedrockError(f"AWS connection error: {exc}", status_code=502) from exc
    except Exception as exc:
        logger.error("Unexpected Bedrock error: %s", exc)
        raise BedrockError(f"Unexpected error: {exc}", status_code=500) from exc
