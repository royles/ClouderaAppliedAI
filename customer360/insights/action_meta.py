"""Map insight recommendation lines to actionable outreach kinds."""

from __future__ import annotations

from customer360.actions.draft import classify_recommendation


def insight_action_meta(text: str) -> dict:
    kind = classify_recommendation(text)
    return {"text": text, "actionable": kind is not None, "action_kind": kind}


def experience_note_actionable(note: str) -> bool:
    if not note.strip():
        return False
    if classify_recommendation(note):
        return True
    lowered = note.lower()
    return any(token in lowered for token in ("email", "call", "message", "sms", "callback"))
