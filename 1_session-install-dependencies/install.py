#!/usr/bin/env python3
"""CAI stage 1: install Python dependencies for Banking Control Solution."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    req = ROOT / "requirements.txt"
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req)])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", str(ROOT)])
    print("Banking Control dependencies installed.")


if __name__ == "__main__":
    main()
