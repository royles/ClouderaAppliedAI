"""Curated Bedrock models for the playground (Active models only)."""

import logging
from functools import lru_cache

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.schemas import ModelInfo
from app.state import runtime_state

logger = logging.getLogger(__name__)

# Curated list — exclude EOL/Legacy IDs (see AWS Bedrock model lifecycle docs).
AVAILABLE_MODELS: list[ModelInfo] = [
    ModelInfo(
        model_id="anthropic.claude-haiku-4-5-20251001-v1:0",
        provider="Anthropic",
        display_name="Claude Haiku 4.5",
    ),
    ModelInfo(
        model_id="anthropic.claude-sonnet-4-5-20250929-v1:0",
        provider="Anthropic",
        display_name="Claude Sonnet 4.5",
    ),
    ModelInfo(
        model_id="amazon.nova-lite-v1:0",
        provider="Amazon",
        display_name="Nova Lite",
    ),
    ModelInfo(
        model_id="amazon.nova-micro-v1:0",
        provider="Amazon",
        display_name="Nova Micro",
    ),
    ModelInfo(
        model_id="amazon.nova-pro-v1:0",
        provider="Amazon",
        display_name="Nova Pro",
    ),
    ModelInfo(
        model_id="amazon.titan-text-express-v1",
        provider="Amazon",
        display_name="Titan Text Express",
    ),
    ModelInfo(
        model_id="amazon.titan-text-lite-v1",
        provider="Amazon",
        display_name="Titan Text Lite",
    ),
    ModelInfo(
        model_id="meta.llama3-8b-instruct-v1:0",
        provider="Meta",
        display_name="Llama 3 8B Instruct",
    ),
    ModelInfo(
        model_id="meta.llama3-70b-instruct-v1:0",
        provider="Meta",
        display_name="Llama 3 70B Instruct",
    ),
    ModelInfo(
        model_id="mistral.mistral-7b-instruct-v0:2",
        provider="Mistral",
        display_name="Mistral 7B Instruct",
    ),
    ModelInfo(
        model_id="mistral.mixtral-8x7b-instruct-v0:1",
        provider="Mistral",
        display_name="Mixtral 8x7B Instruct",
    ),
]

# Hard blocklist: models past EOL or in Legacy on Bedrock (Sep 2026 lifecycle).
EOL_OR_LEGACY_MODEL_IDS = {
    "anthropic.claude-3-haiku-20240307-v1:0",
    "anthropic.claude-3-sonnet-20240229-v1:0",
    "anthropic.claude-3-5-sonnet-20240620-v1:0",
    "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "anthropic.claude-sonnet-4-20250514-v1:0",
}


@lru_cache(maxsize=8)
def _active_bedrock_model_ids(region: str) -> frozenset[str] | None:
    """Return ACTIVE on-demand model IDs from Bedrock, or None if lookup fails."""
    try:
        client = boto3.client("bedrock", region_name=region)
        response = client.list_foundation_models(byInferenceType="ON_DEMAND")
        active = {
            summary["modelId"]
            for summary in response.get("modelSummaries", [])
            if summary.get("modelLifecycle", {}).get("status") == "ACTIVE"
        }
        return frozenset(active) if active else None
    except (ClientError, BotoCoreError, Exception) as exc:
        logger.debug("Bedrock model lifecycle lookup failed: %s", exc)
        return None


def list_available_models() -> list[ModelInfo]:
    """Curated models that are not EOL/Legacy, filtered by Bedrock when possible."""
    region = runtime_state.get_region()
    active_ids = _active_bedrock_model_ids(region)

    models: list[ModelInfo] = []
    for model in AVAILABLE_MODELS:
        if model.model_id in EOL_OR_LEGACY_MODEL_IDS:
            continue
        if active_ids is not None and model.model_id not in active_ids:
            continue
        models.append(model)
    return models


def allowed_model_ids() -> set[str]:
    return {m.model_id for m in list_available_models()}


def get_model_info(model_id: str) -> ModelInfo | None:
    for model in list_available_models():
        if model.model_id == model_id:
            return model
    return None
