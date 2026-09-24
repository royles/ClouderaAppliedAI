from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from banking_control.tools.models import ControlTool


@runtime_checkable
class SchemaProvider(Protocol):
    """Supplies JSON Schema for tool inputs/outputs."""

    priority: int

    def matches(self, tool: ControlTool) -> bool:
        ...

    def input_schema(self, tool: ControlTool) -> dict[str, Any]:
        ...

    def output_schema(self, tool: ControlTool) -> dict[str, Any]:
        ...


@runtime_checkable
class ControlSimulator(Protocol):
    """Maps validated tool inputs to simulated control outputs."""

    priority: int

    def matches(self, tool: ControlTool) -> bool:
        ...

    def simulate(self, tool: ControlTool, inputs: dict[str, Any]) -> dict[str, Any]:
        ...


@runtime_checkable
class BankingControlPlugin(Protocol):
    """Optional bundle registered in one call."""

    name: str

    def register(self, manager: Any) -> None: ...
