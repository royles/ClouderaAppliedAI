"""Locate or bootstrap Node.js/npm for frontend builds on CAI (no root required)."""

from __future__ import annotations

import os
import platform
import shutil
import stat
import subprocess
import tarfile
import urllib.request
from pathlib import Path


DEFAULT_NODE_VERSION = "20.18.0"


def _platform_archive() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    if system == "linux" and machine in ("x86_64", "amd64"):
        return "linux-x64"
    if system == "darwin" and machine == "arm64":
        return "darwin-arm64"
    if system == "darwin" and machine == "x86_64":
        return "darwin-x64"
    raise RuntimeError(f"Unsupported platform for bundled Node.js: {system} {machine}")


def find_npm() -> Path | None:
    npm = shutil.which("npm")
    if npm:
        return Path(npm)
    for candidate in (
        Path("/usr/local/bin/npm"),
        Path("/opt/nodejs/bin/npm"),
    ):
        if candidate.is_file():
            return candidate
    return None


def portable_node_dir(project_root: Path) -> Path:
    version = os.environ.get("CUSTOMER360_NODE_VERSION", DEFAULT_NODE_VERSION)
    archive = _platform_archive()
    return project_root / ".tools" / f"node-v{version}-{archive}"


def ensure_portable_npm(project_root: Path) -> Path:
    existing = find_npm()
    if existing is not None:
        return existing

    version = os.environ.get("CUSTOMER360_NODE_VERSION", DEFAULT_NODE_VERSION)
    archive = _platform_archive()
    extract_dir = portable_node_dir(project_root)
    npm = extract_dir / "bin" / "npm"
    if npm.is_file():
        return npm

    extract_dir.parent.mkdir(parents=True, exist_ok=True)
    tarball_name = f"node-v{version}-{archive}.tar.xz"
    url = f"https://nodejs.org/dist/v{version}/{tarball_name}"
    tarball_path = extract_dir.parent / tarball_name

    print(f"Downloading Node.js {version} ({archive}) for frontend build…", flush=True)
    urllib.request.urlretrieve(url, tarball_path)

    with tarfile.open(tarball_path, "r:xz") as tar:
        tar.extractall(path=extract_dir.parent)

    for name in ("node", "npm", "npx"):
        binary = extract_dir / "bin" / name
        if binary.is_file():
            binary.chmod(binary.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    tarball_path.unlink(missing_ok=True)
    if not npm.is_file():
        raise RuntimeError(f"Portable Node install failed; missing {npm}")
    return npm


def npm_env(npm: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["PATH"] = str(npm.parent) + os.pathsep + env.get("PATH", "")
    return env


def run_npm(npm: Path, args: list[str], *, cwd: Path) -> None:
    subprocess.check_call([str(npm), *args], cwd=str(cwd), env=npm_env(npm))
