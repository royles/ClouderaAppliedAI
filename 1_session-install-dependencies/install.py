"""CAI job: Python 3.11 deps, editable package install, and React production build."""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path


def _bootstrap() -> Path:
    for candidate in (Path.cwd(), *Path.cwd().parents):
        path = candidate / "bootstrap_entry.py"
        if not path.is_file():
            continue
        spec = importlib.util.spec_from_file_location("bootstrap_entry", path)
        if spec is None or spec.loader is None:
            continue
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        try:
            return mod.bootstrap(__file__)
        except NameError:
            return mod.bootstrap(None)
    raise RuntimeError("Project root not found (bootstrap_entry.py).")


ROOT = _bootstrap().resolve()
REQ = (ROOT / "1_session-install-dependencies" / "requirements.txt").resolve()
FRONTEND = (ROOT / "frontend").resolve()


def run(cmd: list[str], *, cwd: Path | None = None) -> None:
    print("Running:", " ".join(cmd), flush=True)
    subprocess.check_call(cmd, cwd=str(cwd or ROOT))


def main() -> None:
    print(f"Project root: {ROOT}", flush=True)

    if not REQ.is_file():
        raise FileNotFoundError(
            f"Requirements file not found: {REQ}\n"
            f"Check that the session working directory is the repo (e.g. midgalpoc/) "
            f"or that CDSW_PROJECT points at the folder containing data/schema.sql."
        )

    if sys.version_info[:2] != (3, 11):
        print(
            f"Warning: this project targets Python 3.11; current interpreter is "
            f"{sys.version_info.major}.{sys.version_info.minor}",
            flush=True,
        )

    run([sys.executable, "-m", "pip", "install", "-r", str(REQ)])
    run([sys.executable, "-m", "pip", "install", "-e", str(ROOT)])

    npm = shutil.which("npm")
    if not npm or not FRONTEND.is_dir():
        print("Skipping frontend build (npm or frontend/ missing).", flush=True)
        return

    if (FRONTEND / "package-lock.json").is_file():
        run([npm, "ci"], cwd=FRONTEND)
    else:
        run([npm, "install"], cwd=FRONTEND)
    run([npm, "run", "build"], cwd=FRONTEND)


if __name__ == "__main__":
    main()
