"""Cloudera AI runtime helpers (ports, project bootstrap)."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

from customer360.paths import project_root


def _run_bootstrap_entry() -> Path:
    for candidate in (Path.cwd(), *Path.cwd().parents):
        path = candidate / "bootstrap_entry.py"
        if path.is_file():
            spec = importlib.util.spec_from_file_location("bootstrap_entry", path)
            if spec is None or spec.loader is None:
                continue
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            try:
                return mod.bootstrap(__file__)
            except NameError:
                return mod.bootstrap(None)
    if cdsw := os.environ.get("CDSW_PROJECT"):
        root = Path(cdsw)
    else:
        root = project_root()
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return root


def ensure_project_on_path() -> Path:
    """Make the project importable when launched as a CAI application or job."""
    return _run_bootstrap_entry()


def application_port(default: str = "8080") -> str:
    """
    Port for HTTP applications.

    Cloudera AI Workbench/CML injects CDSW_APP_PORT; AI Inference uses APP_PORT (8080).
    """
    return os.environ.get("APP_PORT") or os.environ.get("CDSW_APP_PORT") or default
