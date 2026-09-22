"""Modular LLM invocation (Bedrock or OpenAI-compatible)."""

from customer360.llm.errors import LLMError
from customer360.llm.router import invoke_text, is_llm_configured

__all__ = ["LLMError", "invoke_text", "is_llm_configured"]
