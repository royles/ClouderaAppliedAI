#!/usr/bin/env python3
"""
Start the Bedrock Playground backend and frontend.

Ensures Python and npm dependencies are installed, then launches:
  - FastAPI backend on http://localhost:8000 (Swagger at /docs)
  - Vite frontend on http://localhost:5173
"""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"
VENV_DIR = BACKEND_DIR / "venv"


def log(message: str) -> None:
    print(f"[start] {message}", flush=True)


def run(
    cmd: list[str],
    cwd: Path,
    *,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    log(f"running: {' '.join(cmd)} (in {cwd})")
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    result = subprocess.run(
        cmd,
        cwd=cwd,
        env=merged_env,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(cmd)}"
        )
    return result


def find_python() -> str:
    if sys.version_info >= (3, 10):
        return sys.executable
    raise RuntimeError("Python 3.10+ is required to run this script.")


def venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def ensure_backend_deps(python_exe: str, skip_install: bool) -> Path:
    if not VENV_DIR.exists():
        log("creating virtual environment at backend/venv")
        run([python_exe, "-m", "venv", str(VENV_DIR)], cwd=BACKEND_DIR)

    py = venv_python()
    if not py.exists():
        raise RuntimeError(f"Virtual environment python not found: {py}")

    if skip_install:
        return py

    requirements = BACKEND_DIR / "requirements.txt"
    marker = VENV_DIR / ".deps-installed"
    needs_install = not marker.exists()
    if marker.exists() and requirements.exists():
        needs_install = requirements.stat().st_mtime > marker.stat().st_mtime

    if needs_install:
        log("installing Python dependencies")
        run([str(py), "-m", "pip", "install", "--upgrade", "pip"], cwd=BACKEND_DIR)
        run(
            [str(py), "-m", "pip", "install", "-r", "requirements.txt"],
            cwd=BACKEND_DIR,
        )
        marker.write_text(str(time.time()))
    else:
        log("Python dependencies up to date")

    return py


def ensure_frontend_deps(skip_install: bool) -> None:
    if shutil.which("npm") is None:
        raise RuntimeError(
            "npm is not installed. Install Node.js (https://nodejs.org) and retry."
        )

    if skip_install:
        return

    node_modules = FRONTEND_DIR / "node_modules"
    package_json = FRONTEND_DIR / "package.json"
    package_lock = FRONTEND_DIR / "package-lock.json"

    needs_install = not node_modules.exists()
    if node_modules.exists():
        reference = package_lock if package_lock.exists() else package_json
        if reference.exists():
            needs_install = reference.stat().st_mtime > node_modules.stat().st_mtime

    if needs_install:
        log("installing frontend dependencies (npm install)")
        run(["npm", "install"], cwd=FRONTEND_DIR)
    else:
        log("frontend dependencies up to date")


def spawn(
    cmd: list[str],
    cwd: Path,
    env: dict[str, str] | None = None,
) -> subprocess.Popen[bytes]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    log(f"starting: {' '.join(cmd)}")
    return subprocess.Popen(
        cmd,
        cwd=cwd,
        env=merged_env,
        start_new_session=True,
    )


def stop_process(proc: subprocess.Popen[bytes] | None) -> None:
    if proc is None or proc.poll() is not None:
        return
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        proc.wait(timeout=10)
    except ProcessLookupError:
        pass
    except subprocess.TimeoutExpired:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        proc.wait(timeout=5)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install dependencies and start Bedrock Playground services.",
    )
    parser.add_argument(
        "--backend-only",
        action="store_true",
        help="Start only the FastAPI backend.",
    )
    parser.add_argument(
        "--frontend-only",
        action="store_true",
        help="Start only the Vite frontend.",
    )
    parser.add_argument(
        "--skip-install",
        action="store_true",
        help="Skip dependency installation checks.",
    )
    parser.add_argument(
        "--backend-port",
        type=int,
        default=8000,
        help="Backend port (default: 8000).",
    )
    parser.add_argument(
        "--frontend-port",
        type=int,
        default=5173,
        help="Frontend dev server port (default: 5173).",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Bind host for both services (default: 0.0.0.0).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.backend_only and args.frontend_only:
        log("error: use only one of --backend-only or --frontend-only")
        return 1

    start_backend = not args.frontend_only
    start_frontend = not args.backend_only

    backend_proc: subprocess.Popen[bytes] | None = None
    frontend_proc: subprocess.Popen[bytes] | None = None

    try:
        if start_backend:
            py = ensure_backend_deps(find_python(), args.skip_install)
            backend_proc = spawn(
                [
                    str(py),
                    "-m",
                    "uvicorn",
                    "app.main:app",
                    "--host",
                    args.host,
                    "--port",
                    str(args.backend_port),
                    "--reload",
                ],
                cwd=BACKEND_DIR,
            )

        if start_frontend:
            ensure_frontend_deps(args.skip_install)
            frontend_proc = spawn(
                [
                    "npm",
                    "run",
                    "dev",
                    "--",
                    "--host",
                    args.host,
                    "--port",
                    str(args.frontend_port),
                ],
                cwd=FRONTEND_DIR,
            )

        if backend_proc:
            log(f"backend:  http://localhost:{args.backend_port} (docs: /docs)")
        if frontend_proc:
            log(f"frontend: http://localhost:{args.frontend_port}")
        log("press Ctrl+C to stop")

        while True:
            if backend_proc and backend_proc.poll() is not None:
                raise RuntimeError("Backend process exited unexpectedly.")
            if frontend_proc and frontend_proc.poll() is not None:
                raise RuntimeError("Frontend process exited unexpectedly.")
            time.sleep(0.5)

    except KeyboardInterrupt:
        log("shutting down...")
        return 0
    except RuntimeError as exc:
        log(f"error: {exc}")
        return 1
    finally:
        stop_process(backend_proc)
        stop_process(frontend_proc)


if __name__ == "__main__":
    raise SystemExit(main())
