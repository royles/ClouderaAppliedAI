#!/usr/bin/env python3
"""Regenerate demo customer headshot SVGs (20 variants) for frontend/public."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "frontend" / "src" / "assets" / "customer-avatars"

PALETTES = [
    ("#e8eef4", "#f0c8a8", "#3d2914", "#0f6db8", "#134a6e"),
    ("#eef6fc", "#e8b896", "#1a1a1a", "#5c3888", "#4a2d6e"),
    ("#f4effa", "#d4a574", "#6b4423", "#3d9a6a", "#1e5c44"),
    ("#faf0f2", "#f5d0b5", "#8b4513", "#c25565", "#7a2e3a"),
    ("#eef8f2", "#c68642", "#2c1810", "#0f6db8", "#0f3d5e"),
    ("#f5f0e8", "#ffdbac", "#4a3728", "#7c52a8", "#5c3888"),
    ("#e6f2ec", "#e0ac69", "#000000", "#267052", "#1e5c44"),
    ("#ede8f5", "#f1c27d", "#a52a2a", "#943848", "#7a2e3a"),
    ("#e8eef4", "#8d5524", "#1c1c1c", "#134a6e", "#0f6db8"),
    ("#eef6fc", "#c58c85", "#654321", "#3d9a6a", "#267052"),
    ("#f4effa", "#ffcd94", "#2f1810", "#5c3888", "#7c52a8"),
    ("#faf0f2", "#e0b090", "#5c4033", "#c25565", "#943848"),
    ("#eef8f2", "#bf9169", "#0d0d0d", "#1e5c44", "#3d9a6a"),
    ("#f5f0e8", "#deb887", "#3b2f2f", "#0f3d5e", "#134a6e"),
    ("#e6f2ec", "#f5cba7", "#6a3805", "#267052", "#3d9a6a"),
    ("#ede8f5", "#d2a679", "#201912", "#4a2d6e", "#5c3888"),
    ("#e8eef4", "#eac086", "#4b3621", "#0f6db8", "#5a9fd4"),
    ("#eef6fc", "#f4c2a8", "#252525", "#3d9a6a", "#6bb892"),
    ("#f4effa", "#b97a57", "#1b1108", "#7c52a8", "#a888c8"),
    ("#faf0f2", "#ffdab9", "#8b6914", "#c25565", "#d88a96"),
]

HAIR_STYLES = [
    "short",
    "long",
    "curly",
    "bun",
    "side",
    "bald",
    "wavy",
    "pixie",
] * 2 + ["short", "long", "curly", "bun"]


def hair_path(style: str, cx: int, cy: int) -> str:
    if style == "bald":
        return ""
    if style == "long":
        return (
            f'<path d="M{cx - 42} {cy - 5} Q{cx - 45} {cy - 55} {cx} {cy - 62} '
            f'Q{cx + 45} {cy - 55} {cx + 42} {cy - 5} Q{cx + 38} {cy + 25} {cx + 28} {cy + 35} '
            f'L{cx - 28} {cy + 35} Q{cx - 38} {cy + 25} {cx - 42} {cy - 5} Z" class="hair"/>'
        )
    if style == "curly":
        curls = "".join(
            f'<circle cx="{cx + ox}" cy="{cy - 48 - i * 2}" r="12" class="hair"/>'
            for i, ox in enumerate([-30, -15, 0, 15, 30])
        )
        return curls + f'<ellipse cx="{cx}" cy="{cy - 35}" rx="40" ry="28" class="hair"/>'
    if style == "bun":
        return (
            f'<ellipse cx="{cx}" cy="{cy - 35}" rx="38" ry="30" class="hair"/>'
            f'<circle cx="{cx}" cy="{cy - 58}" r="14" class="hair"/>'
        )
    if style == "side":
        return (
            f'<path d="M{cx - 40} {cy - 10} Q{cx - 48} {cy - 50} {cx - 5} {cy - 58} '
            f'Q{cx + 35} {cy - 45} {cx + 38} {cy - 5} Q{cx + 20} {cy - 20} {cx - 40} {cy - 10} Z" class="hair"/>'
        )
    if style == "wavy":
        return (
            f'<path d="M{cx - 41} {cy - 8} C{cx - 50} {cy - 45} {cx - 20} {cy - 65} {cx} {cy - 58} '
            f'C{cx + 20} {cy - 65} {cx + 50} {cy - 45} {cx + 41} {cy - 8} Z" class="hair"/>'
        )
    if style == "pixie":
        return (
            f'<path d="M{cx - 38} {cy - 5} Q{cx - 42} {cy - 40} {cx} {cy - 52} '
            f'Q{cx + 42} {cy - 40} {cx + 38} {cy - 5} L{cx + 30} {cy + 5} Q{cx} {cy - 15} {cx - 30} {cy + 5} Z" class="hair"/>'
        )
    return f'<ellipse cx="{cx}" cy="{cy - 38}" rx="40" ry="32" class="hair"/>'


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cx, cy = 64, 72
    for i, (bg, skin, hair, shirt, accent) in enumerate(PALETTES, start=1):
        style = HAIR_STYLES[i - 1]
        svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" role="img" aria-hidden="true">
  <defs>
    <linearGradient id="bg{i}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{bg}"/>
      <stop offset="100%" stop-color="{accent}" stop-opacity="0.18"/>
    </linearGradient>
  </defs>
  <style>
    .bg {{ fill: url(#bg{i}); }}
    .shirt {{ fill: {shirt}; }}
    .skin {{ fill: {skin}; }}
    .hair {{ fill: {hair}; }}
    .feature {{ fill: {accent}; opacity: 0.85; }}
  </style>
  <rect width="128" height="128" rx="16" class="bg"/>
  <ellipse cx="{cx}" cy="118" rx="52" ry="28" class="shirt"/>
  <ellipse cx="{cx}" cy="{cy}" rx="34" ry="38" class="skin"/>
  {hair_path(style, cx, cy)}
  <ellipse cx="{cx - 12}" cy="{cy - 5}" rx="4" ry="5" class="feature"/>
  <ellipse cx="{cx + 12}" cy="{cy - 5}" rx="4" ry="5" class="feature"/>
  <path d="M{cx - 14} {cy + 18} Q{cx} {cy + 26} {cx + 14} {cy + 18}" fill="none" stroke="{accent}" stroke-width="2.5" stroke-linecap="round" opacity="0.7"/>
</svg>
"""
        (OUT / f"avatar-{i:02d}.svg").write_text(svg, encoding="utf-8")
    print(f"Wrote {len(PALETTES)} avatars to {OUT}")


if __name__ == "__main__":
    main()
