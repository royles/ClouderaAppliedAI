"""Remove model chain-of-thought markup from user-visible assistant text."""

from __future__ import annotations

import re

_OPEN_THINK = "<" + "think>"
_CLOSE_THINK = "</" + "think>"

# Complete blocks (non-greedy), then unclosed openings, then orphan closers.
_BLOCK_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"<redacted_thinking\b[^>]*>[\s\S]*?</think>", re.IGNORECASE),
    re.compile(r"<thinking\b[^>]*>[\s\S]*?</thinking>", re.IGNORECASE),
    re.compile(r"<reasoning\b[^>]*>[\s\S]*?</reasoning>", re.IGNORECASE),
    re.compile(
        re.escape(_OPEN_THINK) + r"[\s\S]*?" + re.escape(_CLOSE_THINK),
        re.IGNORECASE,
    ),
    re.compile(r"<redacted_thinking\b[^>]*>[\s\S]*", re.IGNORECASE),
    re.compile(r"<thinking\b[^>]*>[\s\S]*", re.IGNORECASE),
    re.compile(r"<reasoning\b[^>]*>[\s\S]*", re.IGNORECASE),
    re.compile(re.escape(_OPEN_THINK) + r"[\s\S]*", re.IGNORECASE),
)

_FRAGMENT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"</?redacted_thinking\b[^>]*>", re.IGNORECASE),
    re.compile(r"</?thinking\b[^>]*>", re.IGNORECASE),
    re.compile(r"</?reasoning\b[^>]*>", re.IGNORECASE),
    re.compile(re.escape(_OPEN_THINK), re.IGNORECASE),
    re.compile(re.escape(_CLOSE_THINK), re.IGNORECASE),
)


def suppress_thinking_markup(text: str | None) -> str:
    if not text:
        return ""
    out = str(text)
    for _ in range(4):
        prev = out
        for pat in _BLOCK_PATTERNS:
            out = pat.sub("", out)
        for pat in _FRAGMENT_PATTERNS:
            out = pat.sub("", out)
        if out == prev:
            break
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()
