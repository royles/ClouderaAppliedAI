from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ControlTool:
    """Metadata for one catalog control exposed as an LLM tool."""

    control_code: str
    control_name: str
    domain: str
    description: str
    is_golden: bool
    similarity_key: str | None

    def tool_function_name(self) -> str:
        return self.control_code.replace("-", "_")

    def to_openai_tool(self, input_schema: dict[str, Any]) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.tool_function_name(),
                "description": self.description[:1024],
                "parameters": input_schema,
            },
        }
