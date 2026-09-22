"""Runtime context passed to every agent tool."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field

from customer360.api.segments import normalize_segment


@dataclass
class ToolContext:
    conn: sqlite3.Connection
    default_segment: str = "customers_all"
    list_context: dict | None = field(default=None)

    @property
    def segment(self) -> str:
        return normalize_segment(self.default_segment)
