"""Bedrock configuration from environment (credentials never logged or returned)."""

from __future__ import annotations

import os
from dataclasses import dataclass, replace
from functools import lru_cache
from typing import Any


@dataclass(frozen=True)
class BedrockSettings:
    aws_access_key_id: str | None
    aws_secret_access_key: str | None
    aws_session_token: str | None
    aws_region: str
    bedrock_region: str
    model_id: str
    max_tokens: int
    temperature: float

    def has_explicit_credentials(self) -> bool:
        return bool(self.aws_access_key_id and self.aws_secret_access_key)


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return float(raw)
    except ValueError:
        return default


@lru_cache
def get_bedrock_settings() -> BedrockSettings:
    aws_region = os.environ.get("AWS_REGION", "us-east-1").strip() or "us-east-1"
    bedrock_region = (
        os.environ.get("CUSTOMER360_BEDROCK_REGION", aws_region).strip() or aws_region
    )
    model_id = (
        os.environ.get(
            "CUSTOMER360_BEDROCK_MODEL_ID",
            "anthropic.claude-haiku-4-5-20251001-v1:0",
        ).strip()
        or "anthropic.claude-haiku-4-5-20251001-v1:0"
    )
    return BedrockSettings(
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        aws_session_token=os.environ.get("AWS_SESSION_TOKEN"),
        aws_region=aws_region,
        bedrock_region=bedrock_region,
        model_id=model_id,
        max_tokens=_env_int("CUSTOMER360_BEDROCK_MAX_TOKENS", 900),
        temperature=_env_float("CUSTOMER360_BEDROCK_TEMPERATURE", 0.35),
    )


def effective_bedrock_settings() -> BedrockSettings:
    """Environment defaults with optional admin overrides when Bedrock is active."""
    base = get_bedrock_settings()
    try:
        from customer360.llm_provider import load_llm_config

        admin = load_llm_config()
    except Exception:
        return base
    if admin.provider_type != "bedrock":
        return base
    kwargs: dict[str, Any] = {}
    if admin.bedrock_region and admin.bedrock_region.strip():
        kwargs["bedrock_region"] = admin.bedrock_region.strip()
    if admin.bedrock_model_id and admin.bedrock_model_id.strip():
        kwargs["model_id"] = admin.bedrock_model_id.strip()
    if admin.bedrock_max_tokens is not None and admin.bedrock_max_tokens > 0:
        kwargs["max_tokens"] = int(admin.bedrock_max_tokens)
    if admin.bedrock_temperature is not None:
        kwargs["temperature"] = float(admin.bedrock_temperature)
    if not kwargs:
        return base
    return replace(base, **kwargs)
