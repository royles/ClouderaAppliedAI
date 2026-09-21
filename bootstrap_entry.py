"""Loaded via importlib from job scripts before ``customer360`` is on sys.path."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def bootstrap(script_file: str | None = None) -> Path:
    if cdsw := os.environ.get("CDSW_PROJECT"):
        root = Path(cdsw)
    else:
        root = None
        for candidate in (Path.cwd(), *Path.cwd().parents):
            if (candidate / "data" / "schema.sql").is_file():
                root = candidate
                break
        if root is None and script_file is not None:
            root = Path(script_file).resolve().parents[1]
        if root is None:
            root = Path.cwd()

    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return root
