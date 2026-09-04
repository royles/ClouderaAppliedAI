#!/usr/bin/env python3
"""Cloudera AI application entry point. Register as Application script: entry.py"""

import sys


def _run() -> int:
    from start import main

    return main()


if __name__ == "__main__":
    # CAI may launch via ipykernel with: -f /tmp/jupyter/runtime/kernel-*.json
    sys.argv = [sys.argv[0]]
    raise SystemExit(_run())
