"""Pydantic schemas for API request/response bodies."""

from typing import Literal

from pydantic import BaseModel, Field


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
    usage: dict | None = None


class ModelInfo(BaseModel):
    model_id: str
    provider: str
    display_name: str


class ConfigUpdate(BaseModel):
    model_id: str | None = None
    aws_region: str | None = None


class PublicConfig(BaseModel):
    """Client-safe configuration — no secrets."""

    model_id: str
    aws_region: str
    aws_configured: bool
    credential_source: str


class HealthResponse(BaseModel):
    status: str
    aws_configured: bool
