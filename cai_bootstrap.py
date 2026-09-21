"""
Cloudera AI path bootstrap (see also identical logic in job entry scripts).

``__file__`` is only defined when code runs from a script file. Interactive
Workbench cells must use ``CDSW_PROJECT``, cwd, or ``%run path/to/script.py``.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def discover_project_root() -> Path:
    if cdsw := os.environ.get("CDSW_PROJECT"):
        return Path(cdsw)

    for candidate in (Path.cwd(), *Path.cwd().parents):
        if (candidate / "data" / "schema.sql").is_file():
            return candidate

    try:
        return Path(__file__).resolve().parent
    except NameError:
        return Path.cwd()


def ensure_sys_path() -> Path:
    root = discover_project_root()
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return root


def bootstrap_entry_script(script_file: str | None = None) -> Path:
    """
    Call from CAI job scripts before importing ``customer360``.

    ``script_file`` should be ``__file__`` when the job is run as a file; omit in
    notebooks (uses cwd / CDSW_PROJECT only).
    """
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
