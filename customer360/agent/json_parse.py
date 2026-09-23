"""Parse executive-assistant model output (JSON with tolerant recovery)."""

from __future__ import annotations

import json
import re
from typing import Any


def _strip_markdown_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.IGNORECASE)
        stripped = re.sub(r"\s*```\s*$", "", stripped)
    return stripped.strip()


def load_first_json_object(text: str) -> dict[str, Any]:
    """
    Parse the first JSON object from model text; tolerate fences, leading prose,
    and trailing commentary (common with PrivateAI / local models).
    """
    stripped = _strip_markdown_fences(text)
    if not stripped:
        raise ValueError("Empty model response")

    decoder = json.JSONDecoder()
    for candidate in (stripped, stripped[stripped.find("{") :] if "{" in stripped else ""):
        if not candidate or not candidate.lstrip().startswith("{"):
            continue
        try:
            data, _end = decoder.raw_decode(candidate.lstrip())
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            continue

    match = re.search(r"\{[\s\S]*\}", stripped)
    if match:
        try:
            data, _end = decoder.raw_decode(match.group(0))
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass

    raise ValueError("Model did not return a JSON object")


def parse_final_json(text: str) -> dict[str, Any]:
    """Backward-compatible alias used by the Bedrock tool loop."""
    return load_first_json_object(text)
