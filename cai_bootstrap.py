"""
Cloudera AI path bootstrap helpers.

Job scripts load ``bootstrap_entry.py`` via importlib before importing ``customer360``.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_bootstrap_module() -> object:
    for candidate in (Path.cwd(), *Path.cwd().parents):
        path = candidate / "bootstrap_entry.py"
        if path.is_file():
            spec = importlib.util.spec_from_file_location("bootstrap_entry", path)
            if spec is None or spec.loader is None:
                continue
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
    raise ImportError("bootstrap_entry.py not found")


def discover_project_root() -> Path:
    mod = _load_bootstrap_module()
    try:
        return mod.discover_project_root(__file__)  # type: ignore[attr-defined]
    except NameError:
        return mod.discover_project_root(None)  # type: ignore[attr-defined]


def ensure_sys_path() -> Path:
    mod = _load_bootstrap_module()
    try:
        return mod.bootstrap(__file__)  # type: ignore[attr-defined]
    except NameError:
        return mod.bootstrap(None)  # type: ignore[attr-defined]
