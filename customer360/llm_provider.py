"""Admin-stored LLM provider selection (Bedrock default or OpenAI-compatible HTTP)."""

from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from typing import Any, Literal

from customer360.admin_store import admin_connect, ensure_admin_schema
from customer360.bedrock.config import BedrockSettings, get_bedrock_settings as _bedrock_from_env

LlmProviderType = Literal["bedrock", "openai_compatible"]
VALID_PROVIDERS: frozenset[str] = frozenset({"bedrock", "openai_compatible"})


def normalize_provider(value: str | None) -> LlmProviderType:
    key = (value or "bedrock").strip().lower()
    if key in VALID_PROVIDERS:
        return key  # type: ignore[return-value]
    return "bedrock"


@dataclass
class LlmProviderConfig:
    provider_type: LlmProviderType = "bedrock"
    bedrock_region: str | None = None
    bedrock_model_id: str | None = None
    bedrock_max_tokens: int | None = None
    bedrock_temperature: float | None = None
    openai_base_url: str | None = None
    openai_model_id: str | None = None
    openai_api_token: str | None = None
    updated_at: str | None = None

    def openai_api_token_set(self) -> bool:
        return bool(self.openai_api_token and str(self.openai_api_token).strip())


def _row_get(row: sqlite3.Row, key: str, default=None):
    try:
        return row[key]
    except (KeyError, IndexError):
        return default


def _row_to_config(row: sqlite3.Row | None) -> LlmProviderConfig:
    if row is None:
        return LlmProviderConfig(
            provider_type="bedrock",
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
    return LlmProviderConfig(
        provider_type=normalize_provider(_row_get(row, "PROVIDER_TYPE")),
        bedrock_region=_row_get(row, "BEDROCK_REGION"),
        bedrock_model_id=_row_get(row, "BEDROCK_MODEL_ID"),
        bedrock_max_tokens=_row_get(row, "BEDROCK_MAX_TOKENS"),
        bedrock_temperature=_row_get(row, "BEDROCK_TEMPERATURE"),
        openai_base_url=_row_get(row, "OPENAI_BASE_URL"),
        openai_model_id=_row_get(row, "OPENAI_MODEL_ID"),
        openai_api_token=_row_get(row, "OPENAI_API_TOKEN"),
        updated_at=_row_get(row, "UPDATED_AT"),
    )


def load_llm_config(conn: sqlite3.Connection | None = None) -> LlmProviderConfig:
    own = conn is None
    if own:
        conn = admin_connect()
    else:
        ensure_admin_schema(conn)
    row = conn.execute("SELECT * FROM APP_ADMIN_LLM WHERE ID = 1").fetchone()
    if row is None:
        cfg = LlmProviderConfig(updated_at=datetime.now(timezone.utc).isoformat())
        save_llm_config(cfg, conn=conn)
        if own:
            conn.close()
        return cfg
    cfg = _row_to_config(row)
    if own:
        conn.close()
    return cfg


def save_llm_config(
    config: LlmProviderConfig,
    *,
    conn: sqlite3.Connection | None = None,
    preserve_secrets_if_empty: bool = True,
) -> LlmProviderConfig:
    own = conn is None
    if own:
        conn = admin_connect()
    else:
        ensure_admin_schema(conn)

    existing = conn.execute(
        "SELECT OPENAI_API_TOKEN FROM APP_ADMIN_LLM WHERE ID = 1"
    ).fetchone()

    token = config.openai_api_token
    if preserve_secrets_if_empty and existing:
        if token is None or token == "":
            token = existing["OPENAI_API_TOKEN"]

    updated_at = datetime.now(timezone.utc).isoformat()
    provider = normalize_provider(config.provider_type)

    conn.execute(
        """
        INSERT INTO APP_ADMIN_LLM (
            ID, PROVIDER_TYPE,
            BEDROCK_REGION, BEDROCK_MODEL_ID, BEDROCK_MAX_TOKENS, BEDROCK_TEMPERATURE,
            OPENAI_BASE_URL, OPENAI_MODEL_ID, OPENAI_API_TOKEN,
            UPDATED_AT
        ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(ID) DO UPDATE SET
            PROVIDER_TYPE = excluded.PROVIDER_TYPE,
            BEDROCK_REGION = excluded.BEDROCK_REGION,
            BEDROCK_MODEL_ID = excluded.BEDROCK_MODEL_ID,
            BEDROCK_MAX_TOKENS = excluded.BEDROCK_MAX_TOKENS,
            BEDROCK_TEMPERATURE = excluded.BEDROCK_TEMPERATURE,
            OPENAI_BASE_URL = excluded.OPENAI_BASE_URL,
            OPENAI_MODEL_ID = excluded.OPENAI_MODEL_ID,
            OPENAI_API_TOKEN = excluded.OPENAI_API_TOKEN,
            UPDATED_AT = excluded.UPDATED_AT
        """,
        (
            provider,
            config.bedrock_region,
            config.bedrock_model_id,
            config.bedrock_max_tokens,
            config.bedrock_temperature,
            config.openai_base_url,
            config.openai_model_id,
            token,
            updated_at,
        ),
    )
    conn.commit()
    saved = load_llm_config(conn=conn)
    if own:
        conn.close()
    return saved


def merge_llm_update(
    existing: LlmProviderConfig,
    updates: dict[str, Any],
    *,
    clear_openai_api_token: bool = False,
) -> LlmProviderConfig:
    data = asdict(existing)
    for key, value in updates.items():
        if key in ("openai_api_token_set", "provider_label", "updated_at"):
            continue
        if key not in data:
            continue
        if value is not None:
            data[key] = value

    if clear_openai_api_token:
        data["openai_api_token"] = None
    elif updates.get("openai_api_token"):
        data["openai_api_token"] = updates["openai_api_token"]

    data["provider_type"] = normalize_provider(data.get("provider_type"))
    return LlmProviderConfig(**data)


def config_for_api(config: LlmProviderConfig) -> dict[str, Any]:
    data = asdict(config)
    data.pop("openai_api_token", None)
    data["openai_api_token_set"] = config.openai_api_token_set()
    data["provider_label"] = provider_label(config.provider_type)
    return data


def provider_label(provider: LlmProviderType) -> str:
    if provider == "openai_compatible":
        return "OpenAI-compatible HTTP"
    return "Amazon Bedrock"


def get_active_provider() -> LlmProviderType:
    return load_llm_config().provider_type


def effective_bedrock_settings() -> BedrockSettings:
    """Env defaults with optional admin overrides when Bedrock is the active provider."""
    base = _bedrock_from_env()
    admin = load_llm_config()
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


def is_openai_compatible_configured(config: LlmProviderConfig | None = None) -> bool:
    cfg = config or load_llm_config()
    if cfg.provider_type != "openai_compatible":
        return False
    return bool(
        cfg.openai_base_url
        and cfg.openai_base_url.strip()
        and cfg.openai_model_id
        and cfg.openai_model_id.strip()
        and cfg.openai_api_token_set()
    )


def is_llm_configured() -> bool:
    admin = load_llm_config()
    if admin.provider_type == "openai_compatible":
        return is_openai_compatible_configured(admin)
    from customer360.bedrock.client import is_bedrock_configured

    return is_bedrock_configured()
