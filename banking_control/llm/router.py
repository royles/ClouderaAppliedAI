from __future__ import annotations

import sqlite3
from collections.abc import Iterator

from banking_control.llm.admin_store import load_llm_config
from banking_control.llm.bedrock_client import is_bedrock_configured, stream_bedrock_chat
from banking_control.llm.errors import LLMError
from banking_control.llm.openai_compat import is_openai_configured, stream_openai_chat


def get_active_provider(conn: sqlite3.Connection) -> str:
    return load_llm_config(conn).provider_type


def is_llm_configured(conn: sqlite3.Connection) -> bool:
    cfg = load_llm_config(conn)
    if cfg.provider_type == "openai_compatible":
        return is_openai_configured(cfg)
    return is_bedrock_configured(cfg)


def stream_text_chunks(
    conn: sqlite3.Connection,
    *,
    system_prompt: str,
    user_prompt: str,
) -> Iterator[str]:
    cfg = load_llm_config(conn)
    if cfg.provider_type == "openai_compatible":
        yield from stream_openai_chat(
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            config=cfg,
        )
        return
    if not is_bedrock_configured(cfg):
        raise LLMError("Bedrock is not configured", status_code=503)
    yield from stream_bedrock_chat(
        system=system_prompt,
        messages=[{"role": "user", "content": [{"type": "text", "text": user_prompt}]}],
        admin=cfg,
    )
