"""FastAPI routes for the Bedrock playground."""

import logging

from fastapi import APIRouter, HTTPException

from app.bedrock_service import BedrockError, _credential_source, is_aws_configured, invoke_chat
from app.models_catalog import AVAILABLE_MODELS, MODEL_IDS, get_model_info
from app.schemas import (
    ChatRequest,
    ChatResponse,
    ConfigUpdate,
    HealthResponse,
    ModelInfo,
    PublicConfig,
)
from app.state import runtime_state

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", aws_configured=is_aws_configured())


@router.get("/models", response_model=list[ModelInfo])
def list_models() -> list[ModelInfo]:
    return AVAILABLE_MODELS


@router.get("/config", response_model=PublicConfig)
def get_config() -> PublicConfig:
    return PublicConfig(
        model_id=runtime_state.get_model_id(),
        aws_region=runtime_state.get_region(),
        aws_configured=is_aws_configured(),
        credential_source=_credential_source(),
    )


@router.put("/config", response_model=PublicConfig)
def update_config(payload: ConfigUpdate) -> PublicConfig:
    if payload.model_id is not None:
        if payload.model_id not in MODEL_IDS:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown model_id. Choose from /api/models.",
            )
        runtime_state.set_model_id(payload.model_id)

    if payload.aws_region is not None:
        region = payload.aws_region.strip()
        if not region:
            raise HTTPException(status_code=400, detail="aws_region cannot be empty.")
        runtime_state.set_region(region)

    return get_config()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    if not is_aws_configured():
        raise HTTPException(
            status_code=503,
            detail="AWS credentials not configured. Set AWS_ACCESS_KEY_ID and "
            "AWS_SECRET_ACCESS_KEY in the backend environment, or use an IAM role.",
        )

    model_id = request.model_id or runtime_state.get_model_id()
    if request.model_id and request.model_id not in MODEL_IDS:
        raise HTTPException(status_code=400, detail="Unknown model_id.")

    try:
        content, used_model, usage = invoke_chat(
            messages=request.messages,
            model_id=model_id,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            system_prompt=request.system_prompt,
        )
    except BedrockError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    model_info = get_model_info(used_model)
    logger.info(
        "Chat completed model=%s provider=%s",
        used_model,
        model_info.provider if model_info else "unknown",
    )

    return ChatResponse(content=content, model_id=used_model, usage=usage)
