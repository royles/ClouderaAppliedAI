from __future__ import annotations

import os
from pathlib import Path


def project_root() -> Path:
    env = os.environ.get("CDSW_PROJECT") or os.environ.get("BANKING_CONTROL_PROJECT")
    if env:
        return Path(env).resolve()
    here = Path(__file__).resolve().parent.parent
    return here


def _unique_roots() -> list[Path]:
    """Directories to search for ``data/schema.sql`` (CDSW subfolder layouts)."""
    seeds: list[Path] = [project_root(), Path(__file__).resolve().parent.parent]
    roots: list[Path] = []
    seen: set[Path] = set()
    for seed in seeds:
        resolved = seed.resolve()
        candidates = [resolved, *resolved.parents]
        for candidate in candidates:
            if candidate not in seen:
                seen.add(candidate)
                roots.append(candidate)
    return roots


def default_schema_path() -> Path:
    override = os.environ.get("BANKING_CONTROL_SCHEMA_PATH")
    if override:
        return Path(override).expanduser().resolve()

    data_override = os.environ.get("BANKING_CONTROL_DATA_DIR")
    if data_override:
        return Path(data_override).expanduser().resolve() / "schema.sql"

    for root in _unique_roots():
        candidate = root / "data" / "schema.sql"
        if candidate.is_file():
            return candidate

    return project_root() / "data" / "schema.sql"


def data_directory() -> Path:
    return default_schema_path().parent


def default_frontend_dist_dir() -> Path | None:
    """Directory containing the built SPA (``index.html`` + ``assets/``)."""
    override = os.environ.get("BANKING_CONTROL_FRONTEND_DIR")
    if override:
        dist = Path(override).expanduser().resolve()
        return dist if (dist / "index.html").is_file() else None

    for root in _unique_roots():
        dist = root / "frontend" / "dist"
        if (dist / "index.html").is_file():
            return dist

    return None


def default_db_path() -> Path:
    override = os.environ.get("BANKING_CONTROL_DB_PATH")
    if override:
        path = Path(override).expanduser()
        if path.is_absolute():
            return path.resolve()
        return (project_root() / path).resolve()

    data_override = os.environ.get("BANKING_CONTROL_DATA_DIR")
    if data_override:
        return Path(data_override).expanduser().resolve() / "banking_control.db"

    return data_directory() / "banking_control.db"
