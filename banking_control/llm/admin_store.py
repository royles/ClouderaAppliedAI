from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Literal

LlmProviderType = Literal["bedrock", "openai_compatible"]


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

    @property
    def openai_api_token_set(self) -> bool:
        return bool(self.openai_api_token and str(self.openai_api_token).strip())


def ensure_admin_llm_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS APP_ADMIN_LLM (
          id INTEGER PRIMARY KEY CHECK (id = 1),
          provider_type TEXT NOT NULL DEFAULT 'bedrock',
          bedrock_region TEXT,
          bedrock_model_id TEXT,
          bedrock_max_tokens INTEGER,
          bedrock_temperature REAL,
          openai_base_url TEXT,
          openai_model_id TEXT,
          openai_api_token TEXT,
          updated_at TEXT
        )
        """
    )
    conn.commit()


def _row_to_config(row: sqlite3.Row | None) -> LlmProviderConfig:
    if row is None:
        return LlmProviderConfig(updated_at=datetime.now(timezone.utc).isoformat())
    provider = (row["provider_type"] or "bedrock").strip().lower()
    if provider not in ("bedrock", "openai_compatible"):
        provider = "bedrock"
    return LlmProviderConfig(
        provider_type=provider,  # type: ignore[arg-type]
        bedrock_region=row["bedrock_region"],
        bedrock_model_id=row["bedrock_model_id"],
        bedrock_max_tokens=row["bedrock_max_tokens"],
        bedrock_temperature=row["bedrock_temperature"],
        openai_base_url=row["openai_base_url"],
        openai_model_id=row["openai_model_id"],
        openai_api_token=row["openai_api_token"],
        updated_at=row["updated_at"],
    )


def load_llm_config(conn: sqlite3.Connection) -> LlmProviderConfig:
    ensure_admin_llm_schema(conn)
    row = conn.execute("SELECT * FROM APP_ADMIN_LLM WHERE id = 1").fetchone()
    if row is None:
        cfg = LlmProviderConfig()
        save_llm_config(conn, cfg)
        return cfg
    return _row_to_config(row)


def save_llm_config(conn: sqlite3.Connection, config: LlmProviderConfig) -> LlmProviderConfig:
    ensure_admin_llm_schema(conn)
    existing = conn.execute(
        "SELECT openai_api_token FROM APP_ADMIN_LLM WHERE id = 1"
    ).fetchone()
    token = config.openai_api_token
    if existing and (token is None or token == ""):
        token = existing["openai_api_token"]
    updated_at = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO APP_ADMIN_LLM (
          id, provider_type, bedrock_region, bedrock_model_id,
          bedrock_max_tokens, bedrock_temperature,
          openai_base_url, openai_model_id, openai_api_token, updated_at
        ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          provider_type = excluded.provider_type,
          bedrock_region = excluded.bedrock_region,
          bedrock_model_id = excluded.bedrock_model_id,
          bedrock_max_tokens = excluded.bedrock_max_tokens,
          bedrock_temperature = excluded.bedrock_temperature,
          openai_base_url = excluded.openai_base_url,
          openai_model_id = excluded.openai_model_id,
          openai_api_token = excluded.openai_api_token,
          updated_at = excluded.updated_at
        """,
        (
            config.provider_type,
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
    return _row_to_config(
        conn.execute("SELECT * FROM APP_ADMIN_LLM WHERE id = 1").fetchone()
    )


def public_config_dict(config: LlmProviderConfig) -> dict[str, Any]:
    data = asdict(config)
    data["openai_api_token"] = None
    data["openai_api_token_set"] = config.openai_api_token_set
    return data
