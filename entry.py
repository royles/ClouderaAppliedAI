#!/usr/bin/env python3
"""
Cloudera AI application entry point.

Register this script when creating a Cloudera AI Application:
  Script: entry.py

It installs dependencies and starts the FastAPI backend plus Vite frontend.
"""

from start import main

if __name__ == "__main__":
    raise SystemExit(main())
