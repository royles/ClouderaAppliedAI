from __future__ import annotations

from typing import Any


def append_iso_date_range(
    clauses: list[str],
    params: list[Any],
    *,
    column: str,
    from_date: str | None,
    to_date: str | None,
) -> None:
    """Filter ISO date / datetime strings stored as TEXT (YYYY-MM-DD…)."""
    if from_date and from_date.strip():
        clauses.append(f"substr({column}, 1, 10) >= ?")
        params.append(from_date.strip()[:10])
    if to_date and to_date.strip():
        clauses.append(f"substr({column}, 1, 10) <= ?")
        params.append(to_date.strip()[:10])
