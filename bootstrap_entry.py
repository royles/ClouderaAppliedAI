"""Loaded via importlib from CAI scripts before ``banking_control`` is on sys.path."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _has_project_markers(root: Path) -> bool:
    root = root.resolve()
    return (root / "data" / "schema.sql").is_file() and (root / "banking_control").is_dir()


def discover_project_root(script_file: str | None = None) -> Path:
    """
    Locate the git project root on Cloudera AI.

    ``CDSW_PROJECT`` is not always the repo root (e.g. repo checked out into a subfolder).
    Prefer paths that contain ``data/schema.sql`` and ``banking_control/``.
    """
    ordered: list[Path] = []

    if script_file is not None:
        try:
            ordered.append(Path(script_file).resolve().parent.parent)
        except OSError:
            pass

    cwd = Path.cwd()
    ordered.extend([cwd, *cwd.parents])

    if cdsw := os.environ.get("CDSW_PROJECT"):
        cdsw_path = Path(cdsw)
        ordered.append(cdsw_path)
        try:
            for child in sorted(cdsw_path.iterdir()):
                if child.is_dir():
                    ordered.append(child)
        except OSError:
            pass

    seen: set[Path] = set()
    for candidate in ordered:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        if _has_project_markers(resolved):
            return resolved

    hints = [
        f"  cwd={cwd.resolve()}",
        f"  CDSW_PROJECT={os.environ.get('CDSW_PROJECT', '(unset)')}",
    ]
    if script_file is not None:
        hints.append(f"  script_file={script_file}")
    raise FileNotFoundError(
        "Could not locate the Banking Control project root (expected data/schema.sql and "
        "banking_control/).\n" + "\n".join(hints)
    )


def bootstrap(script_file: str | None = None) -> Path:
    root = discover_project_root(script_file)
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return root
