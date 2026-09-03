#!/usr/bin/env python3
"""
Start the Bedrock Playground backend and frontend.

Ensures Python and npm dependencies are installed, then launches:
  - FastAPI backend on http://127.0.0.1:{CDSW_READONLY_PORT or 8000}
  - Vite frontend on http://127.0.0.1:{CDSW_APP_PORT or 5173}
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
DEFAULT_FRONTEND_HOST = "127.0.0.1"
DEFAULT_BACKEND_HOST = "127.0.0.1"
DEFAULT_BACKEND_PORT = 8000
DEFAULT_FRONTEND_PORT = 5173
# Fixed loopback port for API traffic between Vite and FastAPI on CML/CDSW.
# CDSW_READONLY_PORT is for external readonly URLs and is not reliable for
# in-container proxy connections (EADDRNOTAVAIL on 127.0.0.1).
INTERNAL_API_PORT = 8000


def env_int(name: str, fallback: int) -> int:
    value = os.environ.get(name)
    if value:
        return int(value)
    return fallback


def default_frontend_port() -> int:
    """Use CDSW/CML app port when set by the platform."""
    return env_int("CDSW_APP_PORT", DEFAULT_FRONTEND_PORT)


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
        default=None,
        help="Backend port (default: CDSW_READONLY_PORT env var, else 8000).",
    )
    parser.add_argument(
        "--backend-host",
        default=DEFAULT_BACKEND_HOST,
        help=f"Backend bind host (default: {DEFAULT_BACKEND_HOST}).",
    )
    parser.add_argument(
        "--frontend-port",
        type=int,
        default=None,
        help="Frontend dev server port (default: CDSW_APP_PORT env var, else 5173).",
    )
    parser.add_argument(
        "--frontend-host",
        default=DEFAULT_FRONTEND_HOST,
        help=f"Frontend bind host (default: {DEFAULT_FRONTEND_HOST}).",
    )
    return parser.parse_args()


def is_cml_runtime() -> bool:
    return bool(os.environ.get("CDSW_APP_PORT"))


def resolve_backend_port(args: argparse.Namespace, start_frontend: bool) -> int:
    if args.backend_port is not None:
        return args.backend_port
    # When both services run on CML, keep API on a stable internal port.
    if is_cml_runtime() and start_frontend:
        return INTERNAL_API_PORT
    return env_int("CDSW_READONLY_PORT", INTERNAL_API_PORT)


def resolve_proxy_port(backend_port: int) -> int:
    """Port Vite uses to reach the API (always loopback-safe)."""
    if is_cml_runtime():
        return INTERNAL_API_PORT
    return backend_port


def wait_for_backend(host: str, port: int, timeout: float = 60.0) -> None:
    import urllib.error
    import urllib.request

    url = f"http://{host}:{port}/api/health"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    log(f"backend ready at {url}")
                    return
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(0.25)
    raise RuntimeError(f"Backend did not become ready at {url} within {timeout}s")


def use_reload() -> bool:
    # uvicorn --reload is unreliable on CML-managed ports.
    return not is_cml_runtime()


def resolve_frontend_port(args: argparse.Namespace) -> int:
    if args.frontend_port is not None:
        return args.frontend_port
    return default_frontend_port()


def main() -> int:
    args = parse_args()
    start_backend = not args.frontend_only
    start_frontend = not args.backend_only
    backend_port = resolve_backend_port(args, start_frontend)
    proxy_port = resolve_proxy_port(backend_port)
    frontend_port = resolve_frontend_port(args)

    if args.backend_only and args.frontend_only:
        log("error: use only one of --backend-only or --frontend-only")
        return 1

    if is_cml_runtime() and start_frontend and args.backend_port is None:
        log(
            f"CML runtime: API on internal port {backend_port}, "
            f"Vite proxies to {proxy_port} (CDSW_READONLY_PORT is not used for loopback)"
        )
    elif os.environ.get("CDSW_READONLY_PORT") and args.backend_port is None:
        log(f"using CDSW_READONLY_PORT={os.environ['CDSW_READONLY_PORT']} for backend")
    if os.environ.get("CDSW_APP_PORT") and args.frontend_port is None:
        log(f"using CDSW_APP_PORT={os.environ['CDSW_APP_PORT']} for frontend")

    backend_proc: subprocess.Popen[bytes] | None = None
    frontend_proc: subprocess.Popen[bytes] | None = None

    try:
        if start_backend:
            py = ensure_backend_deps(find_python(), args.skip_install)
            uvicorn_cmd = [
                str(py),
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                args.backend_host,
                "--port",
                str(backend_port),
            ]
            if use_reload():
                uvicorn_cmd.append("--reload")
            backend_proc = spawn(uvicorn_cmd, cwd=BACKEND_DIR)

        if start_frontend:
            if start_backend:
                wait_for_backend(args.backend_host, proxy_port)
            ensure_frontend_deps(args.skip_install)
            proxy_target = f"http://{args.backend_host}:{proxy_port}"
            frontend_env = {
                "BACKEND_PROXY_TARGET": proxy_target,
                "BACKEND_PROXY_PORT": str(proxy_port),
            }
            frontend_proc = spawn(
                [
                    "npm",
                    "run",
                    "dev",
                    "--",
                    "--host",
                    args.frontend_host,
                    "--port",
                    str(frontend_port),
                ],
                cwd=FRONTEND_DIR,
                env=frontend_env,
            )

        if backend_proc:
            log(
                f"backend:  http://{args.backend_host}:{backend_port} (docs: /docs)"
            )
        if frontend_proc:
            log(f"frontend: http://{args.frontend_host}:{frontend_port}")
            if start_backend:
                log(f"api proxy: {proxy_target} (/api, /docs)")
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
