"""Bootstrap imports before ``pip install -e`` (CAI session install, notebook cells)."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path


def _path_seeds(script_file: str | Path | None) -> list[Path]:
    seeds: list[Path] = []
    if script_file:
        seeds.append(Path(script_file).resolve().parent.parent)
    for key in ("CDSW_PROJECT", "BANKING_CONTROL_PROJECT"):
        env = os.environ.get(key)
        if env:
            seeds.append(Path(env).expanduser().resolve())
    seeds.append(Path.cwd())
    return seeds


def discover_project_root(script_file: str | Path | None = None) -> Path:
    for seed in _path_seeds(script_file):
        for candidate in (seed, *seed.parents):
            if (candidate / "requirements.txt").is_file() and (candidate / "banking_control").is_dir():
                return candidate
    return Path.cwd()


def ensure_project_on_path(script_file: str | Path | None = None) -> Path:
    """Return repo root and ensure it is on ``sys.path`` (loads ``paths.py`` if needed)."""
    try:
        from banking_control.paths import discover_project_root as _discover

        root = _discover(script_file)
    except ImportError:
        root = discover_project_root(script_file)
        paths_file = root / "banking_control" / "paths.py"
        if not paths_file.is_file():
            raise RuntimeError(
                f"Cannot locate banking_control/paths.py under {root}. "
                "Set CDSW_PROJECT to the repository root or run from the project directory."
            ) from None
        spec = importlib.util.spec_from_file_location("banking_control.paths", paths_file)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Cannot load {paths_file}") from None
        mod = importlib.util.module_from_spec(spec)
        sys.modules["banking_control.paths"] = mod
        spec.loader.exec_module(mod)
        root = mod.discover_project_root(script_file)

    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return root
