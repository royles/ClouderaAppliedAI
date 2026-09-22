"""Route text generation to the configured LLM backend."""

from __future__ import annotations

from customer360.llm.errors import LLMError
from customer360.llm.openai_compatible import invoke_openai_compatible_text
from customer360.llm_provider import get_active_provider, is_llm_configured as _is_llm_configured


def is_llm_configured() -> bool:
    return _is_llm_configured()


def invoke_text(*, system_prompt: str, user_prompt: str) -> tuple[str, str]:
    provider = get_active_provider()
    if provider == "openai_compatible":
        return invoke_openai_compatible_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

    from customer360.bedrock.client import BedrockError, invoke_text as invoke_bedrock_text

    try:
        return invoke_bedrock_text(system_prompt=system_prompt, user_prompt=user_prompt)
    except BedrockError as exc:
        raise LLMError(str(exc), status_code=exc.status_code) from exc
