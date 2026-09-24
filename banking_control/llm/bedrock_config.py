from __future__ import annotations

import os
from dataclasses import dataclass, replace
from functools import lru_cache

from banking_control.llm.admin_store import LlmProviderConfig


@dataclass(frozen=True)
class BedrockSettings:
    aws_access_key_id: str | None
    aws_secret_access_key: str | None
    aws_session_token: str | None
    bedrock_region: str
    model_id: str
    max_tokens: int
    temperature: float

    def has_explicit_credentials(self) -> bool:
        return bool(self.aws_access_key_id and self.aws_secret_access_key)


GEO_CLIENT_REGIONS = {"global": "us-east-1", "us": "us-east-1", "eu": "eu-west-1", "au": "ap-southeast-2"}


@lru_cache
def env_bedrock_settings() -> BedrockSettings:
    region = os.environ.get("BANKING_CONTROL_BEDROCK_REGION") or os.environ.get(
        "AWS_REGION", "eu-west-1"
    )
    model = os.environ.get(
        "BANKING_CONTROL_BEDROCK_MODEL_ID",
        "anthropic.claude-haiku-4-5-20251001-v1:0",
    )
    return BedrockSettings(
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        aws_session_token=os.environ.get("AWS_SESSION_TOKEN"),
        bedrock_region=region.strip() or "eu-west-1",
        model_id=model.strip(),
        max_tokens=int(os.environ.get("BANKING_CONTROL_BEDROCK_MAX_TOKENS", "900")),
        temperature=float(os.environ.get("BANKING_CONTROL_BEDROCK_TEMPERATURE", "0.35")),
    )


def effective_bedrock_settings(admin: LlmProviderConfig | None = None) -> BedrockSettings:
    base = env_bedrock_settings()
    if admin is None:
        return base
    return replace(
        base,
        bedrock_region=(admin.bedrock_region or base.bedrock_region).strip(),
        model_id=(admin.bedrock_model_id or base.model_id).strip(),
        max_tokens=admin.bedrock_max_tokens or base.max_tokens,
        temperature=(
            admin.bedrock_temperature if admin.bedrock_temperature is not None else base.temperature
        ),
    )


def resolve_client_region(ui_region: str) -> str:
    return GEO_CLIENT_REGIONS.get(ui_region, ui_region)


def resolve_inference_model_id(model_id: str, ui_region: str) -> str:
    if model_id.startswith(("global.", "eu.", "us.", "au.")):
        return model_id
    if ui_region in GEO_CLIENT_REGIONS:
        return f"{ui_region}.{model_id}"
    return model_id
