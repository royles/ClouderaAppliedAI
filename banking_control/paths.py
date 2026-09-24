from __future__ import annotations

import os
from pathlib import Path


def project_root() -> Path:
    env = os.environ.get("CDSW_PROJECT") or os.environ.get("BANKING_CONTROL_PROJECT")
    if env:
        return Path(env).resolve()
    here = Path(__file__).resolve().parent.parent
    return here


def default_db_path() -> Path:
    override = os.environ.get("BANKING_CONTROL_DB_PATH")
    if override:
        return Path(override).expanduser().resolve()
    return project_root() / "data" / "banking_control.db"
