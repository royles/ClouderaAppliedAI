from __future__ import annotations

from typing import Any

from banking_control.tools.models import ControlTool
from banking_control.tools.schemas.base import (
    BASE_INPUT_SCHEMA,
    BASE_OUTPUT_SCHEMA,
    SPECIALIZED_INPUTS,
)


class DefaultSchemaProvider:
    priority = 0

    def matches(self, tool: ControlTool) -> bool:
        return True

    def input_schema(self, tool: ControlTool) -> dict[str, Any]:
        domain_ctx = {
            "type": "object",
            "properties": {"entity_id": {"type": "string"}, "notes": {"type": "string"}},
            "additionalProperties": True,
        }
        return {
            **BASE_INPUT_SCHEMA,
            "properties": {
                **BASE_INPUT_SCHEMA["properties"],
                "context": {**domain_ctx, "description": f"Optional {tool.domain} context."},
            },
        }

    def output_schema(self, tool: ControlTool) -> dict[str, Any]:
        return BASE_OUTPUT_SCHEMA


class SimilarityKeySchemaProvider:
    priority = 20

    def matches(self, tool: ControlTool) -> bool:
        return bool(tool.similarity_key and tool.similarity_key in SPECIALIZED_INPUTS)

    def input_schema(self, tool: ControlTool) -> dict[str, Any]:
        assert tool.similarity_key is not None
        return SPECIALIZED_INPUTS[tool.similarity_key]

    def output_schema(self, tool: ControlTool) -> dict[str, Any]:
        return BASE_OUTPUT_SCHEMA
