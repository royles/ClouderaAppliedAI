"""Control code normalization for catalog lookups."""

from __future__ import annotations

import re

# AML1, aml-1, AML_001 → AML-001
_COMPACT = re.compile(r"^([A-Za-z]{2,10})[-_]?(\d{1,4})$")
_CANONICAL = re.compile(r"^([A-Z]{2,10})-(\d{3,4})$")


def control_code_candidates(raw: str) -> list[str]:
    """Ordered candidates to try when resolving a user/LLM control code."""
    text = (raw or "").strip()
    if not text:
        return []

    seen: set[str] = set()
    out: list[str] = []

    def add(code: str) -> None:
        c = code.strip()
        if not c or c in seen:
            return
        seen.add(c)
        out.append(c)

    add(text)
    add(text.replace("_", "-"))
    add(text.replace("_", "-").upper())

    upper = text.replace("_", "-").upper()
    m = _CANONICAL.match(upper)
    if m:
        domain, num = m.group(1), m.group(2)
        add(f"{domain}-{int(num):03d}")

    compact = upper.replace("-", "")
    m2 = re.match(r"^([A-Z]{2,10})(\d{1,4})$", compact)
    if m2:
        domain, num = m2.group(1), m2.group(2)
        add(f"{domain}-{int(num):03d}")

    m3 = _COMPACT.match(text.replace("_", "-"))
    if m3:
        domain, num = m3.group(1).upper(), m3.group(2)
        add(f"{domain}-{int(num):03d}")

    return out


def normalize_control_code(raw: str) -> str | None:
    candidates = control_code_candidates(raw)
    return candidates[-1] if candidates else None


def suggest_control_codes(raw: str, known_codes: list[str], *, limit: int = 5) -> list[str]:
    """Best-effort suggestions when lookup fails."""
    text = (raw or "").strip().upper().replace("_", "-")
    prefix = re.sub(r"[\d-].*", "", text.replace("-", "")) or text[:3]
    scored: list[tuple[int, str]] = []
    for code in known_codes:
        score = 0
        if code.upper().startswith(prefix):
            score += 10
        if text and text in code.upper().replace("-", ""):
            score += 5
        if score:
            scored.append((score, code))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [c for _, c in scored[:limit]]
