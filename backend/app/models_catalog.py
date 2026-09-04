"""Curated Bedrock models for the playground."""

from app.schemas import ModelInfo

# Common on-demand Bedrock models — extend as needed.
AVAILABLE_MODELS: list[ModelInfo] = [
    ModelInfo(
        model_id="anthropic.claude-3-haiku-20240307-v1:0",
        provider="Anthropic",
        display_name="Claude 3 Haiku",
    ),
    ModelInfo(
        model_id="anthropic.claude-3-sonnet-20240229-v1:0",
        provider="Anthropic",
        display_name="Claude 3 Sonnet",
    ),
    ModelInfo(
        model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
        provider="Anthropic",
        display_name="Claude 3.5 Sonnet",
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

MODEL_IDS = {m.model_id for m in AVAILABLE_MODELS}


def get_model_info(model_id: str) -> ModelInfo | None:
    for model in AVAILABLE_MODELS:
        if model.model_id == model_id:
            return model
    return None
