"""LLM-callable control tools."""

from banking_control.tools.models import ControlTool
from banking_control.tools.registry import get_tool, list_tools

__all__ = ["ControlTool", "get_tool", "list_tools", "get_engine", "simulate_control"]


def get_engine():
    from banking_control.tools.engine import ControlToolEngine

    return ControlToolEngine.with_builtins()


def simulate_control(control_code: str, inputs: dict) -> dict:
    result = get_engine().invoke(control_code, inputs)
    return result["outputs"]
