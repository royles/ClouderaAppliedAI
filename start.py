#!/usr/bin/env python3
"""
Bedrock Playground — start backend + frontend.

What this does (in order):
  1. Install Python and npm dependencies (unless --skip-install)
  2. Start FastAPI on 127.0.0.1:8000
  3. Start Vite on 127.0.0.1:5173  (or CDSW_APP_PORT on Cloudera AI)
  4. Vite proxies /api and /docs to the backend

Cloudera AI: register entry.py as the Application script.
"""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# --- paths -------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"
VENV_DIR = BACKEND_DIR / "venv"

# --- networking (one place to read) ------------------------------------------

HOST = "127.0.0.1"
API_PORT = 8000
FRONTEND_PORT = int(os.environ.get("CDSW_APP_PORT", "5173"))
ON_CLOUDERA_AI = "CDSW_APP_PORT" in os.environ
API_URL = f"http://{HOST}:{API_PORT}"


def log(message: str) -> None:
    print(f"[start] {message}", flush=True)


def venv_python() -> Path:
    name = "Scripts/python.exe" if os.name == "nt" else "bin/python"
    return VENV_DIR / name


def run_checked(cmd: list[str], cwd: Path) -> None:
    log("$ " + " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def install_dependencies(skip: bool) -> Path:
    """Create venv, pip install, npm install."""
    if skip:
        return venv_python()

    if not VENV_DIR.exists():
        log("creating backend/venv")
        run_checked([sys.executable, "-m", "venv", str(VENV_DIR)], BACKEND_DIR)

    python = venv_python()
    log("installing Python packages")
    run_checked([str(python), "-m", "pip", "install", "-r", "requirements.txt"], BACKEND_DIR)

    if shutil.which("npm") is None:
        raise RuntimeError("npm is not installed — use a runtime with Node.js")

    if not (FRONTEND_DIR / "node_modules").exists():
        log("installing frontend packages")
        run_checked(["npm", "install"], FRONTEND_DIR)

    return python


def start_process(cmd: list[str], cwd: Path, extra_env: dict[str, str] | None = None):
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    log("-> " + " ".join(cmd))
    return subprocess.Popen(cmd, cwd=cwd, env=env, start_new_session=True)


def stop_process(proc: subprocess.Popen | None) -> None:
    if proc is None or proc.poll() is not None:
        return
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        proc.wait(timeout=10)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except ProcessLookupError:
            pass


def wait_for_api(timeout: float = 60) -> None:
    url = f"{API_URL}/api/health"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    log(f"backend ready ({url})")
                    return
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(0.25)
    raise RuntimeError(f"backend did not start within {timeout}s ({url})")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start Bedrock Playground")
    parser.add_argument("--skip-install", action="store_true", help="Skip pip/npm install")
    args, unknown = parser.parse_known_args()
    if unknown:
        log("ignoring extra arguments: " + " ".join(unknown))
    return args


def main() -> int:
    args = parse_args()

    if ON_CLOUDERA_AI:
        log(f"Cloudera AI detected — UI port {FRONTEND_PORT}, API port {API_PORT}")
    else:
        log(f"local dev — UI http://{HOST}:{FRONTEND_PORT}, API {API_URL}")

    api_proc = None
    ui_proc = None

    try:
        python = install_dependencies(args.skip_install)

        api_cmd = [
            str(python), "-m", "uvicorn", "app.main:app",
            "--host", HOST, "--port", str(API_PORT),
        ]
        if not ON_CLOUDERA_AI:
            api_cmd.append("--reload")

        api_proc = start_process(api_cmd, BACKEND_DIR)
        wait_for_api()

        ui_proc = start_process(
            ["npm", "run", "dev", "--", "--host", HOST, "--port", str(FRONTEND_PORT)],
            FRONTEND_DIR,
            extra_env={
                "BACKEND_PROXY_TARGET": API_URL,
                "BACKEND_PROXY_PORT": str(API_PORT),
            },
        )

        log(f"running — open the app URL (UI :{FRONTEND_PORT}, swagger /docs)")
        log("press Ctrl+C to stop")

        while True:
            if api_proc.poll() is not None:
                raise RuntimeError("backend exited unexpectedly")
            if ui_proc.poll() is not None:
                raise RuntimeError("frontend exited unexpectedly")
            time.sleep(0.5)

    except KeyboardInterrupt:
        log("stopping...")
        return 0
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        log(f"error: {exc}")
        return 1
    finally:
        stop_process(ui_proc)
        stop_process(api_proc)


if __name__ == "__main__":
    raise SystemExit(main())
