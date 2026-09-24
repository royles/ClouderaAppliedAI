from __future__ import annotations

from functools import lru_cache

from banking_control.catalog import ControlDefinition, build_control_catalog
from banking_control.tools.models import ControlTool


class ToolRegistry:
    """Read-only catalog of control tools (metadata only; schemas via plugins)."""

    def __init__(self, controls: list[ControlDefinition] | None = None) -> None:
        self._controls = controls or build_control_catalog()

    @classmethod
    def default(cls) -> ToolRegistry:
        return cls()

    @classmethod
    @lru_cache(maxsize=1)
    def cached(cls) -> ToolRegistry:
        return cls()

    def list_tools(self, *, golden_only: bool = False) -> list[ControlTool]:
        tools = [self._to_tool(c) for c in self._controls]
        if golden_only:
            tools = [t for t in tools if t.is_golden]
        return sorted(tools, key=lambda t: (t.domain, t.control_code))

    def get_tool(self, control_code: str) -> ControlTool | None:
        key = control_code.strip()
        by_code = {t.control_code: t for t in self.list_tools()}
        if key in by_code:
            return by_code[key]
        alt = key.replace("_", "-").upper()
        return by_code.get(alt)

    @staticmethod
    def _to_tool(ctrl: ControlDefinition) -> ControlTool:
        return ControlTool(
            control_code=ctrl.control_code,
            control_name=ctrl.control_name,
            domain=ctrl.domain,
            description=ctrl.description,
            is_golden=ctrl.is_golden,
            similarity_key=ctrl.similarity_key,
        )


def list_tools(*, golden_only: bool = False) -> list[ControlTool]:
    return ToolRegistry.cached().list_tools(golden_only=golden_only)


def get_tool(control_code: str) -> ControlTool | None:
    return ToolRegistry.cached().get_tool(control_code)
