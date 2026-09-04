"""Pydantic schemas for API request/response bodies."""

from typing import Literal

from pydantic import BaseModel, Field


ProviderType = Literal["bedrock", "local"]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"] = "user"
    content: str = Field(..., min_length=1, max_length=32000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., min_length=1)
    model_id: str | None = None
    max_tokens: int = Field(default=1024, ge=1, le=8192)
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    system_prompt: str | None = Field(default=None, max_length=8000)


class ChatResponse(BaseModel):
    content: str
    model_id: str
    provider: ProviderType
    usage: dict | None = None


class ModelInfo(BaseModel):
    model_id: str
    provider: str
    display_name: str


class ConfigUpdate(BaseModel):
    provider: ProviderType | None = None
    model_id: str | None = None
    aws_region: str | None = None
    local_endpoint_url: str | None = None
    local_model_id: str | None = None
    local_api_token: str | None = None
    clear_local_api_token: bool = False


class PublicConfig(BaseModel):
    """Client-safe configuration — no secrets."""

    provider: ProviderType
    model_id: str
    aws_region: str
    aws_configured: bool
    credential_source: str
    local_endpoint_url: str
    local_model_id: str
    local_configured: bool
    local_token_configured: bool
    chat_ready: bool


class HealthResponse(BaseModel):
    status: str
    provider: ProviderType
    aws_configured: bool
    local_configured: bool
    chat_ready: bool
