#!/usr/bin/env python3
"""
Bedrock Playground — start backend + frontend.

Cloudera AI (no npm):
  1. pip install into backend/venv
  2. FastAPI serves API + pre-built UI on CDSW_APP_PORT

Local dev (with npm):
  1. pip + npm install
  2. FastAPI on :8000, Vite dev server on :5173 (Vite proxies /api)
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

ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"
VENV_DIR = BACKEND_DIR / "venv"
FRONTEND_DIST = FRONTEND_DIR / "dist"

HOST = "127.0.0.1"
DEV_API_PORT = 8000
APP_PORT = int(os.environ.get("CDSW_APP_PORT", "5173"))
ON_CLOUDERA_AI = "CDSW_APP_PORT" in os.environ


def log(message: str) -> None:
    print(f"[start] {message}", flush=True)


def venv_python() -> Path:
    name = "Scripts/python.exe" if os.name == "nt" else "bin/python"
    return VENV_DIR / name


def has_npm() -> bool:
    return shutil.which("npm") is not None


def has_built_frontend() -> bool:
    return (FRONTEND_DIST / "index.html").exists()


def use_single_server() -> bool:
    """CAI and other npm-less environments serve UI+API from FastAPI."""
    return ON_CLOUDERA_AI or (not has_npm() and has_built_frontend())


def pip_env() -> dict[str, str]:
    env = os.environ.copy()
    for key in ("PIP_USER", "PIP_USER_SITE"):
        env.pop(key, None)
    env["PIP_USER"] = "0"
    env["PYTHONNOUSERSITE"] = "1"
    return env


def run_checked(cmd: list[str], cwd: Path) -> None:
    log("$ " + " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True, env=pip_env())


def ensure_venv() -> Path:
    if not VENV_DIR.exists():
        log("creating backend/venv")
        run_checked([sys.executable, "-m", "venv", str(VENV_DIR)], BACKEND_DIR)
    python = venv_python()
    if not python.exists():
        raise RuntimeError(f"venv python not found at {python}")
    return python


def install_python(skip: bool) -> Path:
    if skip:
        return ensure_venv()
    python = ensure_venv()
    log("installing Python packages into backend/venv")
    run_checked([str(python), "-m", "pip", "install", "--upgrade", "pip"], BACKEND_DIR)
    run_checked([str(python), "-m", "pip", "install", "-r", "requirements.txt"], BACKEND_DIR)
    return python


def install_frontend_dev(skip: bool) -> None:
    if skip:
        return
    if not has_npm():
        if has_built_frontend():
            log("using pre-built frontend/dist (npm not required)")
            return
        raise RuntimeError(
            "npm is not installed and frontend/dist is missing. "
            "Run 'cd frontend && npm install && npm run build' locally, then commit dist."
        )
    if not (FRONTEND_DIR / "node_modules").exists():
        log("installing frontend packages")
        run_checked(["npm", "install"], FRONTEND_DIR)


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


def wait_for_api(port: int, timeout: float = 120) -> None:
    url = f"http://{HOST}:{port}/api/health"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    log(f"ready at {url}")
                    return
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(0.25)
    raise RuntimeError(f"server did not start within {timeout}s ({url})")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start Bedrock Playground")
    parser.add_argument("--skip-install", action="store_true", help="Skip pip/npm install")
    args, unknown = parser.parse_known_args()
    if unknown:
        log("ignoring extra arguments: " + " ".join(unknown))
    return args


def main() -> int:
    args = parse_args()
    single = use_single_server()
    api_proc = None
    ui_proc = None

    try:
        python = install_python(args.skip_install)

        if single:
            if not has_built_frontend():
                raise RuntimeError(
                    "frontend/dist is missing. Build locally: cd frontend && npm run build"
                )
            log(f"Cloudera AI / production mode — one server on port {APP_PORT}")
            api_cmd = [
                str(python), "-m", "uvicorn", "app.main:app",
                "--host", HOST, "--port", str(APP_PORT),
            ]
            api_proc = start_process(api_cmd, BACKEND_DIR)
            wait_for_api(APP_PORT)
            log(f"open the Application URL (API + UI on :{APP_PORT}, docs at /docs)")
        else:
            install_frontend_dev(args.skip_install)
            log(f"dev mode — API :{DEV_API_PORT}, Vite :{APP_PORT}")
            api_cmd = [
                str(python), "-m", "uvicorn", "app.main:app",
                "--host", HOST, "--port", str(DEV_API_PORT), "--reload",
            ]
            api_proc = start_process(api_cmd, BACKEND_DIR)
            wait_for_api(DEV_API_PORT)
            ui_proc = start_process(
                ["npm", "run", "dev", "--", "--host", HOST, "--port", str(APP_PORT)],
                FRONTEND_DIR,
                extra_env={
                    "BACKEND_PROXY_TARGET": f"http://{HOST}:{DEV_API_PORT}",
                    "BACKEND_PROXY_PORT": str(DEV_API_PORT),
                },
            )
            log(f"UI http://{HOST}:{APP_PORT}  API http://{HOST}:{DEV_API_PORT}")

        log("press Ctrl+C to stop")
        while True:
            if api_proc.poll() is not None:
                raise RuntimeError("server exited unexpectedly")
            if ui_proc and ui_proc.poll() is not None:
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
