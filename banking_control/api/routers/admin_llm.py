from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from banking_control.api.deps import get_db_connection, get_tool_engine
from banking_control.llm.admin_store import (
    LlmProviderConfig,
    load_llm_config,
    public_config_dict,
    save_llm_config,
)
from banking_control.llm.bedrock_client import is_bedrock_configured
from banking_control.llm.errors import LLMError
from banking_control.llm.openai_compat import is_openai_configured
from banking_control.llm.router import stream_text_chunks
from banking_control.tools.engine import ControlToolEngine

router = APIRouter(prefix="/api/admin", tags=["admin"])


class LlmConfigUpdate(BaseModel):
    provider_type: str | None = None
    bedrock_region: str | None = None
    bedrock_model_id: str | None = None
    bedrock_max_tokens: int | None = None
    bedrock_temperature: float | None = None
    openai_base_url: str | None = None
    openai_model_id: str | None = None
    openai_api_token: str | None = None
    clear_openai_api_token: bool = False


@router.get("/llm")
def get_llm_config(conn: Any = Depends(get_db_connection)) -> dict[str, Any]:
    try:
        cfg = load_llm_config(conn)
        return public_config_dict(cfg)
    finally:
        conn.close()


@router.put("/llm")
def put_llm_config(
    body: LlmConfigUpdate,
    conn: Any = Depends(get_db_connection),
) -> dict[str, Any]:
    try:
        current = load_llm_config(conn)
        provider = (body.provider_type or current.provider_type).strip().lower()
        if provider not in ("bedrock", "openai_compatible"):
            raise HTTPException(status_code=400, detail="Invalid provider_type")
        token = current.openai_api_token
        if body.clear_openai_api_token:
            token = ""
        elif body.openai_api_token:
            token = body.openai_api_token
        updated = LlmProviderConfig(
            provider_type=provider,  # type: ignore[arg-type]
            bedrock_region=body.bedrock_region if body.bedrock_region is not None else current.bedrock_region,
            bedrock_model_id=body.bedrock_model_id if body.bedrock_model_id is not None else current.bedrock_model_id,
            bedrock_max_tokens=body.bedrock_max_tokens if body.bedrock_max_tokens is not None else current.bedrock_max_tokens,
            bedrock_temperature=body.bedrock_temperature if body.bedrock_temperature is not None else current.bedrock_temperature,
            openai_base_url=body.openai_base_url if body.openai_base_url is not None else current.openai_base_url,
            openai_model_id=body.openai_model_id if body.openai_model_id is not None else current.openai_model_id,
            openai_api_token=token,
        )
        saved = save_llm_config(conn, updated)
        return public_config_dict(saved)
    finally:
        conn.close()


@router.post("/llm/test")
def test_llm_config(
    body: LlmConfigUpdate | None = None,
    conn: Any = Depends(get_db_connection),
) -> dict[str, Any]:
    try:
        cfg = load_llm_config(conn)
        if body and body.provider_type:
            cfg = save_llm_config(
                conn,
                LlmProviderConfig(
                    provider_type=body.provider_type,  # type: ignore[arg-type]
                    bedrock_region=body.bedrock_region or cfg.bedrock_region,
                    bedrock_model_id=body.bedrock_model_id or cfg.bedrock_model_id,
                    bedrock_max_tokens=body.bedrock_max_tokens or cfg.bedrock_max_tokens,
                    bedrock_temperature=body.bedrock_temperature if body.bedrock_temperature is not None else cfg.bedrock_temperature,
                    openai_base_url=body.openai_base_url or cfg.openai_base_url,
                    openai_model_id=body.openai_model_id or cfg.openai_model_id,
                    openai_api_token=body.openai_api_token or cfg.openai_api_token,
                ),
            )
        if cfg.provider_type == "openai_compatible":
            if not is_openai_configured(cfg):
                return {"ok": False, "message": "Local LLM settings incomplete (URL, model, token)."}
        elif not is_bedrock_configured(cfg):
            return {"ok": False, "message": "Bedrock is not configured (AWS credentials or region)."}
        chunks = list(
            stream_text_chunks(
                conn,
                system_prompt="You are a concise assistant.",
                user_prompt='Reply with exactly: "Banking Control LLM connection OK."',
            )
        )
        text = "".join(chunks).strip()
        return {"ok": True, "message": "Connection successful", "detail": text[:200]}
    except LLMError as exc:
        return {"ok": False, "message": str(exc)}
    finally:
        conn.close()


@router.get("/assistant/status")
def assistant_status(
    conn: Any = Depends(get_db_connection),
    engine: ControlToolEngine = Depends(get_tool_engine),
) -> dict[str, Any]:
    try:
        cfg = load_llm_config(conn)
        return {
            "llm_configured": (
                (cfg.provider_type == "openai_compatible" and is_openai_configured(cfg))
                or (cfg.provider_type == "bedrock" and is_bedrock_configured(cfg))
            ),
            "provider": cfg.provider_type,
            "control_tools_registered": len(engine.list_tools()),
        }
    finally:
        conn.close()
