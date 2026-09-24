from __future__ import annotations

from typing import Any

from banking_control.plugins.protocols import ControlSimulator, SchemaProvider
from banking_control.tools.models import ControlTool


class PluginManager:
    """Central registry for pluggable schema providers and simulators."""

    def __init__(self) -> None:
        self._schema_providers: list[SchemaProvider] = []
        self._simulators: list[ControlSimulator] = []

    def register_schema_provider(self, provider: SchemaProvider) -> None:
        self._schema_providers.append(provider)
        self._schema_providers.sort(key=lambda p: p.priority, reverse=True)

    def register_simulator(self, simulator: ControlSimulator) -> None:
        self._simulators.append(simulator)
        self._simulators.sort(key=lambda s: s.priority, reverse=True)

    def register_plugin(self, plugin: Any) -> None:
        """Register a plugin object exposing ``register(manager)``."""
        plugin.register(self)

    def resolve_input_schema(self, tool: ControlTool) -> dict[str, Any]:
        for provider in self._schema_providers:
            if provider.matches(tool):
                return provider.input_schema(tool)
        raise RuntimeError(f"No schema provider matched control {tool.control_code}")

    def resolve_output_schema(self, tool: ControlTool) -> dict[str, Any]:
        for provider in self._schema_providers:
            if provider.matches(tool):
                return provider.output_schema(tool)
        raise RuntimeError(f"No schema provider matched control {tool.control_code}")

    def resolve_simulator(self, tool: ControlTool) -> ControlSimulator:
        for simulator in self._simulators:
            if simulator.matches(tool):
                return simulator
        raise RuntimeError(f"No simulator matched control {tool.control_code}")

    def registered_schema_providers(self) -> list[str]:
        return [type(p).__name__ for p in self._schema_providers]

    def registered_simulators(self) -> list[str]:
        return [type(s).__name__ for s in self._simulators]

    @classmethod
    def with_builtins(cls) -> PluginManager:
        from banking_control.plugins.loaders import load_all_plugins

        manager = cls()
        load_all_plugins(manager)
        return manager
