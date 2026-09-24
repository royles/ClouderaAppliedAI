from __future__ import annotations

from typing import Any

from banking_control.plugins.manager import PluginManager
from banking_control.tools.models import ControlTool
from banking_control.tools.registry import ToolRegistry

try:
    import jsonschema

    _HAS_JSONSCHEMA = True
except ImportError:  # pragma: no cover
    _HAS_JSONSCHEMA = False


class ToolValidationError(ValueError):
    pass


class ControlToolEngine:
    """Orchestrates schema resolution, validation, and pluggable simulation."""

    def __init__(
        self,
        plugin_manager: PluginManager,
        registry: ToolRegistry | None = None,
    ) -> None:
        self._plugins = plugin_manager
        self._registry = registry or ToolRegistry.default()

    @classmethod
    def with_builtins(cls) -> ControlToolEngine:
        return cls(PluginManager.with_builtins())

    def list_tools(self, *, golden_only: bool = False) -> list[ControlTool]:
        return self._registry.list_tools(golden_only=golden_only)

    def get_tool(self, control_code: str) -> ControlTool | None:
        return self._registry.get_tool(control_code)

    def describe_tool(self, control_code: str) -> dict[str, Any]:
        tool = self._require_tool(control_code)
        return {
            "control_code": tool.control_code,
            "control_name": tool.control_name,
            "domain": tool.domain,
            "description": tool.description,
            "is_golden": tool.is_golden,
            "similarity_key": tool.similarity_key,
            "input_schema": self._plugins.resolve_input_schema(tool),
            "output_schema": self._plugins.resolve_output_schema(tool),
            "openai_tool": tool.to_openai_tool(self._plugins.resolve_input_schema(tool)),
        }

    def invoke(self, control_code: str, inputs: dict[str, Any]) -> dict[str, Any]:
        tool = self._require_tool(control_code)
        input_schema = self._plugins.resolve_input_schema(tool)
        self._validate(input_schema, inputs)
        simulator = self._plugins.resolve_simulator(tool)
        outputs = simulator.simulate(tool, inputs)
        output_schema = self._plugins.resolve_output_schema(tool)
        self._validate(output_schema, outputs, label="output")
        return {"control_code": tool.control_code, "inputs": inputs, "outputs": outputs}

    def _require_tool(self, control_code: str) -> ControlTool:
        tool = self.get_tool(control_code)
        if tool is None:
            raise ToolValidationError(f"Unknown control tool: {control_code}")
        return tool

    def _validate(self, schema: dict[str, Any], payload: dict[str, Any], *, label: str = "input") -> None:
        if not _HAS_JSONSCHEMA:
            if label == "input" and "business_unit_code" not in payload:
                raise ToolValidationError("business_unit_code is required")
            return
        try:
            jsonschema.validate(instance=payload, schema=schema)
        except jsonschema.ValidationError as exc:
            raise ToolValidationError(f"{label} validation failed: {exc.message}") from exc
