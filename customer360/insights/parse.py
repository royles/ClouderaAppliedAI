"""Parse LLM JSON for customer insights (narrative + optional action sentences)."""

from __future__ import annotations

import json
import re


def parse_insight_json(text: str) -> dict:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError as exc:
        match = re.search(r"\{[\s\S]*\}", stripped)
        if not match:
            raise ValueError("Model did not return JSON") from exc
        data = json.loads(match.group(0))

    preamble = str(data.get("preamble", "")).strip()
    summary = str(data.get("summary", "")).strip()
    primary = str(data.get("primary_focus", "")).strip().lower()
    if primary not in ("upsell", "retention"):
        primary = "retention" if primary.startswith("ret") else "upsell"

    guidance = str(data.get("guidance", "")).strip()
    raw_actions = data.get("suggested_actions") or data.get("recommendations") or []
    suggested_actions = [str(r).strip() for r in raw_actions if str(r).strip()][:5]

    experience = str(data.get("experience_note", "")).strip()

    if not summary:
        raise ValueError("Incomplete insight JSON from model")
    if not guidance and suggested_actions:
        guidance = " ".join(suggested_actions)
    if not guidance:
        raise ValueError("Incomplete insight JSON from model (missing guidance)")

    if not suggested_actions:
        suggested_actions = _sentences_from_guidance(guidance)

    return {
        "preamble": preamble,
        "summary": summary,
        "primary_focus": primary,
        "guidance": guidance,
        "recommendations": suggested_actions,
        "experience_note": experience,
    }


def _sentences_from_guidance(guidance: str) -> list[str]:
    """Fallback action lines when the model omits suggested_actions."""
    parts = re.split(r"(?<=[.!?])\s+", guidance.strip())
    sentences = [p.strip() for p in parts if len(p.strip()) >= 24]
    return sentences[:4] if sentences else [guidance[:240]]
