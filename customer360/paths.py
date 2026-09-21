"""Project paths that resolve correctly in Cloudera AI engines and local dev."""

from __future__ import annotations

import os
from pathlib import Path


def project_root() -> Path:
    """Return the CAI project root without relying on the caller's ``__file__``."""
    try:
        from cai_bootstrap import discover_project_root

        return discover_project_root()
    except ImportError:
        if cdsw := os.environ.get("CDSW_PROJECT"):
            return Path(cdsw)
        for candidate in (Path.cwd(), *Path.cwd().parents):
            if (candidate / "data" / "schema.sql").is_file():
                return candidate
        try:
            return Path(__file__).resolve().parent.parent
        except NameError:
            return Path.cwd()


def schema_path() -> Path:
    return project_root() / "data" / "schema.sql"


def default_db_path() -> Path:
    """SQLite file path; override with CUSTOMER360_DB_PATH (relative to project root)."""
    raw = os.environ.get("CUSTOMER360_DB_PATH", "data/customer360.db")
    path = Path(raw)
    if not path.is_absolute():
        path = project_root() / path
    return path
