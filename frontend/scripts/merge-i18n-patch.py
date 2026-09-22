#!/usr/bin/env python3
"""Deep-merge i18n-patch-*.json into en.json / he.json."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src" / "locales"


def deep_merge(base: dict, patch: dict) -> dict:
    for key, val in patch.items():
        if key in base and isinstance(base[key], dict) and isinstance(val, dict):
            deep_merge(base[key], val)
        else:
            base[key] = val
    return base


def main() -> None:
    for lang in ("en", "he"):
        target = ROOT / f"{lang}.json"
        patch_path = ROOT / f"i18n-patch-{lang}.json"
        if not patch_path.is_file():
            continue
        data = json.loads(target.read_text(encoding="utf-8"))
        patch = json.loads(patch_path.read_text(encoding="utf-8"))
        deep_merge(data, patch)
        target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Merged {patch_path.name} -> {target.name}")


if __name__ == "__main__":
    main()
