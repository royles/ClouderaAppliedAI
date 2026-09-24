"""Executive copilot tools (import side-effects register handlers)."""

from customer360.agent.tools import benchmarks as _benchmarks  # noqa: F401
from customer360.agent.tools import cohort as _cohort  # noqa: F401
from customer360.agent.tools import customers as _customers  # noqa: F401
from customer360.agent.tools import engagement as _engagement  # noqa: F401
from customer360.agent.tools import freshness as _freshness  # noqa: F401
from customer360.agent.tools import meta as _meta  # noqa: F401
from customer360.agent.tools import overview as _overview  # noqa: F401
from customer360.agent.tools import portfolio as _portfolio  # noqa: F401
from customer360.agent.tools import products as _products  # noqa: F401
from customer360.agent.tools import retention as _retention  # noqa: F401
from customer360.agent.tools.context import ToolContext
from customer360.agent.tools.registry import (
    bedrock_tool_definitions,
    execute_tool,
    registered_tool_names,
)

__all__ = [
    "ToolContext",
    "bedrock_tool_definitions",
    "execute_tool",
    "registered_tool_names",
]
