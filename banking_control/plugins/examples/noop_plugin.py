"""Example plugin template — copy and adapt in your own package."""

from __future__ import annotations

from typing import Any

from banking_control.plugins.manager import PluginManager
from banking_control.tools.models import ControlTool


class EchoSimulator:
    """Passes through context as metrics (demo only)."""

    priority = 5

    def matches(self, tool: ControlTool) -> bool:
        return tool.control_code == "REG-001"

    def simulate(self, tool: ControlTool, inputs: dict[str, Any]) -> dict[str, Any]:
        return {
            "control_code": tool.control_code,
            "status": "Effective",
            "summary": "Echo simulator plugin response.",
            "findings": [],
            "metrics": {"echo": 1.0},
            "simulated": True,
        }


class ExamplePlugin:
    name = "example-echo"

    def register(self, manager: PluginManager) -> None:
        manager.register_simulator(EchoSimulator())


def register(manager: PluginManager) -> None:
    ExamplePlugin().register(manager)
