"""Minimal Bedrock Runtime invoke for structured insight generation."""

from __future__ import annotations

import json
import logging
from typing import Any

from customer360.bedrock.config import get_bedrock_settings
from customer360.llm_provider import effective_bedrock_settings

logger = logging.getLogger(__name__)

GEO_SCOPES = frozenset({"global", "eu", "us", "au"})
GEO_CLIENT_REGIONS: dict[str, str] = {
    "global": "us-east-1",
    "us": "us-east-1",
    "eu": "eu-west-1",
    "au": "ap-southeast-2",
}


class BedrockError(Exception):
    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code


def resolve_client_region(ui_region: str) -> str:
    return GEO_CLIENT_REGIONS.get(ui_region, ui_region)


def resolve_inference_model_id(base_model_id: str, ui_region: str) -> str:
    if any(base_model_id.startswith(f"{scope}.") for scope in GEO_SCOPES):
        return base_model_id
    if ui_region in GEO_SCOPES:
        return f"{ui_region}.{base_model_id}"
    return base_model_id


def _normalize_model_id(model_id: str) -> str:
    for prefix in ("global.", "eu.", "us.", "au."):
        if model_id.startswith(prefix):
            return model_id[len(prefix) :]
    return model_id


def _anthropic_disallows_sampling(model_id: str) -> bool:
    lowered = _normalize_model_id(model_id).lower()
    return any(
        marker in lowered
        for marker in (
            "claude-sonnet-5",
            "claude-opus-5",
            "claude-opus-4-7",
            "claude-opus-4-8",
        )
    )


def is_bedrock_configured() -> bool:
    settings = get_bedrock_settings()  # env / instance profile only
    if settings.has_explicit_credentials():
        return True
    try:
        import boto3
    except ImportError:
        return False
    try:
        region = resolve_client_region(settings.bedrock_region)
        session = boto3.Session(region_name=region)
        credentials = session.get_credentials()
        return credentials is not None and credentials.access_key is not None
    except Exception:
        return False


def _build_session():
    import boto3

    settings = effective_bedrock_settings()
    region = resolve_client_region(settings.bedrock_region)
    kwargs: dict[str, Any] = {"region_name": region}
    if settings.has_explicit_credentials():
        kwargs["aws_access_key_id"] = settings.aws_access_key_id
        kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
        if settings.aws_session_token:
            kwargs["aws_session_token"] = settings.aws_session_token
    return boto3.Session(**kwargs), region


def _format_anthropic_body(
    *,
    user_text: str,
    system_prompt: str,
    max_tokens: int,
    temperature: float,
    model_id: str,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": [{"type": "text", "text": user_text}]}],
        "system": [{"type": "text", "text": system_prompt}],
    }
    if not _anthropic_disallows_sampling(model_id):
        body["temperature"] = temperature
    return body


def _parse_anthropic_response(response_body: dict[str, Any]) -> str:
    content = response_body.get("content", [])
    if content and isinstance(content[0], dict):
        return str(content[0].get("text", ""))
    return json.dumps(response_body)


def _invoke_model(client, inference_model: str, body: dict[str, Any]) -> dict[str, Any]:
    response = client.invoke_model(
        modelId=inference_model,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json",
    )
    return json.loads(response["body"].read())


def invoke_text(*, system_prompt: str, user_prompt: str) -> tuple[str, str]:
    """
    Invoke Bedrock and return (text, catalog_model_id).
    Raises BedrockError on failure.
    """
    try:
        from botocore.exceptions import BotoCoreError, ClientError
    except ImportError as exc:
        raise BedrockError("boto3 is not installed", status_code=503) from exc

    settings = effective_bedrock_settings()
    catalog_model = settings.model_id
    ui_region = settings.bedrock_region
    inference_model = resolve_inference_model_id(catalog_model, ui_region)
    body = _format_anthropic_body(
        user_text=user_prompt,
        system_prompt=system_prompt,
        max_tokens=settings.max_tokens,
        temperature=settings.temperature,
        model_id=catalog_model,
    )

    try:
        session, client_region = _build_session()
        client = session.client("bedrock-runtime", region_name=client_region)
        logger.info(
            "Bedrock insights invoke region=%s inference_model=%s",
            client_region,
            inference_model,
        )
        try:
            response_body = _invoke_model(client, inference_model, body)
        except ClientError as first_exc:
            error_code = first_exc.response.get("Error", {}).get("Code", "Unknown")
            if (
                error_code == "ValidationException"
                and inference_model != catalog_model
                and ui_region in GEO_SCOPES
            ):
                logger.info(
                    "Retrying Bedrock with base model id %s after ValidationException",
                    catalog_model,
                )
                response_body = _invoke_model(client, catalog_model, body)
            else:
                raise
        if not catalog_model.startswith("anthropic."):
            logger.warning(
                "Non-Anthropic model %s requested; using Anthropic request format",
                catalog_model,
            )
        return _parse_anthropic_response(response_body), catalog_model
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "Unknown")
        error_msg = exc.response.get("Error", {}).get("Message", str(exc))
        logger.error("Bedrock ClientError [%s]: %s", error_code, error_msg)
        status = 403 if error_code in ("AccessDeniedException", "UnauthorizedException") else 502
        raise BedrockError(f"Bedrock error ({error_code}): {error_msg}", status_code=status) from exc
    except BotoCoreError as exc:
        logger.error("BotoCoreError: %s", exc)
        raise BedrockError(f"AWS connection error: {exc}", status_code=502) from exc
